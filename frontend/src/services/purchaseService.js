import api from './api';

const purchaseService = {
    // Suppliers
    getSuppliers: async () => {
        const response = await api.get('/purchases/suppliers/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createSupplier: async (data) => {
        const response = await api.post('/purchases/suppliers/', data);
        return response.data;
    },
    updateSupplier: async (id, data) => {
        const response = await api.put(`/purchases/suppliers/${id}/`, data);
        return response.data;
    },
    deleteSupplier: async (id) => {
        await api.delete(`/purchases/suppliers/${id}/`);
    },

    // Invoices
    getInvoices: async () => {
        const response = await api.get('/purchases/invoices/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createInvoice: async (data) => {
        const response = await api.post('/purchases/invoices/', data);
        return response.data;
    },
    getInvoice: async (id) => {
        const response = await api.get(`/purchases/invoices/${id}/`);
        return response.data;
    },
    validateInvoice: async (id) => {
        const response = await api.post(`/purchases/invoices/${id}/validate/`, {});
        return response.data;
    },
    cancelInvoice: async (id) => {
        const response = await api.post(`/purchases/invoices/${id}/cancel/`, {});
        return response.data;
    },

    // Credit Notes
    getCreditNotes: async () => {
        const response = await api.get('/purchases/credit-notes/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createCreditNote: async (data) => {
        const response = await api.post('/purchases/credit-notes/', data);
        return response.data;
    },

    // Debit Notes
    getDebitNotes: async () => {
        const response = await api.get('/purchases/debit-notes/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createDebitNote: async (data) => {
        const response = await api.post('/purchases/debit-notes/', data);
        return response.data;
    },

    // Liquidations
    getLiquidations: async () => {
        const response = await api.get('/purchases/liquidations/');
        return response.data;
    },
    getLiquidation: async (id) => {
        const response = await api.get(`/purchases/liquidations/${id}/`);
        return response.data;
    },
    createLiquidation: async (data) => {
        const response = await api.post('/purchases/liquidations/', data);
        return response.data;
    },
    cancelLiquidation: async (id) => {
        const response = await api.post(`/purchases/liquidations/${id}/cancel/`);
        return response.data;
    },
};

export default purchaseService;
