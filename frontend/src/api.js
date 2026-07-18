import { getAccessToken, login } from "./auth";

const BASE_URL = "/api";

async function request(path, options = {}) {
  const token = getAccessToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  if (res.status === 401) {
    // Access token missing/expired — redirect to Cognito's login page.
    // Invisible to the user if their Hosted UI session cookie is still
    // live; a real re-login prompt otherwise. No silent-refresh attempt.
    login();
    throw new Error("Not authenticated — redirecting to login.");
  }
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${options.method || "GET"} ${path} failed: ${res.status} ${body}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export function listCards() {
  return request("/cards");
}

export function listDueCards() {
  return request("/cards/due");
}

export function createCard(french, english) {
  return request("/cards", {
    method: "POST",
    body: JSON.stringify({ french, english }),
  });
}

export function updateCard(id, fields) {
  return request(`/cards/${id}`, {
    method: "PATCH",
    body: JSON.stringify(fields),
  });
}

export function deleteCard(id) {
  return request(`/cards/${id}`, { method: "DELETE" });
}

export function gradeCard(id, grade) {
  return request(`/cards/${id}/grade`, {
    method: "POST",
    body: JSON.stringify({ grade }),
  });
}

export function getStats() {
  return request("/stats");
}

export function completeSession() {
  return request("/stats/session-complete", { method: "POST" });
}

export function deleteAllCards() {
  return request("/cards", { method: "DELETE" });
}

export function resetAllProgress() {
  return request("/reset-all-progress", { method: "POST" });
}

export function getAchievements() {
  return request("/achievements");
}

export function getQuests() {
  return request("/quests");
}
