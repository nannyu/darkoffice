/**
 * 暗黑职场 — 输入校验
 */

import type { ActionType, GameSession } from '../types/game';
import { ACTION_RULES } from '../rules/actions';

const VALID_ACTION_TYPES = new Set<string>(Object.keys(ACTION_RULES));

/** 校验 action_type 是否合法 */
export function validateActionType(actionType: string): ActionType {
  if (!VALID_ACTION_TYPES.has(actionType)) {
    throw new Error(`INVALID_ACTION_TYPE: "${actionType}" is not a valid action`);
  }
  return actionType as ActionType;
}

/** 校验会话状态是否可执行回合 */
export function validateSessionForTurn(session: GameSession): void {
  if (session.status !== 'ACTIVE') {
    throw new Error('SESSION_NOT_ACTIVE: session has ended');
  }
  if (session.deleted_at) {
    throw new Error('SESSION_DELETED: session has been deleted');
  }
}

/** 校验 client_turn_index 是否匹配 */
export function validateTurnIndex(session: GameSession, clientTurnIndex: number): void {
  if (clientTurnIndex !== session.turn_index) {
    throw new Error(
      `TURN_INDEX_CONFLICT: client=${clientTurnIndex}, server=${session.turn_index}`
    );
  }
}

/** 校验 openid 是否匹配会话所有者 */
export function validateOwnership(session: GameSession, openid: string): void {
  if (session.openid !== openid) {
    throw new Error('UNAUTHORIZED: openid does not match session owner');
  }
}

/** 校验 session_id 格式 */
export function validateSessionId(sessionId: string): void {
  if (!sessionId || typeof sessionId !== 'string') {
    throw new Error('INVALID_SESSION_ID: sessionId must be a non-empty string');
  }
}
