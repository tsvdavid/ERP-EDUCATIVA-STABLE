import { create } from 'zustand';
import api from '../services/api';
import { jwtDecode } from "jwt-decode"; 

export const useAuthStore = create((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,

    login: async (username, password) => {
        try {
            const response = await api.post('/token/', { username, password });
            const { access, refresh } = response.data;

            localStorage.setItem('access_token', access);
            localStorage.setItem('refresh_token', refresh);

            // Decodificar token
            const decoded = jwtDecode(access);

            set({
                isAuthenticated: true,
                user: {
                    ...decoded,
                    username,
                    role: decoded.role === 'GLOBAL' ? 'ADMIN' : decoded.role,
                    is_superuser: decoded.role === 'GLOBAL'
                },
                isLoading: false,
                activeInstitution: decoded.institution_id // Set from token
            });
            // Also save to localStorage for persistence
            if (decoded.institution) {
                localStorage.setItem('active_institution', decoded.institution);
            }
            return true;
        } catch (error) {
            console.error('Error de inicio de sesión:', error);
            throw error; // Propagar error
        }
    },

    refresh: async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;
        try {
            const response = await api.post('/auth/refresh/', { refresh: refreshToken });
            const { access } = response.data;
            localStorage.setItem('access_token', access);
            const decoded = jwtDecode(access);
            set({
                user: {
                    ...decoded,
                    role: decoded.role === 'GLOBAL' ? 'ADMIN' : decoded.role,
                    is_superuser: decoded.role === 'GLOBAL'
                },
                isAuthenticated: true,
                activeInstitution: localStorage.getItem('active_institution') || decoded.institution_id
            });
            return true;
        } catch (error) {
            console.error('Error al refrescar token:', error);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            set({ user: null, isAuthenticated: false, activeInstitution: null });
            return false;
        }
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('active_institution');
        set({ user: null, isAuthenticated: false, activeInstitution: null });
    },

    checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');

        if (token) {
            try {
                const decoded = jwtDecode(token);
                // Si el token ha expirado o está cerca de hacerlo (ej: < 60s)
                if (decoded.exp * 1000 < Date.now() + 60000) {
                    if (refreshToken) {
                        const success = await useAuthStore.getState().refresh();
                        if (success) {
                            set({ isLoading: false });
                            return;
                        }
                    }
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('active_institution');
                    set({ user: null, isAuthenticated: false, isLoading: false, activeInstitution: null });
                } else {
                    // prioritize localStorage, but fallback to token
                    let activeInst = localStorage.getItem('active_institution');
                    if (!activeInst && decoded.institution_id) {
                        activeInst = decoded.institution_id;
                        localStorage.setItem('active_institution', activeInst);
                    }
                    set({
                        user: {
                            ...decoded,
                            role: decoded.role === 'GLOBAL' ? 'ADMIN' : decoded.role,
                            is_superuser: decoded.role === 'GLOBAL'
                        },
                        isAuthenticated: true,
                        isLoading: false,
                        activeInstitution: activeInst
                    });
                }
            } catch (e) {
                set({ user: null, isAuthenticated: false, isLoading: false, activeInstitution: null });
            }
        } else if (refreshToken) {
            const success = await useAuthStore.getState().refresh();
            set({ isLoading: false });
        } else {
            set({ isLoading: false });
        }
    },

    activeInstitution: null,
    setActiveInstitution: (id) => {
        if (id) {
            localStorage.setItem('active_institution', id);
        } else {
            localStorage.removeItem('active_institution');
        }
        set({ activeInstitution: id });
    }
}));

if (typeof window !== 'undefined') {
    window.authDebug = () => {
        console.log('AUTH STATE:', useAuthStore.getState());
    };
}
