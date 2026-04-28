"use strict";
Page({
    data: {
        hasActiveSession: false,
        sessionId: '',
    },
    onLoad() {
        var _a;
        const app = getApp();
        const cached = (_a = app.globalData) === null || _a === void 0 ? void 0 : _a.currentSessionId;
        this.setData({
            hasActiveSession: !!cached,
            sessionId: cached || '',
        });
    },
    onShow() {
        var _a;
        const app = getApp();
        const cached = (_a = app.globalData) === null || _a === void 0 ? void 0 : _a.currentSessionId;
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
        var _a;
        const app = getApp();
        if ((_a = app.globalData) === null || _a === void 0 ? void 0 : _a.currentSessionId) {
            wx.navigateTo({
                url: `/pages/game/game?sessionId=${app.globalData.currentSessionId}`,
            });
        }
    },
    onArchive() {
        wx.switchTab({ url: '/pages/archive/archive' });
    },
});
