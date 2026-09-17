import axiosClient from './axiosClient';

export const listDoubts = async () => {
  const response = await axiosClient.get('/api/doubts');
  return response.data;
};

export const getDoubt = async (doubtId) => {
  const response = await axiosClient.get(`/api/doubts/${doubtId}`);
  return response.data;
};

export const createDoubt = async (payload) => {
  const response = await axiosClient.post('/api/doubts', payload);
  return response.data;
};

export const addReply = async (doubtId, message) => {
  const response = await axiosClient.post(`/api/doubts/${doubtId}/replies`, { message });
  return response.data;
};

export const updateDoubtStatus = async (doubtId, statusValue) => {
  const response = await axiosClient.patch(`/api/doubts/${doubtId}/status`, { status: statusValue });
  return response.data;
};
