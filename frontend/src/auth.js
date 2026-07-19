// Cognito Hosted UI login — Authorization Code + PKCE flow, hand-rolled
// (no oidc-client-ts/amazon-cognito-identity-js) to match this app's
// existing style of small, explicit code over a framework. Deliberately
// does NOT implement silent token refresh — the one part of OAuth clients
// that's genuinely easy to get subtly wrong. Access tokens last 60
// minutes; api.js just redirects back to login() on a 401, which is
// invisible to the user if their Hosted UI session cookie is still live.

const COGNITO_DOMAIN = import.meta.env.VITE_COGNITO_DOMAIN;
const CLIENT_ID = import.meta.env.VITE_COGNITO_CLIENT_ID;
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI || `${window.location.origin}/`;

const VERIFIER_KEY = "flashcards_pkce_verifier";
const TOKEN_KEY = "flashcards_access_token";

function base64UrlEncode(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

function generateRandomString(length = 64) {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  return base64UrlEncode(bytes.buffer);
}

async function sha256(text) {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
}

export function getAccessToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}

export async function login() {
  const verifier = generateRandomString();
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  const challenge = base64UrlEncode(await sha256(verifier));

  const params = new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    // aws.cognito.signin.user.admin lets the resulting access token call
    // Cognito's Identity Provider API directly (see changePassword below)
    // — needs matching allowed_oauth_scopes on the app client
    // (terraform/cognito.tf).
    scope: "openid email profile aws.cognito.signin.user.admin",
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
  window.location.assign(`${COGNITO_DOMAIN}/oauth2/authorize?${params}`);
}

export function logout() {
  sessionStorage.removeItem(TOKEN_KEY);
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    logout_uri: REDIRECT_URI,
  });
  window.location.assign(`${COGNITO_DOMAIN}/logout?${params}`);
}

// Called once on app load. Returns true if the URL carried a `?code=`
// that was successfully exchanged for a token (caller should then strip
// it from the URL / proceed), false if there was nothing to do here.
export async function handleRedirectCallback() {
  const url = new URL(window.location.href);
  const code = url.searchParams.get("code");
  if (!code) return false;

  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  sessionStorage.removeItem(VERIFIER_KEY);
  if (!verifier) {
    // Lost sessionStorage across the redirect to Cognito and back — seen
    // on mobile Safari, where cross-site storage restrictions can drop it.
    throw new Error("Lost sign-in state — please try again");
  }

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: CLIENT_ID,
    code,
    redirect_uri: REDIRECT_URI,
    code_verifier: verifier,
  });

  const res = await fetch(`${COGNITO_DOMAIN}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    throw new Error(`Cognito token exchange failed: ${res.status} ${await res.text()}`);
  }
  const { access_token } = await res.json();
  sessionStorage.setItem(TOKEN_KEY, access_token);

  url.searchParams.delete("code");
  url.searchParams.delete("state");
  window.history.replaceState({}, "", url.pathname + url.search);
  return true;
}

// Change password while logged in — calls Cognito's Identity Provider API
// (a *different* endpoint from the Hosted UI domain above:
// cognito-idp.<region>.amazonaws.com, the same regional AWS service
// endpoint every Cognito SDK talks to) directly from the browser with the
// current access token. No AWS credentials/signing needed — this specific
// operation is authorized by the access token's
// aws.cognito.signin.user.admin scope alone, the same "raw fetch, no SDK"
// style as the OAuth calls above. Region is parsed out of
// VITE_COGNITO_DOMAIN (…auth.<region>.amazoncognito.com) rather than
// needing its own env var.
export async function changePassword(previousPassword, newPassword) {
  const match = COGNITO_DOMAIN.match(/\.auth\.([a-z0-9-]+)\.amazoncognito\.com/);
  if (!match) {
    throw new Error("Could not determine AWS region from VITE_COGNITO_DOMAIN");
  }
  const region = match[1];
  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error("Not authenticated");
  }

  const res = await fetch(`https://cognito-idp.${region}.amazonaws.com/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-amz-json-1.1",
      "X-Amz-Target": "AWSCognitoIdentityProviderService.ChangePassword",
    },
    body: JSON.stringify({
      PreviousPassword: previousPassword,
      ProposedPassword: newPassword,
      AccessToken: accessToken,
    }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.message || body.__type || `Change password failed: ${res.status}`);
  }
}
