/**
 * 暗黑职场 — applyTurn 云函数（核心回合结算）
 */

import type { ApplyTurnOutput, SessionSummary, TurnResultPayload } from '../shared/types/api';
import { resolveTurn } from '../shared/engine';
import { getOpenidFromContext } from '../shared/auth';
import { cloudSessionRepo, cloudTurnLogRepo } from '../shared/repositories/cloud';
import { validateActionType, validateSessionForTurn, validateOwnership, validateTurnIndex } from '../shared/validators/input';

export interface ApplyTurnInput {
  session_id: string;
  action_type: string;
  client_turn_index: number;
}

export async function main(event: ApplyTurnInput): Promise<ApplyTurnOutput> {
  const openid = getOpenidFromContext();

  // 1. 获取会话
  const session = await cloudSessionRepo.get(event.session_id);
  if (!session) throw new Error('SESSION_NOT_FOUND');

  // 2. 校验
  validateOwnership(session, openid);
  validateSessionForTurn(session);
  validateTurnIndex(session, event.client_turn_index);
  const actionType = validateActionType(event.action_type);
  const latestTurn = await cloudTurnLogRepo.getLatest(event.session_id);

  // 3. 执行引擎结算
  const result = resolveTurn({
    session,
    actionType,
    contentContext: {
      characters: [],
      eventsByCharacter: {},
      eventHazardMap: {},
      actionHazardMap: {},
      characterNameMap: {},
      previousCharacterId: latestTurn?.character_id ?? null,
      previousEventId: latestTurn?.event_id ?? null,
    },
  });

  // 4. 持久化
  await cloudSessionRepo.updateForTurn(event.session_id, event.client_turn_index, result.sessionPatch);
  await cloudTurnLogRepo.append(result.turnLog);

  // 5. 构造响应
  const turnResult: TurnResultPayload = {
    turn_index: result.turnLog.turn_index,
    day: result.turnLog.day,
    time_period: result.turnLog.time_period,
    character_id: result.turnLog.character_id,
    event_id: result.turnLog.event_id,
    action_type: result.turnLog.action_type,
    roll_value: result.turnLog.roll_value,
    total_score: result.turnLog.total_score,
    result_tier: result.turnLog.result_tier,
    failure_type: result.turnLog.failure_type,
    delta: result.turnLog.delta,
    state_after: result.turnLog.state_after,
  };

  const sessionSummary: SessionSummary = {
    session_id: event.session_id,
    status: result.sessionPatch.status ?? 'ACTIVE',
    turn_index: result.turnLog.turn_index,
    day: result.turnLog.day,
    state: result.turnLog.state_after,
  };

  return {
    turn_result: turnResult,
    next_prompt: result.nextPrompt,
    session_summary: sessionSummary,
  };
}
