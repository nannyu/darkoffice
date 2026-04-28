/**
 * 暗黑职场 — TypeScript 规则引擎核心
 *
 * 纯函数实现，对照 Python runtime/engine.py
 * 引擎不直接读写数据库，输入完整、输出完整
 */

import type {
  ActionType,
  Character,
  ContentContext,
  Event,
  FailureType,
  GameEnding,
  GamePrompt,
  GameSession,
  Hazard,
  HazardMapEntry,
  Project,
  ResolveTurnInput,
  ResolveTurnOutput,
  ResourceState,
  ResultTier,
  StatusEffect,
  TurnLog,
} from '../types/game';

import { ACTION_MODIFIERS, buildOptions } from '../rules/actions';
import { EVENT_HAZARD_MAP, ACTION_HAZARD_MAP } from '../rules/hazards';
import { INITIAL_STATE, TURNS_PER_DAY, defaultProject } from '../rules/resources';
import { resolutionTierForScore } from '../rules/resolution';
import { timePeriodForTurn, timePeriodWeightModifiers } from '../rules/time-period';
import { CHARACTER_NAME_MAP, CHARACTERS } from '../content/characters';
import { EVENTS_BY_CHARACTER, GENERIC_EVENT } from '../content/events';

// ---------------------------------------------------------------------------
// 辅助函数
// ---------------------------------------------------------------------------

/** 数值夹紧 0-100 */
export function clampState(state: ResourceState): ResourceState {
  return {
    hp: Math.max(0, Math.min(100, state.hp)),
    en: Math.max(0, Math.min(100, state.en)),
    st: Math.max(0, Math.min(100, state.st)),
    kpi: Math.max(0, Math.min(100, state.kpi)),
    risk: Math.max(0, Math.min(100, state.risk)),
    cor: Math.max(0, Math.min(100, state.cor)),
  };
}

/** 状态修正值 */
function statusModifier(state: ResourceState): number {
  let mod = 0;
  if (state.en >= 70) mod += 2;
  else if (state.en < 10) mod -= 5;
  else if (state.en < 30) mod -= 2;
  if (state.st < 30) mod -= 1;
  if (state.kpi < 40) mod -= 1;
  if (state.risk >= 50) mod -= 1;
  return mod;
}

/** 推导持续状态 */
function deriveStatuses(state: ResourceState, eventId: string): StatusEffect[] {
  const statuses: StatusEffect[] = [];
  if (state.en < 10) statuses.push({ id: 'STATUS_EXHAUSTED', name: '濒临崩溃', duration: 1 });
  else if (state.en < 30) statuses.push({ id: 'STATUS_LOW_EN', name: '低精力', duration: 1 });
  if (state.st < 30) statuses.push({ id: 'STATUS_LOW_ST', name: '低体力', duration: 1 });
  if (state.kpi < 40) statuses.push({ id: 'STATUS_LOW_KPI', name: '危险绩效', duration: 1 });
  if (state.risk >= 50) statuses.push({ id: 'STATUS_HIGH_RISK', name: '高风险', duration: 1 });
  if (state.cor >= 50) statuses.push({ id: 'STATUS_HIGH_COR', name: '高污染', duration: 1 });
  if (['EVT_03', 'EVT_11', 'EVT_16'].includes(eventId)) {
    statuses.push({ id: 'STATUS_UNDER_WATCH', name: '被盯上', duration: 2 });
  }
  return statuses;
}

/** 时间段 ID */
function timePeriod(turnIndex: number): string {
  return timePeriodForTurn(turnIndex).id;
}

/** 合并 delta */
function mergeDelta(...parts: Partial<ResourceState>[]): ResourceState {
  const merged: ResourceState = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
  for (const part of parts) {
    for (const key of Object.keys(merged) as (keyof ResourceState)[]) {
      merged[key] += part[key] ?? 0;
    }
  }
  return merged;
}

/** 失败检查 */
export function resolveFailure(state: ResourceState): FailureType {
  if (state.hp <= 0) return 'HP_DEPLETED';
  if (state.en <= 0) return 'EN_DEPLETED';
  if (state.st <= 0) return 'ST_DEPLETED';
  if (state.kpi <= 0) return 'KPI_DEPLETED';
  if (state.risk >= 100) return 'RISK_OVERFLOW';
  if (state.cor >= 100) return 'COR_OVERFLOW';
  return null;
}

