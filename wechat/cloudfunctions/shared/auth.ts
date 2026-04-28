/**
 * Cloud function authentication helpers.
 */

let cloudSdk: any = null;

function getCloudSdk(): any {
  if (!cloudSdk) {
    // wx-server-sdk is provided by the WeChat cloud function runtime.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    cloudSdk = require('wx-server-sdk');
    cloudSdk.init({ env: cloudSdk.DYNAMIC_CURRENT_ENV });
  }
  return cloudSdk;
}

export function getOpenidFromContext(): string {
  const wxContext = getCloudSdk().getWXContext();
  const openid = wxContext?.OPENID;
  if (!openid || typeof openid !== 'string') {
    throw new Error('UNAUTHENTICATED: missing OPENID from cloud context');
  }
  return openid;
}

