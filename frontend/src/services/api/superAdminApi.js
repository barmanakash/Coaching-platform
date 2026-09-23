import axiosClient from './axiosClient';

// Platform Super Admin: onboards institutes (PRD sections 3, 29).

export const listInstitutes = async () => {
  const response = await axiosClient.get('/api/super-admin/institutes');
  return response.data;
};

export const createInstitute = async ({ name, code, adminName, adminEmail }) => {
  const response = await axiosClient.post('/api/super-admin/institutes', {
    name, code, admin_name: adminName, admin_email: adminEmail,
  });
  return response.data;
};
