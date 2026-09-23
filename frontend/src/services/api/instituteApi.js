import axiosClient from './axiosClient';

// Institute profile + academic configuration (PRD section 6). Any signed-in
// member can read it; only an admin can update it.

export const getMyInstitute = async () => {
  const response = await axiosClient.get('/api/institute');
  return response.data;
};

export const updateMyInstitute = async (fields) => {
  const response = await axiosClient.patch('/api/institute', fields);
  return response.data;
};
