"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.main = main;
const engine_1 = require("../shared/engine");
const auth_1 = require("../shared/auth");
const cloud_1 = require("../shared/repositories/cloud");
async function main(event) {
    var _a, _b;
    const openid = (0, auth_1.getOpenidFromContext)();
    const session = await cloud_1.cloudSessionRepo.get(event.session_id);
    if (!session)
        throw new Error('SESSION_NOT_FOUND');
    if (session.openid !== openid)
        throw new Error('UNAUTHORIZED');
    const latestTurn = await cloud_1.cloudTurnLogRepo.getLatest(event.session_id);
    return (0, engine_1.buildNextPrompt)(session, {
        characters: [],
        eventsByCharacter: {},
        eventHazardMap: {},
        actionHazardMap: {},
        characterNameMap: {},
        previousCharacterId: (_a = latestTurn === null || latestTurn === void 0 ? void 0 : latestTurn.character_id) !== null && _a !== void 0 ? _a : null,
        previousEventId: (_b = latestTurn === null || latestTurn === void 0 ? void 0 : latestTurn.event_id) !== null && _b !== void 0 ? _b : null,
    });
}
