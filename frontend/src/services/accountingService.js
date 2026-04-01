import api from './api';

const accountingService = {
    // --- Fiscal Years ---
    getFiscalYears: async () => {
        const response = await api.get('/accounting/fiscal-years/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createFiscalYear: async (data) => {
        const response = await api.post('/accounting/fiscal-years/', data);
        return response.data;
    },
    closeFiscalYear: async (id) => {
        const response = await api.post(`/accounting/fiscal-years/${id}/close_year/`);
        return response.data;
    },

    getAccounts: async (params) => {
        const response = await api.get('/accounting/accounts/', {
            params
        });
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createAccount: async (data) => {
        const response = await api.post('/accounting/accounts/', data);
        return response.data;
    },
    getEntries: async () => {
        const response = await api.get('/accounting/entries/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createEntry: async (data) => {
        const response = await api.post('/accounting/entries/', data);
        return response.data;
    },
    getLedger: async (params) => {
        const response = await api.get('/accounting/reports/ledger/', { params });
        return response.data;
    },
    getBalanceSheet: async () => {
        const response = await api.get('/accounting/reports/balance_sheet/');
        const data = response.data;
        // Validate structure
        if (!data || typeof data !== 'object' || Array.isArray(data) || !('total_assets' in data)) {
            console.error("Invalid Balance Sheet response:", data);
            // Return safe default structure to prevent crash
            return {
                assets: [], liabilities: [], equity: [],
                total_assets: 0, total_liabilities: 0, total_equity: 0,
                net_income: 0, total_equity_and_liabilities: 0
            };
        }
        return data;
    },
    getIncomeStatement: async () => {
        const response = await api.get('/accounting/reports/income_statement/');
        const data = response.data;
        // Validate structure
        if (!data || typeof data !== 'object' || Array.isArray(data) || !('total_income' in data)) {
            console.error("Invalid Income Statement response:", data);
            return {
                income: [], expenses: [],
                total_income: 0, total_expenses: 0,
                net_income: 0
            };
        }
        return data;
    },
    downloadATS: async (year, month) => {
        const response = await api.get('/accounting/reports/ats/', {
            params: { year, month },
            responseType: 'blob'
        });
        return response.data;
    },
    cancelEntry: async (id) => {
        const response = await api.post(`/accounting/entries/${id}/cancel_entry/`, {});
        return response.data;
    },

    // --- Banks Management ---
    getBanks: async () => {
        const response = await api.get('/accounting/banks/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createBank: async (data) => {
        const response = await api.post('/accounting/banks/', data);
        return response.data;
    },
    updateBank: async (id, data) => {
        const response = await api.put(`/accounting/banks/${id}/`, data);
        return response.data;
    },
    deleteBank: async (id) => {
        const response = await api.delete(`/accounting/banks/${id}/`);
        return response.data;
    },

    // --- Bank Accounts Management ---
    getBankAccounts: async () => {
        const response = await api.get('/accounting/bank-accounts/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    createBankAccount: async (data) => {
        const response = await api.post('/accounting/bank-accounts/', data);
        return response.data;
    },
    updateBankAccount: async (id, data) => {
        const response = await api.put(`/accounting/bank-accounts/${id}/`, data);
        return response.data;
    },
    deleteBankAccount: async (id) => {
        const response = await api.delete(`/accounting/bank-accounts/${id}/`);
        return response.data;
    },

    // --- Fixed Assets Management ---
    getAssets: async () => {
        const response = await api.get('/accounting/fixed-assets/');
        if (Array.isArray(response.data)) return response.data;
        if (response.data && Array.isArray(response.data.results)) return response.data.results;
        return [];
    },
    getAsset: async (id) => {
        const response = await api.get(`/accounting/fixed-assets/${id}/`);
        return response.data;
    },
    createAsset: async (data) => {
        const response = await api.post('/accounting/fixed-assets/', data);
        return response.data;
    },
    updateAsset: async (id, data) => {
        const response = await api.put(`/accounting/fixed-assets/${id}/`, data);
        return response.data;
    },
    deleteAsset: async (id) => {
        const response = await api.delete(`/accounting/fixed-assets/${id}/`);
        return response.data;
    },
    calculateDepreciation: async (id) => {
        const response = await api.post(`/accounting/fixed-assets/${id}/calculate_depreciation/`);
        return response.data;
    }
};

export default accountingService;
