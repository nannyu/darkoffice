"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.clampState = clampState;
exports.resolveFailure = resolveFailure;
exports.resolveTurn = resolveTurn;
exports.buildNextPrompt = buildNextPrompt;
const actions_1 = require("../rules/actions");
const hazards_1 = require("../rules/hazards");
const resources_1 = require("../rules/resources");
const resolution_1 = require("../rules/resolution");
const time_period_1 = require("../rules/time-period");
const characters_1 = require("../content/characters");
const events_1 = require("../content/events");
function clampState(state) {
    return {
        hp: Math.max(0, Math.min(100, state.hp)),
        en: Math.max(0, Math.min(100, state.en)),
        st: Math.max(0, Math.min(100, state.st)),
        kpi: Math.max(0, Math.min(100, state.kpi)),
        risk: Math.max(0, Math.min(100, state.risk)),
        cor: Math.max(0, Math.min(100, state.cor)),
    };
}
function statusModifier(state) {
    let mod = 0;
    if (state.en >= 70)
        mod += 2;
    else if (state.en < 10)
        mod -= 5;
    else if (state.en < 30)
        mod -= 2;
    if (state.st < 30)
        mod -= 1;
    if (state.kpi < 40)
        mod -= 1;
    if (state.risk >= 50)
        mod -= 1;
    return mod;
}
function deriveStatuses(state, eventId) {
    const statuses = [];
    if (state.en < 10)
        statuses.push({ id: 'STATUS_EXHAUSTED', name: '濒临崩溃', duration: 1 });
    else if (state.en < 30)
        statuses.push({ id: 'STATUS_LOW_EN', name: '低精力', duration: 1 });
    if (state.st < 30)
        statuses.push({ id: 'STATUS_LOW_ST', name: '低体力', duration: 1 });
    if (state.kpi < 40)
        statuses.push({ id: 'STATUS_LOW_KPI', name: '危险绩效', duration: 1 });
    if (state.risk >= 50)
        statuses.push({ id: 'STATUS_HIGH_RISK', name: '高风险', duration: 1 });
    if (state.cor >= 50)
        statuses.push({ id: 'STATUS_HIGH_COR', name: '高污染', duration: 1 });
    if (['EVT_03', 'EVT_11', 'EVT_16'].includes(eventId)) {
        statuses.push({ id: 'STATUS_UNDER_WATCH', name: '被盯上', duration: 2 });
    }
    return statuses;
}
function timePeriod(turnIndex) {
    return (0, time_period_1.timePeriodForTurn)(turnIndex).id;
}
function mergeDelta(...parts) {
    var _a;
    const merged = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
    for (const part of parts) {
        for (const key of Object.keys(merged)) {
            merged[key] += (_a = part[key]) !== null && _a !== void 0 ? _a : 0;
        }
    }
    return merged;
}
function resolveFailure(state) {
    if (state.hp <= 0)
        return 'HP_DEPLETED';
    if (state.en <= 0)
        return 'EN_DEPLETED';
    if (state.st <= 0)
        return 'ST_DEPLETED';
    if (state.kpi <= 0)
        return 'KPI_DEPLETED';
    if (state.risk >= 100)
        return 'RISK_OVERFLOW';
    if (state.cor >= 100)
        return 'COR_OVERFLOW';
    return null;
}
function tickHazards(hazards) {
    const delta = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
    const remaining = [];
    for (const hazard of hazards) {
        const current = { ...hazard, countdown: hazard.countdown - 1 };
        if (current.countdown <= 0) {
            const s = current.severity;
            delta.hp -= 2 * s;
            delta.kpi -= 4 * s;
            delta.risk += 6 * s;
        }
        else {
            remaining.push(current);
        }
    }
    return { remaining, delta };
}
function tickProjects(projects, actionType) {
    const delta = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
    const progressActions = ['DIRECT_EXECUTE', 'WORK_OVERTIME', 'REQUEST_CONFIRMATION'];
    const updated = [];
    for (const project of projects) {
        const current = { ...project };
        const pressure = current.pressure;
        delta.en -= pressure;
        delta.st -= Math.max(1, Math.floor(pressure / 2));
        if (progressActions.includes(actionType)) {
            current.progress += 1;
            delta.kpi += 1;
        }
        if (current.progress >= current.target) {
            delta.kpi += 3;
            delta.risk -= 2;
            continue;
        }
        updated.push(current);
    }
    return { updated, delta };
}
function newHazard(eventId, actionType, ctx) {
    const eventHazard = ctx.eventHazardMap[eventId] || hazards_1.EVENT_HAZARD_MAP[eventId];
    if (eventHazard)
        return { ...eventHazard };
    const actionHazard = ctx.actionHazardMap[actionType] || hazards_1.ACTION_HAZARD_MAP[actionType];
    if (actionHazard)
        return { ...actionHazard };
    return null;
}
function weightedPick(options) {
    const pool = options.map(([item]) => item);
    const weights = options.map(([, w]) => Math.max(1, w));
    const totalWeight = weights.reduce((s, w) => s + w, 0);
    let r = Math.random() * totalWeight;
    for (let i = 0; i < pool.length; i++) {
        r -= weights[i];
        if (r <= 0)
            return pool[i];
    }
    return pool[pool.length - 1];
}
function pickCharacter(session, ctx, timePeriodId) {
    var _a;
    const allCharacters = [...characters_1.CHARACTERS, ...ctx.characters];
    const periodMods = (0, time_period_1.timePeriodWeightModifiers)(timePeriodId);
    const weighted = [];
    for (const c of allCharacters) {
        let w = c.base_weight;
        w = Math.round(w * ((_a = periodMods[c.character_id]) !== null && _a !== void 0 ? _a : 1.0));
        if (c.character_id === 'CHR_04' && session.state.kpi < 40)
            w = Math.round(w * 2);
        if (c.character_id === 'CHR_05' && session.state.risk >= 50)
            w = Math.round(w * 1.6);
        if (c.character_id === 'CHR_06' && session.state.cor >= 50)
            w = Math.round(w * 1.6);
        weighted.push([c.character_id, w]);
    }
    if (ctx.previousCharacterId) {
        for (let i = 0; i < weighted.length; i++) {
            if (weighted[i][0] === ctx.previousCharacterId) {
                weighted[i] = [weighted[i][0], Math.round(weighted[i][1] * 0.45)];
            }
        }
    }
    return weightedPick(weighted);
}
function pickEvent(characterId, ctx) {
    const builtIn = events_1.EVENTS_BY_CHARACTER[characterId] || [];
    const custom = ctx.eventsByCharacter[characterId] || [];
    const pool = [...builtIn, ...custom];
    if (pool.length === 0) {
        return { eventId: events_1.GENERIC_EVENT.event_id, name: events_1.GENERIC_EVENT.name, baseEffect: { ...events_1.GENERIC_EVENT.base_effect } };
    }
    const weighted = pool.map(e => [
        e,
        e.event_id === ctx.previousEventId ? 2 : 10,
    ]);
    const totalWeight = weighted.reduce((s, [, w]) => s + w, 0);
    let r = Math.random() * totalWeight;
    for (const [event, w] of weighted) {
        r -= w;
        if (r <= 0) {
            return { eventId: event.event_id, name: event.name, baseEffect: { ...event.base_effect } };
        }
    }
    const last = pool[pool.length - 1];
    return { eventId: last.event_id, name: last.name, baseEffect: { ...last.base_effect } };
}
function resolveTurn(input) {
    var _a;
    const { session, actionType, contentContext: ctx } = input;
    const newTurn = session.turn_index + 1;
    const prevDayTurns = Math.floor(session.turn_index / resources_1.TURNS_PER_DAY);
    const newDayTurns = Math.floor(newTurn / resources_1.TURNS_PER_DAY);
    const newDay = session.day + (newDayTurns - prevDayTurns);
    const timePeriodId = timePeriod(newTurn);
    const characterId = pickCharacter(session, ctx, timePeriodId);
    const event = pickEvent(characterId, ctx);
    const actionMod = (_a = actions_1.ACTION_MODIFIERS[actionType]) !== null && _a !== void 0 ? _a : 0;
    const statusMod = statusModifier(session.state);
    const roll = Math.floor(Math.random() * 20) + 1;
    const score = roll + actionMod + statusMod;
    const tierRule = (0, resolution_1.resolutionTierForScore)(score);
    const tier = tierRule.id;
    const multiplier = tierRule.multiplier;
    const PENALTY_WHEN_POSITIVE = new Set(['risk', 'cor']);
    const baseEventDelta = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
    for (const [k, v] of Object.entries(event.baseEffect)) {
        const key = k;
        if (v >= 0 && !PENALTY_WHEN_POSITIVE.has(k)) {
            baseEventDelta[key] = Math.round(v * (2.0 - multiplier));
        }
        else {
            baseEventDelta[key] = Math.round(v * multiplier);
        }
    }
    const actionDelta = { hp: 0, en: 0, st: 0, kpi: 0, risk: 0, cor: 0 };
    if (tier === 'CRITICAL_FAIL')
        actionDelta.risk += 5;
    if (actionType === 'EMAIL_TRACE') {
        actionDelta.risk -= 8;
    }
    if (actionType === 'SHIFT_BLAME') {
        actionDelta.cor += 6;
        actionDelta.risk += 3;
    }
    if (actionType === 'WORK_OVERTIME') {
        actionDelta.en -= 4;
        actionDelta.st -= 4;
    }
    if (actionType === 'RECOVERY_BREAK') {
        actionDelta.en += 10;
        actionDelta.st += 6;
        actionDelta.kpi -= 2;
    }
    let hazards = [...session.hazards];
    let projects = [...session.projects];
    const { remaining: tickedHazards, delta: hazardDelta } = tickHazards(hazards);
    hazards = tickedHazards;
    const { updated: tickedProjects, delta: projectDelta } = tickProjects(projects, actionType);
    projects = tickedProjects;
    const maybeHazard = newHazard(event.eventId, actionType, ctx);
    if (maybeHazard && !hazards.some(h => h.id === maybeHazard.id)) {
        hazards.push({ ...maybeHazard });
    }
    const delta = mergeDelta(baseEventDelta, actionDelta, hazardDelta, projectDelta);
    if (projects.length === 0) {
        projects = [(0, resources_1.defaultProject)()];
    }
    const newRawState = {
        hp: session.state.hp + delta.hp,
        en: session.state.en + delta.en,
        st: session.state.st + delta.st,
        kpi: session.state.kpi + delta.kpi,
        risk: session.state.risk + delta.risk,
        cor: session.state.cor + delta.cor,
    };
    const newClampedState = clampState(newRawState);
    const statuses = deriveStatuses(newClampedState, event.eventId);
    const failureType = resolveFailure(newClampedState);
    let ending;
    if (failureType) {
        const failureRule = [
            { type: 'HP_DEPLETED', title: '崩溃结局', description: '你的身体终于撑不住了……' },
            { type: 'EN_DEPLETED', title: '精神崩溃结局', description: '精神已经完全崩溃……' },
            { type: 'ST_DEPLETED', title: '体力耗尽结局', description: '体力彻底耗尽……' },
            { type: 'KPI_DEPLETED', title: '被开除结局', description: '绩效归零，HR找你谈话了……' },
            { type: 'RISK_OVERFLOW', title: '暴雷结局', description: '风险值爆表，雷终于炸了……' },
            { type: 'COR_OVERFLOW', title: '黑化结局', description: '你已经被这个系统完全同化……' },
        ].find(r => r.type === failureType);
        ending = failureRule ? { type: failureType, title: failureRule.title, description: failureRule.description } : undefined;
    }
    const turnLog = {
        session_id: session.session_id,
        openid: session.openid,
        turn_index: newTurn,
        day: newDay,
        time_period: timePeriodId,
        character_id: characterId,
        event_id: event.eventId,
        action_type: actionType,
        action_mod: actionMod,
        roll_value: roll,
        total_score: score,
        result_tier: tier,
        failure_type: failureType,
        delta,
        state_after: newClampedState,
        created_at: Date.now(),
    };
    const sessionPatch = {
        turn_index: newTurn,
        day: newDay,
        state: newClampedState,
        statuses,
        hazards,
        projects,
        status: failureType ? 'ENDED' : 'ACTIVE',
        updated_at: Date.now(),
    };
    const nameMap = { ...characters_1.CHARACTER_NAME_MAP, ...ctx.characterNameMap };
    const nextTimePeriodId = timePeriod(newTurn + 1);
    const nextCharacterId = pickCharacter({ ...session, turn_index: newTurn, state: newClampedState }, { ...ctx, previousCharacterId: characterId, previousEventId: event.eventId }, nextTimePeriodId);
    const nextEvent = pickEvent(nextCharacterId, {
        ...ctx,
        previousCharacterId: characterId,
        previousEventId: event.eventId,
    });
    const riskTip = newClampedState.risk >= 40
        ? '风险偏高，优先考虑留痕或缩小范围。'
        : '保持节奏，避免口头承诺。';
    const nextPrompt = {
        turn_index: newTurn + 1,
        day: newDay,
        time_period: nextTimePeriodId,
        status_bar: {
            '生命': `${newClampedState.hp}/100`,
            '精力': `${newClampedState.en}/100`,
            '体力': `${newClampedState.st}/100`,
            '绩效': newClampedState.kpi,
            '风险': newClampedState.risk,
            '污染': newClampedState.cor,
        },
        event_summary: {
            actor: nameMap[nextCharacterId] || '未知角色',
            event: nextEvent.name,
            prompt: `${nameMap[nextCharacterId] || '某人'} 发来新压力：${nextEvent.name}`,
        },
        risk_tip: riskTip,
        options: (0, actions_1.buildOptions)(newClampedState),
        input_hint: '回复编号或直接说你的应对方式。',
    };
    return {
        turnLog,
        sessionPatch,
        nextPrompt,
        ending,
    };
}
function buildNextPrompt(session, ctx) {
    const nextTurn = session.turn_index + 1;
    const nextTimePeriodId = timePeriod(nextTurn);
    const nameMap = { ...characters_1.CHARACTER_NAME_MAP, ...ctx.characterNameMap };
    const characterId = pickCharacter(session, ctx, nextTimePeriodId);
    const event = pickEvent(characterId, ctx);
    const riskTip = session.state.risk >= 40
        ? '风险偏高，优先考虑留痕或缩小范围。'
        : '保持节奏，避免口头承诺。';
    return {
        turn_index: nextTurn,
        day: session.day,
        time_period: nextTimePeriodId,
        status_bar: {
            '生命': `${session.state.hp}/100`,
            '精力': `${session.state.en}/100`,
            '体力': `${session.state.st}/100`,
            '绩效': session.state.kpi,
            '风险': session.state.risk,
            '污染': session.state.cor,
        },
        event_summary: {
            actor: nameMap[characterId] || '未知角色',
            event: event.name,
            prompt: `${nameMap[characterId] || '某人'} 发来新压力：${event.name}`,
        },
        risk_tip: riskTip,
        options: (0, actions_1.buildOptions)(session.state),
        input_hint: '回复编号或直接说你的应对方式。',
    };
}
