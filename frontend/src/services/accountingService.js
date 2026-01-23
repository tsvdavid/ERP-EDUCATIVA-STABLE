import axios from 'axios';

const API_URL = 'http://localhost:8000/api/accounting';

const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
};

const accountingService = {
    getAccounts: async (params) => {
        const response = await axios.get(`${API_URL}/accounts/`, {
            headers: getAuthHeader(),
            params
        });
        return response.data;
    },
    createAccount: async (data) => {
        const response = await axios.post(`${API_URL}/accounts/`, data, { headers: getAuthHeader() });
        return response.data;
    },
    getEntries: async () => {
        const response = await axios.get(`${API_URL}/entries/`, { headers: getAuthHeader() });
        return response.data;
    },
    getBalanceSheet: async () => {
        const response = await axios.get(`${API_URL}/reports/balance_sheet/`, { headers: getAuthHeader() });
        return response.data;
    },
    getIncomeStatement: async () => {
        const response = await axios.get(`${API_URL}/reports/income_statement/`, { headers: getAuthHeader() });
        return response.data;
    },
    downloadATS: async (year, month) => {
        const response = await axios.get(`${API_URL}/reports/ats/`, {
            headers: getAuthHeader(),
            params: { year, month },
            responseType: 'blob'
        });
        return response.data;
    }
};

export default accountingService;
