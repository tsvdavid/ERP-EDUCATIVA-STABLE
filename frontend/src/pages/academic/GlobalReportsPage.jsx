import React, { useState, useEffect } from 'react';
import { 
    Trophy, Users, DollarSign, AlertCircle, 
    TrendingUp, Calendar, Filter, Download, PieChart as PieChartIcon,
    FileText, Save, CheckCircle2, LayoutDashboard
} from 'lucide-react';
import academicService from '../../services/academicService';
import treasuryService from '../../services/treasuryService';
import { 
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
    PieChart, Pie, Cell, Legend
} from 'recharts';
import * as XLSX from 'xlsx';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import html2canvas from 'html2canvas';

const GlobalReportsPage = () => {
    const [stats, setStats] = useState(null);
    const [rankings, setRankings] = useState([]);
    const [financials, setFinancials] = useState(null);
    const [loading, setLoading] = useState(true);
    
    // Filters
    const [years, setYears] = useState([]);
    const [courses, setCourses] = useState([]);
    const [selectedYear, setSelectedYear] = useState('');
    const [selectedLevel, setSelectedLevel] = useState('all');
    const [selectedCourse, setSelectedCourse] = useState('all');

    const COLORS = ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B', '#EF4444'];

    useEffect(() => {
        loadFilters();
    }, []);

    useEffect(() => {
        fetchData();
    }, [selectedYear, selectedLevel, selectedCourse]);

    const loadFilters = async () => {
        try {
            const [yearsData, coursesData] = await Promise.all([
                academicService.getAcademicYears(),
                academicService.getCourses()
            ]);
            setYears(yearsData);
            setCourses(coursesData);
            
            // Set active year by default
            const activeYear = yearsData.find(y => y.is_active);
            if (activeYear) setSelectedYear(activeYear.id);
        } catch (error) {
            console.error("Error loading filters:", error);
        }
    };

    const fetchData = async () => {
        if (!selectedYear && years.length > 0) return; // Wait for initial year
        
        setLoading(true);
        try {
            const [instStats, rankData, finStats] = await Promise.all([
                academicService.getInstitutionStats(selectedYear, selectedCourse !== 'all' ? selectedCourse : null),
                academicService.getExcellenceRanking(selectedLevel !== 'all' ? selectedLevel : null, selectedCourse !== 'all' ? selectedCourse : null, selectedYear),
                treasuryService.getFinancialStats(selectedYear, selectedCourse !== 'all' ? selectedCourse : null)
            ]);
            setStats(instStats);
            setRankings(rankData);
            setFinancials(finStats);
        } catch (error) {
            console.error("Error fetching report data:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleExportExcel = () => {
        // 1. Prepare Ranking Data
        const rankingWS = XLSX.utils.json_to_sheet(rankings.map((r, i) => ({
            Puesto: i + 1,
            Estudiante: r.student_name,
            Nivel: r.level,
            Curso: r.course_name,
            Promedio: r.average
        })));

        // 2. Prepare Financial Data
        const financialWS = XLSX.utils.json_to_sheet(financials?.by_course?.map(f => ({
            Curso: f.course_name,
            'Monto Pendiente': f.pending_amount,
            'Estudiantes con Deuda': f.pending_students
        })) || []);

        // 3. Prepare Institution Summary (Quick Stats)
        const summaryData = [
            { Categoría: 'Estudiantes Totales', Valor: stats?.demographics?.students?.total || 0 },
            { Categoría: 'Profesores Totales', Valor: stats?.demographics?.teachers?.total || 0 },
            { Categoría: 'Pendiente Cobro', Valor: `$${financials?.global_total?.toLocaleString()}` },
            { Categoría: 'Faltas Críticas', Valor: stats?.discipline?.critical_high || 0 },
            { Categoría: 'Asistencia Global', Valor: `${stats?.attendance?.present ? Math.round((stats.attendance.present / (stats.attendance.present + stats.attendance.absent)) * 100) : 0}%` }
        ];
        const summaryWS = XLSX.utils.json_to_sheet(summaryData);

        // 4. Prepare Demographics Data
        const demoData = [
            { Tipo: 'Estudiantes - Hombres', Cantidad: stats?.demographics?.students?.M || 0 },
            { Tipo: 'Estudiantes - Mujeres', Cantidad: stats?.demographics?.students?.F || 0 },
            { Tipo: 'Profesores - Hombres', Cantidad: stats?.demographics?.teachers?.M || 0 },
            { Tipo: 'Profesores - Mujeres', Cantidad: stats?.demographics?.teachers?.F || 0 }
        ];
        const demoWS = XLSX.utils.json_to_sheet(demoData);

        // 5. Create Workbook
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, summaryWS, "Resumen General");
        XLSX.utils.book_append_sheet(wb, rankingWS, "Ranking Excelencia");
        XLSX.utils.book_append_sheet(wb, financialWS, "Estado Financiero");
        XLSX.utils.book_append_sheet(wb, demoWS, "Demografía");

        // 6. Download
        XLSX.writeFile(wb, `Reporte_Ejecutivo_${years.find(y => y.id == selectedYear)?.name || 'Eduka360'}_${new Date().toLocaleDateString()}.xlsx`);
    };

    const handleExportPDF = async () => {
        const doc = new jsPDF('p', 'mm', 'a4');
        const activeYearName = years.find(y => y.id == selectedYear)?.name || 'N/A';
        
        // --- Header & Visual Style ---
        doc.setFontSize(22);
        doc.setTextColor(30, 64, 175);
        doc.text("Eduka360 - Reporte Estratégico Global", 14, 25);
        
        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(`Año Académico: ${activeYearName}`, 14, 32);
        doc.text(`Generado: ${new Date().toLocaleString()}`, 14, 37);
        doc.text(`Filtros: Nivel: ${selectedLevel} | Curso: ${selectedCourse === 'all' ? 'Todos' : courses.find(c => c.id == selectedCourse)?.name}`, 14, 42);

        // --- Helper for Chart Capture ---
        const captureChart = async (id, title, yPos, height = 45) => {
            const element = document.getElementById(id);
            if (element) {
                const canvas = await html2canvas(element, { scale: 2 });
                const imgData = canvas.toDataURL('image/png');
                doc.setFontSize(12);
                doc.setTextColor(30);
                doc.text(title, 14, yPos);
                // Centered: (210 - 110) / 2 = 50
                doc.addImage(imgData, 'PNG', 50, yPos + 5, 110, height);
                return yPos + height + 15;
            }
            return yPos;
        };

        // --- Section 1: KPIs & Honor Roll ---
        doc.setFontSize(14);
        doc.text("1. Resumen de Indicadores Clave", 14, 55);
        autoTable(doc, {
            startY: 60,
            head: [['Estudiantes', 'Cartera Pendiente', 'Faltas Críticas', 'Asistencia']],
            body: [[
                stats?.demographics?.students?.total || 0,
                `$${financials?.global_total?.toLocaleString()}`,
                stats?.discipline?.critical_high || 0,
                `${stats?.attendance?.present ? Math.round((stats.attendance.present / (stats.attendance.present + stats.attendance.absent)) * 100) : 0}%`
            ]],
            theme: 'grid',
            headStyles: { fillColor: [30, 64, 175] }
        });

        let currentY = doc.lastAutoTable.finalY + 15;
        doc.text("2. Ranking de Excelencia Académica", 14, currentY);
        autoTable(doc, {
            startY: currentY + 5,
            head: [['Pos', 'Estudiante', 'Curso', 'Promedio']],
            body: rankings.slice(0, 10).map((r, i) => [i + 1, r.student_name, r.course_name, r.average.toFixed(2)]),
            theme: 'striped',
            headStyles: { fillColor: [245, 158, 11] }
        });

        // --- Section 2: Visual Analytics (Page 2) ---
        doc.addPage();
        doc.text("3. Análisis Visual Institucional", 14, 20);
        
        let visualY = 30;
        visualY = await captureChart('demographics-chart', '• Composición Estudiantil', visualY);
        visualY = await captureChart('financial-chart', '• Monitor Financiero por Curso', visualY);
        
        if (visualY > 220) { doc.addPage(); visualY = 20; }
        await captureChart('discipline-radar', '• Radar de Convivencia', visualY);

        doc.save(`Reporte_Global_Eduka360_${new Date().toLocaleDateString()}.pdf`);
    };

    if (loading && !stats) {
        return (
            <div className="flex flex-col items-center justify-center h-full space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                <p className="text-slate-500 font-medium animate-pulse">Generando reporte ejecutivo...</p>
            </div>
        );
    }

    const studentDemographics = [
        { name: 'Hombres', value: stats?.demographics?.students?.M || 0 },
        { name: 'Mujeres', value: stats?.demographics?.students?.F || 0 },
    ];

    const disciplineData = [
        { name: 'Conductual', value: stats?.discipline?.behavioral || 0 },
        { name: 'Académico', value: stats?.discipline?.academic || 0 },
        { name: 'Positivo', value: stats?.discipline?.positive || 0 },
    ];

    return (
        <div className="p-4 lg:p-8 space-y-6 lg:space-y-8 bg-slate-50/50 min-h-screen">
            {/* Premium Header */}
            <div className="bg-white p-4 lg:p-8 rounded-2xl lg:rounded-3xl shadow-sm border border-slate-100 flex flex-col lg:flex-row lg:items-center justify-between gap-6 transition-all hover:shadow-md">
                <div className="flex items-start gap-4">
                    <div className="p-3 lg:p-4 bg-primary-100 text-primary-600 rounded-xl lg:rounded-2xl">
                        <LayoutDashboard size={24} className="lg:w-8 lg:h-8" />
                    </div>
                    <div>
                        <h1 className="text-xl lg:text-3xl font-extrabold text-slate-800 tracking-tight">Reportes Institucionales</h1>
                        <p className="text-slate-500 text-xs lg:text-sm font-medium mt-1">Análisis estratégico {years.find(y => y.id == selectedYear)?.name}</p>
                    </div>
                </div>
                
                <div className="flex flex-wrap items-center gap-2 lg:gap-3">
                    <div className="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-xl flex-grow md:flex-none">
                        <Calendar size={16} className="text-slate-500" />
                        <select 
                            value={selectedYear}
                            onChange={(e) => setSelectedYear(e.target.value)}
                            className="bg-transparent border-none text-sm font-semibold text-slate-700 focus:ring-0 outline-none cursor-pointer"
                        >
                            {years.map(y => (
                                <option key={y.id} value={y.id}>{y.name} {y.is_active ? '(Actual)' : ''}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-xl">
                        <Filter size={18} className="text-slate-500" />
                        <select 
                            value={selectedLevel}
                            onChange={(e) => setSelectedLevel(e.target.value)}
                            className="bg-transparent border-none text-sm font-semibold text-slate-700 focus:ring-0 outline-none cursor-pointer"
                        >
                            <option value="all">Todos los Niveles</option>
                            <option value="Primaria">Primaria</option>
                            <option value="Secundaria">Secundaria</option>
                            <option value="Superior">Superior</option>
                        </select>
                    </div>

                    <div className="flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-xl">
                        <Save size={18} className="text-slate-500" />
                        <select 
                            value={selectedCourse}
                            onChange={(e) => setSelectedCourse(e.target.value)}
                            className="bg-transparent border-none text-sm font-semibold text-slate-700 focus:ring-0 outline-none cursor-pointer max-w-[200px]"
                        >
                            <option value="all">Todos los Cursos</option>
                            {courses
                                .filter(c => selectedYear ? c.year == years.find(y => y.id == selectedYear)?.year : true)
                                .filter(c => selectedLevel !== 'all' ? c.level === selectedLevel : true)
                                .map(c => (
                                <option key={c.id} value={c.id}>{c.name} {c.parallel}</option>
                            ))}
                        </select>
                    </div>

                    <div className="h-8 w-[1px] bg-slate-200 mx-2 hidden md:block"></div>

                    <div className="flex gap-2">
                        <button 
                            onClick={handleExportExcel}
                            className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-5 py-2.5 rounded-2xl text-sm font-bold hover:bg-emerald-100 transition-all border border-emerald-100"
                        >
                            <Download size={18} /> Excel
                        </button>
                        <button 
                            onClick={handleExportPDF}
                            className="flex items-center gap-2 bg-rose-50 text-rose-700 px-5 py-2.5 rounded-2xl text-sm font-bold hover:bg-rose-100 transition-all border border-rose-100"
                        >
                            <FileText size={18} /> PDF
                        </button>
                    </div>
                </div>
            </div>

            {/* Premium Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
                <StatCard 
                    icon={<Users className="text-primary-600" />}
                    label="Estudiantes"
                    value={stats?.demographics?.students?.total || 0}
                    trend="+12% vs año anterior"
                    color="primary"
                />
                <StatCard 
                    icon={<DollarSign className="text-emerald-600" />}
                    label="Cartera"
                    value={`$${financials?.global_total?.toLocaleString() || '0'}`}
                    trend="Meta: 85%"
                    color="emerald"
                />
                <StatCard 
                    icon={<AlertCircle className="text-rose-600" />}
                    label="Alertas"
                    value={stats?.discipline?.critical_high || 0}
                    trend="5 pendientes"
                    color="rose"
                />
                <StatCard 
                    icon={<TrendingUp className="text-indigo-600" />}
                    label="Retención"
                    value={`${stats?.attendance?.present ? Math.round((stats.attendance.present / (stats.attendance.present + stats.attendance.absent)) * 100) : 0}%`}
                    trend="Puntualidad: 94%"
                    color="indigo"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
                {/* Ranking Card */}
                <div className="lg:col-span-2 bg-white rounded-2xl lg:rounded-[2rem] shadow-sm border border-slate-100 overflow-hidden flex flex-col transition-all hover:shadow-lg">
                    <div className="p-6 lg:p-8 border-b border-slate-50 flex items-center justify-between bg-gradient-to-r from-white to-slate-50/50">
                        <div>
                            <h2 className="text-lg lg:text-xl font-bold text-slate-800 flex items-center gap-2 lg:gap-3">
                                <Trophy size={20} className="lg:w-6 lg:h-6 text-amber-500 drop-shadow-sm" /> 
                                Cuadro de Honor
                            </h2>
                            <p className="text-slate-400 text-[10px] lg:text-sm mt-1">Mejores promedios</p>
                        </div>
                        <span className="px-3 lg:px-4 py-1.5 bg-amber-50 text-amber-700 rounded-full text-[10px] font-bold uppercase tracking-widest border border-amber-100">
                            Meritocracia
                        </span>
                    </div>
                    <div className="flex-grow overflow-x-auto">
                        <table className="w-full text-left">
                            <thead className="sticky top-0 bg-white/80 backdrop-blur-md z-10">
                                <tr className="text-slate-400 text-[10px] uppercase font-bold tracking-[0.1em]">
                                    <th className="px-8 py-4">#</th>
                                    <th className="px-8 py-4">Estudiante</th>
                                    <th className="px-8 py-4">Curso</th>
                                    <th className="px-8 py-4 text-right">Excelencia</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {rankings.length > 0 ? rankings.map((student, idx) => (
                                    <tr key={idx} className="group hover:bg-slate-50/80 transition-all">
                                        <td className="px-8 py-5">
                                            <span className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-black shadow-sm ${
                                                idx === 0 ? 'bg-gradient-to-br from-amber-400 to-amber-600 text-white' :
                                                idx === 1 ? 'bg-gradient-to-br from-slate-300 to-slate-500 text-white' :
                                                idx === 2 ? 'bg-gradient-to-br from-orange-400 to-orange-600 text-white' :
                                                'bg-slate-100 text-slate-400'
                                            }`}>
                                                {idx + 1}
                                            </span>
                                        </td>
                                        <td className="px-8 py-5">
                                            <div className="font-bold text-slate-800 group-hover:text-primary-700 transition-colors uppercase tracking-tight">{student.student_name}</div>
                                            <div className="text-[10px] font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded inline-block mt-1">{student.level}</div>
                                        </td>
                                        <td className="px-8 py-5">
                                            <div className="text-sm font-semibold text-slate-600">{student.course_name}</div>
                                        </td>
                                        <td className="px-8 py-5 text-right">
                                            <div className="inline-flex items-center gap-1.5 bg-primary-50 px-3 py-1 rounded-xl border border-primary-100">
                                                <TrendingUp size={14} className="text-primary-600" />
                                                <span className="text-sm font-black text-primary-700">
                                                    {student.average.toFixed(2)}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                )) : (
                                    <tr>
                                        <td colSpan="4" className="px-8 py-20 text-center">
                                            <div className="flex flex-col items-center gap-3">
                                                <Trophy size={48} className="text-slate-200" />
                                                <p className="text-slate-400 font-medium">No hay registros para este filtro</p>
                                            </div>
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Demographics Card */}
                <div className="bg-white rounded-[2rem] shadow-sm border border-slate-100 p-8 flex flex-col transition-all hover:shadow-lg">
                    <div className="flex items-center justify-between mb-8">
                        <h2 className="text-xl font-bold text-slate-800 flex items-center gap-3">
                            <PieChartIcon size={26} className="text-primary-500" /> 
                            Composición
                        </h2>
                        <span className="w-10 h-10 rounded-2xl bg-primary-50 text-primary-600 flex items-center justify-center">
                            <TrendingUp size={20} />
                        </span>
                    </div>
                    
                    <div className="flex-grow flex flex-col items-center justify-center" id="demographics-chart">
                        <div className="h-64 w-full relative">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={studentDemographics}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={70}
                                        outerRadius={95}
                                        paddingAngle={10}
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {studentDemographics.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip 
                                        contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center">
                                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Global</p>
                                <p className="text-2xl font-black text-slate-800 tracking-tighter">
                                    {stats?.demographics?.students?.total || 0}
                                </p>
                            </div>
                        </div>

                        <div className="w-full grid grid-cols-2 gap-4 mt-8">
                            <LegendItem icon="♂" label="Hombres" value={stats?.demographics?.students?.M || 0} color="#3B82F6" />
                            <LegendItem icon="♀" label="Mujeres" value={stats?.demographics?.students?.F || 0} color="#8B5CF6" />
                        </div>
                    </div>

                    <div className="mt-8 pt-8 border-t border-slate-50 grid grid-cols-2 gap-6">
                        <div className="flex flex-col">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Docentes M</span>
                            <span className="text-lg font-black text-slate-800">{stats?.demographics?.teachers?.M || 0}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Docentes F</span>
                            <span className="text-lg font-black text-slate-800">{stats?.demographics?.teachers?.F || 0}</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Visual Analysis 1: Finance */}
                <div className="bg-white rounded-[2rem] shadow-sm border border-slate-100 p-8 transition-all hover:shadow-lg">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-3">
                                <DollarSign size={26} className="text-emerald-500" /> 
                                Monitor Financiero
                            </h2>
                            <p className="text-slate-400 text-sm mt-1">Saldos pendientes por año/curso</p>
                        </div>
                        <div className="px-4 py-2 bg-emerald-50 text-emerald-700 rounded-2xl font-black text-sm border border-emerald-100">
                            ${financials?.global_total?.toLocaleString()}
                        </div>
                    </div>
                    <div className="h-80 w-full mt-4" id="financial-chart">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={financials?.by_course || []} margin={{ bottom: 40 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis 
                                    dataKey="course_name" 
                                    fontSize={10} 
                                    fontWeight="bold"
                                    axisLine={false}
                                    tickLine={false}
                                    interval={0}
                                    angle={-45}
                                    textAnchor="end"
                                    tick={{ fill: '#94a3b8' }}
                                />
                                <YAxis 
                                    fontSize={10} 
                                    fontWeight="bold"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#94a3b8' }}
                                    tickFormatter={(v) => `$${v}`}
                                />
                                <Tooltip 
                                    cursor={{fill: '#f8fafc'}}
                                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                />
                                <Bar dataKey="pending_amount" name="Pendiente ($)" fill="#10B981" radius={[8, 8, 8, 8]} barSize={24} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Visual Analysis 2: Discipline */}
                <div className="bg-white rounded-[2rem] shadow-sm border border-slate-100 p-8 transition-all hover:shadow-lg">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-3">
                                <AlertCircle size={26} className="text-rose-500" /> 
                                Radar de Convivencia
                            </h2>
                            <p className="text-slate-400 text-sm mt-1">Frecuencia de observaciones registradas</p>
                        </div>
                    </div>
                    <div className="h-80 w-full mt-4" id="discipline-radar">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={disciplineData} layout="vertical" margin={{ left: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                                <XAxis type="number" hide />
                                <YAxis 
                                    dataKey="name" 
                                    type="category" 
                                    fontSize={12} 
                                    fontWeight="bold"
                                    axisLine={false}
                                    tickLine={false}
                                    tick={{ fill: '#64748b' }}
                                />
                                <Tooltip 
                                    cursor={{fill: '#f8fafc', radius: 8}}
                                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                />
                                <Bar dataKey="value" name="Registros" fill="#F43F5E" radius={[0, 8, 8, 0]} barSize={24} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="mt-6 flex flex-wrap gap-4">
                         <div className="flex items-center gap-2 bg-rose-50 px-3 py-1.5 rounded-xl border border-rose-100">
                            <span className="w-2 h-2 rounded-full bg-rose-600 animate-pulse"></span>
                            <span className="text-xs font-bold text-rose-700">{stats?.discipline?.critical_high} Casos Críticos (Acción Urgente)</span>
                         </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

const StatCard = ({ icon, label, value, trend, color }) => {
    const colorClasses = {
        primary: "bg-primary-50 text-primary-600",
        emerald: "bg-emerald-50 text-emerald-600",
        rose: "bg-rose-50 text-rose-600",
        indigo: "bg-indigo-50 text-indigo-600"
    };

    return (
        <div className="bg-white p-6 lg:p-8 rounded-2xl lg:rounded-[2rem] shadow-sm border border-slate-100 flex flex-col gap-4 transition-all hover:-translate-y-1 hover:shadow-xl group">
            <div className={`w-12 h-12 lg:w-14 lg:h-14 rounded-xl lg:rounded-2xl flex items-center justify-center transition-all group-hover:scale-110 shadow-sm ${colorClasses[color]}`}>
                {React.cloneElement(icon, { size: 20 })}
            </div>
            <div>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-[0.15em] mb-1">{label}</p>
                <h3 className="text-xl lg:text-3xl font-black text-slate-800 tracking-tighter transition-all group-hover:text-primary-600">{value}</h3>
                <p className="text-[10px] font-bold text-slate-400 mt-2 flex items-center gap-1.5 uppercase tracking-wide">
                    <CheckCircle2 size={10} className="text-slate-300" /> {trend}
                </p>
            </div>
        </div>
    );
};

const LegendItem = ({ icon, label, value, color }) => (
    <div className="flex items-center justify-between p-2 lg:p-3 bg-slate-50/50 rounded-xl lg:rounded-2xl border border-slate-100 flex-grow hover:bg-slate-50 transition-colors">
        <div className="flex items-center gap-2">
            <span className="text-base lg:text-lg font-bold" style={{ color }}>{icon}</span>
            <span className="text-[10px] lg:text-[11px] font-extrabold text-slate-600 uppercase tracking-tight">{label}</span>
        </div>
        <span className="text-xs lg:text-sm font-black text-slate-800">{value}</span>
    </div>
);

export default GlobalReportsPage;
