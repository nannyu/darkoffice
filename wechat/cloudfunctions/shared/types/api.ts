/**
 * 暗黑职场 — API 请求/响应类型
 */

import type {
  ActionType,
  FailureType,
  GamePrompt,
  GameSession,
  ResultTier,
  ResourceState,
  TurnLog,
  User,
} from './game';

// ---------------------------------------------------------------------------
// 通用响应
// ---------------------------------------------------------------------------

export interface ApiResponse<T> {
  ok: boolean;
  request_id: string;
  data: T | null;
  error: ApiError | null;
}

export interface ApiError {
  code: string;
  message: string;
}

// ---------------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------------

export interface LoginInput {
  code: string; // 微信 login code
}

export interface LoginOutput {
  user: User;
  is_new: boolean;
}

// ---------------------------------------------------------------------------
// CreateGameSession
// ---------------------------------------------------------------------------

export interface CreateGameSessionInput {
  storyline_id?: string;
  difficulty?: 'normal' | 'hard';
}

export interface CreateGameSessionOutput {
  session: GameSession;
  first_prompt: GamePrompt;
}

// ---------------------------------------------------------------------------
// GetNextPrompt
// ---------------------------------------------------------------------------

export interface GetNextPromptInput {
  session_id: string;
}

export type GetNextPromptOutput = GamePrompt;

// ---------------------------------------------------------------------------
// ApplyTurn
// ---------------------------------------------------------------------------

export interface ApplyTurnInput {
  session_id: string;
  action_type: ActionType;
  client_turn_index: number;
}

export interface ApplyTurnOutput {
  turn_result: TurnResultPayload;
  next_prompt: GamePrompt;
  session_summary: SessionSummary;
}

export interface TurnResultPayload {
  turn_index: number;
  day: number;
  time_period: string;
  character_id: string;
  event_id: string;
  action_type: ActionType;
  roll_value: number;
  total_score: number;
  result_tier: ResultTier;
  failure_type: FailureType;
  delta: ResourceState;
  state_after: ResourceState;
}

export interface SessionSummary {
  session_id: string;
  status: string;
  turn_index: number;
  day: number;
  state: ResourceState;
}

// ---------------------------------------------------------------------------
// ListStorylines
// ---------------------------------------------------------------------------

export interface ListStorylinesInput {
  tag?: string;
  status?: string;
}

export interface StorylineSummary {
  storyline_id: string;
  title: string;
  description: string;
  tags: string[];
  difficulty: string;
  act_count: number;
}

export interface ListStorylinesOutput {
  storylines: StorylineSummary[];
}

// ---------------------------------------------------------------------------
// ListArchives
// ---------------------------------------------------------------------------

export interface ListArchivesInput {
  // openid 从上下文获取
}

export interface ArchiveSummary {
  session_id: string;
  storyline_id: string | null;
  turn_index: number;
  day: number;
  state: ResourceState;
  status: string;
  updated_at: number;
}

export interface ListArchivesOutput {
  archives: ArchiveSummary[];
}

// ---------------------------------------------------------------------------
// GetRecap
// ---------------------------------------------------------------------------

export interface GetRecapInput {
  session_id: string;
}

export interface RecapEntry {
  turn_index: number;
  character_id: string;
  event_id: string;
  action_type: ActionType;
  result_tier: ResultTier;
  delta: ResourceState;
  state_after: ResourceState;
  created_at: number;
}

export interface GetRecapOutput {
  session_id: string;
  turns: RecapEntry[];
  failure_type: FailureType;
}

// ---------------------------------------------------------------------------
// DeleteArchive
// ---------------------------------------------------------------------------

export interface DeleteArchiveInput {
  session_id: string;
}

export interface DeleteArchiveOutput {
  deleted: boolean;
}
