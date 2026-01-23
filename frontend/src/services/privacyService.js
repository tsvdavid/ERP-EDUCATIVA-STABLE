import api from './api';

const privacyService = {
    // Policies
    getPolicies: () => api.get('/privacy/policies/'),

    // Consents
    getConsents: () => api.get('/privacy/consents/'),
    recordConsent: (policyId, accepted) => api.post('/privacy/consents/', { policy: policyId, accepted }),

    // ARCO
    getARCORequests: () => api.get('/privacy/arco/'),
    createARCORequest: (data) => api.post('/privacy/arco/', data),

    // Admin
    getRAT: () => api.get('/privacy/rat/'),
    getBreaches: () => api.get('/privacy/breaches/'),
};

export default privacyService;
