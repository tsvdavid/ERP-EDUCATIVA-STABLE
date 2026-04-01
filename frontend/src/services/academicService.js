import api from './api';

const academicService = {
    // Cursos
    getCourses: async () => {
        const response = await api.get('/academic/courses/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
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
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
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

        // Agregar parámetro para obtener lista completa sin que DRF corte a 10/50 registros por página
        params.append('limit', '5000');

        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;

        const response = await api.get(url);
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
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
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
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
    getCourseStats: async (courseId, subjectId = null) => {
        let url = `/academic/grades/course-stats/?course_id=${courseId}`;
        if (subjectId) url += `&subject_id=${subjectId}`;
        const response = await api.get(url);
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
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
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
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    createAttendance: async (data) => {
        const response = await api.post('/academic/attendance/', data);
        return response.data;
    },
    updateAttendance: async (id, data) => {
        const response = await api.patch(`/academic/attendance/${id}/`, data);
        return response.data;
    },
    getAttendanceStats: async (courseId) => {
        const response = await api.get(`/academic/attendance/dashboard-stats/?course_id=${courseId}`);
        return response.data;
    },
    getAttendanceReport: async (courseId) => {
        const response = await api.get(`/academic/attendance/report/?course_id=${courseId}`);
        return response.data;
    },
    // Años y Periodos Lectivos
    getAcademicYears: async () => {
        const response = await api.get('/academic/academic-years/');
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
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
    },
    // New Reporting Methods
    getExcellenceRanking: async (level = null, courseId = null, academicYearId = null) => {
        let url = '/academic/enrollments/excellence-ranking/';
        const params = new URLSearchParams();
        if (level) params.append('level', level);
        if (courseId) params.append('course_id', courseId);
        if (academicYearId) params.append('academic_year_id', academicYearId);
        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;
        const response = await api.get(url);
        return response.data;
    },
    getInstitutionStats: async (academicYearId = null, courseId = null) => {
        let url = '/academic/enrollments/institution-stats/';
        const params = new URLSearchParams();
        if (academicYearId) params.append('academic_year_id', academicYearId);
        if (courseId) params.append('course_id', courseId);
        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;
        const response = await api.get(url);
        return response.data;
    },
    
    // Horarios de Clases
    getSchedules: async (courseId = null, studentId = null) => {
        let url = '/academic/schedules/';
        const params = new URLSearchParams();
        if (courseId) params.append('course', courseId);
        if (studentId) params.append('student_id', studentId);
        const queryString = params.toString();
        if (queryString) url += `?${queryString}`;
        
        const response = await api.get(url);
        if (Array.isArray(response.data)) {
            return response.data;
        }
        if (response.data && Array.isArray(response.data.results)) {
            return response.data.results;
        }
        return [];
    },
    createSchedule: async (data) => {
        const response = await api.post('/academic/schedules/', data);
        return response.data;
    },
    deleteSchedule: async (id) => {
        const response = await api.delete(`/academic/schedules/${id}/`);
        return response.data;
    }
};

export default academicService;
