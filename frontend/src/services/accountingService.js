import api from './api';

const accountingService = {
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
    }
};

export default accountingService;
