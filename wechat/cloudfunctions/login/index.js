"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.main = main;
const auth_1 = require("../shared/auth");
const cloud_1 = require("../shared/repositories/cloud");
async function main(event) {
    const openid = (0, auth_1.getOpenidFromContext)();
    let user = await cloud_1.cloudUserRepo.get(openid);
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
        await cloud_1.cloudUserRepo.create(user);
        isNew = true;
    }
    return { user, is_new: isNew };
}