/** 隐患倒计时 */
function tickHazards(hazards: Hazard[]): { remaining: Hazard[]; delta: ResourceState } {
  const delta: ResourceState = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
  const remaining: Hazard[] = [];
  for (const hazard of hazards) {
    const current = { ...hazard, countdown: hazard.countdown - 1 };
    if (current.countdown <= 0) {
      const s = current.severity;
      delta.hp -= 2 * s;
      delta.kpi -= 4 * s;
      delta.risk += 6 * s;
    } else {
      remaining.push(current);
    }
  }
  return { remaining, delta };
}

/** 项目推进 */
function tickProjects(projects: Project[], actionType: ActionType): { updated: Project[]; delta: ResourceState } {
  const delta: ResourceState = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
  const progressActions: ActionType[] = ['DIRECT_EXECUTE', 'WORK_OVERTIME', 'REQUEST_CONFIRMATION'];
  const updated: Project[] = [];
  for (const project of projects) {
    const current = { ...project };
    const pressure = current.pressure;
    delta.en -= pressure;
    delta.st -= Math.max(1, Math.floor(pressure / 2));
    if (progressActions.includes(actionType)) {
      current.progress += 1;
      delta.kpi += 1;
    }
    if (current.progress >= current.target) {
      delta.kpi += 3;
      delta.risk -= 2;
      continue; // 项目完成，不保留
    }
    updated.push(current);
  }
  return { updated, delta };
}

/** 生成隐患 */
function newHazard(eventId: string, actionType: ActionType, ctx: ContentContext): HazardMapEntry | null {
  // 优先检查事件映射
  const eventHazard = ctx.eventHazardMap[eventId] || EVENT_HAZARD_MAP[eventId];
  if (eventHazard) return { ...eventHazard };
  // 其次检查行动映射
  const actionHazard = ctx.actionHazardMap[actionType] || ACTION_HAZARD_MAP[actionType];
  if (actionHazard) return { ...actionHazard };
  return null;
}

// ---------------------------------------------------------------------------
// 角色抽取（纯函数，使用 ContentContext）
// ---------------------------------------------------------------------------

function weightedPick(options: [string, number][]): string {
  const pool = options.map(([item]) => item);
  const weights = options.map(([, w]) => Math.max(1, w));
  const totalWeight = weights.reduce((s, w) => s + w, 0);
  let r = Math.random() * totalWeight;
  for (let i = 0; i < pool.length; i++) {
    r -= weights[i];
    if (r <= 0) return pool[i];
  }
  return pool[pool.length - 1];
}

function pickCharacter(session: GameSession, ctx: ContentContext, timePeriodId: string): string {
  const allCharacters: Character[] = [...CHARACTERS, ...ctx.characters];
  const periodMods = timePeriodWeightModifiers(timePeriodId);

  const weighted: [string, number][] = [];
  for (const c of allCharacters) {
    let w = c.base_weight;
    w = Math.round(w * (periodMods[c.character_id] ?? 1.0));
    if (c.character_id === 'CHR_04' && session.state.kpi < 40) w = Math.round(w * 2);
    if (c.character_id === 'CHR_05' && session.state.risk >= 50) w = Math.round(w * 1.6);
    if (c.character_id === 'CHR_06' && session.state.cor >= 50) w = Math.round(w * 1.6);
    weighted.push([c.character_id, w]);
  }

  // 重复抑制
  if (ctx.previousCharacterId) {
    for (let i = 0; i < weighted.length; i++) {
      if (weighted[i][0] === ctx.previousCharacterId) {
        weighted[i] = [weighted[i][0], Math.round(weighted[i][1] * 0.45)];
      }
    }
  }

  return weightedPick(weighted);
}

function pickEvent(characterId: string, ctx: ContentContext): { eventId: string; name: string; baseEffect: ResourceState } {
  const builtIn = EVENTS_BY_CHARACTER[characterId] || [];
  const custom = ctx.eventsByCharacter[characterId] || [];
  const pool = [...builtIn, ...custom];

  if (pool.length === 0) {
    return { eventId: GENERIC_EVENT.event_id, name: GENERIC_EVENT.name, baseEffect: { ...GENERIC_EVENT.base_effect } as ResourceState };
  }

  // 重复事件降权
  const weighted: [Event, number][] = pool.map(e => [
    e,
    e.event_id === ctx.previousEventId ? 2 : 10,
  ]);

  const totalWeight = weighted.reduce((s, [, w]) => s + w, 0);
  let r = Math.random() * totalWeight;
  for (const [event, w] of weighted) {
    r -= w;
    if (r <= 0) {
      return { eventId: event.event_id, name: event.name, baseEffect: { ...event.base_effect } as ResourceState };
    }
  }
  const last = pool[pool.length - 1];
  return { eventId: last.event_id, name: last.name, baseEffect: { ...last.base_effect } as ResourceState };
}

