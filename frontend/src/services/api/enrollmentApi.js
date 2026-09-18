import axiosClient from './axiosClient';

export const listCourseEnrollments = async (courseId) => {
  const response = await axiosClient.get(`/api/courses/${courseId}/enrollments`);
  return response.data;
};

export const enrollStudent = async (courseId, studentId) => {
  const response = await axiosClient.post(`/api/courses/${courseId}/enrollments`, { student_id: studentId });
  return response.data;
};

export const unenrollStudent = async (courseId, studentId) => {
  await axiosClient.delete(`/api/courses/${courseId}/enrollments/${studentId}`);
};

export const listMyStudents = async () => {
  const response = await axiosClient.get('/api/enrollments/my-students');
  return response.data;
};
