import axios from 'axios';

const API_URL = 'http://localhost:8000/api/purchases';

const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
};

const purchaseService = {
    // Suppliers
    getSuppliers: async () => {
        const response = await axios.get(`${API_URL}/suppliers/`, { headers: getAuthHeader() });
        return response.data;
    },
    createSupplier: async (data) => {
        const response = await axios.post(`${API_URL}/suppliers/`, data, { headers: getAuthHeader() });
        return response.data;
    },
    updateSupplier: async (id, data) => {
        const response = await axios.put(`${API_URL}/suppliers/${id}/`, data, { headers: getAuthHeader() });
        return response.data;
    },
    deleteSupplier: async (id) => {
        await axios.delete(`${API_URL}/suppliers/${id}/`, { headers: getAuthHeader() });
    },

    // Invoices
    getInvoices: async () => {
        const response = await axios.get(`${API_URL}/invoices/`, { headers: getAuthHeader() });
        return response.data;
    },
    createInvoice: async (data) => {
        const response = await axios.post(`${API_URL}/invoices/`, data, { headers: getAuthHeader() });
        return response.data;
    },
    getInvoice: async (id) => {
        const response = await axios.get(`${API_URL}/invoices/${id}/`, { headers: getAuthHeader() });
        return response.data;
    },
    validateInvoice: async (id) => {
        const response = await axios.post(`${API_URL}/invoices/${id}/validate/`, {}, { headers: getAuthHeader() });
        return response.data;
    }
};

export default purchaseService;
