Page({
  data: {
    archives: [] as any[],
  },

  onLoad() {},

  onShow() {},

  onNewGame() {
    wx.navigateTo({ url: '/pages/storylines/storylines' });
  },
});
