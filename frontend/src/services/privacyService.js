import api from './api';

const privacyService = {
    // Policies
    getPolicies: async () => {
        const response = await api.get('/privacy/policies/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },

    // Consents
    getConsents: async () => {
        const response = await api.get('/privacy/consents/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    recordConsent: (policyId, accepted) => api.post('/privacy/consents/', { policy: policyId, accepted }),

    // ARCO
    getARCORequests: async () => {
        const response = await api.get('/privacy/arco/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createARCORequest: (data) => api.post('/privacy/arco/', data),

    // Admin
    getRAT: async () => {
        const response = await api.get('/privacy/rat/');
        return response.data;
    },
    getBreaches: async () => {
        const response = await api.get('/privacy/breaches/');
        return response.data;
    },
};

export default privacyService;
