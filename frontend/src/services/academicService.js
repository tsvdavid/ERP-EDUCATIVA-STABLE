import api from './api';

const academicService = {
    // Cursos
    getCourses: async () => {
        const response = await api.get('/academic/courses/');
        return response.data;
    },
    createCourse: async (courseData) => {
        const response = await api.post('/academic/courses/', courseData);
        return response.data;
    },
    updateCourse: async (id, courseData) => {
        const response = await api.put(`/academic/courses/${id}/`, courseData);
        return response.data;
    },
    deleteCourse: async (id) => {
        const response = await api.delete(`/academic/courses/${id}/`);
        return response.data;
    },

    // Materias
    getSubjects: async () => {
        const response = await api.get('/academic/subjects/');
        return response.data;
    },
    createSubject: async (data) => {
        const response = await api.post('/academic/subjects/', data);
        return response.data;
    },
    updateSubject: async (id, data) => {
        const response = await api.put(`/academic/subjects/${id}/`, data);
        return response.data;
    },
    deleteSubject: async (id) => {
        const response = await api.delete(`/academic/subjects/${id}/`);
        return response.data;
    },

    // Matrículas
    getEnrollments: async (courseId = null, studentId = null) => {
        let url = '/academic/enrollments/';
        const params = new URLSearchParams();
        if (courseId) params.append('course_id', courseId);
        if (studentId) params.append('student_id', studentId);

        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;

        const response = await api.get(url);
        return response.data;
    },
    createEnrollment: async (data) => {
        const response = await api.post('/academic/enrollments/', data);
        return response.data;
    },
    downloadReportCard: async (enrollmentId) => {
        const response = await api.get(`/academic/enrollments/${enrollmentId}/download_report_card/`, {
            responseType: 'blob'
        });
        return response.data;
    },

    // Calificaciones
    getGrades: async (subjectId = null, studentId = null, courseId = null) => {
        let url = '/academic/grades/';
        const params = new URLSearchParams();
        if (subjectId) params.append('subject_id', subjectId);
        if (studentId) params.append('student_id', studentId);
        if (courseId) params.append('course_id', courseId);

        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;

        const response = await api.get(url);
        return response.data;
    },
    createGrade: async (data) => {
        const response = await api.post('/academic/grades/', data);
        return response.data;
    },
    updateGrade: async (id, data) => {
        const response = await api.put(`/academic/grades/${id}/`, data);
        return response.data;
    },
    deleteGrade: async (id) => {
        const response = await api.delete(`/academic/grades/${id}/`);
        return response.data;
    },

    // Categorías de Evaluación (Aportes)
    getEvaluationCategories: async (subjectId = null, trimester = null) => {
        let url = '/academic/evaluation-categories/';
        const params = new URLSearchParams();
        if (subjectId) params.append('subject_id', subjectId);
        if (trimester) params.append('trimester', trimester);

        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;

        const response = await api.get(url);
        return response.data;
    },
    createEvaluationCategory: async (data) => {
        const response = await api.post('/academic/evaluation-categories/', data);
        return response.data;
    },
    deleteEvaluationCategory: async (id) => {
        const response = await api.delete(`/academic/evaluation-categories/${id}/`);
        return response.data;
    },

    // Asistencia
    getAttendance: async (courseId, date) => {
        const response = await api.get(`/academic/attendance/?course_id=${courseId}&date=${date}`);
        return response.data;
    },
    createAttendance: async (data) => {
        const response = await api.post('/academic/attendance/', data);
        return response.data;
    },
    updateAttendance: async (id, data) => {
        const response = await api.patch(`/academic/attendance/${id}/`, data);
        return response.data;
    },
    // Años y Periodos Lectivos
    getAcademicYears: async () => {
        const response = await api.get('/academic/academic-years/');
        return response.data;
    },
    createAcademicYear: async (data) => {
        const response = await api.post('/academic/academic-years/', data);
        return response.data;
    },
    updateAcademicYear: async (id, data) => {
        const response = await api.patch(`/academic/academic-years/${id}/`, data);
        return response.data;
    },
    updateAcademicPeriod: async (id, data) => {
        const response = await api.patch(`/academic/academic-periods/${id}/`, data);
        return response.data;
    }
};

export default academicService;
