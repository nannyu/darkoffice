"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getOpenidFromContext = getOpenidFromContext;
let cloudSdk = null;
function getCloudSdk() {
    if (!cloudSdk) {
        cloudSdk = require('wx-server-sdk');
        cloudSdk.init({ env: cloudSdk.DYNAMIC_CURRENT_ENV });
    }
    return cloudSdk;
}
function getOpenidFromContext() {
    const wxContext = getCloudSdk().getWXContext();
    const openid = wxContext === null || wxContext === void 0 ? void 0 : wxContext.OPENID;
    if (!openid || typeof openid !== 'string') {
        throw new Error('UNAUTHENTICATED: missing OPENID from cloud context');
    }
    return openid;
}
