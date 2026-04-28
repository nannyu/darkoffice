"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TIME_PERIOD_RULES = void 0;
exports.timePeriodForTurn = timePeriodForTurn;
exports.timePeriodWeightModifiers = timePeriodWeightModifiers;
const resources_1 = require("./resources");
exports.TIME_PERIOD_RULES = [
    { id: '上午', window: '09:00-12:00', turn_start: 0, turn_end: 8, enabled: true, mood: '例行推进', summary: '常规压力平均分布，甲方与上司都可能发难。', weight_modifiers: { CHR_01: 1.0, CHR_02: 1.0, CHR_03: 1.2, CHR_04: 0.8, CHR_05: 1.0, CHR_06: 0.8 } },
    { id: '午休', window: '12:00-13:00', turn_start: 9, turn_end: 11, enabled: true, mood: '表面放松', summary: '同事社交和推活更活跃，制度压力暂时回落。', weight_modifiers: { CHR_01: 0.5, CHR_02: 1.5, CHR_03: 0.5, CHR_04: 0.5, CHR_05: 0.5, CHR_06: 0.3 } },
    { id: '下午', window: '13:00-18:00', turn_start: 12, turn_end: 20, enabled: true, mood: '正式拉扯', summary: '甲方需求和交付压力最容易集中爆发。', weight_modifiers: { CHR_01: 1.0, CHR_02: 1.0, CHR_03: 1.5, CHR_04: 1.0, CHR_05: 1.2, CHR_06: 1.0 } },
    { id: '加班', window: '18:00-21:00', turn_start: 21, turn_end: 23, enabled: true, mood: '透支救火', summary: '上司和甲方权重上升，选择更偏向硬扛与留痕。', weight_modifiers: { CHR_01: 1.5, CHR_02: 0.5, CHR_03: 1.8, CHR_04: 0.8, CHR_05: 1.0, CHR_06: 0.5 } },
    { id: '深夜', window: '21:00+（预留）', turn_start: 24, turn_end: 99, enabled: false, mood: '危险时段', summary: '文档保留的危险时段；当前 24 回合日制下尚未启用。', weight_modifiers: { CHR_01: 1.8, CHR_02: 0.3, CHR_03: 0.8, CHR_04: 1.2, CHR_05: 0.5, CHR_06: 0.3 } },
];
function timePeriodForTurn(turnIndex) {
    const dayTurn = turnIndex % resources_1.TURNS_PER_DAY;
    for (const rule of exports.TIME_PERIOD_RULES) {
        if (!rule.enabled)
            continue;
        if (rule.turn_start <= dayTurn && dayTurn <= rule.turn_end) {
            return Object.assign(Object.assign({}, rule), { weight_modifiers: Object.assign({}, rule.weight_modifiers) });
        }
    }
    const fallback = exports.TIME_PERIOD_RULES[0];
    return Object.assign(Object.assign({}, fallback), { weight_modifiers: Object.assign({}, fallback.weight_modifiers) });
}
function timePeriodWeightModifiers(timePeriod) {
    for (const rule of exports.TIME_PERIOD_RULES) {
        if (rule.id === timePeriod) {
            return Object.assign({}, rule.weight_modifiers);
        }
    }
    return Object.assign({}, exports.TIME_PERIOD_RULES[0].weight_modifiers);
}
