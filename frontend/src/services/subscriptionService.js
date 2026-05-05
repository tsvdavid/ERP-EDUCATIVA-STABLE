import api from './api';

const subscriptionService = {
    getDashboard: async () => {
        const response = await api.get('/subscriptions/admin/dashboard/');
        return response.data;
    },
    confirmPayment: async (id, data) => {
        const response = await api.post(`/subscriptions/admin/${id}/confirm-payment/`, data);
        return response.data;
    },
    getMyBillingInfo: async () => {
        const response = await api.get('/subscriptions/my-billing/info/');
        return response.data;
    },
    getObservability: async () => {
        const response = await api.get('/subscriptions/observability/monitoring/');
        return response.data;
    },
    getSubscriptions: async () => {
        const response = await api.get('/subscriptions/admin/');
        return response.data;
    },
    getSubscription: async (id) => {
        const response = await api.get(`/subscriptions/admin/${id}/`);
        return response.data;
    },
    suspendSubscription: async (id, reason) => {
        const response = await api.post(`/subscriptions/admin/${id}/suspend/`, { reason });
        return response.data;
    },
    reactivateSubscription: async (id) => {
        const response = await api.post(`/subscriptions/admin/${id}/reactivate/`);
        return response.data;
    },
    cancelSubscription: async (id) => {
        const response = await api.post(`/subscriptions/admin/${id}/cancel/`);
        return response.data;
    },
    editDates: async (id, next_billing_date) => {
        const response = await api.post(`/subscriptions/admin/${id}/edit-dates/`, { next_billing_date });
        return response.data;
    },
    updateModules: async (id, module_ids) => {
        const response = await api.post(`/subscriptions/admin/${id}/update-modules/`, { module_ids });
        return response.data;
    },
    getModules: async () => {
        const response = await api.get('/subscriptions/admin/modules/');
        return response.data;
    },
    getPlans: async () => {
        const response = await api.get('/subscriptions/plans/');
        return response.data;
    },
    createPlan: async (data) => {
        const response = await api.post('/subscriptions/plans/', data);
        return response.data;
    },
    updatePlan: async (id, data) => {
        const response = await api.patch(`/subscriptions/plans/${id}/`, data);
        return response.data;
    },
    deletePlan: async (id) => {
        const response = await api.delete(`/subscriptions/plans/${id}/`);
        return response.data;
    },
    changePlan: async (id, plan_id) => {
        const response = await api.post(`/subscriptions/admin/${id}/change-plan/`, { plan_id });
        return response.data;
    },
    getInstitutionsWithoutSubscription: async () => {
        const response = await api.get('/subscriptions/admin/institutions-without-sub/');
        return response.data;
    },
    createSubscription: async (data) => {
        const response = await api.post('/subscriptions/admin/', data);
        return response.data;
    },
    convertTrial: async (id) => {
        const response = await api.post(`/subscriptions/admin/${id}/convert-trial/`);
        return response.data;
    },
    getGlobalSettings: async () => {
        const response = await api.get('/subscriptions/global-settings/current/');
        return response.data;
    },
    updateGlobalSettings: async (data) => {
        const response = await api.patch('/subscriptions/global-settings/1/', data);
        return response.data;
    }
};

export default subscriptionService;
