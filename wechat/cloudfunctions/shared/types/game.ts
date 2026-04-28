/**
 * 暗黑职场 — 核心游戏类型定义
 *
 * 从 Python runtime/engine.py + rules.py + content.py 对齐转译
 */

// ---------------------------------------------------------------------------
// 资源 & 状态
// ---------------------------------------------------------------------------

/** 六维资源类型 */
export type ResourceType = 'hp' | 'en' | 'st' | 'kpi' | 'risk' | 'cor';

/** 资源定义元数据 */
export interface ResourceDefinition {
  label: string;
  track: string;
  direction: string;
  failure_condition: string;
  failure_outcome: string;
}

/** 资源排列顺序 */
export const RESOURCE_ORDER: ResourceType[] = ['hp', 'en', 'st', 'kpi', 'risk', 'cor'];

/** 六维资源数值快照 */
export type ResourceState = Record<ResourceType, number>;

/** 初始状态 */
export const INITIAL_STATE: ResourceState = {
  hp: 100, en: 100, st: 100, kpi: 100, risk: 0, cor: 0,
};

// ---------------------------------------------------------------------------
// 行动 & 结算
// ---------------------------------------------------------------------------

/** 行动类型枚举 */
export type ActionType =
  | 'DIRECT_EXECUTE'
  | 'EMAIL_TRACE'
  | 'NARROW_SCOPE'
  | 'SOFT_REFUSE'
  | 'WORK_OVERTIME'
  | 'REQUEST_CONFIRMATION'
  | 'DELAY_AVOID'
  | 'SHIFT_BLAME'
  | 'RECOVERY_BREAK'
  | 'BOUNDARY_RESTATE';

/** 行动规则定义 */
export interface ActionRule {
  title: string;
  summary: string;
  modifier: number;
  category: string;
  tradeoff: string;
}

/** 行动展示信息 */
export interface ActionDisplay {
  title: string;
  summary: string;
}

/** 行动选项（渲染给玩家） */
export interface ActionOption {
  index: number;
  action: ActionType;
  title: string;
  summary: string;
  category: string;
}

// ---------------------------------------------------------------------------
// 档位 & 结算
// ---------------------------------------------------------------------------

/** 结算档位 */
export type ResultTier =
  | 'CRITICAL_FAIL'
  | 'FAIL'
  | 'BARELY'
  | 'SUCCESS'
  | 'CRITICAL_SUCCESS';

/** 档位规则定义 */
export interface ResolutionTierRule {
  id: ResultTier;
  label: string;
  range: string;
  min_score: number;
  max_score: number;
  multiplier: number;
  summary: string;
}

// ---------------------------------------------------------------------------
// 失败 & 结局
// ---------------------------------------------------------------------------

/** 失败类型 */
export type FailureType =
  | 'HP_DEPLETED'
  | 'EN_DEPLETED'
  | 'ST_DEPLETED'
  | 'KPI_DEPLETED'
  | 'RISK_OVERFLOW'
  | 'COR_OVERFLOW'
  | null;

/** 失败规则 */
export interface FailureRule {
  id: string;
  label: string;
  condition: string;
  priority: number;
}

/** 游戏结局 */
export interface GameEnding {
  type: FailureType;
  title: string;
  description: string;
}

// ---------------------------------------------------------------------------
// 时间段
// ---------------------------------------------------------------------------

/** 时间段定义 */
export interface TimePeriodRule {
  id: string;
  window: string;
  turn_start: number;
  turn_end: number;
  enabled: boolean;
  mood: string;
  summary: string;
  weight_modifiers: Record<string, number>;
}

// ---------------------------------------------------------------------------
// 状态效果 & 隐患 & 项目
// ---------------------------------------------------------------------------

/** 持续状态效果 */
export interface StatusEffect {
  id: string;
  name: string;
  duration: number;
}

/** 隐患卡 */
export interface Hazard {
  id: string;
  name: string;
  countdown: number;
  severity: number;
}

/** 项目 */
export interface Project {
  id: string;
  name: string;
  progress: number;
  target: number;
  pressure: number;
}

/** 状态规则定义 */
export interface StatusRule {
  id: string;
  name: string;
  trigger: string;
  duration: number;
  impact: string;
}

// ---------------------------------------------------------------------------
// 角色权重规则
// ---------------------------------------------------------------------------

