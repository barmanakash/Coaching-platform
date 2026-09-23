import axiosClient from './axiosClient';

export const login = async (email, password) => {
  const response = await axiosClient.post('/api/auth/login', { email, password });
  return response.data;
};

// Admin-invite-only onboarding: there is no public signup. These two calls
// power the /accept-invite page instead.
export const previewInvitation = async (token) => {
  const response = await axiosClient.get(`/api/auth/invitations/${token}`);
  return response.data;
};

export const acceptInvite = async ({ token, password, name, phone }) => {
  const response = await axiosClient.post('/api/auth/accept-invite', { token, password, name, phone });
  return response.data;
};
