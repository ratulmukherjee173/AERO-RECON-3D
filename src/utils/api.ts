

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000';

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const url = `${BACKEND_URL}${endpoint}`;

  const headers = new Headers(options.headers || {});

  // Set default content type if not provided and body is present (and not FormData)
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Dispatch a custom event to handle unauthorized access globally (e.g. logging out)
    window.dispatchEvent(new Event('unauthorized'));
  }

  return response;
}
