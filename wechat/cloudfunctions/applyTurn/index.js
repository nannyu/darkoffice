"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.main = main;
const engine_1 = require("../shared/engine");
const auth_1 = require("../shared/auth");
const cloud_1 = require("../shared/repositories/cloud");
const input_1 = require("../shared/validators/input");
async function main(event) {
    var _a, _b, _c;
    const openid = (0, auth_1.getOpenidFromContext)();
    const session = await cloud_1.cloudSessionRepo.get(event.session_id);
    if (!session)
        throw new Error('SESSION_NOT_FOUND');
    (0, input_1.validateOwnership)(session, openid);
    (0, input_1.validateSessionForTurn)(session);
    (0, input_1.validateTurnIndex)(session, event.client_turn_index);
    const actionType = (0, input_1.validateActionType)(event.action_type);
    const latestTurn = await cloud_1.cloudTurnLogRepo.getLatest(event.session_id);
    const result = (0, engine_1.resolveTurn)({
        session,
        actionType,
        contentContext: {
            characters: [],
            eventsByCharacter: {},
            eventHazardMap: {},
            actionHazardMap: {},
            characterNameMap: {},
            previousCharacterId: (_a = latestTurn === null || latestTurn === void 0 ? void 0 : latestTurn.character_id) !== null && _a !== void 0 ? _a : null,
            previousEventId: (_b = latestTurn === null || latestTurn === void 0 ? void 0 : latestTurn.event_id) !== null && _b !== void 0 ? _b : null,
        },
    });
    await cloud_1.cloudSessionRepo.updateForTurn(event.session_id, event.client_turn_index, result.sessionPatch);
    await cloud_1.cloudTurnLogRepo.append(result.turnLog);
    const turnResult = {
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
    const sessionSummary = {
        session_id: event.session_id,
        status: (_c = result.sessionPatch.status) !== null && _c !== void 0 ? _c : 'ACTIVE',
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
