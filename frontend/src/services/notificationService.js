import api from './api';

const notificationService = {
    // Config SMTP
    getConfigs: async () => {
        const response = await api.get('/notifications/config/');
        return response.data;
    },
    createConfig: async (data) => {
        const response = await api.post('/notifications/config/', data);
        return response.data;
    },
    updateConfig: async (id, data) => {
        const response = await api.patch(`/notifications/config/${id}/`, data);
        return response.data;
    },
    testConnection: async (id) => {
        const response = await api.post(`/notifications/config/${id}/test_connection/`, {}, {
            timeout: 30000 // 30 seconds
        });
        return response.data;
    },

    // Templates
    getTemplates: async () => {
        const response = await api.get('/notifications/templates/');
        return response.data;
    },
    createTemplate: async (data) => {
        const response = await api.post('/notifications/templates/', data);
        return response.data;
    },
    updateTemplate: async (id, data) => {
        const response = await api.put(`/notifications/templates/${id}/`, data);
        return response.data;
    },

    // Logs
    getLogs: async (params) => {
        const response = await api.get('/notifications/logs/', { params });
        return response.data;
    }
};

export default notificationService;
