// app.ts
App({
  onLaunch() {
    console.log('[DarkOffice] App launched');
  },
  globalData: {
    currentSessionId: null as string | null,
    mockOpenid: 'mock_user_001',
  },
});
