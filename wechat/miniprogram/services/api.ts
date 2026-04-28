/**
 * 暗黑职场 — API 服务层（本地 Mock 模式）
 *
 * 直接调用 shared 层引擎和数据层，所有方法同步执行
 * 后续对接云开发时，替换为 wx.cloud.callFunction（异步）
 */

import {
  GameSession,
  ActionType,
  ResourceState,
  ActionOption,
  EventSummary,
  TurnLog,
  GameEnding,
  ContentContext,
  Character,
  Event,
} from '../shared/types/game';

import { MockRepositories } from '../shared/repositories/mock';
import { resolveTurn } from '../shared/engine';
import { validateActionType, validateOwnership, validateSessionId, validateTurnIndex } from '../shared/validators/input';
import { INITIAL_STATE } from '../shared/rules/resources';
import { buildOptions } from '../shared/rules/actions';
import { CHARACTERS, EVENTS_BY_CHARACTER } from '../shared/content';
import { EVENT_HAZARD_MAP, ACTION_HAZARD_MAP, checkFailure } from '../shared/rules/hazards';
import { resolutionTierForScore } from '../shared/rules/resolution';
import { timePeriodForTurn } from '../shared/rules/time-period';

// ---------------------------------------------------------------------------
// 前端视图类型
// ---------------------------------------------------------------------------

export interface GamePromptView {
  turn_index: number;
  day: number;
  time_period: string;
  event_summary: EventSummary;
  options: ActionOption[];
  risk_tip: string;
  state: ResourceState;
  hazards: { id: string; name: string; countdown: number; severity: number }[];
  projects: { id: string; name: string; progress: number; target: number }[];
}

export interface ApplyTurnResult {
  turn_result: {
    roll_value: number;
    total_score: number;
    result_tier: string;
    result_tier_label: string;
    multiplier: number;
    delta: ResourceState;
    deltaList: { key: string; label: string; value: number; display: string; positive: boolean; color: string }[];
  };
  session_summary: {
    state: ResourceState;
    day: number;
    time_period: string;
    turn_index: number;
    status: string;
    hazards: { id: string; name: string; countdown: number; severity: number }[];
    projects: { id: string; name: string; progress: number; target: number }[];
  };
  next_prompt: GamePromptView | null;
  ending: GameEnding | null;
}

// ---------------------------------------------------------------------------
// Mock 单例
// ---------------------------------------------------------------------------

const repos = new MockRepositories();

function generateId(): string {
  return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
}

// ---------------------------------------------------------------------------
// 辅助
// ---------------------------------------------------------------------------

const RESOURCE_LABELS: Record<string, { label: string; color: string }> = {
  hp: { label: '生命', color: 'var(--color-hp)' },
  en: { label: '精神', color: 'var(--color-en)' },
  st: { label: '体力', color: 'var(--color-st)' },
  kpi: { label: 'KPI', color: 'var(--color-kpi)' },
  risk: { label: '风险', color: 'var(--color-risk)' },
  cor: { label: '腐化', color: 'var(--color-cor)' },
};

function buildDeltaList(delta: ResourceState) {
  return Object.entries(delta).map(([key, val]) => ({
    key,
    label: RESOURCE_LABELS[key]?.label || key,
    value: val,
    display: val > 0 ? `+${val}` : val === 0 ? '0' : `${val}`,
    positive: val > 0,
    color: RESOURCE_LABELS[key]?.color || '#fff',
  }));
}

function contentContextForSession(session: GameSession): ContentContext {
  const characterNameMap: Record<string, string> = {};
  const chars: Character[] = CHARACTERS.map(c => ({ ...c }));
  for (const c of chars) {
    characterNameMap[c.character_id] = c.name;
  }

  const ebc: Record<string, Event[]> = {};
  for (const [k, arr] of Object.entries(EVENTS_BY_CHARACTER)) {
    ebc[k] = (arr as Event[]).map(e => ({ ...e }));
  }

  const previousTurns = repos.turnLogs.getBySession(session.session_id);
  const lastTurn = previousTurns.length > 0 ? previousTurns[previousTurns.length - 1] : null;

  return {
    characters: chars,
    eventsByCharacter: ebc,
    eventHazardMap: { ...EVENT_HAZARD_MAP } as any,
    actionHazardMap: { ...ACTION_HAZARD_MAP } as any,
    characterNameMap,
    previousCharacterId: lastTurn?.character_id || null,
    previousEventId: lastTurn?.event_id || null,
  };
}

function promptViewFromSession(session: GameSession): GamePromptView {
  const ctx = contentContextForSession(session);

  const characterId = session.state.risk > 60
    ? chars(ctx)[Math.floor(Math.random() * chars(ctx).length)].character_id
    : chars(ctx)[0].character_id;

  const events = ctx.eventsByCharacter[characterId] || [];
  const event = events.length > 0
    ? events[Math.floor(Math.random() * events.length)]
    : { event_id: 'EVT_001', name: '突发状况', character_id: characterId, base_effect: { hp: -10, en: -5, st: -5, kpi: -5, risk: 5, cor: 0 }, flavor_text: '又出事了...' } as Event;

  const options = buildOptions(session.state);
  const tp = timePeriodForTurn(session.turn_index);

  return {
    turn_index: session.turn_index,
    day: session.day,
    time_period: tp.id,
    event_summary: {
      actor: ctx.characterNameMap[characterId] || characterId,
      event: event.name,
      prompt: event.flavor_text || `${ctx.characterNameMap[characterId] || characterId}找上门来了...`,
    },
    options,
    risk_tip: session.state.risk > 60 ? '⚠ 风险值偏高，注意行动选择' : '',
    state: { ...session.state },
    hazards: session.hazards.map(h => ({ id: h.id, name: h.name, countdown: h.countdown, severity: h.severity })),
    projects: session.projects.map(p => ({ id: p.id, name: p.name, progress: p.progress, target: p.target })),
  };
}

