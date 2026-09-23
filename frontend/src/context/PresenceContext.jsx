import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { createSocket } from '../services/websocket/socketClient';
import { useAuth } from './AuthContext';
import { listNotifications, markNotificationRead, markAllNotificationsRead } from '../services/api/notificationApi';

const PresenceContext = createContext({
  onlineUserIds: new Set(),
  notifications: [],
  unreadCount: 0,
  markRead: () => {},
  markAllRead: () => {},
});

/**
 * Opens a single WebSocket to /ws/presence for the whole session.
 * It carries two kinds of live events:
 *  - "online_users" / "presence": who's online right now, and deltas.
 *  - "notification": a new notification pushed for this user (new doubt,
 *    reply, message, signup, approval, etc.) — no separate socket needed.
 */
export function PresenceProvider({ children }) {
  const { isAuthenticated, isSuperAdmin } = useAuth();
  const [onlineUserIds, setOnlineUserIds] = useState(new Set());
  const [notifications, setNotifications] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    // The platform Super Admin belongs to no institute, so there is no
    // presence room or notification inbox for them to connect to.
    if (!isAuthenticated || isSuperAdmin) {
      setOnlineUserIds(new Set());
      setNotifications([]);
      return;
    }

    listNotifications().then(setNotifications).catch(() => {});

    const socket = createSocket('/ws/presence');
    socketRef.current = socket;

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'online_users') {
        setOnlineUserIds(new Set(data.user_ids));
      } else if (data.type === 'presence') {
        setOnlineUserIds((prev) => {
          const next = new Set(prev);
          if (data.online) next.add(data.user_id);
          else next.delete(data.user_id);
          return next;
        });
      } else if (data.type === 'notification') {
        setNotifications((prev) => [
          {
            id: data.id,
            type: data.notification_type,
            title: data.title,
            message: data.message,
            link: data.link,
            read: false,
            created_at: data.created_at,
          },
          ...prev,
        ]);
      }
    };

    return () => {
      socket.close();
    };
  }, [isAuthenticated, isSuperAdmin]);

  const markRead = useCallback(async (id) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    try { await markNotificationRead(id); } catch { /* ignore */ }
  }, []);

  const markAllRead = useCallback(async () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    try { await markAllNotificationsRead(); } catch { /* ignore */ }
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <PresenceContext.Provider value={{ onlineUserIds, notifications, unreadCount, markRead, markAllRead }}>
      {children}
    </PresenceContext.Provider>
  );
}

export function usePresence() {
  return useContext(PresenceContext);
}
