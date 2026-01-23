import React, { useEffect, useState } from 'react';
import academicService from '../services/academicService';
import { BookOpen, Award, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';

const StudentGradesPage = () => {
    const [loading, setLoading] = useState(true);
    const [enrollment, setEnrollment] = useState(null);
    const [course, setCourse] = useState(null);
    const [summary, setSummary] = useState({});
    const [expandedSubject, setExpandedSubject] = useState(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const enrollments = await academicService.getEnrollments();

            if (enrollments.length === 0) {
                setLoading(false);
                return;
            }
            const myEnrollment = enrollments[0];
            setEnrollment(myEnrollment);
            setCourse(myEnrollment.course_detail);
            setSummary(myEnrollment.academic_summary || {});

        } catch (error) {
            console.error("Error loading student grades:", error);
        } finally {
            setLoading(false);
        }
    };

    const getScoreColor = (score) => {
        if (score === null || score === undefined || score === '-') return 'text-slate-400';
        const num = parseFloat(score);
        if (isNaN(num)) return 'text-slate-500';
        if (num >= 9) return 'text-emerald-600 font-bold';
        if (num >= 7) return 'text-indigo-600 font-medium';
        return 'text-red-500 font-bold';
    };

    const toggleExpand = (subjectId) => {
        if (expandedSubject === subjectId) {
            setExpandedSubject(null);
        } else {
            setExpandedSubject(subjectId);
        }
    };

    if (loading) return <div className="p-8 text-center flex justify-center"><div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div></div>;

    if (!enrollment) {
        return (
            <div className="p-10 text-center bg-white rounded-2xl shadow-sm border border-slate-100 mt-6">
                <div className="w-16 h-16 bg-orange-50 text-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <AlertCircle size={32} />
                </div>
                <h2 className="text-xl font-bold text-slate-800">Sin Matrícula Activa</h2>
                <p className="text-slate-500 mt-2">No tienes cursos asignados. Contacta a secretaría.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 max-w-6xl mx-auto">
            {/* Header Card */}
            <div className="bg-white p-8 rounded-3xl shadow-xl shadow-indigo-100 border border-slate-100 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -translate-y-32 translate-x-32 opacity-50 blur-3xl"></div>
                <div className="relative z-10">
                    <div className="flex items-center gap-4 mb-2 justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-indigo-600 rounded-2xl text-white shadow-lg shadow-indigo-600/30">
                                <BookOpen size={24} />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-slate-800">Mi Reporte Académico</h1>
                                <p className="text-slate-500">Año Lectivo {course?.year}</p>
                            </div>
                        </div>
                        <button
                            onClick={async () => {
                                try {
                                    const blob = await academicService.downloadReportCard(enrollment.id);
                                    const url = window.URL.createObjectURL(blob);
                                    const link = document.createElement('a');
                                    link.href = url;
                                    link.setAttribute('download', 'Reporte_Academico.pdf');
                                    document.body.appendChild(link);
                                    link.click();
                                    link.remove();
                                } catch (e) {
                                    console.error("Error downloading PDF", e);
                                    alert("Error al descargar el reporte. Intente nuevamente.");
                                }
                            }}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-md transition-all font-medium text-sm z-20"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" x2="12" y1="15" y2="3" /></svg>
                            Descargar PDF
                        </button>
                    </div>

                    <div className="mt-6 flex flex-wrap gap-4">
                        <div className="px-4 py-2 bg-slate-50 rounded-xl border border-slate-200">
                            <span className="text-xs font-bold text-slate-400 uppercase block mb-1">Curso</span>
                            <span className="text-slate-700 font-semibold">{course?.name} "{course?.parallel}"</span>
                        </div>
                        <div className="px-4 py-2 bg-slate-50 rounded-xl border border-slate-200">
                            <span className="text-xs font-bold text-slate-400 uppercase block mb-1">Nivel</span>
                            <span className="text-slate-700 font-semibold">{course?.level || 'General'}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Grades Table */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-100">
                        <tr>
                            <th className="p-5 text-xs font-bold text-slate-500 uppercase tracking-wider">Materia</th>
                            <th className="p-5 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Trimestre 1</th>
                            <th className="p-5 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Trimestre 2</th>
                            <th className="p-5 text-center text-xs font-bold text-slate-500 uppercase tracking-wider">Trimestre 3</th>
                            <th className="p-5 text-center text-xs font-bold text-indigo-600 uppercase tracking-wider bg-indigo-50/50">Promedio Final</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                        {Object.entries(summary).length === 0 ? (
                            <tr><td colSpan="5" className="p-8 text-center text-slate-400">No hay datos académicos disponibles.</td></tr>
                        ) : (
                            Object.entries(summary).map(([subjectId, data]) => (
                                <React.Fragment key={subjectId}>
                                    <tr
                                        onClick={() => toggleExpand(subjectId)}
                                        className="hover:bg-slate-50/50 transition-colors cursor-pointer group"
                                    >
                                        <td className="p-5 font-medium text-slate-700 flex items-center gap-2">
                                            <div className={`p-1 rounded-full transition-colors ${expandedSubject === subjectId ? 'bg-indigo-100 text-indigo-600' : 'text-slate-300 group-hover:text-indigo-500'}`}>
                                                {expandedSubject === subjectId ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                                            </div>
                                            {data.name}
                                        </td>
                                        <td className={`p-5 text-center ${getScoreColor(data.t1)}`}>{data.t1 || '-'}</td>
                                        <td className={`p-5 text-center ${getScoreColor(data.t2)}`}>{data.t2 || '-'}</td>
                                        <td className={`p-5 text-center ${getScoreColor(data.t3)}`}>{data.t3 || '-'}</td>
                                        <td className="p-5 text-center font-bold text-indigo-700 bg-indigo-50/20">
                                            {data.final || '-'}
                                        </td>
                                    </tr>
                                    {/* Detailed View */}
                                    {expandedSubject === subjectId && data.details && (
                                        <tr className="bg-slate-50/50 animate-in fade-in slide-in-from-top-2 duration-200">
                                            <td colSpan="5" className="p-0">
                                                <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 border-b border-indigo-100/50">
                                                    {[1, 2, 3].map(trim => (
                                                        <div key={trim} className="bg-white rounded-xl border border-slate-100 p-4 shadow-sm">
                                                            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-50">
                                                                <h4 className="text-sm font-bold text-slate-700">Trimestre {trim}</h4>
                                                                <span className={`text-sm ${getScoreColor(data['t' + trim])}`}>
                                                                    Prom: {data['t' + trim] || '-'}
                                                                </span>
                                                            </div>
                                                            <div className="space-y-2">
                                                                {data.details[trim] && data.details[trim].length > 0 ? (
                                                                    data.details[trim].map((det, idx) => (
                                                                        <div key={idx} className="flex justify-between items-center text-xs">
                                                                            <div>
                                                                                <span className="text-slate-600 block">{det.category}</span>
                                                                                <span className="text-slate-400 text-[10px]">{det.weight}% del promedio</span>
                                                                            </div>
                                                                            <span className={`font-medium ${getScoreColor(det.score)}`}>
                                                                                {det.score !== null ? det.score : '-'}
                                                                            </span>
                                                                        </div>
                                                                    ))
                                                                ) : (
                                                                    <p className="text-xs text-slate-400 italic py-2 text-center">Sin calificaciones</p>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            <div className="flex gap-4 p-4 bg-blue-50 text-blue-700 rounded-xl border border-blue-100 text-sm">
                <Award size={20} className="shrink-0" />
                <p>
                    <strong>Nota:</strong> Este reporte es parcial. Haz clic en una materia para ver el detalle de aportes por trimestre.
                </p>
            </div>
        </div>
    );
};

export default StudentGradesPage;
