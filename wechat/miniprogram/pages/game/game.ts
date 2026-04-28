import { api, GamePromptView, ApplyTurnResult } from '../../services/api';

Page({
  data: {
    sessionId: '' as string,
    turnIndex: 0,
    day: 1,
    timePeriod: '上午',
    state: { hp: 100, en: 100, st: 100, kpi: 100, risk: 0, cor: 0 } as Record<string, number>,
    eventSummary: { actor: '', event: '', prompt: '' },
    options: [] as any[],
    riskTip: '' as string,
    hazards: [] as any[],
    projects: [] as any[],
    showResult: false,
    turnResult: null as any,
    isEnded: false,
    ending: null as any,
    loading: false,
  },

  onLoad(options: any) {
    const app = getApp() as any;
    const openid = app.globalData?.mockOpenid || 'mock_user_001';
    let sessionId = options?.sessionId;

    if (!sessionId) {
      const storylineId = options?.storylineId;
      try {
        const res = api.createGameSession({
          openid,
          storyline_id: storylineId || undefined,
        });
        sessionId = res.session.session_id;
      } catch (e) {
        console.error('[Game] createGameSession failed', e);
        wx.showToast({ title: '创建会话失败', icon: 'none' });
        return;
      }
    }

    const app2 = getApp() as any;
    app2.globalData = app2.globalData || {};
    app2.globalData.currentSessionId = sessionId;
    this.setData({ sessionId });

    this.loadPrompt();
  },

  loadPrompt() {
    const app = getApp() as any;
    const openid = app.globalData?.mockOpenid || 'mock_user_001';

    try {
      const res = api.getNextPrompt({
        session_id: this.data.sessionId,
        openid,
      });
      this.setData({
        turnIndex: res.turn_index,
        day: res.day,
        timePeriod: res.time_period,
        eventSummary: res.event_summary,
        options: res.options,
        riskTip: res.risk_tip,
        state: res.state,
        hazards: res.hazards,
        projects: res.projects,
      });
    } catch (e) {
      console.error('[Game] loadPrompt failed', e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onAction(e: any) {
    if (this.data.loading || this.data.showResult) return;

    const actionType = e.detail?.action || e.currentTarget.dataset.action;
    const app = getApp() as any;
    const openid = app.globalData?.mockOpenid || 'mock_user_001';

    this.setData({ loading: true });

    try {
      const res = api.applyTurn({
        session_id: this.data.sessionId,
        action_type: actionType,
        client_turn_index: this.data.turnIndex,
        openid,
      });

      this.setData({
        state: res.session_summary.state,
        showResult: true,
        turnResult: res.turn_result,
        isEnded: res.session_summary.status === 'ENDED',
        ending: res.ending,
        loading: false,
      });
    } catch (e) {
      console.error('[Game] applyTurn failed', e);
      wx.showToast({ title: '结算失败', icon: 'none' });
      this.setData({ loading: false });
    }
  },

  onResultClose() {
    if (this.data.isEnded) return;
    this.setData({ showResult: false });
    this.loadPrompt();
  },

  onRestart() {
    const app = getApp() as any;
    if (app.globalData) {
      app.globalData.currentSessionId = null;
    }
    wx.redirectTo({ url: '/pages/home/home' });
  },

  onBackHome() {
    wx.switchTab({ url: '/pages/home/home' });
  },
});
