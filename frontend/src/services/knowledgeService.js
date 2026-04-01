import api from './api';

const knowledgeService = {
    // Categories
    getCategories: async () => {
        const response = await api.get('/knowledge/categories/');
        return response.data;
    },
    createCategory: async (data) => {
        const response = await api.post('/knowledge/categories/', data);
        return response.data;
    },
    updateCategory: async (id, data) => {
        const response = await api.put(`/knowledge/categories/${id}/`, data);
        return response.data;
    },
    deleteCategory: async (id) => {
        const response = await api.delete(`/knowledge/categories/${id}/`);
        return response.data;
    },

    // Articles
    getArticles: async (params) => {
        const response = await api.get('/knowledge/articles/', { params });
        return response.data;
    },
    getArticle: async (id) => {
        const response = await api.get(`/knowledge/articles/${id}/`);
        return response.data;
    },
    createArticle: async (data) => {
        const response = await api.post('/knowledge/articles/', data);
        return response.data;
    },
    updateArticle: async (id, data) => {
        const response = await api.put(`/knowledge/articles/${id}/`, data);
        return response.data;
    },
    deleteArticle: async (id) => {
        const response = await api.delete(`/knowledge/articles/${id}/`);
        return response.data;
    }
};

export default knowledgeService;
