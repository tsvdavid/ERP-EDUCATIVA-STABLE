import React, { useState, useEffect, useMemo } from 'react';
import academicService from '../../services/academicService';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { AlertCircle, FileText, CheckCircle, TrendingUp, Users, Activity, Download, FileJson } from 'lucide-react';
import * as XLSX from 'xlsx';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import html2canvas from 'html2canvas';

const AcademicReportsPage = () => {
    const [courses, setCourses] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState('');
    const [selectedSubject, setSelectedSubject] = useState('');

    const [loadingStats, setLoadingStats] = useState(false);

    // Attendance Stats
    const [attStats, setAttStats] = useState(null);

    // Grades Stats
    const [gradeStats, setGradeStats] = useState(null);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if (selectedCourse) {
            loadAttendanceData(selectedCourse);
        } else {
            setAttStats(null);
        }

        if (selectedCourse && selectedSubject) {
            loadGradesData(selectedCourse, selectedSubject);
        } else {
            setGradeStats(null);
        }
    }, [selectedCourse, selectedSubject]);

    const loadInitialData = async () => {
        try {
            const [coursesData, subjectsData] = await Promise.all([
                academicService.getCourses(),
                academicService.getSubjects()
            ]);
            setCourses(coursesData);
            setSubjects(subjectsData);
        } catch (error) {
            console.error("Error loading initial data", error);
        }
    };

    const loadAttendanceData = async (courseId) => {
        setLoadingStats(true);
        try {
            const data = await academicService.getAttendanceStats(courseId);
            setAttStats(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoadingStats(false);
        }
    };

    const loadGradesData = async (courseId, subjectId) => {
        setLoadingStats(true);
        try {
            const data = await academicService.getCourseStats(courseId, subjectId);
            setGradeStats(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoadingStats(false);
        }
    };

    const handleExportExcel = () => {
        const wb = XLSX.utils.book_new();
        const courseName = courses.find(c => c.id == selectedCourse)?.name || 'Curso';
        const subjectName = subjects.find(s => s.id == selectedSubject)?.name || 'Materia';

        // 1. Attendance Sheet
        if (attStats) {
            const attData = attStats.series.map(s => ({ Categoría: s.name, Cantidad: s.value }));
            attData.push({ Categoría: 'Total Estudiantes', Cantidad: attStats.total_students });
            attData.push({ Categoría: '% Asistencia', Cantidad: attStats.global_attendance_pct });
            const attWS = XLSX.utils.json_to_sheet(attData);
            XLSX.utils.book_append_sheet(wb, attWS, "Asistencia");
        }

        // 2. Grades Sheet
        if (gradeStats) {
            const gradesData = gradeStats.trimesters.map(t => ({ Periodo: t.name, Promedio: t.promedio }));
            gradesData.push({ Periodo: 'PROMEDIO FINAL', Promedio: gradeStats.course_average });
            const gradesWS = XLSX.utils.json_to_sheet(gradesData);
            XLSX.utils.book_append_sheet(wb, gradesWS, "Calificaciones");

            if (gradeStats.risk_students.length > 0) {
                const riskWS = XLSX.utils.json_to_sheet(gradeStats.risk_students.map(rs => ({
                    Estudiante: rs.student_name,
                    Nota: rs.score
                })));
                XLSX.utils.book_append_sheet(wb, riskWS, "Alertas_Riesgo");
            }
        }

        XLSX.writeFile(wb, `Reporte_${courseName}_${subjectName}.xlsx`);
    };

    const handleExportPDF = async () => {
        const doc = new jsPDF('p', 'mm', 'a4');
        const courseObj = courses.find(c => c.id == selectedCourse);
        const subjectObj = subjects.find(s => s.id == selectedSubject);
        
        doc.setFontSize(20);
        doc.setTextColor(79, 70, 229); // Indigo
        doc.text(`Reporte Académico: ${courseObj?.name} ${courseObj?.parallel}`, 14, 20);
        
        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(`Generado: ${new Date().toLocaleString()}`, 14, 27);
        if (subjectObj) doc.text(`Materia: ${subjectObj.name}`, 14, 32);

        let currentY = 40;

        // --- Captured Charts ---
        const captureChart = async (id, title, yPos) => {
            const element = document.getElementById(id);
            if (element) {
                const canvas = await html2canvas(element, { scale: 2 });
                const imgData = canvas.toDataURL('image/png');
                doc.setFontSize(12);
                doc.setTextColor(30);
                doc.text(title, 14, yPos);
                // Centered: (210 - 110) / 2 = 50
                doc.addImage(imgData, 'PNG', 50, yPos + 5, 110, 50);
                return yPos + 65;
            }
            return yPos;
        };

        if (attStats) {
            currentY = await captureChart('attendance-distribution', 'Distribución de Asistencia', currentY);
        }

        if (gradeStats && selectedSubject) {
            if (currentY > 200) { doc.addPage(); currentY = 20; }
            currentY = await captureChart('grade-trends', 'Tendencia de Calificaciones (Parciales)', currentY);
        }

        // --- Data Tables ---
        if (gradeStats && gradeStats.risk_students.length > 0) {
            if (currentY > 240) { doc.addPage(); currentY = 20; }
            doc.setFontSize(12);
            doc.setTextColor(185, 28, 28); // Red
            doc.text("Estudiantes en Riesgo Académico (< 7.0)", 14, currentY);
            autoTable(doc, {
                startY: currentY + 5,
                head: [['Estudiante', 'Promedio Actual']],
                body: gradeStats.risk_students.map(rs => [rs.student_name, rs.score]),
                theme: 'striped',
                headStyles: { fillColor: [185, 28, 28] }
            });
        }

        doc.save(`Reporte_Academico_${courseObj?.name}.pdf`);
    };

    const filteredSubjects = useMemo(() => {
        if (!selectedCourse) return [];
        return subjects.filter(s => s.course === parseInt(selectedCourse));
    }, [selectedCourse, subjects]);

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <div className="flex-1">
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
                        <Activity className="text-indigo-600" /> Reportes y Estadísticas
                    </h1>
                    <p className="text-slate-500 mt-1">Análisis de rendimiento y asistencia por curso y materia.</p>
                </div>
                
                <div className="flex flex-col gap-3 w-full md:w-auto">
                    <div className="flex flex-col sm:flex-row gap-4">
                        <select
                            className="input-modern min-w-[200px]"
                            value={selectedCourse}
                            onChange={e => { setSelectedCourse(e.target.value); setSelectedSubject(''); }}
                        >
                            <option value="">Seleccione Curso...</option>
                            {courses.map(c => (
                                <option key={c.id} value={c.id}>{c.name} {c.parallel}</option>
                            ))}
                        </select>

                        <select
                            className="input-modern min-w-[200px]"
                            value={selectedSubject}
                            onChange={e => setSelectedSubject(e.target.value)}
                            disabled={!selectedCourse}
                        >
                            <option value="">Seleccione Materia (Opcional)...</option>
                            {filteredSubjects.map(s => (
                                <option key={s.id} value={s.id}>{s.name}</option>
                            ))}
                        </select>
                    </div>

                    {selectedCourse && (
                        <div className="flex gap-2 justify-end">
                            <button 
                                onClick={handleExportExcel}
                                className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-4 py-2 rounded-xl text-sm font-bold hover:bg-emerald-100 transition-all border border-emerald-100"
                            >
                                <Download size={16} /> Excel
                            </button>
                            <button 
                                onClick={handleExportPDF}
                                className="flex items-center gap-2 bg-rose-50 text-rose-700 px-4 py-2 rounded-xl text-sm font-bold hover:bg-rose-100 transition-all border border-rose-100"
                            >
                                <FileJson size={16} /> PDF con Gráficos
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {!selectedCourse ? (
                <div className="text-center py-20 bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200">
                    <FileText className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <h3 className="text-lg font-medium text-slate-600">Seleccione un curso</h3>
                    <p className="text-slate-400">Elija un curso en la parte superior para ver las estadísticas.</p>
                </div>
            ) : loadingStats && !attStats ? (
                <div className="text-center py-10">Cargando métricas...</div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* ATTENDANCE SECTION */}
                    {attStats && (
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col">
                            <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                                <Users className="text-indigo-500" /> Resumen de Asistencia
                            </h2>
                            <div className="grid grid-cols-2 gap-4 mb-6">
                                <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                                    <div className="text-slate-500 text-sm font-medium">Estudiantes Matr.</div>
                                    <div className="text-2xl font-bold text-slate-800">{attStats.total_students}</div>
                                </div>
                                <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100">
                                    <div className="text-emerald-600 text-sm font-medium">% Asistencia Global</div>
                                    <div className="text-2xl font-bold text-emerald-700">{attStats.global_attendance_pct}%</div>
                                </div>
                            </div>

                            <div className="h-64 flex-1 w-full" id="attendance-distribution">
                                {attStats.total_records > 0 ? (
                                    <ResponsiveContainer width="100%" height="100%">
                                        <PieChart>
                                            <Pie
                                                data={attStats.series}
                                                cx="50%"
                                                cy="50%"
                                                innerRadius={60}
                                                outerRadius={80}
                                                paddingAngle={5}
                                                dataKey="value"
                                                nameKey="name"
                                                label
                                            >
                                                {attStats.series.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                                ))}
                                            </Pie>
                                            <RechartsTooltip />
                                            <Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                ) : (
                                    <div className="h-full flex items-center justify-center text-slate-400">
                                        No hay registros de asistencia
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* GRADES SECTION */}
                    {selectedSubject && gradeStats && (
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col">
                            <h2 className="text-lg font-bold text-slate-800 mb-4 flex items-center gap-2">
                                <TrendingUp className="text-indigo-500" /> Rendimiento Académico
                            </h2>

                            <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100 mb-6">
                                <div className="text-indigo-600 text-sm font-medium">Promedio General</div>
                                <div className="text-3xl font-bold text-indigo-700">{gradeStats.course_average} / 10</div>
                            </div>

                            {/* BAR CHART: Trimesters */}
                            <div className="h-48 w-full mb-6" id="grade-trends">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={gradeStats.trimesters} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                                        <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
                                        <RechartsTooltip cursor={{ fill: 'rgba(0,0,0,0.05)' }} />
                                        <Bar dataKey="promedio" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Promedio" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>

                            {/* PIE CHART: Distribution */}
                            <h3 className="text-sm font-bold text-slate-600 mb-2 uppercase tracking-wide">Distribución de Notas</h3>
                            <div className="h-48 w-full" id="distribution-pie-chart">
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={gradeStats.distribution.filter(d => d.value > 0)}
                                            cx="50%"
                                            cy="50%"
                                            outerRadius={60}
                                            dataKey="value"
                                            nameKey="name"
                                            label
                                        >
                                            {gradeStats.distribution.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.fill} />
                                            ))}
                                        </Pie>
                                        <RechartsTooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* RISK ALERTS */}
                    {selectedSubject && gradeStats && gradeStats.risk_students.length > 0 && (
                        <div className="lg:col-span-2 bg-red-50 p-6 rounded-2xl border border-red-100">
                            <h2 className="text-lg font-bold text-red-800 mb-4 flex items-center gap-2">
                                <AlertCircle /> Alerta Temprana de Bajo Rendimiento
                            </h2>
                            <p className="text-red-600 text-sm mb-4">Los siguientes estudiantes tienen un promedio menor a 7.00. Se requiere plan de refuerzo académico.</p>

                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                {gradeStats.risk_students.map(rs => (
                                    <div key={rs.id} className="bg-white p-3 rounded-xl border border-red-200 flex justify-between items-center shadow-sm">
                                        <span className="font-medium text-slate-800 text-sm">{rs.student_name}</span>
                                        <span className="bg-red-100 text-red-700 font-bold px-2 py-1 rounded text-sm">{rs.score}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default AcademicReportsPage;
