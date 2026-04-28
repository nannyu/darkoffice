/** 中文分类 → 英文 CSS class 映射 */
const CATEGORY_CLASS_MAP: Record<string, string> = {
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
    mappedOptions: [] as Array<Record<string, any>>,
  },

  observers: {
    options(opts: Array<Record<string, any>>) {
      this.setData({
        mappedOptions: opts.map((opt) => ({
          ...opt,
          cssClass: CATEGORY_CLASS_MAP[opt.category] || 'defend',
        })),
      });
    },
  },

  methods: {
    onSelect(e: any) {
      if (this.data.loading) return;
      const action = e.currentTarget.dataset.action;
      this.triggerEvent('select', { action });
    },
  },
});
