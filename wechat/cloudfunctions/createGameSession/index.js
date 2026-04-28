"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.main = main;
const resources_1 = require("../shared/rules/resources");
const engine_1 = require("../shared/engine");
const auth_1 = require("../shared/auth");
const cloud_1 = require("../shared/repositories/cloud");
async function main(event) {
    var _a;
    const openid = (0, auth_1.getOpenidFromContext)();
    const sessionId = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const session = {
        session_id: sessionId,
        openid,
        storyline_id: (_a = event.storyline_id) !== null && _a !== void 0 ? _a : null,
        storyline_version: null,
        rule_set_id: 'rules_2026_04',
        day: 1,
        turn_index: 0,
        state: { ...resources_1.INITIAL_STATE },
        statuses: [],
        hazards: [],
        projects: [(0, resources_1.defaultProject)()],
        current_act_index: 0,
        status: 'ACTIVE',
        created_at: Date.now(),
        updated_at: Date.now(),
        deleted_at: null,
    };
    await cloud_1.cloudSessionRepo.create(session);
    const user = await cloud_1.cloudUserRepo.get(openid);
    if (user) {
        await cloud_1.cloudUserRepo.update(openid, { total_games: user.total_games + 1 });
    }
    const firstPrompt = (0, engine_1.buildNextPrompt)(session, {
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
