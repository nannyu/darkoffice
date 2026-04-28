"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CHARACTER_WEIGHT_RULES = exports.FAILURE_RULES = exports.STATUS_RULES = exports.ACTION_HAZARD_MAP = exports.EVENT_HAZARD_MAP = void 0;
exports.checkFailure = checkFailure;
exports.EVENT_HAZARD_MAP = {
    EVT_04: { id: 'HZD_RESPONSIBILITY', name: '责任未明确', countdown: 3, severity: 2 },
    EVT_06: { id: 'HZD_RESPONSIBILITY', name: '责任未明确', countdown: 3, severity: 2 },
    EVT_07: { id: 'HZD_ORAL_PROMISE', name: '口头承诺', countdown: 2, severity: 1 },
    EVT_08: { id: 'HZD_REQ_UNCONFIRMED', name: '需求未确认', countdown: 3, severity: 1 },
    EVT_10: { id: 'HZD_ORAL_PROMISE', name: '口头承诺', countdown: 2, severity: 1 },
    EVT_17: { id: 'HZD_BACKDATED_DOC', name: '倒签文件', countdown: 5, severity: 2 },
    EVT_18: { id: 'HZD_MISSING_RECEIPT', name: '报销缺材料', countdown: 3, severity: 1 },
    EVT_19: { id: 'HZD_COMPLIANCE', name: '合规隐患', countdown: 3, severity: 2 },
    EVT_23: { id: 'HZD_WEEKLY_REPORT', name: '周报未交', countdown: 2, severity: 1 },
    EVT_24: { id: 'HZD_UNREAD_MSG', name: '未回消息', countdown: 2, severity: 1 },
};
exports.ACTION_HAZARD_MAP = {
    SHIFT_BLAME: { id: 'HZD_ACTION_BLAME', name: '甩锅痕迹', countdown: 3, severity: 1 },
    DELAY_AVOID: { id: 'HZD_ACTION_DELAY', name: '拖延积压', countdown: 2, severity: 1 },
};
exports.STATUS_RULES = [
    { id: 'STATUS_EXHAUSTED', name: '濒临崩溃', trigger: 'EN < 10', duration: 1, impact: '判定严重受挫。' },
    { id: 'STATUS_LOW_EN', name: '低精力', trigger: '10 <= EN < 30', duration: 1, impact: '行动效率下降。' },
    { id: 'STATUS_LOW_ST', name: '低体力', trigger: 'ST < 30', duration: 1, impact: '持续作业更容易翻车。' },
    { id: 'STATUS_LOW_KPI', name: '危险绩效', trigger: 'KPI < 40', duration: 1, impact: '组织压力会继续抬头。' },
    { id: 'STATUS_HIGH_RISK', name: '高风险', trigger: 'RISK >= 50', duration: 1, impact: '暴雷链条被放大。' },
    { id: 'STATUS_HIGH_COR', name: '高污染', trigger: 'COR >= 50', duration: 1, impact: '政治型与灰色后果增强。' },
    { id: 'STATUS_UNDER_WATCH', name: '被盯上', trigger: 'EVT_03 / EVT_11 / EVT_16', duration: 2, impact: '后续会继续收到敌意追击。' },
];
exports.FAILURE_RULES = [
    { id: 'HP_DEPLETED', label: '崩溃结局', condition: 'HP <= 0', priority: 1 },
    { id: 'EN_DEPLETED', label: '精神崩溃结局', condition: 'EN <= 0', priority: 2 },
    { id: 'ST_DEPLETED', label: '体力耗尽结局', condition: 'ST <= 0', priority: 3 },
    { id: 'KPI_DEPLETED', label: '被开除结局', condition: 'KPI <= 0', priority: 4 },
    { id: 'RISK_OVERFLOW', label: '暴雷结局', condition: 'RISK >= 100', priority: 5 },
    { id: 'COR_OVERFLOW', label: '黑化结局', condition: 'COR >= 100', priority: 6 },
];
exports.CHARACTER_WEIGHT_RULES = [
    { id: 'TIME_PERIOD', scope: 'global', label: '时间段修正', condition: '按当前时间段读取角色权重表', effect: '不同时段改变角色出现概率' },
    { id: 'REPEAT_DAMPING', scope: 'global', label: '重复抑制', condition: '若与上一回合是同一角色', effect: '该角色权重乘以 0.45' },
    { id: 'HR_LOW_KPI', scope: 'character', character_id: 'CHR_04', label: '绩效压迫', condition: 'KPI < 40', effect: 'HR 权重乘以 2.0' },
    { id: 'FINANCE_HIGH_RISK', scope: 'character', character_id: 'CHR_05', label: '审计逼近', condition: 'RISK >= 50', effect: '财务关键人权重乘以 1.6' },
    { id: 'DIRECTOR_HIGH_COR', scope: 'character', character_id: 'CHR_06', label: '站队加压', condition: 'COR >= 50', effect: '派系总监权重乘以 1.6' },
];
function checkFailure(state) {
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
