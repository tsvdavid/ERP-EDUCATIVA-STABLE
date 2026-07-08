import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api',
    headers: {
        // 'Content-Type': 'application/json', // Let axios set it automatically
    },
});

api.interceptors.request.use(
    (config) => {
        // Fix for Axios baseURL with path component: strip leading slash from url


        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        const activeInstitution = localStorage.getItem('active_institution');
        if (activeInstitution && activeInstitution !== 'null' && activeInstitution !== 'undefined') {
            config.headers['X-Institution-ID'] = activeInstitution;
        }
        // ==== DEBUG LOGS FOR AXIOS REQUEST ====
        console.log('========== AXIOS REQUEST =========');
        console.log('BASE URL:', config.baseURL);
        console.log('REQUEST URL:', config.url);
        console.log('FULL URL:', (config.baseURL || '') + (config.url || ''));
        console.log('TOKEN:', localStorage.getItem('access_token'));
        console.log('HEADERS:', config.headers);
        console.log('==================================');
        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        // Evitar intentar refrescar si el error viene del propio endpoint de login o refresh
        if (error.response && error.response.status === 401 && !originalRequest._retry && !originalRequest.url.includes('/token/') && !originalRequest.url.includes('/auth/login') && !originalRequest.url.includes('/auth/refresh')) {
            originalRequest._retry = true;
            try {
                const refreshToken = localStorage.getItem('refresh_token');
                const response = await api.post('/auth/refresh/', {
                    refresh: refreshToken,
                });
                const { access } = response.data;
                localStorage.setItem('access_token', access);
                api.defaults.headers.common['Authorization'] = `Bearer ${access}`;
                return api(originalRequest);
            } catch (refreshError) {
                // Logout user if refresh fails
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        if (error.response && error.response.status === 403 && error.response.data?.code === 'SUBSCRIPTION_SUSPENDED') {
            const currentPath = window.location.pathname;
            const safeRoutes = [
                '/subscription-suspended',
                '/dashboard/settings/billing',
                '/login'
            ];
            
            const isSafe = safeRoutes.some(route => currentPath.startsWith(route));
            
            if (!isSafe) {
                window.location.replace('/subscription-suspended');
            }
        }
        return Promise.reject(error);
    }
);

export default api;
