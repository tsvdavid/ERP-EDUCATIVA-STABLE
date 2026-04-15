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
    },

    // Assignments
    getAssignments: async (params) => {
        const response = await api.get('/learning/assignments/', { params });
        return response.data;
    },
    createAssignment: async (formData) => {
        const response = await api.post('/learning/assignments/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },
    updateAssignment: async (id, data) => {
        const response = await api.patch(`/learning/assignments/${id}/`, data);
        return response.data;
    },
    deleteAssignment: async (id) => {
        const response = await api.delete(`/learning/assignments/${id}/`);
        return response.data;
    },
    submitAssignmentResponse: async (formData) => {
        const response = await api.post('/learning/submissions/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },
    getAssignmentSubmissions: async (assignmentId) => {
        const response = await api.get(`/learning/submissions/?assignment_id=${assignmentId}`);
        return response.data;
    },
    updateSubmission: async (id, data) => {
        const response = await api.patch(`/learning/submissions/${id}/`, data);
        return response.data;
    },

    // Gestión de Alumnos
    getCourseEnrollments: async (courseId) => {
        const response = await api.get(`/learning/enrollments/?course_id=${courseId}`);
        if (Array.isArray(response.data)) return response.data;
        if (response.data?.results) return response.data.results;
        return [];
    },
    syncCourseStudents: async (courseId) => {
        const response = await api.post(`/learning/courses/${courseId}/sync_students/`);
        return response.data;
    },
    getCalendarEvents: async () => {
        const response = await api.get('/learning/calendar/events/');
        return response.data;
    },
    getInstructorStats: async () => {
        const response = await api.get('/learning/instructor/stats/');
        return response.data;
    },
    getUnifiedSubmissions: async (courseId = null) => {
        const url = courseId ? `/learning/instructor/submissions/?course_id=${courseId}` : '/learning/instructor/submissions/';
        const response = await api.get(url);
        return response.data;
    },
    getGroups: async () => {
        const response = await api.get('/learning/groups/');
        return response.data;
    },
    createGroup: async (data) => {
        const response = await api.post('/learning/groups/', data);
        return response.data;
    },
    updateGroup: async (id, data) => {
        const response = await api.patch(`/learning/groups/${id}/`, data);
        return response.data;
    },
    deleteGroup: async (id) => {
        const response = await api.delete(`/learning/groups/${id}/`);
        return response.data;
    },
    getTags: async (groupId = null) => {
        const url = groupId ? `/learning/tags/?group=${groupId}` : '/learning/tags/';
        const response = await api.get(url);
        return response.data;
    },
    createTag: async (data) => {
        const response = await api.post('/learning/tags/', data);
        return response.data;
    },
    updateTag: async (id, data) => {
        const response = await api.patch(`/learning/tags/${id}/`, data);
        return response.data;
    },
    deleteTag: async (id) => {
        const response = await api.delete(`/learning/tags/${id}/`);
        return response.data;
    },
    exportInstructorData: async (format, courseId = null) => {
        const url = courseId 
            ? `/learning/instructor/export/?format=${format}&course_id=${courseId}` 
            : `/learning/instructor/export/?format=${format}`;
        
        const response = await api.get(url, { responseType: 'blob' });
        
        const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = blobUrl;
        link.setAttribute('download', `reporte_panel_docente.${format === 'excel' ? 'xlsx' : 'pdf'}`);
        document.body.appendChild(link);
        link.click();
        link.remove();
    }
};

export default learningService;
