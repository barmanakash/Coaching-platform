import axiosClient from './axiosClient';

// Server scopes results by role automatically:
// admin -> all courses, teacher -> assigned courses, student -> published courses
export const listCourses = async () => {
  const response = await axiosClient.get('/api/courses');
  return response.data;
};
