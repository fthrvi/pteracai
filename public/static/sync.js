// Google Drive sync — stores per-user practice data in the
// hidden `appDataFolder` of the user's own Drive.
//
// Architecture:
//   - On sign-in, we pull a single JSON file (pteracai.json) from
//     appDataFolder, merge into in-memory state, re-render.
//   - On state changes, debounced 2s, we push the file back.
//   - Conflict resolution: each top-level key (settings, attempts,
//     spaced_rep) carries an `updated` timestamp; most-recent wins
//     on merge.
//   - The user owns the data; the app owner never sees it.
//
// Setup: deploy needs an OAuth Client ID with the
// `https://www.googleapis.com/auth/drive.appdata` scope.
// See README → "Google Sign-In setup".

const SYNC_SCOPE = 'https://www.googleapis.com/auth/drive.appdata';
const DRIVE_FILE_NAME = 'pteracai.json';
const STORAGE_AUTH_KEY = 'pteracai_google_auth_v1';
const STORAGE_USER_KEY = 'pteracai_google_user_v1';
const DEBOUNCE_MS = 2000;

window.PteracaiSync = (function () {
  const state = {
    clientId: null,
    tokenClient: null,
    accessToken: null,
    tokenExpiry: 0,
    fileId: null,
    user: null, // {email, name, picture}
    onSignInChange: null,
    pushTimer: null,
    initialized: false,
  };

  function configured() {
    return !!state.clientId;
  }

  function signedIn() {
    return !!state.accessToken && Date.now() < state.tokenExpiry;
  }

  // Diagnostic snapshot of current auth state — used by Settings to show
  // the user exactly what the app sees, so failures are debuggable.
  function debugState() {
    return {
      configured: !!state.clientId,
      hasToken: !!state.accessToken,
      tokenExpiresIn: state.accessToken
        ? Math.round((state.tokenExpiry - Date.now()) / 1000)
        : null,
      cachedUser: state.user ? {
        email: state.user.email || null,
        name: state.user.name || null,
      } : null,
      tokenClientReady: !!state.tokenClient,
      gsiLoaded: !!(window.google && window.google.accounts && window.google.accounts.oauth2),
    };
  }

  function user() {
    return state.user;
  }

  function init({ clientId, onSignInChange }) {
    if (state.initialized) return;
    state.clientId = clientId || null;
    state.onSignInChange = onSignInChange || (() => {});
    state.initialized = true;
    if (!state.clientId) {
      console.info('[sync] No Google OAuth Client ID configured — sync disabled.');
      return;
    }
    loadGSI()
      .then(() => {
        state.tokenClient = google.accounts.oauth2.initTokenClient({
          client_id: state.clientId,
          scope: SYNC_SCOPE,
          callback: handleTokenResponse,
        });
        // Try silent restore from cached token
        const cached = JSON.parse(localStorage.getItem(STORAGE_AUTH_KEY) || 'null');
        const cachedUser = JSON.parse(localStorage.getItem(STORAGE_USER_KEY) || 'null');
        if (cached && cached.expiry > Date.now() + 60_000) {
          state.accessToken = cached.token;
          state.tokenExpiry = cached.expiry;
          state.user = cachedUser;
          state.onSignInChange({ signedIn: true, user: state.user, source: 'cached' });
        } else if (cachedUser) {
          // Token expired but we know who they were — keep user info around so
          // UI can show "session expired, click to resume" instead of falling
          // all the way back to the unsigned landing page. Try a silent refresh
          // first; if Google still has them logged in elsewhere this is invisible.
          state.user = cachedUser;
          refreshSilent()
            .then(() => {
              // handleTokenResponse already fired onSignInChange with signedIn:true
            })
            .catch(() => {
              state.onSignInChange({ signedIn: false, expired: true, user: cachedUser });
            });
        } else {
          state.onSignInChange({ signedIn: false });
        }
      })
      .catch((e) => {
        console.warn('[sync] GSI failed to load:', e);
        state.onSignInChange({ signedIn: false, error: e.message });
      });
  }

  function loadGSI() {
    return new Promise((resolve, reject) => {
      if (window.google?.accounts?.oauth2) return resolve();
      const s = document.createElement('script');
      s.src = 'https://accounts.google.com/gsi/client';
      s.async = true;
      s.defer = true;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error('Failed to load Google Identity Services'));
      document.head.appendChild(s);
    });
  }

  async function signIn() {
    if (!state.tokenClient) throw new Error('Sign-in not initialized. Check Client ID config.');
    return new Promise((resolve, reject) => {
      state.tokenClient.callback = (resp) => {
        if (resp.error) return reject(new Error(resp.error_description || resp.error));
        handleTokenResponse(resp).then(resolve).catch(reject);
      };
      state.tokenClient.requestAccessToken({ prompt: 'consent' });
    });
  }

  // Silent token refresh — no popup, no consent. Works when the user has
  // already granted consent and Google still has a valid session for them.
  // Resolves with the new token; rejects if interaction is required.
  async function refreshSilent() {
    if (!state.tokenClient) throw new Error('Sign-in not initialized.');
    return new Promise((resolve, reject) => {
      state.tokenClient.callback = (resp) => {
        if (resp.error) return reject(new Error(resp.error_description || resp.error));
        handleTokenResponse(resp).then(resolve).catch(reject);
      };
      // Empty prompt = no UI, fails fast if user must interact
      state.tokenClient.requestAccessToken({ prompt: '' });
    });
  }

  // "Was signed in but token expired" — distinguishes from never-signed-in.
  // True when we have a cached user but no valid token.
  function sessionExpired() {
    return !!state.user && (!state.accessToken || Date.now() >= state.tokenExpiry);
  }

  async function handleTokenResponse(resp) {
    if (resp.error) throw new Error(resp.error);
    state.accessToken = resp.access_token;
    state.tokenExpiry = Date.now() + (resp.expires_in || 3600) * 1000;
    localStorage.setItem(STORAGE_AUTH_KEY, JSON.stringify({
      token: state.accessToken,
      expiry: state.tokenExpiry,
    }));
    // Fetch user profile (via /oauth2/v3/userinfo — no extra scope needed beyond openid which Google grants implicitly)
    try {
      const info = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
        headers: { Authorization: `Bearer ${state.accessToken}` },
      }).then((r) => (r.ok ? r.json() : null));
      if (info) {
        state.user = { email: info.email, name: info.name, picture: info.picture };
        localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(state.user));
      }
    } catch (_) {
      // user info is best-effort; not fatal
    }
    state.onSignInChange({ signedIn: true, user: state.user, source: 'fresh' });
  }

  function signOut() {
    if (state.accessToken && window.google?.accounts?.oauth2) {
      google.accounts.oauth2.revoke(state.accessToken, () => {});
    }
    state.accessToken = null;
    state.tokenExpiry = 0;
    state.fileId = null;
    state.user = null;
    localStorage.removeItem(STORAGE_AUTH_KEY);
    localStorage.removeItem(STORAGE_USER_KEY);
    state.onSignInChange({ signedIn: false });
  }

  // --- Drive REST helpers ---
  async function driveFetch(path, opts = {}) {
    if (!signedIn()) throw new Error('Not signed in');
    const url = path.startsWith('http') ? path : `https://www.googleapis.com/drive/v3/${path}`;
    const headers = {
      Authorization: `Bearer ${state.accessToken}`,
      ...(opts.headers || {}),
    };
    const res = await fetch(url, { ...opts, headers });
    if (res.status === 401) {
      // Token expired — clear local copy and force re-auth next time
      signOut();
      throw new Error('Drive auth expired — please sign in again.');
    }
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      throw new Error(`Drive ${res.status}: ${body.slice(0, 200)}`);
    }
    return res;
  }

  async function findFileId() {
    if (state.fileId) return state.fileId;
    const q = encodeURIComponent(`name='${DRIVE_FILE_NAME}' and 'appDataFolder' in parents and trashed=false`);
    const res = await driveFetch(`files?spaces=appDataFolder&q=${q}&fields=files(id,name)`);
    const data = await res.json();
    if (data.files?.length) {
      state.fileId = data.files[0].id;
    }
    return state.fileId;
  }

  async function pull() {
    if (!signedIn()) return null;
    const fileId = await findFileId();
    if (!fileId) return null; // no file yet
    const res = await driveFetch(`files/${fileId}?alt=media`);
    return res.json();
  }

  async function push(data) {
    if (!signedIn()) return false;
    const body = JSON.stringify(data);
    const fileId = await findFileId();
    if (fileId) {
      await driveFetch(`https://www.googleapis.com/upload/drive/v3/files/${fileId}?uploadType=media`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body,
      });
    } else {
      // multipart create with metadata
      const boundary = '-------pteracai_boundary_' + Math.random().toString(36).slice(2);
      const metadata = { name: DRIVE_FILE_NAME, parents: ['appDataFolder'] };
      const multipart =
        `--${boundary}\r\n` +
        `Content-Type: application/json; charset=UTF-8\r\n\r\n` +
        JSON.stringify(metadata) + `\r\n` +
        `--${boundary}\r\n` +
        `Content-Type: application/json\r\n\r\n` +
        body + `\r\n` +
        `--${boundary}--`;
      const res = await driveFetch(`https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id`, {
        method: 'POST',
        headers: { 'Content-Type': `multipart/related; boundary=${boundary}` },
        body: multipart,
      });
      const j = await res.json();
      state.fileId = j.id;
    }
    return true;
  }

  function schedulePush(getData) {
    if (!signedIn()) return;
    if (state.pushTimer) clearTimeout(state.pushTimer);
    state.pushTimer = setTimeout(async () => {
      try {
        await push(getData());
      } catch (e) {
        console.warn('[sync] push failed:', e.message);
      }
    }, DEBOUNCE_MS);
  }

  return {
    init,
    signIn,
    signOut,
    pull,
    push,
    schedulePush,
    signedIn,
    sessionExpired,
    refreshSilent,
    user,
    configured,
    debugState,
  };
})();
