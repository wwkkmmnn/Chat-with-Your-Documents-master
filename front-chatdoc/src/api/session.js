import { apiGet, apiPost } from './client';

export function fetchSessions() {
  return apiGet('/api/sessions');
}

export function createSession(title = '') {
  return apiPost('/api/sessions', title ? { title } : {});
}

export function fetchSessionMessages(sessionId) {
  return apiGet(`/api/sessions/${sessionId}/messages`);
}
