import api from './api';

const userService = {
    getUsers: async (role = null) => {
        let url = '/users/';
        if (role) {
            url += `?role=${role}`;
        }
        const response = await api.get(url);
        return response.data;
    },
    createUser: async (userData) => {
        const response = await api.post('/users/', userData);
        return response.data;
    },
    updateUser: async (id, userData) => {
        const response = await api.patch(`/users/${id}/`, userData);
        return response.data;
    },
    deleteUser: async (id) => {
        const response = await api.delete(`/users/${id}/`);
        return response.data;
    },

    // Institutions
    getInstitutions: async () => {
        const response = await api.get('/users/institutions/');
        return response.data;
    },
    createInstitution: async (data) => {
        const response = await api.post('/users/institutions/', data);
        return response.data;
    },
    updateInstitution: async (id, data) => {
        const response = await api.patch(`/users/institutions/${id}/`, data);
        return response.data;
    },
    deleteInstitution: async (id) => {
        const response = await api.delete(`/users/institutions/${id}/`);
        return response.data;
    }
};

export default userService;
