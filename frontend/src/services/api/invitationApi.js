import axiosClient from './axiosClient';

// Institute Admin side of admin-invite-only onboarding (teachers/students).
// The platform Super Admin's institute-creation invite uses superAdminApi.js instead.

export const listInvitations = async () => {
  const response = await axiosClient.get('/api/invitations');
  return response.data;
};

export const createInvitation = async ({ name, email, role }) => {
  const response = await axiosClient.post('/api/invitations', { name, email, role });
  return response.data;
};

export const regenerateInvitation = async (invitationId) => {
  const response = await axiosClient.post(`/api/invitations/${invitationId}/regenerate`);
  return response.data;
};

export const revokeInvitation = async (invitationId) => {
  await axiosClient.delete(`/api/invitations/${invitationId}`);
};
