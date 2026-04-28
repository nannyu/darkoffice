"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DEFAULT_PROJECT = exports.TURNS_PER_DAY = exports.RESOURCE_DEFINITIONS = exports.INITIAL_STATE = exports.RESOURCE_ORDER = void 0;
exports.defaultProject = defaultProject;
var game_1 = require("../types/game");
Object.defineProperty(exports, "RESOURCE_ORDER", { enumerable: true, get: function () { return game_1.RESOURCE_ORDER; } });
Object.defineProperty(exports, "INITIAL_STATE", { enumerable: true, get: function () { return game_1.INITIAL_STATE; } });
exports.RESOURCE_DEFINITIONS = {
    hp: { label: '生命', track: '生存线', direction: '越高越安全', failure_condition: 'HP <= 0', failure_outcome: '崩溃出局' },
    en: { label: '精力', track: '心智线', direction: '越高越稳定', failure_condition: 'EN <= 0', failure_outcome: '精神崩溃' },
    st: { label: '体力', track: '耐久线', direction: '越高越能硬扛', failure_condition: 'ST <= 0', failure_outcome: '体力耗尽' },
    kpi: { label: '绩效', track: '组织评价线', direction: '越高越能苟住岗位', failure_condition: 'KPI <= 0', failure_outcome: '被开除' },
    risk: { label: '风险', track: '暴雷线', direction: '越低越安全', failure_condition: 'RISK >= 100', failure_outcome: '暴雷结局' },
    cor: { label: '污染', track: '黑化线', direction: '越低越干净', failure_condition: 'COR >= 100', failure_outcome: '黑化结局' },
};
exports.TURNS_PER_DAY = 24;
exports.DEFAULT_PROJECT = {
    id: 'PRJ_WEEKLY', name: '本周交付', progress: 0, target: 5, pressure: 2,
};
function defaultProject() {
    return Object.assign({}, exports.DEFAULT_PROJECT);
}
