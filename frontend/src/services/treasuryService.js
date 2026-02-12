import api from './api';

const treasuryService = {
    // Concepts
    getConcepts: async () => {
        const response = await api.get('/treasury/concepts/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    createConcept: async (data) => {
        const response = await api.post('/treasury/concepts/', data);
        return response.data;
    },
    updateConcept: async (id, data) => {
        const response = await api.put(`/treasury/concepts/${id}/`, data);
        return response.data;
    },
    deleteConcept: async (id) => {
        const response = await api.delete(`/treasury/concepts/${id}/`);
        return response.data;
    },

    // Methods
    getMethods: async () => {
        const response = await api.get('/treasury/methods/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },

    // Accounts
    getAccounts: async () => {
        const response = await api.get('/treasury/accounts/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },

    // Invoices
    getInvoices: async (params) => {
        const response = await api.get('/treasury/invoices/', { params });
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },

    // Process Payment
    processPayment: async (paymentData) => {
        const response = await api.post('/treasury/invoices/process-payment/', paymentData);
        return response.data;
    },

    // Charges
    getCharges: async (params) => {
        // params: { student_id, pending: true/false }
        const response = await api.get('/treasury/charges/', { params });
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    generateCharges: async (data) => {
        const response = await api.post('/treasury/charges/generate-monthly/', data);
        return response.data;
    },

    // Download
    downloadInvoice: async (invoiceId) => {
        const response = await api.get(`/treasury/invoices/${invoiceId}/download_pdf/`, {
            responseType: 'blob'
        });
        return response.data;
    },

    // SRI
    sendToSri: async (invoiceId) => {
        const response = await api.post(`/treasury/invoices/${invoiceId}/send-sri/`);
        return response.data;
    },

    downloadInvoiceXml: async (invoiceId) => {
        const response = await api.get(`/treasury/invoices/${invoiceId}/download_xml/`, {
            responseType: 'blob'
        });
        return response.data;
    }
};

export default treasuryService;