function chars(ctx: ContentContext): Character[] {
  return ctx.characters;
}

// ---------------------------------------------------------------------------
// API 方法
// ---------------------------------------------------------------------------

export const api = {

  createGameSession(params: { openid: string; storyline_id?: string }): { session: GameSession; prompt: GamePromptView } {
    const sessionId = generateId();
    const now = Date.now();
    const session: GameSession = {
      session_id: sessionId,
      openid: params.openid,
      storyline_id: params.storyline_id || null,
      storyline_version: null,
      rule_set_id: null,
      day: 1,
      turn_index: 0,
      state: { ...INITIAL_STATE },
      statuses: [],
      hazards: [],
      projects: [],
      current_act_index: 0,
      status: 'ACTIVE',
      created_at: now,
      updated_at: now,
      deleted_at: null,
    };
    repos.sessions.create(session);
    const prompt = promptViewFromSession(session);
    return { session, prompt };
  },

  getNextPrompt(params: { session_id: string; openid: string }): GamePromptView {
    const session = repos.sessions.get(params.session_id);
    if (!session) throw new Error(`Session not found: ${params.session_id}`);
    validateOwnership(session, params.openid);
    return promptViewFromSession(session);
  },

  applyTurn(params: { session_id: string; action_type: ActionType; client_turn_index: number; openid: string }): ApplyTurnResult {
    validateSessionId(params.session_id);
    validateActionType(params.action_type);

    const session = repos.sessions.get(params.session_id);
    if (!session) throw new Error(`Session not found: ${params.session_id}`);
    validateOwnership(session, params.openid);
    validateTurnIndex(session, params.client_turn_index);
    if (session.status === 'ENDED') throw new Error('Game already ended');

    const ctx = contentContextForSession(session);
    const result = resolveTurn({ session, actionType: params.action_type, contentContext: ctx });

    const updatedSession: GameSession = {
      ...session,
      ...result.sessionPatch,
      updated_at: Date.now(),
    };

    const failure = checkFailure(updatedSession.state);
    if (failure) updatedSession.status = 'ENDED';

    repos.sessions.update(updatedSession);
    repos.turnLogs.create(result.turnLog);

    const tierRule = resolutionTierForScore(result.turnLog.total_score);

    const turnResult = {
      roll_value: result.turnLog.roll_value,
      total_score: result.turnLog.total_score,
      result_tier: result.turnLog.result_tier,
      result_tier_label: tierRule.label,
      multiplier: tierRule.multiplier,
      delta: { ...result.turnLog.delta },
      deltaList: buildDeltaList(result.turnLog.delta),
    };

    let nextPrompt: GamePromptView | null = null;
    if (!failure) {
      nextPrompt = promptViewFromSession(updatedSession);
    }

    const sessionSummary = {
      state: { ...updatedSession.state },
      day: updatedSession.day,
      time_period: timePeriodForTurn(updatedSession.turn_index).id,
      turn_index: updatedSession.turn_index,
      status: updatedSession.status,
      hazards: updatedSession.hazards.map(h => ({ id: h.id, name: h.name, countdown: h.countdown, severity: h.severity })),
      projects: updatedSession.projects.map(p => ({ id: p.id, name: p.name, progress: p.progress, target: p.target })),
    };

    const ending: GameEnding | null = failure ? {
      type: failure,
      title: getEndingTitle(failure),
      description: getEndingDesc(failure),
    } : null;

    return { turn_result: turnResult, session_summary: sessionSummary, next_prompt: nextPrompt, ending };
  },
};

function getEndingTitle(failure: string): string {
  const map: Record<string, string> = {
    HP_DEPLETED: '身心崩溃', EN_DEPLETED: '精神崩溃', ST_DEPLETED: '体力耗尽',
    KPI_DEPLETED: '被开除', RISK_OVERFLOW: '暴雷', COR_OVERFLOW: '黑化',
  };
  return map[failure] || '未知结局';
}

function getEndingDesc(failure: string): string {
  const map: Record<string, string> = {
    HP_DEPLETED: '你的身体再也撑不住了，在职场的重压下彻底崩溃。',
    EN_DEPLETED: '精神上的消耗已经到达极限，你再也提不起任何干劲。',
    ST_DEPLETED: '长期的高强度工作让你的体力完全透支。',
    KPI_DEPLETED: 'KPI 连续不达标，公司决定不再留你。',
    RISK_OVERFLOW: '你积累的风险终于暴雷，所有暗箱操作被曝光。',
    COR_OVERFLOW: '在黑暗中浸淫太久，你已经变成了曾经最讨厌的人。',
  };
  return map[failure] || '游戏结束。';
}
