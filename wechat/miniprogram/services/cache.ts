/**
 * 暗黑职场 — 会话缓存服务
 */

const STORAGE_KEY_SESSION = 'darkoffice_current_session';

export const sessionCache = {
  save(sessionId: string): void {
    try {
      wx.setStorageSync(STORAGE_KEY_SESSION, sessionId);
    } catch (e) {
      console.error('[sessionCache] save failed', e);
    }
  },

  load(): string | null {
    try {
      return wx.getStorageSync(STORAGE_KEY_SESSION) || null;
    } catch (e) {
      console.error('[sessionCache] load failed', e);
      return null;
    }
  },

  clear(): void {
    try {
      wx.removeStorageSync(STORAGE_KEY_SESSION);
    } catch (e) {
      console.error('[sessionCache] clear failed', e);
    }
  },
};
