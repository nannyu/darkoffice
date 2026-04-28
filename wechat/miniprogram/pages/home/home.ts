Page({
  data: {
    hasActiveSession: false as boolean,
    sessionId: '' as string,
  },

  onLoad() {
    const app = getApp() as any;
    const cached = app.globalData?.currentSessionId;
    this.setData({
      hasActiveSession: !!cached,
      sessionId: cached || '',
    });
  },

  onShow() {
    const app = getApp() as any;
    const cached = app.globalData?.currentSessionId;
    if (cached !== this.data.sessionId) {
      this.setData({
        hasActiveSession: !!cached,
        sessionId: cached || '',
      });
    }
  },

  onNewGame() {
    wx.navigateTo({ url: '/pages/storylines/storylines' });
  },

  onContinue() {
    const app = getApp() as any;
    if (app.globalData?.currentSessionId) {
      wx.navigateTo({
        url: `/pages/game/game?sessionId=${app.globalData.currentSessionId}`,
      });
    }
  },

  onArchive() {
    wx.switchTab({ url: '/pages/archive/archive' });
  },
});
