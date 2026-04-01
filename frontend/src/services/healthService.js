import api from './api';

const healthService = {
    // ── Fichas Médicas ──────────────────────────────────────────────────────
    getMedicalRecords: async () => (await api.get('/health/medical-records/')).data,
    getMedicalRecord:  async (id) => (await api.get(`/health/medical-records/${id}/`)).data,
    createMedicalRecord: async (data) => (await api.post('/health/medical-records/', data)).data,
    updateMedicalRecord: async (id, data) => (await api.put(`/health/medical-records/${id}/`, data)).data,
    deleteMedicalRecord: async (id) => (await api.delete(`/health/medical-records/${id}/`)).data,

    // ── Consultas Médicas ───────────────────────────────────────────────────
    getMedicalVisits: async (params = {}) => (await api.get('/health/medical-visits/', { params })).data,
    createMedicalVisit: async (data) => (await api.post('/health/medical-visits/', data)).data,
    deleteMedicalVisit: async (id) => (await api.delete(`/health/medical-visits/${id}/`)).data,

    // ── Fichas DECE ─────────────────────────────────────────────────────────
    getDeceRecords: async () => (await api.get('/health/dece-records/')).data,
    getDeceRecord:  async (id) => (await api.get(`/health/dece-records/${id}/`)).data,
    createDeceRecord: async (data) => (await api.post('/health/dece-records/', data)).data,
    updateDeceRecord: async (id, data) => (await api.put(`/health/dece-records/${id}/`, data)).data,

    // ── Intervenciones DECE ─────────────────────────────────────────────────
    getDeceVisits: async (params = {}) => (await api.get('/health/dece-visits/', { params })).data,
    createDeceVisit: async (data) => (await api.post('/health/dece-visits/', data)).data,
    deleteDeceVisit: async (id) => (await api.delete(`/health/dece-visits/${id}/`)).data,

    // ── Registros Conductuales ──────────────────────────────────────────────
    getBehaviorRecords: async (params = {}) => (await api.get('/health/behavior-records/', { params })).data,
    getBehaviorRecord:  async (id) => (await api.get(`/health/behavior-records/${id}/`)).data,
    getStudentBehaviors: async (studentId, academicYear) =>
        (await api.get('/health/behavior-records/by-student/', { params: { student: studentId, academic_year: academicYear } })).data,
    quickCreateBehavior: async (data) => (await api.post('/health/behavior-records/quick-create/', data)).data,
    createBehaviorRecord: async (data) => (await api.post('/health/behavior-records/', data)).data,
    deleteBehaviorRecord: async (id) => (await api.delete(`/health/behavior-records/${id}/`)).data,
    updateBehaviorRecord: async (id, data) => (await api.patch(`/health/behavior-records/${id}/`, data)).data,

    // ── Casos Conductuales ──────────────────────────────────────────────────
    getBehaviorCases: async (params = {}) => (await api.get('/health/behavior-cases/', { params })).data,
    getBehaviorCase:  async (id) => (await api.get(`/health/behavior-cases/${id}/`)).data,
    createBehaviorCase: async (data) => (await api.post('/health/behavior-cases/', data)).data,
    updateBehaviorCase: async (id, data) => (await api.patch(`/health/behavior-cases/${id}/`, data)).data,
    deriveCase: async (id, data) => (await api.post(`/health/behavior-cases/${id}/derive/`, data)).data,
    closeCase:  async (id, data) => (await api.post(`/health/behavior-cases/${id}/close/`, data)).data,
    reopenCase: async (id) => (await api.post(`/health/behavior-cases/${id}/reopen/`)).data,

    // ── Seguimientos de Caso ────────────────────────────────────────────────
    getCaseFollowUps: async (caseId) =>
        (await api.get('/health/case-follow-ups/', { params: { case: caseId } })).data,
    createFollowUp: async (data) => (await api.post('/health/case-follow-ups/', data)).data,
    updateFollowUp: async (id, data) => (await api.patch(`/health/case-follow-ups/${id}/`, data)).data,

    // ── Perfiles de Riesgo ─────────────────────────────────────────────────
    getRiskProfiles: async (params = {}) => (await api.get('/health/student-risk-profiles/', { params })).data,
    getDashboardStats: async (academicYear) =>
        (await api.get('/health/student-risk-profiles/dashboard-stats/', { params: { academic_year: academicYear } })).data,
    recalculateRiskProfiles: async (data = {}) =>
        (await api.post('/health/student-risk-profiles/recalculate-all/', data)).data,

    // ── Reglas de Alerta ───────────────────────────────────────────────────
    getAlertRules: async () => (await api.get('/health/alert-rules/')).data,
    createAlertRule: async (data) => (await api.post('/health/alert-rules/', data)).data,
    updateAlertRule: async (id, data) => (await api.put(`/health/alert-rules/${id}/`, data)).data,
    deleteAlertRule: async (id) => (await api.delete(`/health/alert-rules/${id}/`)).data,
};

export default healthService;
