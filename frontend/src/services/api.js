import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});


api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const status = error.response ? error.response.status : null;

    if (status === 401) {
      console.error("Sessione scaduta, reindirizzamento al login...");
      window.location.href = '/login';
    } else if (status === 404) {
      console.error("Risorsa non trovata");
    } else {
      console.error("Errore API:", error.response?.data?.message || error.message);
    }

    return Promise.reject(error);
  }
);

export default api;