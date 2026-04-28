Page({
  data: {
    storylines: [] as any[],
    selectedId: '' as string,
  },

  onLoad() {
    // 暂无剧情线数据，显示占位
  },

  onSelectStoryline(e: any) {
    const id = e.currentTarget.dataset.id;
    this.setData({ selectedId: id });
  },

  onStartGame() {
    const id = this.data.selectedId;
    wx.navigateTo({
      url: `/pages/game/game${id ? '?storylineId=' + id : ''}`,
    });
  },

  onFreeMode() {
    wx.navigateTo({ url: '/pages/game/game' });
  },
});
