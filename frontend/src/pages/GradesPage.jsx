import React, { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import academicService from '../services/academicService';
import healthService from '../services/healthService';
import { Plus, Filter, Save, X, Settings, Calculator, Download, MessageSquare, BarChart, FileText, CheckCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import BehaviorQuickModal from '../components/BehaviorQuickModal';

const GradesPage = () => {
    // Selection State
    const [selectedCourse, setSelectedCourse] = useState('');
    const [selectedSubject, setSelectedSubject] = useState('');
    const [selectedTrimester, setSelectedTrimester] = useState('1');

    // Data State
    const [courses, setCourses] = useState([]);
    const [subjects, setSubjects] = useState([]); 
    const [students, setStudents] = useState([]); 
    const [categories, setCategories] = useState([]);
    const [grades, setGrades] = useState([]); 

    // UI State
    const [loading, setLoading] = useState(true);
    const [loadingGrid, setLoadingGrid] = useState(false);
    const [showCategoryModal, setShowCategoryModal] = useState(false);
    const [showBehaviorModal, setShowBehaviorModal] = useState(false);
    const [todayBehaviors, setTodayBehaviors] = useState({});
    const [selectedBehaviorStudent, setSelectedBehaviorStudent] = useState(null);

    // Category Form
    const [categoryForm, setCategoryForm] = useState({ id: null, subject: '', name: '', weight: '', parent_category: '' });

    useEffect(() => {
        loadInitialData();
    }, []);

    useEffect(() => {
        if (selectedCourse && selectedSubject && selectedTrimester) {
            loadGradebookData();
        } else {
            setStudents([]);
            setCategories([]);
            setGrades([]);
        }
    }, [selectedCourse, selectedSubject, selectedTrimester]);

    const loadInitialData = async () => {
        try {
            const [coursesData, subjectsData] = await Promise.all([
                academicService.getCourses(),
                academicService.getSubjects()
            ]);
            setCourses(coursesData);
            setSubjects(subjectsData);
            
            if (coursesData && coursesData.length > 0 && !selectedCourse) {
                const firstCourseId = coursesData[0].id.toString();
                setSelectedCourse(firstCourseId);
                const firstSubj = subjectsData.find(s => s.course === parseInt(firstCourseId));
                if (firstSubj) setSelectedSubject(firstSubj.id.toString());
            }
        } catch (error) {
            console.error("Error loading initial data", error);
        } finally {
            setLoading(false);
        }
    };

    const loadGradebookData = async () => {
        setLoadingGrid(true);
        try {
            const [courseEnrollments, categoriesData, relevantGrades, behaviorRes] = await Promise.all([
                academicService.getEnrollments(selectedCourse),
                selectedTrimester === 'summary' 
                    ? academicService.getEvaluationCategories(selectedSubject)
                    : academicService.getEvaluationCategories(selectedSubject, selectedTrimester),
                academicService.getGrades(selectedSubject, null, selectedCourse),
                healthService.getBehaviorRecords({ course: selectedCourse, date: new Date().toISOString().split('T')[0] })
            ]);

            const bMap = {};
            const behaviorRecords = behaviorRes.results || behaviorRes;
            behaviorRecords.forEach(r => { bMap[r.student] = r; });
            
            setStudents(courseEnrollments);
            setCategories(categoriesData);
            setGrades(relevantGrades);
            setTodayBehaviors(bMap);
        } catch (error) {
            console.error("Error loading gradebook", error);
            toast.error("Error al cargar datos");
        } finally {
            setLoadingGrid(false);
        }
    };

    const openBehaviorModal = (studentId, studentName) => {
        const existing = todayBehaviors[studentId];
        setSelectedBehaviorStudent({ id: studentId, fullName: studentName, existingRecord: existing });
        setShowBehaviorModal(true);
    };

    const saveGrade = async (enrollmentId, categoryId, value) => {
        if (value === '' || value === undefined || value === null) return;
        try {
            // Normalize score value (handle comma and ensure number)
            const numericScore = parseFloat(String(value).replace(',', '.'));
            if (isNaN(numericScore)) {
                toast.error("Formato de nota inválido");
                return;
            }

            // Use == for flexible ID comparison (string vs int)
            const existingGrade = grades.find(g => g.enrollment == enrollmentId && g.category == categoryId);
            
            const payload = {
                enrollment: parseInt(enrollmentId),
                subject: parseInt(selectedSubject),
                category: parseInt(categoryId),
                score: numericScore,
                date: new Date().toISOString().split('T')[0]
            };

            if (existingGrade) {
                if (existingGrade.score == numericScore) return;
                // Use patchGrade for safer partial updates
                const updated = await academicService.patchGrade(existingGrade.id, { score: numericScore });
                setGrades(grades.map(g => g.id === existingGrade.id ? updated : g));
            } else {
                const created = await academicService.createGrade(payload);
                setGrades([...grades, created]);
            }
        } catch (error) {
            console.error("Failed to save grade", error);
            const errorDetail = error.response?.data ? JSON.stringify(error.response.data) : error.message;
            toast.error(`Error al guardar nota: ${errorDetail}`);
        }
    };

    const getCategoryScore = (enrollmentId, category) => {
        if (category.subcategories && category.subcategories.length > 0) {
            let total = 0;
            let hasAtLeastOne = false;
            category.subcategories.forEach(sub => {
                const subScore = getCategoryScore(enrollmentId, sub);
                if (subScore !== null) {
                    const sVal = parseFloat(subScore); if(!isNaN(sVal)) total += (sVal * parseFloat(sub.weight)) / 100;
                    hasAtLeastOne = true;
                }
            });
            return hasAtLeastOne ? total.toFixed(2) : null;
        }
        const grade = grades.find(g => g.enrollment === enrollmentId && g.category === category.id);
        return grade ? grade.score : null;
    };

    const calculateFinalScore = (enrollmentId) => {
        let totalWeightedScore = 0;
        const mainCats = categories.filter(c => !c.parent_category);
        mainCats.forEach(cat => {
            const score = getCategoryScore(enrollmentId, cat);
            if (score !== null) {
                totalWeightedScore += (parseFloat(score) * parseFloat(cat.weight)) / 100;
            }
        });
        return totalWeightedScore.toFixed(2);
    };

    const calculateTrimesterAverage = (enrollmentId, trimester) => {
        const trimCategories = categories.filter(c => c.trimester === parseInt(trimester) && !c.parent_category);
        if (trimCategories.length === 0) return 0;
        let totalWeightedScore = 0;
        trimCategories.forEach(cat => {
            const score = getCategoryScore(enrollmentId, cat);
            if (score !== null) {
                totalWeightedScore += (parseFloat(score) * parseFloat(cat.weight)) / 100;
            }
        });
        return parseFloat(totalWeightedScore.toFixed(2));
    };

    const calculateGlobalAverage = (enrollmentId) => {
        const t1 = calculateTrimesterAverage(enrollmentId, 1);
        const t2 = calculateTrimesterAverage(enrollmentId, 2);
        const t3 = calculateTrimesterAverage(enrollmentId, 3);
        const final = (t1 + t2 + t3) / 3;
        return { t1, t2, t3, final: final.toFixed(2) };
    };

    const filteredSubjects = useMemo(() => {
        if (!selectedCourse) return [];
        return subjects.filter(s => s.course === parseInt(selectedCourse));
    }, [selectedCourse, subjects]);
    
    const selectedCourseData = useMemo(() => courses.find(c => c.id === parseInt(selectedCourse)), [selectedCourse, courses]);
    const selectedSubjectData = useMemo(() => subjects.find(s => s.id === parseInt(selectedSubject)), [selectedSubject, subjects]);

    const effectiveGradingType = useMemo(() => {
        if (!selectedSubjectData || !selectedCourseData) return 'QUANTITATIVE';
        if (selectedSubjectData.grading_type && selectedSubjectData.grading_type !== 'INHERIT') return selectedSubjectData.grading_type;
        return selectedCourseData.grading_type || 'QUANTITATIVE';
    }, [selectedSubjectData, selectedCourseData]);

    const isQualitative = effectiveGradingType !== 'QUANTITATIVE';

    const getQualitativeGrade = (score, scaleType = 'QUALITATIVE_DESTREZAS') => {
        if (score === null || score === undefined || score === '' || isNaN(score)) return '-';
        const num = parseFloat(score);
        if (scaleType === 'QUALITATIVE_PROYECTOS') {
            if (num >= 9) return 'EX'; if (num >= 7) return 'MB'; if (num >= 5) return 'B'; return 'R';
        } else if (scaleType === 'QUALITATIVE_COMPORTAMIENTO') {
            if (num >= 9) return 'A'; if (num >= 7) return 'B'; if (num >= 5) return 'C'; if (num >= 4) return 'D'; return 'E';
        } else {
            if (num >= 9) return 'DA'; if (num >= 7) return 'EP'; if (num >= 5) return 'I'; return 'NE';
        }
    };

    const handleCategorySubmit = async (e) => {
        e.preventDefault();
        try {
            await academicService.createEvaluationCategory({
                ...categoryForm,
                subject: selectedSubject,
                trimester: selectedTrimester,
                parent_category: categoryForm.parent_category || null
            });
            toast.success('Categoría creada');
            loadGradebookData();
            setCategoryForm({ ...categoryForm, name: '', weight: '', parent_category: '' });
        } catch (error) { toast.error('Error al crear categoría'); }
    };

    const handleCategoryDelete = async (id) => {
        if (!window.confirm("¿Eliminar categoría? Se borrarán los sub-aportes y notas asociadas.")) return;
        try {
            await academicService.deleteEvaluationCategory(id);
            loadGradebookData();
        } catch (error) { toast.error("Error al eliminar"); }
    };

    const renderCategoryHeaders = () => {
        if (selectedTrimester === 'summary') {
            return (
                <>
                    <th className="p-4 border-b border-slate-200 text-center min-w-[100px]">Trimestre 1</th>
                    <th className="p-4 border-b border-slate-200 text-center min-w-[100px]">Trimestre 2</th>
                    <th className="p-4 border-b border-slate-200 text-center min-w-[100px]">Trimestre 3</th>
                    <th className="p-4 border-b border-l border-slate-200 text-center min-w-[100px] bg-indigo-50 font-bold text-indigo-700">Nota Final</th>
                </>
            );
        }

        const mainCats = categories.filter(c => !c.parent_category);
        return (
            <>
                {mainCats.map(cat => (
                    <React.Fragment key={cat.id}>
                        {cat.subcategories && cat.subcategories.length > 0 ? (
                            cat.subcategories.map(sub => (
                                <th key={sub.id} className="p-4 border-b border-slate-200 text-center min-w-[100px]">
                                    <div className="flex flex-col">
                                        <span className="text-[9px] text-slate-400 uppercase">{cat.name}</span>
                                        <span className="font-semibold">{sub.name}</span>
                                        <span className="text-[9px] text-indigo-500">{sub.weight}% (de {cat.name})</span>
                                    </div>
                                </th>
                            ))
                        ) : (
                            <th className="p-4 border-b border-slate-200 text-center min-w-[120px]">
                                <div className="flex flex-col">
                                    <span className="font-bold">{cat.name}</span>
                                    <span className="text-[10px] text-indigo-600 bg-indigo-50 px-1 rounded self-center mt-1">{cat.weight}%</span>
                                </div>
                            </th>
                        )}
                        {cat.subcategories && cat.subcategories.length > 0 && (
                            <th className="p-4 border-b border-l border-slate-200 text-center min-w-[100px] bg-amber-50/50 font-bold text-amber-700 border-r">
                                Prom. {cat.name} ({cat.weight}%)
                            </th>
                        )}
                    </React.Fragment>
                ))}
                <th className="p-4 border-b border-l border-slate-200 text-center min-w-[100px] bg-slate-50 font-bold text-slate-700">Promedio Final</th>
            </>
        );
    };

    if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Cargando módulo de calificaciones...</div>;

    return (
        <div className="space-y-6">
            <Toaster />
            <div className="flex flex-col md:flex-row justify-between items-start gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight italic">Libro de Calificaciones</h1>
                    <p className="text-slate-500 mt-1">Gestión automática de promedios y aportes jerárquicos.</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto">
                    <select className="input-modern min-w-[200px]" value={selectedCourse} onChange={e => { setSelectedCourse(e.target.value); setSelectedSubject(''); }}>
                        <option value="">Seleccione Curso...</option>
                        {courses.map(c => <option key={c.id} value={c.id}>{c.name} {c.parallel}</option>)}
                    </select>

                    <select className="input-modern min-w-[200px]" value={selectedSubject} onChange={e => setSelectedSubject(e.target.value)} disabled={!selectedCourse}>
                        <option value="">Seleccione Materia...</option>
                        {filteredSubjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>

                    <select className="input-modern min-w-[150px]" value={selectedTrimester} onChange={e => setSelectedTrimester(e.target.value)}>
                        <option value="1">Trimestre 1</option>
                        <option value="2">Trimestre 2</option>
                        <option value="3">Trimestre 3</option>
                        <option value="summary">Resumen Final</option>
                    </select>

                    {selectedSubject && (
                        <button onClick={() => setShowCategoryModal(true)} className="btn-secondary flex items-center justify-center gap-2">
                            <Settings size={18} /> Configurar Aportes
                        </button>
                    )}
                </div>
            </div>

            {!selectedCourse || !selectedSubject ? (
                <div className="text-center py-20 bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200">
                    <Filter className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <h3 className="text-lg font-medium text-slate-600">Seleccione curso y materia para comenzar</h3>
                </div>
            ) : categories.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 shadow-sm">
                    <h3 className="text-xl font-bold text-slate-800 mb-2">No hay aportes definidos</h3>
                    <button onClick={() => setShowCategoryModal(true)} className="btn-primary inline-flex items-center gap-2 mt-4"><Plus size={20} /> Crear Aportes</button>
                </div>
            ) : (
                <div className="card-premium overflow-hidden">
                    {loadingGrid ? (
                        <div className="p-12 text-center text-slate-500">Cargando planilla...</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead className="bg-slate-50 text-xs uppercase text-slate-500 font-semibold tracking-wider">
                                    <tr>
                                        <th className="p-4 border-b border-r border-slate-200 min-w-[250px] sticky left-0 bg-slate-50 z-10">Estudiante / Observaciones</th>
                                        {renderCategoryHeaders()}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {students.map(studentEnrollment => {
                                        const globalData = selectedTrimester === 'summary' ? calculateGlobalAverage(studentEnrollment.id) : null;
                                        const studentName = studentEnrollment.student_detail ? `${studentEnrollment.student_detail.last_name} ${studentEnrollment.student_detail.first_name}` : "Estudiante";
                                        
                                        return (
                                            <tr key={studentEnrollment.id} className="hover:bg-slate-50/50 transition-colors group">
                                                <td className="p-4 border-r border-slate-100 font-medium text-slate-700 sticky left-0 bg-white group-hover:bg-slate-50/50 z-10 flex justify-between items-center">
                                                    <span>{studentName}</span>
                                                    <button 
                                                        onClick={() => openBehaviorModal(studentEnrollment.student, studentName)}
                                                        className={`p-1 rounded-full transition-colors ${todayBehaviors[studentEnrollment.student] ? 'text-emerald-500 bg-emerald-50' : 'text-slate-400 hover:text-indigo-500 bg-slate-50 hover:bg-indigo-50'}`}
                                                        title="Conducta / Detalle"
                                                    >
                                                        {todayBehaviors[studentEnrollment.student] ? <CheckCircle size={14} /> : <MessageSquare size={14} />}
                                                    </button>
                                                </td>
                                                {selectedTrimester === 'summary' ? (
                                                    <>
                                                        <td className="p-4 text-center border-r border-slate-100">{isQualitative ? getQualitativeGrade(globalData.t1, effectiveGradingType) : globalData.t1}</td>
                                                        <td className="p-4 text-center border-r border-slate-100">{isQualitative ? getQualitativeGrade(globalData.t2, effectiveGradingType) : globalData.t2}</td>
                                                        <td className="p-4 text-center border-r border-slate-100">{isQualitative ? getQualitativeGrade(globalData.t3, effectiveGradingType) : globalData.t3}</td>
                                                        <td className="p-4 border-l border-slate-200 text-center font-bold text-indigo-800 bg-indigo-50/30">{isQualitative ? getQualitativeGrade(globalData.final, effectiveGradingType) : globalData.final}</td>
                                                    </>
                                                ) : (
                                                    <>
                                                        {categories.filter(c => !c.parent_category).map(cat => (
                                                            <React.Fragment key={cat.id}>
                                                                {cat.subcategories && cat.subcategories.length > 0 ? (
                                                                    cat.subcategories.map(sub => (
                                                                        <td key={sub.id} className="p-2 text-center border-r border-slate-50">
                                                                             <input
                                                                                type="number" min="0" max="10" step="0.01"
                                                                                className="w-16 text-center p-2 rounded-md hover:border-slate-300 focus:border-indigo-500 transition-all bg-transparent focus:bg-white font-medium text-slate-700"
                                                                                placeholder="-"
                                                                                defaultValue={grades.find(g => g.enrollment === studentEnrollment.id && g.category === sub.id)?.score || ''}
                                                                                onBlur={(e) => saveGrade(studentEnrollment.id, sub.id, e.target.value)}
                                                                            />
                                                                        </td>
                                                                    ))
                                                                ) : (
                                                                    <td className="p-2 text-center border-r border-slate-50">
                                                                        <input
                                                                            type="number" min="0" max="10" step="0.01"
                                                                            className="w-16 text-center p-2 rounded-md hover:border-slate-300 focus:border-indigo-500 transition-all bg-transparent focus:bg-white font-medium text-slate-700"
                                                                            placeholder="-"
                                                                            defaultValue={grades.find(g => g.enrollment === studentEnrollment.id && g.category === cat.id)?.score || ''}
                                                                            onBlur={(e) => saveGrade(studentEnrollment.id, cat.id, e.target.value)}
                                                                        />
                                                                    </td>
                                                                )}
                                                                {cat.subcategories && cat.subcategories.length > 0 && (
                                                                    <td className="p-4 border-l border-slate-200 text-center font-bold text-amber-700 bg-amber-50/20">
                                                                        {isQualitative ? getQualitativeGrade(getCategoryScore(studentEnrollment.id, cat), effectiveGradingType) : getCategoryScore(studentEnrollment.id, cat)}
                                                                    </td>
                                                                )}
                                                            </React.Fragment>
                                                        ))}
                                                        <td className="p-4 border-l border-slate-200 text-center font-bold text-slate-800 bg-slate-50/30">
                                                            {isQualitative ? getQualitativeGrade(calculateFinalScore(studentEnrollment.id), effectiveGradingType) : calculateFinalScore(studentEnrollment.id)}
                                                        </td>
                                                    </>
                                                )}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {showCategoryModal && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                            <h2 className="text-xl font-bold text-slate-800 italic">Parámetros de Evaluación</h2>
                            <button onClick={() => setShowCategoryModal(false)} className="p-2 hover:bg-slate-200 rounded-full transition-colors"><X size={20} /></button>
                        </div>
                        <div className="p-6 max-h-[70vh] overflow-y-auto">
                            <form onSubmit={handleCategorySubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8 bg-indigo-50/50 p-4 rounded-xl border border-indigo-100">
                                <div className="md:col-span-1">
                                    <label className="text-xs font-bold text-slate-500 uppercase mb-1 block">Nombre</label>
                                    <input type="text" required className="input-modern w-full" placeholder="Ej: Tareas" value={categoryForm.name} onChange={e => setCategoryForm({ ...categoryForm, name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-slate-500 uppercase mb-1 block">Peso (%)</label>
                                    <input type="number" required min="1" max="100" className="input-modern w-full" placeholder="30" value={categoryForm.weight} onChange={e => setCategoryForm({ ...categoryForm, weight: e.target.value })} />
                                </div>
                                <div>
                                    <label className="text-xs font-bold text-slate-500 uppercase mb-1 block">Aporte Padre (Opcional)</label>
                                    <select className="input-modern w-full" value={categoryForm.parent_category} onChange={e => setCategoryForm({ ...categoryForm, parent_category: e.target.value })}>
                                        <option value="">Ninguno (Raíz)</option>
                                        {categories.filter(c => !c.parent_category).map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                    </select>
                                </div>
                                <div className="md:col-span-3">
                                    <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2">
                                        <Plus size={18} /> Agregar Aporte
                                    </button>
                                </div>
                            </form>

                            <div className="space-y-3">
                                <h3 className="font-bold text-slate-700 flex items-center gap-2">Estructura Actual</h3>
                                {categories.filter(c => !c.parent_category).map(cat => (
                                    <div key={cat.id} className="border border-slate-200 rounded-xl overflow-hidden">
                                        <div className="flex items-center justify-between p-3 bg-slate-50">
                                            <span className="font-bold text-slate-700">{cat.name} <span className="text-indigo-600 ml-2">{cat.weight}%</span></span>
                                            <button onClick={() => handleCategoryDelete(cat.id)} className="text-rose-500 hover:bg-rose-50 p-1.5 rounded-lg transition-colors"><X size={16} /></button>
                                        </div>
                                        {cat.subcategories && cat.subcategories.length > 0 && (
                                            <div className="p-3 bg-white space-y-2 border-t border-slate-100">
                                                {cat.subcategories.map(sub => (
                                                    <div key={sub.id} className="flex items-center justify-between pl-4 text-sm text-slate-600 border-l-2 border-indigo-100 py-1">
                                                        <span>{sub.name} ({sub.weight}% de {cat.name})</span>
                                                        <button onClick={() => handleCategoryDelete(sub.id)} className="text-slate-400 hover:text-rose-500 p-1"><X size={14} /></button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {showBehaviorModal && selectedBehaviorStudent && (
                <BehaviorQuickModal
                    studentId={selectedBehaviorStudent.id}
                    studentName={selectedBehaviorStudent.fullName}
                    existingRecord={selectedBehaviorStudent.existingRecord}
                    courseId={selectedCourse}
                    allowedTypes={['ACADEMIC']}
                    onClose={() => { setShowBehaviorModal(false); setSelectedBehaviorStudent(null); }}
                    onSaved={() => { loadGradebookData(); }}
                />
            )}
        </div>
    );
};

export default GradesPage;
