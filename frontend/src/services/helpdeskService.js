import api from './api';

const helpdeskService = {
    // Catalog
    getCatalog: async () => {
        const response = await api.get('/helpdesk/catalog/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    createCategory: (data) => api.post('/helpdesk/catalog/', data),

    // Tickets
    getTickets: async () => {
        const response = await api.get('/helpdesk/tickets/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    getTicket: (id) => api.get(`/helpdesk/tickets/${id}/`),
    createTicket: (data) => api.post('/helpdesk/tickets/', data),
    updateTicket: (id, data) => api.patch(`/helpdesk/tickets/${id}/`, data),

    // Actions
    rateTicket: (id, rating, comment) => api.post(`/helpdesk/tickets/${id}/rate/`, { rating, comment }),
    reopenTicket: (id) => api.post(`/helpdesk/tickets/${id}/reopen/`),

    // Comments & Attachments
    addComment: (data) => api.post('/helpdesk/comments/', data),
    addAttachment: (data) => {
        const formData = new FormData();
        formData.append('ticket', data.ticket);
        formData.append('file', data.file);
        return api.post('/helpdesk/attachments/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        });
    },

    // Workflows (Admin)
    getWorkflows: async () => {
        const response = await api.get('/helpdesk/workflows/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
};

export default helpdeskService;
