import axiosClient from './axiosClient';

export const uploadFile = async (file, resourceType, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('resource_type', resourceType);

  const response = await axiosClient.post('/api/uploads', formData, {
    // Do NOT set Content-Type manually — the browser must generate the
    // multipart boundary itself. Overriding to undefined removes the
    // instance's default 'application/json' header for this request only.
    headers: { 'Content-Type': undefined },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });
  return response.data;
};
