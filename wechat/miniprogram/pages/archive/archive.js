"use strict";
Page({
    data: {
        archives: [],
    },
    onLoad() { },
    onShow() { },
    onNewGame() {
        wx.navigateTo({ url: '/pages/storylines/storylines' });
    },
});
