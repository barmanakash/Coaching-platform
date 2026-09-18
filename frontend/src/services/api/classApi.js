import axiosClient from './axiosClient';

export const listClasses = async () => {
  const response = await axiosClient.get('/api/classes');
  return response.data;
};

export const getClass = async (classId) => {
  const response = await axiosClient.get(`/api/classes/${classId}`);
  return response.data;
};

export const createClass = async (payload) => {
  const response = await axiosClient.post('/api/classes', payload);
  return response.data;
};

export const updateClass = async (classId, fields) => {
  const response = await axiosClient.patch(`/api/classes/${classId}`, fields);
  return response.data;
};

export const deleteClass = async (classId) => {
  await axiosClient.delete(`/api/classes/${classId}`);
};

export const startClass = async (classId) => {
  const response = await axiosClient.post(`/api/classes/${classId}/start`);
  return response.data;
};

export const endClass = async (classId) => {
  const response = await axiosClient.post(`/api/classes/${classId}/end`);
  return response.data;
};
