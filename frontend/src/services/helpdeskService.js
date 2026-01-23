import api from './api';

const helpdeskService = {
    // Catalog
    getCatalog: () => api.get('/helpdesk/catalog/'),
    createCategory: (data) => api.post('/helpdesk/catalog/', data),

    // Tickets
    getTickets: () => api.get('/helpdesk/tickets/'),
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
    getWorkflows: () => api.get('/helpdesk/workflows/'),
};

export default helpdeskService;
