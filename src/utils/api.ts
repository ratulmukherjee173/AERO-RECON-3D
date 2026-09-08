

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const url = `${BACKEND_URL}${endpoint}`;

  const headers = new Headers(options.headers || {});
  
  const token = localStorage.getItem('token') || sessionStorage.getItem('token');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Set default content type if not provided and body is present (and not FormData)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    window.dispatchEvent(new Event('unauthorized'));
  }

  return response;
}
