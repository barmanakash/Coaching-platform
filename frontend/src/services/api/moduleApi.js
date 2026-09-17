import axiosClient from './axiosClient';

export const listModules = async (courseId) => {
  const response = await axiosClient.get(`/api/courses/${courseId}/modules`);
  return response.data;
};

export const createModule = async (courseId, payload) => {
  const response = await axiosClient.post(`/api/courses/${courseId}/modules`, payload);
  return response.data;
};

export const updateModule = async (moduleId, fields) => {
  const response = await axiosClient.patch(`/api/modules/${moduleId}`, fields);
  return response.data;
};

export const deleteModule = async (moduleId) => {
  await axiosClient.delete(`/api/modules/${moduleId}`);
};

export const listResources = async (moduleId) => {
  const response = await axiosClient.get(`/api/modules/${moduleId}/resources`);
  return response.data;
};

export const createResource = async (moduleId, payload) => {
  const response = await axiosClient.post(`/api/modules/${moduleId}/resources`, payload);
  return response.data;
};

export const updateResource = async (resourceId, fields) => {
  const response = await axiosClient.patch(`/api/resources/${resourceId}`, fields);
  return response.data;
};

export const deleteResource = async (resourceId) => {
  await axiosClient.delete(`/api/resources/${resourceId}`);
};
