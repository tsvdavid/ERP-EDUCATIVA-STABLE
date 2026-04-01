import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import academicService from '../services/academicService';
import healthService from '../services/healthService';
import { Calendar, Save, CheckCircle, XCircle, Clock, AlertTriangle, BarChart, FileText } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import BehaviorQuickModal from '../components/BehaviorQuickModal';

const AttendancePage = () => {
    const [courses, setCourses] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState('');
    const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
    const [students, setStudents] = useState([]);
    const [attendanceMap, setAttendanceMap] = useState({}); // { studentId: { status, id (if exists), remarks } }
    const [loading, setLoading] = useState(false);
    const [showBehaviorModal, setShowBehaviorModal] = useState(false);
    const [todayBehaviors, setTodayBehaviors] = useState({});
    const [selectedStudentForBehavior, setSelectedStudentForBehavior] = useState(null);

    useEffect(() => {
        loadCourses();
    }, []);

    useEffect(() => {
        if (selectedCourse && selectedDate) {
            loadAttendanceData();
        } else {
            setStudents([]);
            setAttendanceMap({});
        }
    }, [selectedCourse, selectedDate]);

    const loadCourses = async () => {
        try {
            const data = await academicService.getCourses();
            setCourses(data);
        } catch (error) {
            console.error(error);
        }
    };

    const loadAttendanceData = async () => {
        setLoading(true);
        try {
            try {
                const behaviorRes = await healthService.getBehaviorRecords({ course: selectedCourse, date: selectedDate });
                const bMap = {};
                const records = behaviorRes.results || behaviorRes;
                records.forEach(r => { bMap[r.student] = r; });
                setTodayBehaviors(bMap);
            } catch (err) { console.error("Behavior Error", err); }
            // 1. Get Enrollments (Students for this course)
            // We need a way to filter enrollments by course. 
            // The current getEnrollments returns ALL. We should probably filter on client or backend.
            // For MVP client filter is ok if dataset is small, but backend filter is better.
            // Let's assume we filter client side for now as getEnrollments doesn't have params yet in service?
            // Wait, we can add params to getEnrollments in service or just fetch all and filter.
            // Let's optimize: fetch all enrollments is bad. 
            // But I didn't update getEnrollments to filter by course in service, just backend allows it?
            // Let's check backend ViewSet. EnrollmentViewSet allows filtering by course?
            // "get_queryset" doesn't seem to have specific filters other than institution/role.
            // I should have updated EnrollmentViewSet.
            // WORKAROUND: filter client side for now.
            const allEnrollments = await academicService.getEnrollments();
            const courseEnrollments = allEnrollments.filter(e => e.course === parseInt(selectedCourse));

            // 2. Get Existing Attendance for Date
            const existingAttendance = await academicService.getAttendance(selectedCourse, selectedDate);

            // 3. Merge
            const mapa = {};
            courseEnrollments.forEach(enrollment => {
                const record = existingAttendance.find(a => a.enrollment === enrollment.id);
                mapa[enrollment.id] = {
                    status: record ? record.status : 'PENDING', // PENDING means not saved yet
                    id: record ? record.id : null,
                    remarks: record ? record.remarks : '',
                    studentName: enrollment.student_detail?.first_name
                        ? `${enrollment.student_detail.first_name} ${enrollment.student_detail.last_name}`
                        : enrollment.student_detail?.username
                };
            });

            setStudents(courseEnrollments);
            setAttendanceMap(mapa);

        } catch (error) {
            console.error(error);
            toast.error("Error al cargar datos");
        } finally {
            setLoading(false);
        }
    };

    const handleStatusChange = (enrollmentId, newStatus) => {
        setAttendanceMap(prev => ({
            ...prev,
            [enrollmentId]: { ...prev[enrollmentId], status: newStatus }
        }));
    };

    const openBehaviorModal = (studentId, studentName) => {
        setSelectedStudentForBehavior({ id: studentId, fullName: studentName });
        setShowBehaviorModal(true);
    };

    const markAll = (status) => {
        setAttendanceMap(prev => {
            const next = { ...prev };
            Object.keys(next).forEach(key => {
                next[key].status = status;
            });
            return next;
        });
    };

    const saveAttendance = async () => {
        const promises = [];
        let errors = 0;

        // Iterate over map
        for (const [enrollmentId, data] of Object.entries(attendanceMap)) {
            if (data.status === 'PENDING') continue; // Don't save if not touched/marked

            const payload = {
                enrollment: parseInt(enrollmentId),
                date: selectedDate,
                status: data.status,
                remarks: data.remarks
            };

            if (data.id) {
                // Update
                promises.push(academicService.updateAttendance(data.id, payload));
            } else {
                // Create
                promises.push(academicService.createAttendance(payload));
            }
        }

        try {
            await Promise.all(promises);
            toast.success("Asistencia guardada correctamente");
            loadAttendanceData(); // Reload to get IDs
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar algunos registros");
        }
    };

    const STATUS_OPTIONS = [
        { value: 'PRESENT', label: 'Presente', icon: CheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50' },
        { value: 'ABSENT', label: 'Ausente', icon: XCircle, color: 'text-red-600', bg: 'bg-red-50' },
        { value: 'LATE', label: 'Atraso', icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
        { value: 'EXCUSED', label: 'Justif.', icon: AlertTriangle, color: 'text-blue-600', bg: 'bg-blue-50' },
    ];

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />

            <div className="flex flex-wrap justify-between items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                        <Calendar className="text-indigo-600" /> Control de Asistencia
                    </h1>
                    <div className="flex items-center gap-3 mt-1">
                        <p className="text-slate-500">Registra y gestiona la asistencia diaria.</p>
                        <Link to="/dashboard/academic/reports" className="text-sm text-indigo-600 hover:text-indigo-800 font-medium flex items-center gap-1 bg-indigo-50 px-3 py-1 rounded-full transition-colors hidden sm:flex">
                            <BarChart size={14} /> Tablero de Estadísticas
                        </Link>
                    </div>
                </div>
                {students.length > 0 && (
                    <button
                        onClick={saveAttendance}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Save size={18} /> Guardar Cambios
                    </button>
                )}
            </div>

            {/* Controls */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                    <label className="label-modern">Curso</label>
                    <select
                        className="input-modern w-full"
                        value={selectedCourse}
                        onChange={(e) => setSelectedCourse(e.target.value)}
                    >
                        <option value="">Seleccione un curso...</option>
                        {courses.map(c => (
                            <option key={c.id} value={c.id}>{c.name} {c.parallel} ({c.level})</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="label-modern">Fecha</label>
                    <input
                        type="date"
                        className="input-modern w-full"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                    />
                </div>
                <div className="flex items-end">
                    {students.length > 0 && (
                        <button onClick={() => markAll('PRESENT')} className="text-sm font-medium text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 px-3 py-2 rounded-lg transition-colors">
                            Marcar Todos Presente
                        </button>
                    )}
                </div>
            </div>

            {/* Grid */}
            {selectedCourse ? (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    {loading ? (
                        <div className="p-10 text-center text-slate-400">Cargando estudiantes...</div>
                    ) : students.length === 0 ? (
                        <div className="p-10 text-center text-slate-400">No hay estudiantes en este curso.</div>
                    ) : (
                        <table className="w-full text-left">
                            <thead className="bg-slate-50 text-slate-500 font-medium border-b border-slate-100">
                                <tr>
                                    <th className="p-4">Estudiante</th>
                                    <th className="p-4 text-center">Estado</th>
                                    <th className="p-4">Observación</th>
                                    <th className="p-4 text-center">Conducta</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50">
                                {students.map(student => {
                                    const state = attendanceMap[student.id] || { status: 'PENDING' };
                                    return (
                                        <tr key={student.id} className="hover:bg-slate-50/50">
                                            <td className="p-4 font-medium text-slate-700">
                                                {state.studentName}
                                            </td>
                                            <td className="p-4">
                                                <div className="flex justify-center gap-2">
                                                    {STATUS_OPTIONS.map(opt => (
                                                        <button
                                                            key={opt.value}
                                                            onClick={() => handleStatusChange(student.id, opt.value)}
                                                            className={`p-2 rounded-lg transition-all ${state.status === opt.value
                                                                ? `${opt.bg} ${opt.color} ring-2 ring-offset-1 ring-${opt.color.split('-')[1]}-200`
                                                                : 'text-slate-300 hover:bg-slate-100'}`}
                                                            title={opt.label}
                                                        >
                                                            <opt.icon size={20} />
                                                        </button>
                                                    ))}
                                                </div>
                                                <div className="text-center mt-1">
                                                    <span className={`text-[10px] font-bold uppercase tracking-wider ${state.status === 'PENDING' ? 'text-slate-300' :
                                                        STATUS_OPTIONS.find(o => o.value === state.status)?.color
                                                        }`}>
                                                        {state.status === 'PENDING' ? 'Sin Registro' : STATUS_OPTIONS.find(o => o.value === state.status)?.label}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="p-4">
                                                <input
                                                    type="text"
                                                    placeholder="Opcional..."
                                                    className="input-modern text-xs w-full"
                                                    value={state.remarks || ''}
                                                    onChange={(e) => setAttendanceMap(prev => ({
                                                        ...prev,
                                                        [student.id]: { ...prev[student.id], remarks: e.target.value }
                                                    }))}
                                                />
                                            </td>
                                            <td className="p-4 text-center">
                                                <button
                                                    onClick={() => openBehaviorModal(student.student, state.studentName, todayBehaviors[student.student])}
                                                    className="p-2 hover:bg-indigo-50 rounded-lg transition-colors inline-block"
                                                    title={todayBehaviors[student.student] ? "Añadir a la Conducta" : "Registro Rápido de Conducta"}
                                                >
                                                    {todayBehaviors[student.student] ? <CheckCircle size={20} className="inline text-emerald-500" /> : <FileText size={20} className="inline text-indigo-400 hover:text-indigo-600" />}
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    )}
                </div>
            ) : (
                <div className="p-10 text-center bg-slate-50 rounded-xl border border-dashed border-slate-300 text-slate-400">
                    Selecciona un curso para comenzar a tomar asistencia.
                </div>
            )}

            {/* Modal de Conducta */}
            {showBehaviorModal && selectedStudentForBehavior && (
                <BehaviorQuickModal
                    existingRecord={selectedStudentForBehavior.existingRecord}
                    allowedTypes={['POSITIVE', 'NEGATIVE']}
                    studentId={selectedStudentForBehavior.id}
                    studentName={selectedStudentForBehavior.fullName}
                    courseId={selectedCourse}
                    onSaved={(result) => { if(result && result.student) { setTodayBehaviors(prev => ({...prev, [result.student]: result})); } loadAttendanceData(); }}
                    onClose={() => { setShowBehaviorModal(false); setSelectedStudentForBehavior(null); }}
                />
            )}
        </div>
    );
};

export default AttendancePage;
