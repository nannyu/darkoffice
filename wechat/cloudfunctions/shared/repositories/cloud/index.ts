/**
 * WeChat cloud database repositories.
 */

import type { GameSession, TurnLog, User } from '../../types/game';
import type { ISessionRepo, ITurnLogRepo, IUserRepo } from '../interfaces';

let cloudSdk: any = null;

function getCloudSdk(): any {
  if (!cloudSdk) {
    // wx-server-sdk is provided by the WeChat cloud function runtime.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    cloudSdk = require('wx-server-sdk');
    cloudSdk.init({ env: cloudSdk.DYNAMIC_CURRENT_ENV });
  }
  return cloudSdk;
}

function db(): any {
  return getCloudSdk().database();
}

function stripId<T extends Record<string, any>>(doc: T | null | undefined): T | null {
  if (!doc) return null;
  const { _id, ...rest } = doc;
  return rest as T;
}

export class CloudSessionRepo implements ISessionRepo {
  private collection() {
    return db().collection('game_sessions');
  }

  async get(sessionId: string): Promise<GameSession | null> {
    try {
      const res = await this.collection().doc(sessionId).get();
      return stripId<GameSession>(res.data);
    } catch (error: any) {
      if (error?.errCode === -1 || /does not exist|not exist/i.test(error?.message || '')) {
        return null;
      }
      throw error;
    }
  }

  async create(session: GameSession): Promise<GameSession> {
    await this.collection().doc(session.session_id).set({ data: session });
    return session;
  }

  async update(sessionId: string, patch: Partial<GameSession>): Promise<GameSession> {
    await this.collection().doc(sessionId).update({ data: patch });
    const updated = await this.get(sessionId);
    if (!updated) throw new Error(`session not found after update: ${sessionId}`);
    return updated;
  }

  async updateForTurn(sessionId: string, expectedTurnIndex: number, patch: Partial<GameSession>): Promise<GameSession> {
    const res = await this.collection()
      .where({
        session_id: sessionId,
        turn_index: expectedTurnIndex,
        status: 'ACTIVE',
        deleted_at: null,
      })
      .update({ data: patch });

    if (!res.stats?.updated) {
      throw new Error('TURN_INDEX_CONFLICT: session changed before update');
    }

    const updated = await this.get(sessionId);
    if (!updated) throw new Error(`session not found after turn update: ${sessionId}`);
    return updated;
  }

  async listByUser(openid: string): Promise<GameSession[]> {
    const res = await this.collection()
      .where({ openid, deleted_at: null })
      .orderBy('updated_at', 'desc')
      .get();
    return (res.data || []).map((doc: GameSession) => stripId<GameSession>(doc) as GameSession);
  }

  async delete(sessionId: string): Promise<boolean> {
    const res = await this.collection()
      .where({ session_id: sessionId, deleted_at: null })
      .update({ data: { deleted_at: Date.now(), updated_at: Date.now() } });
    return Boolean(res.stats?.updated);
  }
}

export class CloudTurnLogRepo implements ITurnLogRepo {
  private collection() {
    return db().collection('turn_logs');
  }

  async append(log: TurnLog): Promise<TurnLog> {
    const logId = `${log.session_id}_${log.turn_index}`;
    await this.collection().doc(logId).set({ data: log });
    return log;
  }

  async list(sessionId: string, limit: number = 10): Promise<TurnLog[]> {
    const res = await this.collection()
      .where({ session_id: sessionId })
      .orderBy('turn_index', 'desc')
      .limit(limit)
      .get();
    return (res.data || []).map((doc: TurnLog) => stripId<TurnLog>(doc) as TurnLog);
  }

  async getLatest(sessionId: string): Promise<TurnLog | null> {
    const logs = await this.list(sessionId, 1);
    return logs[0] ?? null;
  }
}

export class CloudUserRepo implements IUserRepo {
  private collection() {
    return db().collection('users');
  }

  async get(openid: string): Promise<User | null> {
    try {
      const res = await this.collection().doc(openid).get();
      return stripId<User>(res.data);
    } catch (error: any) {
      if (error?.errCode === -1 || /does not exist|not exist/i.test(error?.message || '')) {
        return null;
      }
      throw error;
    }
  }

  async create(user: User): Promise<User> {
    await this.collection().doc(user.openid).set({ data: user });
    return user;
  }

  async update(openid: string, patch: Partial<User>): Promise<User> {
    await this.collection().doc(openid).update({ data: { ...patch, updated_at: Date.now() } });
    const updated = await this.get(openid);
    if (!updated) throw new Error(`user not found after update: ${openid}`);
    return updated;
  }
}

export const cloudSessionRepo = new CloudSessionRepo();
export const cloudTurnLogRepo = new CloudTurnLogRepo();
export const cloudUserRepo = new CloudUserRepo();
