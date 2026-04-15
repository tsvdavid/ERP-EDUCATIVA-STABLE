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
    const [attendanceMap, setAttendanceMap] = useState({});
    const [loading, setLoading] = useState(false);
    const [showBehaviorModal, setShowBehaviorModal] = useState(false);
    const [todayBehaviors, setTodayBehaviors] = useState({});
    const [selectedStudentForBehavior, setSelectedStudentForBehavior] = useState(null);

    useEffect(() => { loadCourses(); }, []);

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
            if (data && data.length > 0 && !selectedCourse) {
                setSelectedCourse(data[0].id.toString());
            }
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
            
            const allEnrollments = await academicService.getEnrollments();
            const courseEnrollments = allEnrollments.filter(e => e.course === parseInt(selectedCourse));

            const existingAttendance = await academicService.getAttendance(selectedCourse, selectedDate);

            const mapa = {};
            courseEnrollments.forEach(enrollment => {
                const record = existingAttendance.find(a => a.enrollment === enrollment.id);
                mapa[enrollment.id] = {
                    status: record ? record.status : 'PENDING',
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

    const handleSaveAttendance = async () => {
        setLoading(true);
        try {
            const promises = Object.entries(attendanceMap).map(([enrollmentId, data]) => {
                if (data.status === 'PENDING') return null;
                
                const payload = {
                    enrollment: parseInt(enrollmentId),
                    date: selectedDate,
                    status: data.status,
                    remarks: data.remarks
                };

                if (data.id) {
                    return academicService.updateAttendance(data.id, payload);
                } else {
                    return academicService.createAttendance(payload);
                }
            }).filter(p => p !== null);

            await Promise.all(promises);
            toast.success("Asistencia guardada correctamente");
            loadAttendanceData();
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar la asistencia");
        } finally {
            setLoading(false);
        }
    };

    const openBehaviorModal = (studentId, studentName) => {
        const existing = todayBehaviors[studentId];
        setSelectedStudentForBehavior({ id: studentId, fullName: studentName, existingRecord: existing });
        setShowBehaviorModal(true);
    };

    return (
        <div className="space-y-6">
            <Toaster />
            <div className="flex flex-col md:flex-row justify-between items-start gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Control de Asistencia</h1>
                    <p className="text-slate-500 mt-1">Gestión diaria de presencia estudiantil.</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto">
                    <select 
                        className="input-modern min-w-[200px]"
                        value={selectedCourse}
                        onChange={(e) => setSelectedCourse(e.target.value)}
                    >
                        <option value="">Seleccione un curso...</option>
                        {courses.map(course => (
                            <option key={course.id} value={course.id}>
                                {course.name} {course.parallel}
                            </option>
                        ))}
                    </select>

                    <input 
                        type="date"
                        className="input-modern"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                    />

                    <button 
                        onClick={handleSaveAttendance}
                        disabled={loading || students.length === 0}
                        className="btn-primary flex items-center justify-center gap-2"
                    >
                        <Save size={18} /> {loading ? 'Guardando...' : 'Guardar Todo'}
                    </button>
                </div>
            </div>

            <div className="card-premium overflow-hidden mt-6">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-slate-50 text-xs uppercase text-slate-500 font-semibold tracking-wider">
                            <tr>
                                <th className="p-4 border-b border-r border-slate-200 min-w-[250px]">Estudiante</th>
                                <th className="p-4 border-b border-slate-200 text-center">Estado</th>
                                <th className="p-4 border-b border-slate-200 min-w-[200px]">Observaciones</th>
                                <th className="p-4 border-b border-slate-200 text-center">Conducta</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {students.map((student) => {
                                const att = attendanceMap[student.id] || { status: 'PENDING', remarks: '' };
                                const studentName = att.studentName || 'Estudiante';
                                
                                return (
                                    <tr key={student.id} className="hover:bg-slate-50/50 transition-colors group">
                                        <td className="p-4 border-r border-slate-100 font-medium text-slate-700">
                                            {studentName}
                                        </td>
                                        <td className="p-4">
                                            <div className="flex justify-center gap-2">
                                                {['PRESENT', 'ABSENT', 'LATE', 'EXCUSED'].map(status => (
                                                    <button 
                                                        key={status}
                                                        onClick={() => handleStatusChange(student.id, status)}
                                                        className={`p-2 rounded-lg border transition-all ${att.status === status ? 'bg-indigo-100 border-indigo-300 text-indigo-700' : 'bg-slate-50 border-slate-200 opacity-60 hover:opacity-100'}`}
                                                        title={status}
                                                    >
                                                        {status === 'PRESENT' && <CheckCircle size={18} className={att.status === 'PRESENT' ? 'text-green-600' : 'text-slate-400'} />}
                                                        {status === 'ABSENT' && <XCircle size={18} className={att.status === 'ABSENT' ? 'text-rose-600' : 'text-slate-400'} />}
                                                        {status === 'LATE' && <Clock size={18} className={att.status === 'LATE' ? 'text-amber-600' : 'text-slate-400'} />}
                                                        {status === 'EXCUSED' && <AlertTriangle size={18} className={att.status === 'EXCUSED' ? 'text-blue-600' : 'text-slate-400'} />}
                                                    </button>
                                                ))}
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <input 
                                                type="text"
                                                className="w-full bg-slate-50/50 border-none rounded-lg p-2 text-sm focus:ring-2 focus:ring-indigo-500/20"
                                                value={att.remarks}
                                                onChange={(e) => setAttendanceMap(prev => ({
                                                    ...prev,
                                                    [student.id]: { ...prev[student.id], remarks: e.target.value }
                                                }))}
                                            />
                                        </td>
                                        <td className="p-4 text-center">
                                            <button 
                                                onClick={() => openBehaviorModal(student.student, studentName)}
                                                className={`p-2 rounded-full transition-colors ${todayBehaviors[student.student] ? 'text-emerald-500 bg-emerald-50' : 'text-slate-300 hover:text-slate-500'}`}
                                            >
                                                {todayBehaviors[student.student] ? <CheckCircle size={22} /> : <FileText size={22} />}
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {showBehaviorModal && selectedStudentForBehavior && (
                <BehaviorQuickModal
                    studentId={selectedStudentForBehavior.id}
                    studentName={selectedStudentForBehavior.fullName}
                    existingRecord={selectedStudentForBehavior.existingRecord}
                    courseId={selectedCourse}
                    onClose={() => { setShowBehaviorModal(false); setSelectedStudentForBehavior(null); }}
                    onSaved={() => { loadAttendanceData(); }}
                />
            )}
        </div>
    );
};

export default AttendancePage;
