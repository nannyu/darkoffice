"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const api_1 = require("../../services/api");
Page({
    data: {
        sessionId: '',
        turnIndex: 0,
        day: 1,
        timePeriod: '上午',
        state: { hp: 100, en: 100, st: 100, kpi: 100, risk: 0, cor: 0 },
        eventSummary: { actor: '', event: '', prompt: '' },
        options: [],
        riskTip: '',
        hazards: [],
        projects: [],
        showResult: false,
        turnResult: null,
        isEnded: false,
        ending: null,
        loading: false,
    },
    onLoad(options) {
        var _a;
        const app = getApp();
        const openid = ((_a = app.globalData) === null || _a === void 0 ? void 0 : _a.mockOpenid) || 'mock_user_001';
        let sessionId = options === null || options === void 0 ? void 0 : options.sessionId;
        if (!sessionId) {
            const storylineId = options === null || options === void 0 ? void 0 : options.storylineId;
            try {
                const res = api_1.api.createGameSession({
                    openid,
                    storyline_id: storylineId || undefined,
                });
                sessionId = res.session.session_id;
            }
            catch (e) {
                console.error('[Game] createGameSession failed', e);
                wx.showToast({ title: '创建会话失败', icon: 'none' });
                return;
            }
        }
        const app2 = getApp();
        app2.globalData = app2.globalData || {};
        app2.globalData.currentSessionId = sessionId;
        this.setData({ sessionId });
        this.loadPrompt();
    },
    loadPrompt() {
        var _a;
        const app = getApp();
        const openid = ((_a = app.globalData) === null || _a === void 0 ? void 0 : _a.mockOpenid) || 'mock_user_001';
        try {
            const res = api_1.api.getNextPrompt({
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
        }
        catch (e) {
            console.error('[Game] loadPrompt failed', e);
            wx.showToast({ title: '加载失败', icon: 'none' });
        }
    },
    onAction(e) {
        var _a, _b;
        if (this.data.loading || this.data.showResult)
            return;
        const actionType = ((_a = e.detail) === null || _a === void 0 ? void 0 : _a.action) || e.currentTarget.dataset.action;
        const app = getApp();
        const openid = ((_b = app.globalData) === null || _b === void 0 ? void 0 : _b.mockOpenid) || 'mock_user_001';
        this.setData({ loading: true });
        try {
            const res = api_1.api.applyTurn({
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
        }
        catch (e) {
            console.error('[Game] applyTurn failed', e);
            wx.showToast({ title: '结算失败', icon: 'none' });
            this.setData({ loading: false });
        }
    },
    onResultClose() {
        if (this.data.isEnded)
            return;
        this.setData({ showResult: false });
        this.loadPrompt();
    },
    onRestart() {
        const app = getApp();
        if (app.globalData) {
            app.globalData.currentSessionId = null;
        }
        wx.redirectTo({ url: '/pages/home/home' });
    },
    onBackHome() {
        wx.switchTab({ url: '/pages/home/home' });
    },
});
