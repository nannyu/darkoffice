"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sessionCache = void 0;
const STORAGE_KEY_SESSION = 'darkoffice_current_session';
exports.sessionCache = {
    save(sessionId) {
        try {
            wx.setStorageSync(STORAGE_KEY_SESSION, sessionId);
        }
        catch (e) {
            console.error('[sessionCache] save failed', e);
        }
    },
    load() {
        try {
            return wx.getStorageSync(STORAGE_KEY_SESSION) || null;
        }
        catch (e) {
            console.error('[sessionCache] load failed', e);
            return null;
        }
    },
    clear() {
        try {
            wx.removeStorageSync(STORAGE_KEY_SESSION);
        }
        catch (e) {
            console.error('[sessionCache] clear failed', e);
        }
    },
};
