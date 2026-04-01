import api from './api';

const learningService = {
    // Courses
    getCourses: async (params) => {
        const response = await api.get('/learning/courses/', { params });
        return response.data;
    },
    getCourse: async (id) => {
        const response = await api.get(`/learning/courses/${id}/`);
        return response.data;
    },
    createCourse: async (data) => {
        const response = await api.post('/learning/courses/', data);
        return response.data;
    },
    updateCourse: async (id, data) => {
        // Prevent sending absolute URLs for image fields or nested read-only objects
        const payload = { ...data };
        if (typeof payload.cover_image === 'string' && payload.cover_image.startsWith('http')) {
            delete payload.cover_image;
        }
        const response = await api.patch(`/learning/courses/${id}/`, payload);
        return response.data;
    },
    deleteCourse: async (id) => {
        const response = await api.delete(`/learning/courses/${id}/`);
        return response.data;
    },
    
    // Enrollment
    enrollInCourse: async (courseId) => {
        const response = await api.post(`/learning/courses/${courseId}/enroll/`);
        return response.data;
    },
    
    getMyEnrollments: async () => {
        const response = await api.get('/learning/enrollments/');
        return response.data;
    },
    
    // Progress
    completeLesson: async (lessonId) => {
        const response = await api.post(`/learning/lessons/${lessonId}/complete/`);
        return response.data;
    },

    // Modules & Lessons
    createModule: async (data) => {
        const response = await api.post('/learning/modules/', data);
        return response.data;
    },
    updateModule: async (id, data) => {
        const response = await api.patch(`/learning/modules/${id}/`, data);
        return response.data;
    },
    deleteModule: async (id) => {
        const response = await api.delete(`/learning/modules/${id}/`);
        return response.data;
    },
    createLesson: async (data) => {
        const response = await api.post('/learning/lessons/', data);
        return response.data;
    },
    updateLesson: async (id, data) => {
        const response = await api.patch(`/learning/lessons/${id}/`, data);
        return response.data;
    },
    deleteLesson: async (id) => {
        const response = await api.delete(`/learning/lessons/${id}/`);
        return response.data;
    },

    // Resources
    addResource: async (formData) => {
        const response = await api.post('/learning/resources/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    // Quizzes
    getQuizzes: async (params) => {
        const response = await api.get('/learning/quizzes/', { params });
        return response.data;
    },
    createQuiz: async (data) => {
        const response = await api.post('/learning/quizzes/', data);
        return response.data;
    },
    updateQuiz: async (id, data) => {
        const response = await api.patch(`/learning/quizzes/${id}/`, data);
        return response.data;
    },
    
    // Quiz Attempts
    startQuizAttempt: async (quizId) => {
        const response = await api.post('/learning/quiz-attempts/', { quiz: quizId });
        return response.data;
    },
    submitQuizAnswers: async (attemptId, answers) => {
        const response = await api.post(`/learning/quiz-attempts/${attemptId}/submit_answers/`, { answers });
        return response.data;
    }
};

export default learningService;
