import axiosClient from './axiosClient';

export const listContacts = async () => {
  const response = await axiosClient.get('/api/conversations/contacts');
  return response.data;
};

export const startConversation = async (otherUserId) => {
  const response = await axiosClient.post('/api/conversations', { other_user_id: otherUserId });
  return response.data;
};

export const listConversations = async () => {
  const response = await axiosClient.get('/api/conversations');
  return response.data;
};

export const getMessages = async (conversationId) => {
  const response = await axiosClient.get(`/api/conversations/${conversationId}/messages`);
  return response.data;
};
