"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.api = void 0;
const mock_1 = require("../shared/repositories/mock");
const engine_1 = require("../shared/engine");
const input_1 = require("../shared/validators/input");
const resources_1 = require("../shared/rules/resources");
const actions_1 = require("../shared/rules/actions");
const content_1 = require("../shared/content");
const hazards_1 = require("../shared/rules/hazards");
const resolution_1 = require("../shared/rules/resolution");
const time_period_1 = require("../shared/rules/time-period");
const repos = new mock_1.MockRepositories();
function generateId() {
    return 'sess_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
}
const RESOURCE_LABELS = {
    hp: { label: '生命', color: 'var(--color-hp)' },
    en: { label: '精神', color: 'var(--color-en)' },
    st: { label: '体力', color: 'var(--color-st)' },
    kpi: { label: 'KPI', color: 'var(--color-kpi)' },
    risk: { label: '风险', color: 'var(--color-risk)' },
    cor: { label: '腐化', color: 'var(--color-cor)' },
};
function buildDeltaList(delta) {
    return Object.entries(delta).map(([key, val]) => {
        var _a, _b;
        return ({
            key,
            label: ((_a = RESOURCE_LABELS[key]) === null || _a === void 0 ? void 0 : _a.label) || key,
            value: val,
            display: val > 0 ? `+${val}` : val === 0 ? '0' : `${val}`,
            positive: val > 0,
            color: ((_b = RESOURCE_LABELS[key]) === null || _b === void 0 ? void 0 : _b.color) || '#fff',
        });
    });
}
function contentContextForSession(session) {
    const characterNameMap = {};
    const chars = content_1.CHARACTERS.map(c => (Object.assign({}, c)));
    for (const c of chars) {
        characterNameMap[c.character_id] = c.name;
    }
    const ebc = {};
    for (const [k, arr] of Object.entries(content_1.EVENTS_BY_CHARACTER)) {
        ebc[k] = arr.map(e => (Object.assign({}, e)));
    }
    const previousTurns = repos.turnLogs.getBySession(session.session_id);
    const lastTurn = previousTurns.length > 0 ? previousTurns[previousTurns.length - 1] : null;
    return {
        characters: chars,
        eventsByCharacter: ebc,
        eventHazardMap: Object.assign({}, hazards_1.EVENT_HAZARD_MAP),
        actionHazardMap: Object.assign({}, hazards_1.ACTION_HAZARD_MAP),
        characterNameMap,
        previousCharacterId: (lastTurn === null || lastTurn === void 0 ? void 0 : lastTurn.character_id) || null,
        previousEventId: (lastTurn === null || lastTurn === void 0 ? void 0 : lastTurn.event_id) || null,
    };
}
function promptViewFromSession(session) {
    const ctx = contentContextForSession(session);
    const characterId = session.state.risk > 60
        ? chars(ctx)[Math.floor(Math.random() * chars(ctx).length)].character_id
        : chars(ctx)[0].character_id;
    const events = ctx.eventsByCharacter[characterId] || [];
    const event = events.length > 0
        ? events[Math.floor(Math.random() * events.length)]
        : { event_id: 'EVT_001', name: '突发状况', character_id: characterId, base_effect: { hp: -10, en: -5, st: -5, kpi: -5, risk: 5, cor: 0 }, flavor_text: '又出事了...' };
    const options = (0, actions_1.buildOptions)(session.state);
    const tp = (0, time_period_1.timePeriodForTurn)(session.turn_index);
    return {
        turn_index: session.turn_index,
        day: session.day,
        time_period: tp.id,
        event_summary: {
            actor: ctx.characterNameMap[characterId] || characterId,
            event: event.name,
            prompt: event.flavor_text || `${ctx.characterNameMap[characterId] || characterId}找上门来了...`,
        },
        options,
        risk_tip: session.state.risk > 60 ? '⚠ 风险值偏高，注意行动选择' : '',
        state: Object.assign({}, session.state),
        hazards: session.hazards.map(h => ({ id: h.id, name: h.name, countdown: h.countdown, severity: h.severity })),
        projects: session.projects.map(p => ({ id: p.id, name: p.name, progress: p.progress, target: p.target })),
    };
}
function chars(ctx) {
    return ctx.characters;
}
exports.api = {
    createGameSession(params) {
        const sessionId = generateId();
        const now = Date.now();
        const session = {
            session_id: sessionId,
            openid: params.openid,
            storyline_id: params.storyline_id || null,
            storyline_version: null,
            rule_set_id: null,
            day: 1,
            turn_index: 0,
            state: Object.assign({}, resources_1.INITIAL_STATE),
            statuses: [],
            hazards: [],
            projects: [],
            current_act_index: 0,
            status: 'ACTIVE',
            created_at: now,
            updated_at: now,
            deleted_at: null,
        };
        repos.sessions.create(session);
        const prompt = promptViewFromSession(session);
        return { session, prompt };
    },
    getNextPrompt(params) {
        const session = repos.sessions.get(params.session_id);
        if (!session)
            throw new Error(`Session not found: ${params.session_id}`);
        (0, input_1.validateOwnership)(session, params.openid);
        return promptViewFromSession(session);
    },
    applyTurn(params) {
        (0, input_1.validateSessionId)(params.session_id);
        (0, input_1.validateActionType)(params.action_type);
        const session = repos.sessions.get(params.session_id);
        if (!session)
            throw new Error(`Session not found: ${params.session_id}`);
        (0, input_1.validateOwnership)(session, params.openid);
        (0, input_1.validateTurnIndex)(session, params.client_turn_index);
        if (session.status === 'ENDED')
            throw new Error('Game already ended');
        const ctx = contentContextForSession(session);
        const result = (0, engine_1.resolveTurn)({ session, actionType: params.action_type, contentContext: ctx });
        const updatedSession = Object.assign(Object.assign(Object.assign({}, session), result.sessionPatch), { updated_at: Date.now() });
        const failure = (0, hazards_1.checkFailure)(updatedSession.state);
        if (failure)
            updatedSession.status = 'ENDED';
        repos.sessions.update(updatedSession);
        repos.turnLogs.create(result.turnLog);
        const tierRule = (0, resolution_1.resolutionTierForScore)(result.turnLog.total_score);
        const turnResult = {
            roll_value: result.turnLog.roll_value,
            total_score: result.turnLog.total_score,
            result_tier: result.turnLog.result_tier,
            result_tier_label: tierRule.label,
            multiplier: tierRule.multiplier,
            delta: Object.assign({}, result.turnLog.delta),
            deltaList: buildDeltaList(result.turnLog.delta),
        };
        let nextPrompt = null;
        if (!failure) {
            nextPrompt = promptViewFromSession(updatedSession);
        }
        const sessionSummary = {
            state: Object.assign({}, updatedSession.state),
            day: updatedSession.day,
            time_period: (0, time_period_1.timePeriodForTurn)(updatedSession.turn_index).id,
            turn_index: updatedSession.turn_index,
            status: updatedSession.status,
            hazards: updatedSession.hazards.map(h => ({ id: h.id, name: h.name, countdown: h.countdown, severity: h.severity })),
            projects: updatedSession.projects.map(p => ({ id: p.id, name: p.name, progress: p.progress, target: p.target })),
        };
        const ending = failure ? {
            type: failure,
            title: getEndingTitle(failure),
            description: getEndingDesc(failure),
        } : null;
        return { turn_result: turnResult, session_summary: sessionSummary, next_prompt: nextPrompt, ending };
    },
};
function getEndingTitle(failure) {
    const map = {
        HP_DEPLETED: '身心崩溃', EN_DEPLETED: '精神崩溃', ST_DEPLETED: '体力耗尽',
        KPI_DEPLETED: '被开除', RISK_OVERFLOW: '暴雷', COR_OVERFLOW: '黑化',
    };
    return map[failure] || '未知结局';
}
function getEndingDesc(failure) {
    const map = {
        HP_DEPLETED: '你的身体再也撑不住了，在职场的重压下彻底崩溃。',
        EN_DEPLETED: '精神上的消耗已经到达极限，你再也提不起任何干劲。',
        ST_DEPLETED: '长期的高强度工作让你的体力完全透支。',
        KPI_DEPLETED: 'KPI 连续不达标，公司决定不再留你。',
        RISK_OVERFLOW: '你积累的风险终于暴雷，所有暗箱操作被曝光。',
        COR_OVERFLOW: '在黑暗中浸淫太久，你已经变成了曾经最讨厌的人。',
    };
    return map[failure] || '游戏结束。';
}
