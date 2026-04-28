/**
 * 暗黑职场 — login 云函数
 */

import type { User } from '../shared/types/game';
import { getOpenidFromContext } from '../shared/auth';
import { cloudUserRepo } from '../shared/repositories/cloud';

export interface LoginInput {
  code?: string;
}

export interface LoginOutput {
  user: User;
  is_new: boolean;
}

export async function main(event: LoginInput): Promise<LoginOutput> {
  const openid = getOpenidFromContext();

  let user = await cloudUserRepo.get(openid);
  let isNew = false;

  if (!user) {
    user = {
      openid,
      nickname: null,
      avatar_url: null,
      total_games: 0,
      total_turns: 0,
      created_at: Date.now(),
      updated_at: Date.now(),
    };
    await cloudUserRepo.create(user);
    isNew = true;
  }

  return { user, is_new: isNew };
}
