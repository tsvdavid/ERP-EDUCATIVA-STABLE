import api from './api';

const maintenanceService = {
    downloadBackup: async () => {
        const response = await api.get('/maintenance/backup/', {
            responseType: 'blob', // Important for file download
        });
        return response.data;
    },

    restoreBackup: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/maintenance/restore/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    getUsersForMaintenance: async () => {
        const response = await api.get('/maintenance/users/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },

    deleteUsers: async (userIds) => {
        const response = await api.delete('/maintenance/users/', {
            data: { user_ids: userIds }
        });
        return response.data;
    },

    getLog: async () => {
        const response = await api.get('/maintenance/log/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },

    resetApplication: async () => {
        const response = await api.post('/maintenance/reset/');
        return response.data;
    }
};

export default maintenanceService;