/** 角色权重修正规则 */
export interface CharacterWeightRule {
  id: string;
  scope: 'global' | 'character';
  label: string;
  condition: string;
  effect: string;
  character_id?: string;
}

// ---------------------------------------------------------------------------
// 卡牌内容
// ---------------------------------------------------------------------------

/** 角色 */
export interface Character {
  character_id: string;
  name: string;
  base_weight: number;
  role_type?: string;
  faction?: string;
  tags?: string[];
  passive_effect?: string;
  speech_style?: string;
}

/** 事件 */
export interface Event {
  event_id: string;
  character_id: string;
  name: string;
  base_effect: ResourceState;
  event_category?: string;
  pressure_level?: string;
  tags?: string[];
  flavor_text?: string;
  possible_followups?: string[];
  dice_dc?: number;
}

/** 隐患映射（事件 → 隐患 / 行动 → 隐患） */
export interface HazardMapEntry {
  id: string;
  name: string;
  countdown: number;
  severity: number;
}

// ---------------------------------------------------------------------------
// 游戏会话
// ---------------------------------------------------------------------------

/** 会话状态 */
export type SessionStatus = 'ACTIVE' | 'ENDED';

/** 游戏会话 */
export interface GameSession {
  session_id: string;
  openid: string;
  storyline_id: string | null;
  storyline_version: string | null;
  rule_set_id: string | null;
  day: number;
  turn_index: number;
  state: ResourceState;
  statuses: StatusEffect[];
  hazards: Hazard[];
  projects: Project[];
  current_act_index: number;
  status: SessionStatus;
  created_at: number;
  updated_at: number;
  deleted_at: number | null;
}

// ---------------------------------------------------------------------------
// 回合日志
// ---------------------------------------------------------------------------

/** 回合日志 */
export interface TurnLog {
  session_id: string;
  openid: string;
  turn_index: number;
  day: number;
  time_period: string;
  character_id: string;
  event_id: string;
  action_type: ActionType;
  action_mod: number;
  roll_value: number;
  total_score: number;
  result_tier: ResultTier;
  failure_type: FailureType;
  delta: ResourceState;
  state_after: ResourceState;
  created_at: number;
}

// ---------------------------------------------------------------------------
// 回合结算输入/输出
// ---------------------------------------------------------------------------

/** 内容上下文（引擎结算时需要的只读内容） */
export interface ContentContext {
  characters: Character[];
  eventsByCharacter: Record<string, Event[]>;
  eventHazardMap: Record<string, HazardMapEntry>;
  actionHazardMap: Record<string, HazardMapEntry>;
  characterNameMap: Record<string, string>;
  previousCharacterId: string | null;
  previousEventId: string | null;
}

/** 回合结算输入 */
export interface ResolveTurnInput {
  session: GameSession;
  actionType: ActionType;
  contentContext: ContentContext;
  rngSeed?: string;
}

/** 回合结算输出 */
export interface ResolveTurnOutput {
  turnLog: TurnLog;
  sessionPatch: Partial<GameSession>;
  nextPrompt: GamePrompt;
  ending?: GameEnding;
}

// ---------------------------------------------------------------------------
// 游戏提示（下一回合展示给玩家）
// ---------------------------------------------------------------------------

/** 事件摘要 */
export interface EventSummary {
  actor: string;
  event: string;
  prompt: string;
}

/** 游戏提示 */
export interface GamePrompt {
  turn_index: number;
  day: number;
  time_period: string;
  status_bar: Record<string, string | number>;
  event_summary: EventSummary;
  risk_tip: string;
  options: ActionOption[];
  input_hint: string;
}

// ---------------------------------------------------------------------------
// 用户
// ---------------------------------------------------------------------------

/** 用户档案 */
export interface User {
  openid: string;
  nickname: string | null;
  avatar_url: string | null;
  total_games: number;
  total_turns: number;
  created_at: number;
  updated_at: number;
}

// ---------------------------------------------------------------------------
// 剧情线
// ---------------------------------------------------------------------------

/** 剧情线幕 */
export interface StorylineAct {
  act_index: number;
  title: string;
  character_id: string;
  event_ids: string[];
  completion_condition: string;
  branches: unknown[];
}

/** 剧情线 */
export interface Storyline {
  storyline_id: string;
  title: string;
  description: string;
  version: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  tags: string[];
  acts: StorylineAct[];
  endings: unknown[];
}
