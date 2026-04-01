import React, { useState, useEffect } from 'react';
import { 
    BarChart, PieChart, Activity, AlertCircle, FileText, Download, 
    Calendar, Users, Filter, ArrowUpRight, ArrowDownRight, Printer 
} from 'lucide-react';
import academicService from '../../services/academicService';
import healthService from '../../services/healthService';
import { toast } from 'react-hot-toast';

const BehaviorReportsPage = () => {
    const [academicYears, setAcademicYears] = useState([]);
    const [selectedYear, setSelectedYear] = useState('');
    const [courses, setCourses] = useState([]);
    const [selectedCourse, setSelectedCourse] = useState('');
    
    const [stats, setStats] = useState(null);
    const [behaviorList, setBehaviorList] = useState([]);
    const [categoryData, setCategoryData] = useState([]);
    const [monthlyData, setMonthlyData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if (selectedYear) {
            loadStats();
        }
    }, [selectedYear, selectedCourse]);

    const loadInitialData = async () => {
        try {
            const [yearsData, coursesData] = await Promise.all([
                academicService.getAcademicYears(),
                academicService.getCourses()
            ]);
            setAcademicYears(yearsData);
            setCourses(coursesData);
            
            const activeYear = yearsData.find(y => y.is_active);
            if (activeYear) setSelectedYear(activeYear.id);
            else if (yearsData.length > 0) setSelectedYear(yearsData[0].id);
            
        } catch (error) {
            console.error("Error loading initial data", error);
            toast.error("Error al cargar configuraciones");
        }
    };

    const loadStats = async () => {
        setLoading(true);
        try {
            // Cargar métricas bases
            const data = await healthService.getDashboardStats(selectedYear);
            setStats(data);

            // Cargar lista completa de registros
            const filters = { academic_year: selectedYear };
            if (selectedCourse) filters.course = selectedCourse;
            const res = await healthService.getBehaviorRecords(filters);
            const records = res.results || res;

            // Ordenar por fecha desc
            records.sort((a,b) => new Date(b.date) - new Date(a.date));
            setBehaviorList(records);

            // Computar categorías dinámicas
            let acc = { 'ACADEMIC': 0, 'POSITIVE': 0, 'NEGATIVE_MILD': 0, 'NEGATIVE_SEVERE': 0 };
            records.forEach(r => {
                const type = r.record_type;
                if(acc[type] !== undefined) acc[type]++;
                else acc['OTHER'] = (acc['OTHER']||0) + 1;
            });

            const total = records.length || 1;
            const computedCategories = [
                { name: 'Académico', value: Math.round((acc['ACADEMIC'] / total) * 100), count: acc['ACADEMIC'], color: 'bg-blue-500' },
                { name: 'Positivo', value: Math.round((acc['POSITIVE'] / total) * 100), count: acc['POSITIVE'], color: 'bg-emerald-500' },
                { name: 'Negativo (Leve)', value: Math.round((acc['NEGATIVE_MILD'] / total) * 100), count: acc['NEGATIVE_MILD'], color: 'bg-amber-500' },
                { name: 'Negativo (Grave)', value: Math.round((acc['NEGATIVE_SEVERE'] / total) * 100), count: acc['NEGATIVE_SEVERE'], color: 'bg-red-500' }
            ].filter(c => c.count > 0);
            
            // Si no hay datos, mostrar algo base
            if (computedCategories.length === 0) {
                 computedCategories.push({ name: 'Sin datos', value: 100, count: 0, color: 'bg-slate-200' });
            }
            setCategoryData(computedCategories);

            // Computar meses dinámicos
            let mesesMap = {};
            records.forEach(r => {
                if(!r.date) return;
                const m = r.date.substring(0, 7); // YYYY-MM
                mesesMap[m] = (mesesMap[m] || 0) + 1;
            });
            const mesesList = Object.keys(mesesMap).sort();
            const maxMonth = Math.max(...Object.values(mesesMap), 1);
            setMonthlyData(mesesList.slice(-10).map(m => ({
                month: m.split('-')[1], // solo mes num
                count: mesesMap[m],
                height: Math.round((mesesMap[m] / maxMonth) * 100)
            })));

        } catch (error) {
            console.error("Error loading stats", error);
            toast.error("Error al cargar datos");
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadCSV = () => {
        if (behaviorList.length === 0) {
            toast.error("No hay datos para exportar");
            return;
        }
        const headers = ["ID", "Fecha", "Estudiante", "Curso", "Materia", "Tipo_Registro", "Descripcion"];
        const rows = behaviorList.map(r => [
            r.id,
            r.date,
            `"${(r.student_name || 'Desconocido').replace(/"/g, '""')}"`,
            `"${(r.course_name || 'General').replace(/"/g, '""')}"`,
            `"${(r.subject_name || '-').replace(/"/g, '""')}"`,
            r.record_type,
            `"${(r.description || '').replace(/"/g, '""').replace(/\n/g, ' ')}"`
        ]);

        const csvContent = "data:text/csv;charset=utf-8,﻿" + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `reporte_conducta_${selectedYear}_${selectedCourse || 'todos'}.csv`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        toast.success("Excel descargado con éxito");
    };

    const handlePrint = () => {
        window.print();
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto print:max-w-full print:m-0 print:p-4">
            {/* CSS inyectado estrictamente para forzar limpieza de sidebar/header de Turbo en impresion */}
            <style dangerouslySetInnerHTML={{__html: `
                @media print {
                    nav, aside, header { display: none !important; }
                    .print\\:hidden { display: none !important; }
                    main { padding: 0 !important; margin: 0 !important; width: 100% !important; overflow: visible !important; }
                    body { background: white !important; }
                }
            `}} />

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 print:shadow-none print:border-none print:p-0">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight flex items-center gap-3">
                        <BarChart className="text-indigo-600 print:hidden" size={32} /> 
                        Reportes Conductuales
                    </h1>
                    <p className="text-slate-500 mt-1 print:text-black">Análisis integral del comportamiento y bienestar estudiantil.</p>
                </div>
                <div className="flex gap-3 print:hidden">
                    <button onClick={handlePrint} className="btn-secondary flex items-center gap-2">
                        <Printer size={18} /> Imprimir
                    </button>
                    <button onClick={handleDownloadCSV} className="btn-primary flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white shadow-md">
                        <Download size={18} /> Exportar CSV (Excel)
                    </button>
                    <button onClick={handlePrint} className="btn-primary flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white shadow-md">
                        <FileText size={18} /> Exp. PDF
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-wrap gap-4 items-end print:hidden">
                <div className="flex-1 min-w-[200px]">
                    <label className="label-modern">Año Lectivo</label>
                    <select 
                        className="input-modern w-full"
                        value={selectedYear}
                        onChange={(e) => setSelectedYear(e.target.value)}
                    >
                        {academicYears.map(y => (
                            <option key={y.id} value={y.id}>{y.name}</option>
                        ))}
                    </select>
                </div>
                <div className="flex-1 min-w-[200px]">
                    <label className="label-modern">Curso (Opcional)</label>
                    <select 
                        className="input-modern w-full"
                        value={selectedCourse}
                        onChange={(e) => setSelectedCourse(e.target.value)}
                    >
                        <option value="">Todos los cursos</option>
                        {courses.map(c => (
                            <option key={c.id} value={c.id}>{c.name} {c.parallel}</option>
                        ))}
                    </select>
                </div>
                <button onClick={loadStats} className="btn-secondary flex items-center gap-2 mb-0.5 shadow-sm">
                    <Filter size={18} /> Filtrar
                </button>
            </div>

            {loading ? (
                <div className="h-64 flex items-center justify-center bg-white rounded-2xl shadow-sm border border-slate-100 print:hidden">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                </div>
            ) : (
                <>
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 print:grid-cols-4 print:gap-2 print:text-sm">
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 border-l-4 border-l-indigo-500 print:p-4 print:shadow-none">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-slate-500 text-sm font-medium mb-1 print:text-black">Total Registros Formativos</p>
                                    <h3 className="text-3xl font-bold text-slate-800">{behaviorList.length || 0}</h3>
                                </div>
                                <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl print:hidden">
                                    <Activity size={24} />
                                </div>
                            </div>
                        </div>
                        
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 border-l-4 border-l-red-500 print:p-4 print:shadow-none">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-slate-500 text-sm font-medium mb-1 print:text-black">Faltas Graves (Reporte D.E.C.E)</p>
                                    <h3 className="text-3xl font-bold text-slate-800">{categoryData.find(c => c.name.includes('Grave'))?.count || 0}</h3>
                                </div>
                                <div className="p-3 bg-red-50 text-red-600 rounded-xl print:hidden">
                                    <AlertCircle size={24} />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 border-l-4 border-l-amber-500 print:p-4 print:shadow-none">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-slate-500 text-sm font-medium mb-1 print:text-black">Faltas Leves (Moderadas)</p>
                                    <h3 className="text-3xl font-bold text-slate-800">{categoryData.find(c => c.name.includes('Leve'))?.count || 0}</h3>
                                </div>
                                <div className="p-3 bg-amber-50 text-amber-600 rounded-xl print:hidden">
                                    <Users size={24} />
                                </div>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 border-l-4 border-l-emerald-500 print:p-4 print:shadow-none">
                            <div className="flex justify-between items-start">
                                <div>
                                    <p className="text-slate-500 text-sm font-medium mb-1 print:text-black">Reportes Positivos</p>
                                    <h3 className="text-3xl font-bold text-slate-800">{categoryData.find(c => c.name.includes('Positivo'))?.count || 0}</h3>
                                </div>
                                <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl print:hidden">
                                    <CheckCircle size={24} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Charts & Detail Area */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 print:grid-cols-3 print:gap-4 print:page-break-inside-avoid">
                        {/* Mock Chart Area, ahora dinámico con monthlyData */}
                        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-100 print:shadow-none">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-lg font-bold text-slate-800">Evolución de Casos (Últimos meses)</h3>
                                <button onClick={handleDownloadCSV} className="text-indigo-600 text-sm font-medium flex items-center gap-1 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors print:hidden">
                                    <Download size={14} /> CSV
                                </button>
                            </div>
                            <div className="h-64 flex items-end justify-between gap-2 px-4 border-b border-slate-200 pb-2">
                                {monthlyData.length > 0 ? monthlyData.map((d, i) => (
                                    <div key={i} className="w-1/12 bg-indigo-100 rounded-t-sm relative group print:bg-slate-300">
                                        <div 
                                            className="absolute bottom-0 w-full bg-indigo-500 rounded-t-md transition-all duration-500 group-hover:bg-indigo-600 print:bg-slate-800"
                                            style={{ height: `${d.height}%` }}
                                        ></div>
                                        <div className="absolute -bottom-6 w-full text-center text-xs text-slate-400 font-medium">
                                            {d.month}
                                        </div>
                                        <div className="absolute -top-6 w-full text-center text-xs text-indigo-700 font-bold opacity-0 group-hover:opacity-100 transition-opacity">
                                            {d.count}
                                        </div>
                                    </div>
                                )) : <div className="flex-1 flex items-center justify-center text-slate-400">Faltan datos en este ciclo</div>}
                            </div>
                        </div>

                        {/* Distribution Area */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 print:shadow-none">
                            <h3 className="text-lg font-bold text-slate-800 mb-6">Distribución por Categoría</h3>
                            
                            <div className="space-y-6">
                                {categoryData.map(cat => (
                                    <div key={cat.name}>
                                        <div className="flex justify-between text-sm font-medium mb-2">
                                            <span className="text-slate-700 print:text-black">{cat.name} ({cat.count})</span>
                                            <span className="text-slate-500 print:text-black">{cat.value}%</span>
                                        </div>
                                        <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden print:border print:border-black">
                                            <div className={`h-full ${cat.color} rounded-full print:bg-slate-800 print:rounded-none`} style={{ width: `${cat.value}%` }}></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Reporte de Datos Listados */}
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mt-6 print:shadow-none print:mt-10 print:w-full">
                        <h3 className="text-lg font-bold text-slate-800 mb-6">Últimos Casos Registrados (Resumen)</h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-slate-200">
                                        <th className="py-3 px-4 text-sm font-semibold text-slate-500 uppercase">Fecha</th>
                                        <th className="py-3 px-4 text-sm font-semibold text-slate-500 uppercase">Estudiante</th>
                                        <th className="py-3 px-4 text-sm font-semibold text-slate-500 uppercase">Materia</th>
                                        <th className="py-3 px-4 text-sm font-semibold text-slate-500 uppercase">Tipo</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {behaviorList.slice(0, 8).map(r => (
                                        <tr key={r.id} className="border-b border-slate-100 hover:bg-slate-50 print:border-slate-300">
                                            <td className="py-3 px-4 text-sm font-medium text-slate-700">{r.date}</td>
                                            <td className="py-3 px-4 text-sm text-slate-600">{r.student_name || 'Alum.'+r.student} <span className="text-xs text-slate-400 block">{r.course_name}</span></td>
                                            <td className="py-3 px-4 text-sm text-slate-600">{r.subject_name || '-'}</td>
                                            <td className="py-3 px-4 text-sm">
                                                <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                                    r.record_type.includes('POSITIVE') ? 'bg-emerald-100 text-emerald-700' :
                                                    r.record_type.includes('SEVERE') ? 'bg-red-100 text-red-700' :
                                                    r.record_type.includes('MILD') ? 'bg-amber-100 text-amber-700' :
                                                    'bg-blue-100 text-blue-700'
                                                }`}>
                                                    {r.record_type}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                    {behaviorList.length === 0 && (
                                        <tr><td colSpan="4" className="py-8 text-center text-slate-500">No hay registros para este curso en este año lectivo.</td></tr>
                                    )}
                                </tbody>
                            </table>
                            {behaviorList.length > 8 && (
                                <div className="text-center mt-4">
                                    <button onClick={handleDownloadCSV} className="text-indigo-600 font-medium text-sm hover:underline print:hidden">Descargar Excel para ver los {behaviorList.length} consolidados completos...</button>
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

const CheckCircle = ({ size, className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
);

export default BehaviorReportsPage;
