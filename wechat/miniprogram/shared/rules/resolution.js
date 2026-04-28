"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.RESOLUTION_TIER_RULES = void 0;
exports.resolutionTierForScore = resolutionTierForScore;
exports.tierByRoll = tierByRoll;
exports.RESOLUTION_TIER_RULES = [
    { id: 'CRITICAL_FAIL', label: '大失败', range: '<= 5', min_score: -999, max_score: 5, multiplier: 1.5, summary: '惩罚放大，还可能额外叠加风险。' },
    { id: 'FAIL', label: '失败', range: '6 - 10', min_score: 6, max_score: 10, multiplier: 1.0, summary: '按事件原始压力完整吃满代价。' },
    { id: 'BARELY', label: '勉强成功', range: '11 - 14', min_score: 11, max_score: 14, multiplier: 0.7, summary: '目标勉强完成，但代价仍然很痛。' },
    { id: 'SUCCESS', label: '成功', range: '15 - 18', min_score: 15, max_score: 18, multiplier: 0.4, summary: '多数惩罚被缓和，收益保留得更完整。' },
    { id: 'CRITICAL_SUCCESS', label: '强成功', range: '>= 19', min_score: 19, max_score: 999, multiplier: 0.2, summary: '高质量脱身，惩罚大幅削弱。' },
];
function resolutionTierForScore(score) {
    for (const rule of exports.RESOLUTION_TIER_RULES) {
        if (rule.min_score <= score && score <= rule.max_score) {
            return Object.assign({}, rule);
        }
    }
    return Object.assign({}, exports.RESOLUTION_TIER_RULES[exports.RESOLUTION_TIER_RULES.length - 1]);
}
function tierByRoll(score) {
    return resolutionTierForScore(score).id;
}
