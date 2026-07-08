import { useAuthStore } from '../context/authStore';

const handleSwitch = async (instId) => {
    try {
        const refresh = localStorage.getItem('refresh_token');
        const response = await fetch('/api/users/token/switch/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                refresh_token: refresh,
                institution_id: instId 
            })
        });
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        localStorage.setItem('active_institution', String(data.institution_id));
        useAuthStore.getState().applyAuthTokens({
            access: data.access,
            refresh: data.refresh,
        });
        window.location.href = '/dashboard';
    } catch (error) {
        console.error('Error al cambiar institución', error);
        window.location.reload();
    }
};