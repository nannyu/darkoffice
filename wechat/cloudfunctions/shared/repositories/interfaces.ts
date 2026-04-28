/**
 * 暗黑职场 — Repository 接口定义
 *
 * Mock 和 Cloud 实现都遵循此接口
 */

import type { GameSession, TurnLog, User } from '../types/game';

export interface ISessionRepo {
  get(sessionId: string): Promise<GameSession | null>;
  create(session: GameSession): Promise<GameSession>;
  update(sessionId: string, patch: Partial<GameSession>): Promise<GameSession>;
  listByUser(openid: string): Promise<GameSession[]>;
  delete(sessionId: string): Promise<boolean>;
}

export interface ITurnLogRepo {
  append(log: TurnLog): Promise<TurnLog>;
  list(sessionId: string, limit?: number): Promise<TurnLog[]>;
  getLatest(sessionId: string): Promise<TurnLog | null>;
}

export interface IUserRepo {
  get(openid: string): Promise<User | null>;
  create(user: User): Promise<User>;
  update(openid: string, patch: Partial<User>): Promise<User>;
}
