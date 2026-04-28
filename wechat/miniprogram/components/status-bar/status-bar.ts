Component({
  properties: {
    state: {
      type: Object,
      value: { hp: 100, en: 100, st: 100, kpi: 100, risk: 0, cor: 0 },
    },
  },

  observers: {
    'state.**'() {
      this.updateBars();
    },
  },

  data: {
    bars: [] as { key: string; label: string; value: number; percent: number; color: string }[],
  },

  lifetimes: {
    attached() {
      this.updateBars();
    },
  },

  methods: {
    updateBars() {
      const state = this.data.state || {};
      const defs = [
        { key: 'hp', label: '生命', max: 100, color: 'var(--color-hp)' },
        { key: 'en', label: '精神', max: 100, color: 'var(--color-en)' },
        { key: 'st', label: '体力', max: 100, color: 'var(--color-st)' },
        { key: 'kpi', label: 'KPI', max: 100, color: 'var(--color-kpi)' },
        { key: 'risk', label: '风险', max: 100, color: 'var(--color-risk)' },
        { key: 'cor', label: '腐化', max: 100, color: 'var(--color-cor)' },
      ];

      const bars = defs.map(d => {
        const value = (state as any)[d.key] ?? 0;
        const clamped = Math.max(0, Math.min(d.max, value));
        return {
          key: d.key,
          label: d.label,
          value: clamped,
          percent: d.key === 'risk' || d.key === 'cor'
            ? Math.round((clamped / d.max) * 100)
            : Math.round((clamped / d.max) * 100),
          color: d.color,
        };
      });

      this.setData({ bars });
    },
  },
});
