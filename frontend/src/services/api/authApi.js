import axiosClient from './axiosClient';

export const login = async (email, password) => {
  const response = await axiosClient.post('/api/auth/login', { email, password });
  return response.data;
};

export const signup = async ({ name, email, password, role, phone }) => {
  const response = await axiosClient.post('/api/auth/signup', { name, email, password, role, phone });
  return response.data;
};
