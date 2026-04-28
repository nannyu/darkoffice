"use strict";
Page({
    data: {
        storylines: [],
        selectedId: '',
    },
    onLoad() {
    },
    onSelectStoryline(e) {
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
