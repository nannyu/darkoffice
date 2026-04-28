"use strict";
const CATEGORY_CLASS_MAP = {
    '硬扛推进': 'force',
    '证据管理': 'evidence',
    '边界管理': 'boundary',
    '保守防守': 'defend',
    '紧急救火': 'emergency',
    '降风险': 'reduce-risk',
    '回避策略': 'evade',
    '灰色操作': 'gray',
    '保命恢复': 'survive',
};
Component({
    properties: {
        options: { type: Array, value: [] },
        loading: { type: Boolean, value: false },
    },
    data: {
        mappedOptions: [],
    },
    observers: {
        options(opts) {
            this.setData({
                mappedOptions: opts.map((opt) => (Object.assign(Object.assign({}, opt), { cssClass: CATEGORY_CLASS_MAP[opt.category] || 'defend' }))),
            });
        },
    },
    methods: {
        onSelect(e) {
            if (this.data.loading)
                return;
            const action = e.currentTarget.dataset.action;
            this.triggerEvent('select', { action });
        },
    },
});
