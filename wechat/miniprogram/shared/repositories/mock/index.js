"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MockRepositories = exports.mockUserRepo = exports.mockTurnLogRepo = exports.mockSessionRepo = exports.MockUserRepo = exports.MockTurnLogRepo = exports.MockSessionRepo = void 0;
class MockSessionRepo {
    constructor() {
        this.store = new Map();
    }
    async get(sessionId) {
        var _a;
        return (_a = this.store.get(sessionId)) !== null && _a !== void 0 ? _a : null;
    }
    async create(session) {
        this.store.set(session.session_id, Object.assign({}, session));
        return session;
    }
    async update(sessionId, patch) {
        var _a;
        const existing = this.store.get(sessionId);
        if (!existing)
            throw new Error(`session not found: ${sessionId}`);
        const updated = Object.assign(Object.assign(Object.assign({}, existing), patch), { state: (_a = patch.state) !== null && _a !== void 0 ? _a : existing.state });
        this.store.set(sessionId, updated);
        return updated;
    }
    async listByUser(openid) {
        return Array.from(this.store.values()).filter(s => s.openid === openid && !s.deleted_at);
    }
    async delete(sessionId) {
        const existing = this.store.get(sessionId);
        if (!existing)
            return false;
        existing.deleted_at = Date.now();
        this.store.set(sessionId, existing);
        return true;
    }
}
exports.MockSessionRepo = MockSessionRepo;
class MockTurnLogRepo {
    constructor() {
        this.logs = [];
    }
    async append(log) {
        this.logs.push(Object.assign({}, log));
        return log;
    }
    async list(sessionId, limit = 10) {
        return this.logs
            .filter(l => l.session_id === sessionId)
            .sort((a, b) => b.turn_index - a.turn_index)
            .slice(0, limit);
    }
    async getLatest(sessionId) {
        var _a;
        const sessionLogs = this.logs
            .filter(l => l.session_id === sessionId)
            .sort((a, b) => b.turn_index - a.turn_index);
        return (_a = sessionLogs[0]) !== null && _a !== void 0 ? _a : null;
    }
}
exports.MockTurnLogRepo = MockTurnLogRepo;
class MockUserRepo {
    constructor() {
        this.store = new Map();
    }
    async get(openid) {
        var _a;
        return (_a = this.store.get(openid)) !== null && _a !== void 0 ? _a : null;
    }
    async create(user) {
        this.store.set(user.openid, Object.assign({}, user));
        return user;
    }
    async update(openid, patch) {
        const existing = this.store.get(openid);
        if (!existing)
            throw new Error(`user not found: ${openid}`);
        const updated = Object.assign(Object.assign({}, existing), patch);
        this.store.set(openid, updated);
        return updated;
    }
}
exports.MockUserRepo = MockUserRepo;
exports.mockSessionRepo = new MockSessionRepo();
exports.mockTurnLogRepo = new MockTurnLogRepo();
exports.mockUserRepo = new MockUserRepo();
class SyncSessionStore {
    constructor() {
        this.store = new Map();
    }
    get(id) { var _a; return (_a = this.store.get(id)) !== null && _a !== void 0 ? _a : null; }
    create(session) { this.store.set(session.session_id, Object.assign({}, session)); return session; }
    update(session) { this.store.set(session.session_id, Object.assign({}, session)); return session; }
    listByUser(openid) { return Array.from(this.store.values()).filter(s => s.openid === openid && !s.deleted_at); }
}
class SyncTurnLogStore {
    constructor() {
        this.logs = [];
    }
    create(log) { this.logs.push(Object.assign({}, log)); return log; }
    getBySession(sessionId) { return this.logs.filter(l => l.session_id === sessionId).sort((a, b) => a.turn_index - b.turn_index); }
}
class SyncUserStore {
    constructor() {
        this.store = new Map();
    }
    get(openid) { var _a; return (_a = this.store.get(openid)) !== null && _a !== void 0 ? _a : null; }
    create(user) { this.store.set(user.openid, Object.assign({}, user)); return user; }
}
class MockRepositories {
    constructor() {
        this.sessions = new SyncSessionStore();
        this.turnLogs = new SyncTurnLogStore();
        this.users = new SyncUserStore();
    }
}
exports.MockRepositories = MockRepositories;
