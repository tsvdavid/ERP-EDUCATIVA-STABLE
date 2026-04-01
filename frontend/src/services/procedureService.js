import api from './api';

export const procedureService = {
    // Templates
    getTemplates: async () => {
        const response = await api.get('/procedures/templates/');
        return response.data;
    },
    getTemplate: async (id) => {
        const response = await api.get(`/procedures/templates/${id}/`);
        return response.data;
    },
    createTemplate: async (data) => {
        const response = await api.post('/procedures/templates/', data);
        return response.data;
    },
    updateTemplate: async (id, data) => {
        const response = await api.put(`/procedures/templates/${id}/`, data);
        return response.data;
    },
    deleteTemplate: async (id) => {
        const response = await api.delete(`/procedures/templates/${id}/`);
        return response.data;
    },

    // Student Requests
    getRequests: async () => {
        const response = await api.get('/procedures/requests/');
        return response.data;
    },
    createRequest: async (data) => {
        // data should be { template: ID, details: "..." }
        const response = await api.post('/procedures/requests/', data);
        return response.data;
    },

    // Resolve (Approve/Reject)
    resolveRequest: async (id, data) => {
        // data should be { action: "APPROVE", notes: "..." }
        const response = await api.post(`/procedures/requests/${id}/resolve/`, data);
        return response.data;
    },
};