// ---------------------------------------------------------------------------
// 核心：resolveTurn 纯函数
// ---------------------------------------------------------------------------

export function resolveTurn(input: ResolveTurnInput): ResolveTurnOutput {
  const { session, actionType, contentContext: ctx } = input;

  // 时间与日期
  const newTurn = session.turn_index + 1;
  const prevDayTurns = Math.floor(session.turn_index / TURNS_PER_DAY);
  const newDayTurns = Math.floor(newTurn / TURNS_PER_DAY);
  const newDay = session.day + (newDayTurns - prevDayTurns);
  const timePeriodId = timePeriod(newTurn);

  // 事件生成
  const characterId = pickCharacter(session, ctx, timePeriodId);
  const event = pickEvent(characterId, ctx);

  // 骰子结算
  const actionMod = ACTION_MODIFIERS[actionType] ?? 0;
  const statusMod = statusModifier(session.state);
  const roll = Math.floor(Math.random() * 20) + 1;
  const score = roll + actionMod + statusMod;
  const tierRule = resolutionTierForScore(score);
  const tier = tierRule.id;
  const multiplier = tierRule.multiplier;

  // 正值区分"奖励"和"惩罚"属性
  const PENALTY_WHEN_POSITIVE = new Set<string>(['risk', 'cor']);
  const baseEventDelta: ResourceState = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
  for (const [k, v] of Object.entries(event.baseEffect)) {
    const key = k as keyof ResourceState;
    if (v >= 0 && !PENALTY_WHEN_POSITIVE.has(k)) {
      baseEventDelta[key] = Math.round(v * (2.0 - multiplier));
    } else {
      baseEventDelta[key] = Math.round(v * multiplier);
    }
  }

  // 行动修正
  const actionDelta: ResourceState = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
  if (tier === 'CRITICAL_FAIL') actionDelta.risk += 5;
  if (actionType === 'EMAIL_TRACE') { actionDelta.risk -= 8; }
  if (actionType === 'SHIFT_BLAME') { actionDelta.cor += 6; actionDelta.risk += 3; }
  if (actionType === 'WORK_OVERTIME') { actionDelta.en -= 4; actionDelta.st -= 4; }
  if (actionType === 'RECOVERY_BREAK') { actionDelta.en += 10; actionDelta.st += 6; actionDelta.kpi -= 2; }

  // 系统结算
  let hazards = [...session.hazards];
  let projects = [...session.projects];
  const { remaining: tickedHazards, delta: hazardDelta } = tickHazards(hazards);
  hazards = tickedHazards;
  const { updated: tickedProjects, delta: projectDelta } = tickProjects(projects, actionType);
  projects = tickedProjects;

  // 生成新隐患
  const maybeHazard = newHazard(event.eventId, actionType, ctx);
  if (maybeHazard && !hazards.some(h => h.id === maybeHazard.id)) {
    hazards.push({ ...maybeHazard });
  }

  // 合并 delta
  const delta = mergeDelta(baseEventDelta, actionDelta, hazardDelta, projectDelta);

  // 项目自动补充
  if (projects.length === 0) {
    projects = [defaultProject()];
  }

  // 计算新状态
  const newRawState: ResourceState = {
    hp: session.state.hp + delta.hp,
    en: session.state.en + delta.en,
    st: session.state.st + delta.st,
    kpi: session.state.kpi + delta.kpi,
    risk: session.state.risk + delta.risk,
    cor: session.state.cor + delta.cor,
  };
  const newClampedState = clampState(newRawState);
  const statuses = deriveStatuses(newClampedState, event.eventId);
  const failureType = resolveFailure(newClampedState);

  // 结局
  let ending: GameEnding | undefined;
  if (failureType) {
    const failureRule = [
      { type: 'HP_DEPLETED', title: '崩溃结局', description: '你的身体终于撑不住了……' },
      { type: 'EN_DEPLETED', title: '精神崩溃结局', description: '精神已经完全崩溃……' },
      { type: 'ST_DEPLETED', title: '体力耗尽结局', description: '体力彻底耗尽……' },
      { type: 'KPI_DEPLETED', title: '被开除结局', description: '绩效归零，HR找你谈话了……' },
      { type: 'RISK_OVERFLOW', title: '暴雷结局', description: '风险值爆表，雷终于炸了……' },
      { type: 'COR_OVERFLOW', title: '黑化结局', description: '你已经被这个系统完全同化……' },
    ].find(r => r.type === failureType);
    ending = failureRule ? { type: failureType, title: failureRule.title, description: failureRule.description } : undefined;
  }

  // 构建 TurnLog
  const turnLog: TurnLog = {
    session_id: session.session_id,
    openid: session.openid,
    turn_index: newTurn,
    day: newDay,
    time_period: timePeriodId,
    character_id: characterId,
    event_id: event.eventId,
    action_type: actionType,
    action_mod: actionMod,
    roll_value: roll,
    total_score: score,
    result_tier: tier,
    failure_type: failureType,
    delta,
    state_after: newClampedState,
    created_at: Date.now(),
  };

  // 构建 sessionPatch
  const sessionPatch: Partial<GameSession> = {
    turn_index: newTurn,
    day: newDay,
    state: newClampedState,
    statuses,
    hazards,
    projects,
    status: failureType ? 'ENDED' : 'ACTIVE',
    updated_at: Date.now(),
  };

  // 构建 nextPrompt
  const nameMap = { ...CHARACTER_NAME_MAP, ...ctx.characterNameMap };
  const nextTimePeriodId = timePeriod(newTurn + 1);
  const nextCharacterId = pickCharacter(
    { ...session, turn_index: newTurn, state: newClampedState } as GameSession,
    { ...ctx, previousCharacterId: characterId, previousEventId: event.eventId },
    nextTimePeriodId
  );
  const nextEvent = pickEvent(nextCharacterId, {
    ...ctx,
    previousCharacterId: characterId,
    previousEventId: event.eventId,
  });

  const riskTip = newClampedState.risk >= 40
    ? '风险偏高，优先考虑留痕或缩小范围。'
    : '保持节奏，避免口头承诺。';

  const nextPrompt: GamePrompt = {
    turn_index: newTurn + 1,
    day: newDay,
    time_period: nextTimePeriodId,
    status_bar: {
      '生命': `${newClampedState.hp}/100`,
      '精力': `${newClampedState.en}/100`,
      '体力': `${newClampedState.st}/100`,
      '绩效': newClampedState.kpi,
      '风险': newClampedState.risk,
      '污染': newClampedState.cor,
    },
    event_summary: {
      actor: nameMap[nextCharacterId] || '未知角色',
      event: nextEvent.name,
      prompt: `${nameMap[nextCharacterId] || '某人'} 发来新压力：${nextEvent.name}`,
    },
    risk_tip: riskTip,
    options: buildOptions(newClampedState),
    input_hint: '回复编号或直接说你的应对方式。',
  };

  return {
    turnLog,
    sessionPatch,
    nextPrompt,
    ending,
  };
}

