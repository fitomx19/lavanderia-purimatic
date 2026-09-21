// En desarrollo (Vite :5173) habla con la API en :5000.
// En el .exe el front se sirve desde el mismo host/puerto de la API:
// hay que usar URL relativa. Si se usa localhost vs 127.0.0.1 el navegador
// bloquea el login (CORS: solo se ve OPTIONS /auth/login, nunca el POST).
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  ?? (import.meta.env.DEV ? 'http://localhost:5000' : '');
