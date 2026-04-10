import { apiGet, apiPostForm } from './client';

export function fetchFiles() {
  return apiGet('/api/files');
}

export function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  return apiPostForm('/api/upload', formData);
}
