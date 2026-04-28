"use strict";
Page({
    data: {
        version: '0.1.0-alpha',
    },
    onClearCache() {
        wx.showModal({
            title: '确认清除',
            content: '将清除所有本地缓存数据，游戏进度将丢失。确定吗？',
            confirmColor: '#FF4D4F',
            success(res) {
                if (res.confirm) {
                    try {
                        wx.clearStorageSync();
                        wx.showToast({ title: '已清除', icon: 'success' });
                    }
                    catch (e) {
                        wx.showToast({ title: '清除失败', icon: 'none' });
                    }
                }
            },
        });
    },
    onAbout() {
        wx.showModal({
            title: '关于暗黑职场',
            content: '暗黑职场 — 卡牌驱动叙事生存游戏\n基于真实案例的职场博弈模拟器\nv0.1.0-alpha',
            showCancel: false,
            confirmColor: '#FF4D4F',
        });
    },
});
