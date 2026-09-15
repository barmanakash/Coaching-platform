const WS_BASE_URL = process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000';

/**
 * Creates a WebSocket connection to a backend socket route.
 * Usage: createSocket('/ws/chat/CONVERSATION_ID')
 */
export function createSocket(path) {
  const token = localStorage.getItem('access_token');
  const url = `${WS_BASE_URL}${path}${token ? `?token=${token}` : ''}`;
  return new WebSocket(url);
}
