/**
 * 暗黑职场 — createGameSession 云函数
 */

import type { GameSession, GamePrompt } from '../shared/types/game';
import { INITIAL_STATE, defaultProject } from '../shared/rules/resources';
import { buildNextPrompt } from '../shared/engine';
import { getOpenidFromContext } from '../shared/auth';
import { cloudSessionRepo, cloudUserRepo } from '../shared/repositories/cloud';

export interface CreateGameSessionInput {
  storyline_id?: string;
  difficulty?: 'normal' | 'hard';
}

export interface CreateGameSessionOutput {
  session: GameSession;
  first_prompt: GamePrompt;
}

export async function main(event: CreateGameSessionInput): Promise<CreateGameSessionOutput> {
  const openid = getOpenidFromContext();
  const sessionId = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

  const session: GameSession = {
    session_id: sessionId,
    openid,
    storyline_id: event.storyline_id ?? null,
    storyline_version: null,
    rule_set_id: 'rules_2026_04',
    day: 1,
    turn_index: 0,
    state: { ...INITIAL_STATE },
    statuses: [],
    hazards: [],
    projects: [defaultProject()],
    current_act_index: 0,
    status: 'ACTIVE',
    created_at: Date.now(),
    updated_at: Date.now(),
    deleted_at: null,
  };

  await cloudSessionRepo.create(session);

  // 更新用户游戏数
  const user = await cloudUserRepo.get(openid);
  if (user) {
    await cloudUserRepo.update(openid, { total_games: user.total_games + 1 });
  }

  // 生成首回合提示
  const firstPrompt = buildNextPrompt(session, {
    characters: [],
    eventsByCharacter: {},
    eventHazardMap: {},
    actionHazardMap: {},
    characterNameMap: {},
    previousCharacterId: null,
    previousEventId: null,
  });

  return { session, first_prompt: firstPrompt };
}
