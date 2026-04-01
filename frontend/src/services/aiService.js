import api from './api';

const aiService = {
    // Configuration
    getConfigs: async () => {
        const response = await api.get('/ai/config/');
        return response.data;
    },
    createConfig: async (data) => {
        const response = await api.post('/ai/config/', data);
        return response.data;
    },
    updateConfig: async (id, data) => {
        const response = await api.put(`/ai/config/${id}/`, data);
        return response.data;
    },
    deleteConfig: async (id) => {
        const response = await api.delete(`/ai/config/${id}/`);
        return response.data;
    },
    testConnection: async () => {
        const response = await api.post('/ai/config/test_connection/');
        return response.data;
    },

    // Assistant Actions
    askAssistant: async (prompt, context = '') => {
        const response = await api.post('/ai/assistant/ask/', { prompt, context });
        return response.data;
    },
    summarizeContent: async (content) => {
        const response = await api.post('/ai/assistant/summarize/', { content });
        return response.data;
    }
};

export default aiService;
