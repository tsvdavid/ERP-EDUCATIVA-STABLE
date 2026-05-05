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

    // Mass Billing
    createMassBilling: async (payload) => {
        const response = await api.post('/treasury/invoices/mass-billing/', payload);
        return response.data;
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

    // Credit Notes
    getCreditNotes: async () => {
        const response = await api.get('/treasury/credit-notes/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    createCreditNote: async (data) => {
        const response = await api.post('/treasury/credit-notes/', data);
        return response.data;
    },

    // Debit Notes
    getDebitNotes: async () => {
        const response = await api.get('/treasury/debit-notes/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    createDebitNote: async (data) => {
        const response = await api.post('/treasury/debit-notes/', data);
        return response.data;
    },

    // SRI
    sendToSri: async (invoiceId) => {
        const response = await api.post(`/treasury/invoices/${invoiceId}/send-sri/`);
        return response.data;
    },
    preflightCheck: async (invoiceId) => {
        const response = await api.post(`/treasury/invoices/${invoiceId}/preflight-check/`);
        return response.data;
    },

    downloadInvoiceXml: async (invoiceId) => {
        const response = await api.get(`/treasury/invoices/${invoiceId}/download_xml/`, {
            responseType: 'blob'
        });
        return response.data;
    },
    sendEmail: async (invoiceId, params = {}) => {
        const response = await api.post(`/treasury/invoices/${invoiceId}/send-email/`, null, { params });
        return response.data;
    },
    sendToAltEmail: async (invoiceId, email) => {
        const response = await api.post(`/treasury/invoices/${invoiceId}/send-to-alt-email/`, { email });
        return response.data;
    },
    getEmailHistory: async (invoiceId) => {
        const response = await api.get(`/treasury/invoices/${invoiceId}/email-history/`);
        return response.data;
    },
    // Customers
    getCustomers: async (params) => {
        const response = await api.get('/treasury/customers/', { params });
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    createCustomer: async (data) => {
        const response = await api.post('/treasury/customers/', data);
        return response.data;
    },
    updateCustomer: async (id, data) => {
        const response = await api.put(`/treasury/customers/${id}/`, data);
        return response.data;
    },

    // New Reporting Methods
    getFinancialStats: async (academicYearId = null, courseId = null) => {
        let url = '/treasury/charges/financial-stats/';
        const params = new URLSearchParams();
        if (academicYearId) params.append('academic_year_id', academicYearId);
        if (courseId) params.append('course_id', courseId);
        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;
        const response = await api.get(url);
        return response.data;
    },
    getCommercialDashboard: async () => {
        const response = await api.get('/treasury/invoices/commercial-dashboard/');
        return response.data;
    },
    getSriMonitoring: async (params) => {
        const response = await api.get('/treasury/invoices/sri-monitoring/', { params });
        return response.data;
    }
};

export default treasuryService;
