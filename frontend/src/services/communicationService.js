import api from './api';

const communicationService = {
    getMessages: async () => {
        const response = await api.get('/communication/messages/');
        return response.data;
    },
    getInbox: async () => {
        const response = await api.get('/communication/messages/inbox/');
        return response.data;
    },
    getSent: async () => {
        const response = await api.get('/communication/messages/sent/');
        return response.data;
    },
    sendMessage: async (data) => {
        const config = (data instanceof FormData) ? { headers: { 'Content-Type': 'multipart/form-data' } } : {};
        const response = await api.post('/communication/messages/', data, config);
        return response.data;
    },
    markNotificationRead: async (id) => {
        const response = await api.post(`/communication/notifications/${id}/mark_read/`);
        return response.data;
    },
    getNotifications: async () => {
        const response = await api.get('/communication/notifications/');
        return response.data;
    },
    getNotices: async () => {
        const response = await api.get('/communication/notices/');
        return response.data;
    },
    createNotice: async (data) => {
        // Handle both JSON and FormData logic if needed, but for files we need FormData
        // If data is FormData, let axios handle headers. If object and has file, convert.
        if (!(data instanceof FormData)) {
            // Basic JSON fallback if no file logic, but prefer FormData for consistency if mixing
            const response = await api.post('/communication/notices/', data);
            return response.data;
        }
        const response = await api.post('/communication/notices/', data, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },
    updateNotice: async (id, data) => {
        const config = (data instanceof FormData) ? { headers: { 'Content-Type': 'multipart/form-data' } } : {};
        const response = await api.put(`/communication/notices/${id}/`, data, config);
        return response.data;
    },
    deleteNotice: async (id) => {
        const response = await api.delete(`/communication/notices/${id}/`);
        return response.data;
    },
    getHolidays: async () => {
        const response = await api.get('/communication/holidays/');
        return response.data;
    },
    populateHolidays: async (year) => {
        const response = await api.post('/communication/holidays/populate_holidays/', { year });
        return response.data;
    },
    createHoliday: async (data) => {
        const response = await api.post('/communication/holidays/', data);
        return response.data;
    },
    deleteHoliday: async (id) => {
        const response = await api.delete(`/communication/holidays/${id}/`);
        return response.data;
    }

};

export default communicationService;
