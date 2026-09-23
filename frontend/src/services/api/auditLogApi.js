import axiosClient from './axiosClient';

export const listAuditLogs = async ({ limit = 50, skip = 0, action } = {}) => {
  const response = await axiosClient.get('/api/audit-logs', { params: { limit, skip, action } });
  return response.data;
};
