import axiosClient from './axiosClient';

export const listNotifications = async () => {
  const response = await axiosClient.get('/api/notifications');
  return response.data;
};

export const getUnreadCount = async () => {
  const response = await axiosClient.get('/api/notifications/unread-count');
  return response.data.count;
};

export const markNotificationRead = async (notificationId) => {
  const response = await axiosClient.post(`/api/notifications/${notificationId}/read`);
  return response.data;
};

export const markAllNotificationsRead = async () => {
  await axiosClient.post('/api/notifications/read-all');
};
