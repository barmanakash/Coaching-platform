import axiosClient from './axiosClient';

export const getDashboardStats = async () => {
  const response = await axiosClient.get('/api/admin/dashboard');
  return response.data;
};

export const listStudents = async () => {
  const response = await axiosClient.get('/api/users/students');
  return response.data;
};

export const listTeachers = async () => {
  const response = await axiosClient.get('/api/users/teachers');
  return response.data;
};

export const updateUser = async (userId, fields) => {
  const response = await axiosClient.patch(`/api/users/${userId}`, fields);
  return response.data;
};

export const deleteUser = async (userId) => {
  await axiosClient.delete(`/api/users/${userId}`);
};

export const listCourses = async () => {
  const response = await axiosClient.get('/api/courses');
  return response.data;
};

export const createCourse = async (payload) => {
  const response = await axiosClient.post('/api/courses', payload);
  return response.data;
};

export const updateCourse = async (courseId, fields) => {
  const response = await axiosClient.patch(`/api/courses/${courseId}`, fields);
  return response.data;
};

export const deleteCourse = async (courseId) => {
  await axiosClient.delete(`/api/courses/${courseId}`);
};
