/** Same-origin business transport. Authentication and CSRF material stay in memory. */
let session = null;
let csrfToken = '';
let refreshPromise = null;
const listeners = new Set();

export class ApiError extends Error {
  constructor(message, {status = 0, code = 'request_failed', details = null} = {}) {
    super(message); this.name = 'ApiError'; this.status = status; this.code = code; this.details = details;
  }
}
export function currentSession() { return session; }
export function subscribeSession(listener) { listeners.add(listener); return () => listeners.delete(listener); }
function publish(value) { session = value; for (const listener of listeners) listener(value); }
function acceptSession(value) {
  if (!value?.authenticated || typeof value.csrfToken !== 'string') throw new ApiError('登录响应不完整，请重新登录');
  csrfToken = value.csrfToken; publish(value); return value;
}
function endpoint(path) {
  if (typeof path !== 'string' || !/^[a-z][a-z0-9/-]*(?:\?[^#]*)?$/.test(path) || path.includes('..') || /[\\\u0000-\u001f]/.test(path)) throw new ApiError('无效的接口路径');
  const base = new URL('./api/', document.baseURI);
  const url = new URL(path, base);
  if (url.origin !== location.origin || !url.pathname.startsWith(base.pathname)) throw new ApiError('请求必须发送到本站服务器');
  return url;
}
async function request(path, {method = 'GET', body, signal} = {}) {
  const verb = method.toUpperCase();
  if (!['GET','POST','PUT','DELETE'].includes(verb)) throw new ApiError('不支持的请求方法');
  const headers = {Accept:'application/json'};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (verb !== 'GET' && csrfToken) headers['X-CSRF-Token'] = csrfToken;
  const timeout = typeof AbortSignal.timeout === 'function' ? AbortSignal.timeout(90000) : undefined;
  const combined = signal && timeout && typeof AbortSignal.any === 'function' ? AbortSignal.any([signal, timeout]) : signal || timeout;
  const url = endpoint(path);
  let response;
  try { response = await fetch(url, {method:verb, headers, credentials:'same-origin', cache:'no-store', referrerPolicy:'same-origin', body:body === undefined ? undefined : JSON.stringify(body), signal:combined}); }
  catch (error) { throw new ApiError(error?.name === 'AbortError' || error?.name === 'TimeoutError' ? '请求超时，草稿已保留；请检查提交状态后重试' : '无法连接本站服务器，请稍后重试'); }
  let value;
  try { value = await response.json(); } catch { throw new ApiError('服务器未返回有效数据，请检查后端配置', {status:response.status}); }
  if (!response.ok) {
    // A valid refresh cookie may disclose its CSRF value only through same-origin session lookup.
    if (path === 'session' && value.needsRefresh && typeof value.csrfToken === 'string') csrfToken = value.csrfToken;
    throw new ApiError(value.error?.message || '请求未完成', {status:response.status, code:value.error?.code || 'request_failed', details:value});
  }
  return value;
}
async function refresh() {
  if (!csrfToken) throw new ApiError('请重新登录', {status:401, code:'unauthorized'});
  if (!refreshPromise) refreshPromise = request('session/refresh', {method:'POST', body:{}}).then(acceptSession).finally(() => { refreshPromise = null; });
  return refreshPromise;
}
export async function apiRequest(path, options = {}) {
  try { return await request(path, options); }
  catch (error) {
    if (error.status !== 401 || ['login','logout','session/refresh'].includes(path)) throw error;
    try { await refresh(); return await request(path, options); }
    catch (renewError) { csrfToken = ''; publish(null); throw renewError; }
  }
}
export async function getSession() {
  try { return acceptSession(await request('session')); }
  catch (error) {
    if (error.status === 401 && error.details?.needsRefresh) {
      try { return await refresh(); } catch (refreshError) { csrfToken = ''; publish(null); throw refreshError; }
    }
    csrfToken = ''; publish(null); throw error;
  }
}
export async function login(username, password) { return acceptSession(await request('login', {method:'POST',body:{username,password}})); }
export async function logout() {
  // Do not pretend the server revoked a session if the network failed.
  await apiRequest('logout', {method:'POST', body:{}});
  csrfToken = ''; publish(null);
}
