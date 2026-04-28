"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.cloudUserRepo = exports.cloudTurnLogRepo = exports.cloudSessionRepo = exports.CloudUserRepo = exports.CloudTurnLogRepo = exports.CloudSessionRepo = void 0;
let cloudSdk = null;
function getCloudSdk() {
    if (!cloudSdk) {
        cloudSdk = require('wx-server-sdk');
        cloudSdk.init({ env: cloudSdk.DYNAMIC_CURRENT_ENV });
    }
    return cloudSdk;
}
function db() {
    return getCloudSdk().database();
}
function stripId(doc) {
    if (!doc)
        return null;
    const { _id, ...rest } = doc;
    return rest;
}
class CloudSessionRepo {
    collection() {
        return db().collection('game_sessions');
    }
    async get(sessionId) {
        try {
            const res = await this.collection().doc(sessionId).get();
            return stripId(res.data);
        }
        catch (error) {
            if ((error === null || error === void 0 ? void 0 : error.errCode) === -1 || /does not exist|not exist/i.test((error === null || error === void 0 ? void 0 : error.message) || '')) {
                return null;
            }
            throw error;
        }
    }
    async create(session) {
        await this.collection().doc(session.session_id).set({ data: session });
        return session;
    }
    async update(sessionId, patch) {
        await this.collection().doc(sessionId).update({ data: patch });
        const updated = await this.get(sessionId);
        if (!updated)
            throw new Error(`session not found after update: ${sessionId}`);
        return updated;
    }
    async updateForTurn(sessionId, expectedTurnIndex, patch) {
        var _a;
        const res = await this.collection()
            .where({
            session_id: sessionId,
            turn_index: expectedTurnIndex,
            status: 'ACTIVE',
            deleted_at: null,
        })
            .update({ data: patch });
        if (!((_a = res.stats) === null || _a === void 0 ? void 0 : _a.updated)) {
            throw new Error('TURN_INDEX_CONFLICT: session changed before update');
        }
        const updated = await this.get(sessionId);
        if (!updated)
            throw new Error(`session not found after turn update: ${sessionId}`);
        return updated;
    }
    async listByUser(openid) {
        const res = await this.collection()
            .where({ openid, deleted_at: null })
            .orderBy('updated_at', 'desc')
            .get();
        return (res.data || []).map((doc) => stripId(doc));
    }
    async delete(sessionId) {
        var _a;
        const res = await this.collection()
            .where({ session_id: sessionId, deleted_at: null })
            .update({ data: { deleted_at: Date.now(), updated_at: Date.now() } });
        return Boolean((_a = res.stats) === null || _a === void 0 ? void 0 : _a.updated);
    }
}
exports.CloudSessionRepo = CloudSessionRepo;
class CloudTurnLogRepo {
    collection() {
        return db().collection('turn_logs');
    }
    async append(log) {
        const logId = `${log.session_id}_${log.turn_index}`;
        await this.collection().doc(logId).set({ data: log });
        return log;
    }
    async list(sessionId, limit = 10) {
        const res = await this.collection()
            .where({ session_id: sessionId })
            .orderBy('turn_index', 'desc')
            .limit(limit)
            .get();
        return (res.data || []).map((doc) => stripId(doc));
    }
    async getLatest(sessionId) {
        var _a;
        const logs = await this.list(sessionId, 1);
        return (_a = logs[0]) !== null && _a !== void 0 ? _a : null;
    }
}
exports.CloudTurnLogRepo = CloudTurnLogRepo;
class CloudUserRepo {
    collection() {
        return db().collection('users');
    }
    async get(openid) {
        try {
            const res = await this.collection().doc(openid).get();
            return stripId(res.data);
        }
        catch (error) {
            if ((error === null || error === void 0 ? void 0 : error.errCode) === -1 || /does not exist|not exist/i.test((error === null || error === void 0 ? void 0 : error.message) || '')) {
                return null;
            }
            throw error;
        }
    }
    async create(user) {
        await this.collection().doc(user.openid).set({ data: user });
        return user;
    }
    async update(openid, patch) {
        await this.collection().doc(openid).update({ data: { ...patch, updated_at: Date.now() } });
        const updated = await this.get(openid);
        if (!updated)
            throw new Error(`user not found after update: ${openid}`);
        return updated;
    }
}
exports.CloudUserRepo = CloudUserRepo;
exports.cloudSessionRepo = new CloudSessionRepo();
exports.cloudTurnLogRepo = new CloudTurnLogRepo();
exports.cloudUserRepo = new CloudUserRepo();
