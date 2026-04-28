/**
 * 暗黑职场 — getNextPrompt 云函数
 */

import type { GamePrompt } from '../shared/types/game';
import { buildNextPrompt } from '../shared/engine';
import { getOpenidFromContext } from '../shared/auth';
import { cloudSessionRepo, cloudTurnLogRepo } from '../shared/repositories/cloud';

export interface GetNextPromptInput {
  session_id: string;
}

export async function main(event: GetNextPromptInput): Promise<GamePrompt> {
  const openid = getOpenidFromContext();
  const session = await cloudSessionRepo.get(event.session_id);
  if (!session) throw new Error('SESSION_NOT_FOUND');
  if (session.openid !== openid) throw new Error('UNAUTHORIZED');

  const latestTurn = await cloudTurnLogRepo.getLatest(event.session_id);

  return buildNextPrompt(session, {
    characters: [],
    eventsByCharacter: {},
    eventHazardMap: {},
    actionHazardMap: {},
    characterNameMap: {},
    previousCharacterId: latestTurn?.character_id ?? null,
    previousEventId: latestTurn?.event_id ?? null,
  });
}
