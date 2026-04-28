"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ACTION_OPTION_POLICY = exports.ACTION_DISPLAY = exports.ACTION_MODIFIERS = exports.ACTION_RULES = void 0;
exports.buildOptions = buildOptions;
exports.ACTION_RULES = {
    DIRECT_EXECUTE: { title: '立即执行', summary: '保住绩效，但精力和体力消耗较高', modifier: 2, category: '硬扛推进', tradeoff: '短期稳 KPI，长期透支 EN/ST。' },
    EMAIL_TRACE: { title: '邮件留痕', summary: '降低后续背锅风险，但会激怒施压方', modifier: 3, category: '证据管理', tradeoff: '主动降低风险，但要承受关系摩擦。' },
    NARROW_SCOPE: { title: '缩小范围', summary: '降低本回合压力，但可能留下后续争议', modifier: 1, category: '边界管理', tradeoff: '当回合减压，后续可能转成隐患。' },
    SOFT_REFUSE: { title: '温和拒绝', summary: '保住边界，但绩效可能受损', modifier: 0, category: '保守防守', tradeoff: '降低透支，但容易牺牲 KPI。' },
    WORK_OVERTIME: { title: '熬夜硬扛', summary: '短期稳住局面，但透支精力和体力', modifier: 4, category: '紧急救火', tradeoff: '高成功率换来更重的透支。' },
    REQUEST_CONFIRMATION: { title: '需求确认', summary: '减少口头风险，但会增加沟通摩擦', modifier: 2, category: '降风险', tradeoff: '以沟通成本换后续确定性。' },
    DELAY_AVOID: { title: '拖延规避', summary: '暂时减压，但后续隐患会累积', modifier: -1, category: '回避策略', tradeoff: '把现在的痛换成以后的雷。' },
    SHIFT_BLAME: { title: '转移责任', summary: '短期脱身，但风险和污染上升', modifier: 1, category: '灰色操作', tradeoff: '马上轻松一点，长期更脏也更危险。' },
    RECOVERY_BREAK: { title: '恢复自保', summary: '恢复精力体力，但当回合绩效可能下降', modifier: -2, category: '保命恢复', tradeoff: '主动回血，但会放弃眼前绩效。' },
    BOUNDARY_RESTATE: { title: '边界重申', summary: '明确责任边界，避免后续扯皮', modifier: 0, category: '边界管理', tradeoff: '收益不立刻爆发，但能压住连锁后果。' },
};
exports.ACTION_MODIFIERS = Object.fromEntries(Object.entries(exports.ACTION_RULES).map(([id, rule]) => [id, rule.modifier]));
exports.ACTION_DISPLAY = Object.fromEntries(Object.entries(exports.ACTION_RULES).map(([id, rule]) => [id, { title: rule.title, summary: rule.summary }]));
exports.ACTION_OPTION_POLICY = {
    core: ['DIRECT_EXECUTE', 'EMAIL_TRACE', 'NARROW_SCOPE', 'SOFT_REFUSE'],
    low_energy_bonus: 'RECOVERY_BREAK',
    default_bonus: 'REQUEST_CONFIRMATION',
};
function buildOptions(state) {
    const optionKeys = [...exports.ACTION_OPTION_POLICY.core];
    if (state.en < 35) {
        optionKeys.push(exports.ACTION_OPTION_POLICY.low_energy_bonus);
    }
    else {
        optionKeys.push(exports.ACTION_OPTION_POLICY.default_bonus);
    }
    const options = [];
    for (let i = 0; i < Math.min(optionKeys.length, 5); i++) {
        const key = optionKeys[i];
        const display = exports.ACTION_DISPLAY[key] || { title: key, summary: '执行该策略' };
        const rule = exports.ACTION_RULES[key];
        options.push({
            index: i + 1,
            action: key,
            title: display.title,
            summary: display.summary,
            category: (rule === null || rule === void 0 ? void 0 : rule.category) || '通用策略',
        });
    }
    return options;
}
