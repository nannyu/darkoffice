/**
 * 暗黑职场 — Mock Repository 实现（内存存储）
 *
 * 用于本地开发和测试，后续可替换为云数据库实现
 */

import type { GameSession, TurnLog, User } from '../../types/game';
import type { ISessionRepo, ITurnLogRepo, IUserRepo } from '../interfaces';

// ---------------------------------------------------------------------------
// SessionRepo
// ---------------------------------------------------------------------------

export class MockSessionRepo implements ISessionRepo {
  private store = new Map<string, GameSession>();

  async get(sessionId: string): Promise<GameSession | null> {
    return this.store.get(sessionId) ?? null;
  }

  async create(session: GameSession): Promise<GameSession> {
    this.store.set(session.session_id, { ...session });
    return session;
  }

  async update(sessionId: string, patch: Partial<GameSession>): Promise<GameSession> {
    const existing = this.store.get(sessionId);
    if (!existing) throw new Error(`session not found: ${sessionId}`);
    const updated = { ...existing, ...patch, state: patch.state ?? existing.state };
    this.store.set(sessionId, updated);
    return updated;
  }

  async listByUser(openid: string): Promise<GameSession[]> {
    return Array.from(this.store.values()).filter(s => s.openid === openid && !s.deleted_at);
  }

  async delete(sessionId: string): Promise<boolean> {
    const existing = this.store.get(sessionId);
    if (!existing) return false;
    existing.deleted_at = Date.now();
    this.store.set(sessionId, existing);
    return true;
  }
}

// ---------------------------------------------------------------------------
// TurnLogRepo
// ---------------------------------------------------------------------------

export class MockTurnLogRepo implements ITurnLogRepo {
  private logs: TurnLog[] = [];

  async append(log: TurnLog): Promise<TurnLog> {
    this.logs.push({ ...log });
    return log;
  }

  async list(sessionId: string, limit: number = 10): Promise<TurnLog[]> {
    return this.logs
      .filter(l => l.session_id === sessionId)
      .sort((a, b) => b.turn_index - a.turn_index)
      .slice(0, limit);
  }

  async getLatest(sessionId: string): Promise<TurnLog | null> {
    const sessionLogs = this.logs
      .filter(l => l.session_id === sessionId)
      .sort((a, b) => b.turn_index - a.turn_index);
    return sessionLogs[0] ?? null;
  }
}

// ---------------------------------------------------------------------------
// UserRepo
// ---------------------------------------------------------------------------

export class MockUserRepo implements IUserRepo {
  private store = new Map<string, User>();

  async get(openid: string): Promise<User | null> {
    return this.store.get(openid) ?? null;
  }

  async create(user: User): Promise<User> {
    this.store.set(user.openid, { ...user });
    return user;
  }

  async update(openid: string, patch: Partial<User>): Promise<User> {
    const existing = this.store.get(openid);
    if (!existing) throw new Error(`user not found: ${openid}`);
    const updated = { ...existing, ...patch };
    this.store.set(openid, updated);
    return updated;
  }
}

// ---------------------------------------------------------------------------
// 全局单例（开发用）
// ---------------------------------------------------------------------------

export const mockSessionRepo = new MockSessionRepo();
export const mockTurnLogRepo = new MockTurnLogRepo();
export const mockUserRepo = new MockUserRepo();

// ---------------------------------------------------------------------------
// 组合类（前端本地 Mock 使用，同步版本）
// ---------------------------------------------------------------------------

/** 同步版 Session 存储 */
class SyncSessionStore {
  private store = new Map<string, GameSession>();
  get(id: string): GameSession | null { return this.store.get(id) ?? null; }
  create(session: GameSession): GameSession { this.store.set(session.session_id, { ...session }); return session; }
  update(session: GameSession): GameSession { this.store.set(session.session_id, { ...session }); return session; }
  listByUser(openid: string): GameSession[] { return Array.from(this.store.values()).filter(s => s.openid === openid && !s.deleted_at); }
}

/** 同步版 TurnLog 存储 */
class SyncTurnLogStore {
  private logs: TurnLog[] = [];
  create(log: TurnLog): TurnLog { this.logs.push({ ...log }); return log; }
  getBySession(sessionId: string): TurnLog[] { return this.logs.filter(l => l.session_id === sessionId).sort((a, b) => a.turn_index - b.turn_index); }
}

/** 同步版 User 存储 */
class SyncUserStore {
  private store = new Map<string, User>();
  get(openid: string): User | null { return this.store.get(openid) ?? null; }
  create(user: User): User { this.store.set(user.openid, { ...user }); return user; }
}

/** Mock 数据层组合（前端本地调用用） */
export class MockRepositories {
  sessions = new SyncSessionStore();
  turnLogs = new SyncTurnLogStore();
  users = new SyncUserStore();
}
