"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateActionType = validateActionType;
exports.validateSessionForTurn = validateSessionForTurn;
exports.validateTurnIndex = validateTurnIndex;
exports.validateOwnership = validateOwnership;
exports.validateSessionId = validateSessionId;
const actions_1 = require("../rules/actions");
const VALID_ACTION_TYPES = new Set(Object.keys(actions_1.ACTION_RULES));
function validateActionType(actionType) {
    if (!VALID_ACTION_TYPES.has(actionType)) {
        throw new Error(`INVALID_ACTION_TYPE: "${actionType}" is not a valid action`);
    }
    return actionType;
}
function validateSessionForTurn(session) {
    if (session.status !== 'ACTIVE') {
        throw new Error('SESSION_NOT_ACTIVE: session has ended');
    }
    if (session.deleted_at) {
        throw new Error('SESSION_DELETED: session has been deleted');
    }
}
function validateTurnIndex(session, clientTurnIndex) {
    if (clientTurnIndex !== session.turn_index) {
        throw new Error(`TURN_INDEX_CONFLICT: client=${clientTurnIndex}, server=${session.turn_index}`);
    }
}
function validateOwnership(session, openid) {
    if (session.openid !== openid) {
        throw new Error('UNAUTHORIZED: openid does not match session owner');
    }
}
function validateSessionId(sessionId) {
    if (!sessionId || typeof sessionId !== 'string') {
        throw new Error('INVALID_SESSION_ID: sessionId must be a non-empty string');
    }
}
