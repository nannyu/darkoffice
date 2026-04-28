"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GENERIC_EVENT = exports.EVENTS_BY_CHARACTER = exports.EVENTS = void 0;
exports.EVENTS = [
    { event_id: 'EVT_01', character_id: 'CHR_01', name: '今晚先把新版方案出掉', base_effect: { hp: 0, en: -18, st: -12, kpi: 3, risk: 2, cor: 0 } },
    { event_id: 'EVT_02', character_id: 'CHR_01', name: '这个阶段大家都不容易', base_effect: { hp: 0, en: -10, st: -4, kpi: 0, risk: 1, cor: 0 } },
    { event_id: 'EVT_03', character_id: 'CHR_01', name: '上次那个问题是谁负责', base_effect: { hp: 0, en: -12, st: -5, kpi: -8, risk: 6, cor: 0 } },
    { event_id: 'EVT_05', character_id: 'CHR_02', name: '你顺手帮我处理一下', base_effect: { hp: 0, en: -7, st: -4, kpi: 1, risk: 1, cor: 0 } },
    { event_id: 'EVT_06', character_id: 'CHR_02', name: '这不是大家一起的吗', base_effect: { hp: 0, en: -8, st: -3, kpi: -3, risk: 4, cor: 0 } },
    { event_id: 'EVT_07', character_id: 'CHR_02', name: '先做了再说', base_effect: { hp: 0, en: -7, st: -2, kpi: 0, risk: 3, cor: 0 } },
    { event_id: 'EVT_08', character_id: 'CHR_03', name: '需求先做了再确认', base_effect: { hp: 0, en: -14, st: -9, kpi: 2, risk: 7, cor: 0 } },
    { event_id: 'EVT_09', character_id: 'CHR_03', name: '明天老板要看', base_effect: { hp: -1, en: -18, st: -14, kpi: 4, risk: 4, cor: 0 } },
    { event_id: 'EVT_10', character_id: 'CHR_03', name: '之前不是说好的吗', base_effect: { hp: 0, en: -9, st: -3, kpi: -5, risk: 4, cor: 0 } },
    { event_id: 'EVT_11', character_id: 'CHR_04', name: '来聊聊最近的状态', base_effect: { hp: 0, en: -7, st: -2, kpi: -3, risk: 2, cor: 0 } },
    { event_id: 'EVT_12', character_id: 'CHR_04', name: '绩效沟通安排一下', base_effect: { hp: 0, en: -11, st: -3, kpi: -8, risk: 3, cor: 0 } },
    { event_id: 'EVT_16', character_id: 'CHR_04', name: '你最近态度有点问题', base_effect: { hp: 0, en: -9, st: -3, kpi: -5, risk: 2, cor: 2 } },
    { event_id: 'EVT_17', character_id: 'CHR_05', name: '先倒签一下', base_effect: { hp: -1, en: -6, st: -3, kpi: 2, risk: 15, cor: 8 } },
    { event_id: 'EVT_18', character_id: 'CHR_05', name: '报销材料再补一下', base_effect: { hp: 0, en: -5, st: -2, kpi: 0, risk: 4, cor: 1 } },
    { event_id: 'EVT_19', character_id: 'CHR_05', name: '审计要来了', base_effect: { hp: -3, en: -12, st: -5, kpi: -6, risk: 10, cor: 2 } },
    { event_id: 'EVT_20', character_id: 'CHR_06', name: '你支持哪个方案', base_effect: { hp: 0, en: -9, st: -2, kpi: 0, risk: 8, cor: 5 } },
    { event_id: 'EVT_21', character_id: 'CHR_06', name: '有空聊聊', base_effect: { hp: 0, en: -6, st: -1, kpi: 0, risk: 3, cor: 3 } },
    { event_id: 'EVT_22', character_id: 'CHR_06', name: '你在陈总监那边怎么汇报', base_effect: { hp: 0, en: -11, st: -2, kpi: -1, risk: 7, cor: 4 } },
];
exports.EVENTS_BY_CHARACTER = (() => {
    const map = {};
    for (const event of exports.EVENTS) {
        if (!map[event.character_id])
            map[event.character_id] = [];
        map[event.character_id].push(event);
    }
    return map;
})();
exports.GENERIC_EVENT = {
    event_id: 'EVT_GENERIC',
    character_id: '',
    name: '临时任务压迫',
    base_effect: { hp: 0, en: -8, st: -4, kpi: 0, risk: 2, cor: 0 },
};