// ---------------------------------------------------------------------------
// buildNextPrompt（独立使用，用于获取下一回合提示）
// ---------------------------------------------------------------------------

export function buildNextPrompt(session: GameSession, ctx: ContentContext): GamePrompt {
  const nextTurn = session.turn_index + 1;
  const nextTimePeriodId = timePeriod(nextTurn);
  const nameMap = { ...CHARACTER_NAME_MAP, ...ctx.characterNameMap };

  const characterId = pickCharacter(session, ctx, nextTimePeriodId);
  const event = pickEvent(characterId, ctx);

  const riskTip = session.state.risk >= 40
    ? '风险偏高，优先考虑留痕或缩小范围。'
    : '保持节奏，避免口头承诺。';

  return {
    turn_index: nextTurn,
    day: session.day,
    time_period: nextTimePeriodId,
    status_bar: {
      '生命': `${session.state.hp}/100`,
      '精力': `${session.state.en}/100`,
      '体力': `${session.state.st}/100`,
      '绩效': session.state.kpi,
      '风险': session.state.risk,
      '污染': session.state.cor,
    },
    event_summary: {
      actor: nameMap[characterId] || '未知角色',
      event: event.name,
      prompt: `${nameMap[characterId] || '某人'} 发来新压力：${event.name}`,
    },
    risk_tip: riskTip,
    options: buildOptions(session.state),
    input_hint: '回复编号或直接说你的应对方式。',
  };
}
