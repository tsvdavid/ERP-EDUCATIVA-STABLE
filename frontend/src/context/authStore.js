import { create } from 'zustand';
import api from '../services/api';
import { jwtDecode } from "jwt-decode"; // Asegúrate de instalar jwt-decode si no está

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
                user: { username, ...decoded },
                isLoading: false,
                activeInstitution: decoded.institution // Set from token
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

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('active_institution');
        set({ user: null, isAuthenticated: false, activeInstitution: null });
    },

    checkAuth: () => {
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                const decoded = jwtDecode(token);
                // Verificar expiración básica
                if (decoded.exp * 1000 < Date.now()) {
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('refresh_token');
                    localStorage.removeItem('active_institution');
                    set({ user: null, isAuthenticated: false, isLoading: false, activeInstitution: null });
                } else {
                    // prioritize localStorage, but fallback to token
                    let activeInst = localStorage.getItem('active_institution');
                    if (!activeInst && decoded.institution) {
                        activeInst = decoded.institution;
                        localStorage.setItem('active_institution', activeInst);
                    }
                    set({ user: decoded, isAuthenticated: true, isLoading: false, activeInstitution: activeInst });
                }
            } catch (e) {
                set({ user: null, isAuthenticated: false, isLoading: false, activeInstitution: null });
            }
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
