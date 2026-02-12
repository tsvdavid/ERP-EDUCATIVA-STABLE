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
    }
};

export default purchaseService;
