import { create } from 'zustand';
import api from '../services/api';
import { jwtDecode } from "jwt-decode"; 
import { extractModuleCodesFromBillingPayload } from '../config/moduleVisibilityCatalog';

const loadAvailableModules = async () => {
    try {
        const response = await api.get('/subscriptions/my-billing/info/');
        const payload = response?.data || {};
        const availableModules = extractModuleCodesFromBillingPayload(payload);
        console.log('billing payload recibido:', payload);
        console.log('availableModules:', availableModules);
        return availableModules;
    } catch {
        return [];
    }
};

const syncAuthSession = ({ access, refresh = null }) => {
    if (access) {
        localStorage.setItem('access_token', access);
    }
    if (refresh) {
        localStorage.setItem('refresh_token', refresh);
    }

    const decoded = jwtDecode(access);
    const normalizedRole = decoded.role === 'GLOBAL' ? 'ADMIN' : decoded.role;
    const activeInstitution = decoded.institution_id || decoded.institution || null;

    if (activeInstitution) {
        localStorage.setItem('active_institution', String(activeInstitution));
    } else {
        localStorage.removeItem('active_institution');
    }

    return {
        decoded,
        normalizedRole,
        activeInstitution,
    };
};

export const useAuthStore = create((set) => ({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    availableModules: [],

    login: async (username, password) => {
        try {
            const response = await api.post('/token/', { username, password });
            const { access, refresh } = response.data;
            const { decoded, normalizedRole, activeInstitution } = syncAuthSession({ access, refresh });
            const availableModules = await loadAvailableModules();

            set({
                isAuthenticated: true,
                user: {
                    ...decoded,
                    username,
                    role: normalizedRole,
                    is_superuser: decoded.role === 'GLOBAL'
                },
                isLoading: false,
                activeInstitution,
                availableModules
            });
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
            const { decoded, normalizedRole, activeInstitution } = syncAuthSession({ access });
            const availableModules = await loadAvailableModules();
            set({
                user: {
                    ...decoded,
                    role: normalizedRole,
                    is_superuser: decoded.role === 'GLOBAL'
                },
                isAuthenticated: true,
                activeInstitution,
                availableModules
            });
            return true;
        } catch (error) {
            console.error('Error al refrescar token:', error);
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            set({ user: null, isAuthenticated: false, activeInstitution: null, availableModules: [] });
            return false;
        }
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('active_institution');
        set({ user: null, isAuthenticated: false, activeInstitution: null, availableModules: [] });
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
                    set({ user: null, isAuthenticated: false, isLoading: false, activeInstitution: null, availableModules: [] });
                } else {
                    // prioritize localStorage, but fallback to token
                    let activeInst = localStorage.getItem('active_institution');
                    if (!activeInst && decoded.institution_id) {
                        activeInst = String(decoded.institution_id);
                        localStorage.setItem('active_institution', activeInst);
                    }
                    const availableModules = await loadAvailableModules();
                    set({
                        user: {
                            ...decoded,
                            role: decoded.role === 'GLOBAL' ? 'ADMIN' : decoded.role,
                            is_superuser: decoded.role === 'GLOBAL'
                        },
                        isAuthenticated: true,
                        isLoading: false,
                        activeInstitution: activeInst,
                        availableModules
                    });
                }
            } catch (e) {
                set({ user: null, isAuthenticated: false, isLoading: false, activeInstitution: null, availableModules: [] });
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
            localStorage.setItem('active_institution', String(id));
        } else {
            localStorage.removeItem('active_institution');
        }
        set({ activeInstitution: id });
    },
    applyAuthTokens: ({ access, refresh = null }) => {
        const { decoded, normalizedRole, activeInstitution } = syncAuthSession({ access, refresh });
        set({
            user: {
                ...decoded,
                role: normalizedRole,
                is_superuser: decoded.role === 'GLOBAL'
            },
            isAuthenticated: true,
            isLoading: false,
            activeInstitution: activeInstitution ? String(activeInstitution) : null,
            availableModules: [],
        });
        return decoded;
    },
    setAvailableModules: (modules) => {
        set({ availableModules: Array.isArray(modules) ? modules : [] });
    }
}));

if (typeof window !== 'undefined') {
    window.authDebug = () => {
        console.log('AUTH STATE:', useAuthStore.getState());
    };
}
