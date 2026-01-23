import React, { useEffect, useState, useMemo } from 'react';
import academicService from '../services/academicService';
import { Plus, Filter, Save, X, Settings, Calculator, Download, MessageSquare } from 'lucide-react';

const GradesPage = () => {
    // Selection State
    const [selectedCourse, setSelectedCourse] = useState('');
    const [selectedSubject, setSelectedSubject] = useState('');
    const [selectedTrimester, setSelectedTrimester] = useState('1');

    // Data State
    const [courses, setCourses] = useState([]);
    const [subjects, setSubjects] = useState([]); // All subjects or filtered
    const [students, setStudents] = useState([]); // From enrollments
    const [categories, setCategories] = useState([]);
    const [grades, setGrades] = useState([]); // Raw grades list

    // UI State
    const [loading, setLoading] = useState(true);
    const [loadingGrid, setLoadingGrid] = useState(false);
    const [showCategoryModal, setShowCategoryModal] = useState(false);

    // Comment Editing State
    const [editingComment, setEditingComment] = useState(null); // { enrollmentId, categoryId, gradeId, text }

    // Category Form
    const [categoryForm, setCategoryForm] = useState({ id: null, subject: '', name: '', weight: '' });

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
                academicService.getSubjects() // fetching all for now, could optimize
            ]);
            setCourses(coursesData);
            setSubjects(subjectsData);
        } catch (error) {
            console.error("Error loading initial data", error);
        } finally {
            setLoading(false);
        }
    };

    const loadGradebookData = async () => {
        setLoadingGrid(true);
        try {
            // 1. Get Enrollments (Filtered by API)
            // Pass selectedCourse to get enrollments only for this course
            const courseEnrollments = await academicService.getEnrollments(selectedCourse);

            // 2. Get Categories
            let categoriesData = [];
            if (selectedTrimester === 'summary') {
                // Fetch ALL categories for this subject
                categoriesData = await academicService.getEvaluationCategories(selectedSubject);
            } else {
                categoriesData = await academicService.getEvaluationCategories(selectedSubject, selectedTrimester);
            }

            // 3. Get Grades (Filtered by API)
            // Fetch grades specifically for this subject and course
            const relevantGrades = await academicService.getGrades(selectedSubject, null, selectedCourse);

            setStudents(courseEnrollments);
            setCategories(categoriesData);
            setGrades(relevantGrades);
        } catch (error) {
            console.error("Error loading gradebook", error);
        } finally {
            setLoadingGrid(false);
        }
    };

    // Helper to find existing grade
    const getGradeValue = (enrollmentId, categoryId) => {
        const grade = grades.find(g => g.enrollment === enrollmentId && g.category === categoryId);
        return grade ? grade.score : '';
    };

    const getGradeObservation = (enrollmentId, categoryId) => {
        const grade = grades.find(g => g.enrollment === enrollmentId && g.category === categoryId);
        return grade ? grade.observation : '';
    };

    const handleOpenComment = (enrollmentId, categoryId) => {
        const grade = grades.find(g => g.enrollment === enrollmentId && g.category === categoryId);
        setEditingComment({
            enrollmentId,
            categoryId,
            gradeId: grade ? grade.id : null,
            text: grade ? (grade.observation || '') : ''
        });
    };

    const handleSaveComment = async () => {
        if (!editingComment) return;
        const { enrollmentId, categoryId, gradeId, text } = editingComment;

        try {
            if (gradeId) {
                // Update specific field if possible, or full update
                // The API usually takes full object. We need to find the grade to get its score.
                const grade = grades.find(g => g.id === gradeId);
                if (grade) {
                    const updated = await academicService.updateGrade(gradeId, { ...grade, observation: text });
                    setGrades(grades.map(g => g.id === gradeId ? updated : g));
                }
            } else {
                // Grade doesn't exist. Create it with score 0? Or prompt?
                // For better UX, we'll create with 0 if missing.
                const payload = {
                    enrollment: enrollmentId,
                    subject: selectedSubject,
                    category: categoryId,
                    score: 0,
                    date: new Date().toISOString().split('T')[0],
                    observation: text
                };
                const created = await academicService.createGrade(payload);
                setGrades([...grades, created]);
            }
            setEditingComment(null);
        } catch (error) {
            console.error("Error saving comment", error);
            alert("Error al guardar el comentario.");
        }
    };

    const handleGradeChange = async (enrollmentId, categoryId, value) => {
        // Optimistic update or wait for blur?
        // Let's update local state deeply then sync on blur
        // Actually, let's just create a quick mechanism to save on blur to avoid too many requests
    };

    const saveGrade = async (enrollmentId, categoryId, value) => {
        if (value === '') return; // Don't save empty if it wasn't there

        try {
            const existingGrade = grades.find(g => g.enrollment === enrollmentId && g.category === categoryId);

            const payload = {
                enrollment: enrollmentId,
                subject: selectedSubject,
                category: categoryId,
                score: value,
                date: new Date().toISOString().split('T')[0],
                // removed eval_type as it is deprecated by category
            };

            if (existingGrade) {
                // Update
                if (existingGrade.score == value) return; // No change
                const updated = await academicService.updateGrade(existingGrade.id, { ...existingGrade, score: value }); // Maintain observation!
                setGrades(grades.map(g => g.id === existingGrade.id ? updated : g));
            } else {
                // Create
                const created = await academicService.createGrade(payload);
                setGrades([...grades, created]);
            }
        } catch (error) {
            console.error("Failed to save grade", error);
            alert("Error al guardar nota");
        }
    };

    // Calculation Logic
    const calculateFinalScore = (enrollmentId) => {
        // Standard Trimester Calculation
        let totalWeightedScore = 0;
        // let totalWeight = 0;

        categories.forEach(cat => {
            const grade = grades.find(g => g.enrollment === enrollmentId && g.category === cat.id);
            if (grade) {
                totalWeightedScore += (parseFloat(grade.score) * parseFloat(cat.weight)) / 100;
            }
        });

        return totalWeightedScore.toFixed(2);
    };

    const calculateTrimesterAverage = (enrollmentId, trimester) => {
        // Calculate average for specific trimester based on fetched categories/grades (even if hidden)
        // We need the categories for THAT trimester.
        const trimCategories = categories.filter(c => c.trimester === parseInt(trimester));
        if (trimCategories.length === 0) return 0;

        let totalWeightedScore = 0;
        trimCategories.forEach(cat => {
            const grade = grades.find(g => g.enrollment === enrollmentId && g.category === cat.id);
            if (grade) {
                totalWeightedScore += (parseFloat(grade.score) * parseFloat(cat.weight)) / 100;
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

    // Filtered subjects based on selected course
    const filteredSubjects = useMemo(() => {
        if (!selectedCourse) return [];
        return subjects.filter(s => s.course === parseInt(selectedCourse));
    }, [selectedCourse, subjects]);


    // Category Management Handlers
    const handleCategorySubmit = async (e) => {
        e.preventDefault();
        try {
            await academicService.createEvaluationCategory({
                ...categoryForm,
                subject: selectedSubject,
                trimester: selectedTrimester
            });
            alert('Categoría creada');
            loadGradebookData(); // Reload to refresh cols
            setCategoryForm({ ...categoryForm, name: '', weight: '' });
        } catch (error) {
            alert('Error al crear categoría');
        }
    };

    const handleCategoryDelete = async (id) => {
        if (!window.confirm("Eliminar categoría? Se borrarán las notas asociadas.")) return;
        try {
            await academicService.deleteEvaluationCategory(id);
            loadGradebookData();
        } catch (error) {
            alert("Error al eliminar");
        }
    };

    if (loading) return <div className="p-8 text-center">Cargando módulo de calificaciones...</div>;

    return (
        <div className="space-y-6">
            {/* Header & Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Libro de Calificaciones</h1>
                    <p className="text-slate-500 mt-1">Seleccione curso y materia para gestionar notas en tiempo real.</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto">
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
                        <option value="">Seleccione Materia...</option>
                        {filteredSubjects.map(s => (
                            <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                    </select>

                    <select
                        className="input-modern min-w-[150px]"
                        value={selectedTrimester}
                        onChange={e => setSelectedTrimester(e.target.value)}
                    >
                        <option value="1">Trimestre 1</option>
                        <option value="2">Trimestre 2</option>
                        <option value="3">Trimestre 3</option>
                        <option value="summary" className="font-bold text-indigo-600">Resumen Final</option>
                    </select>

                    {selectedSubject && (
                        <button
                            onClick={() => setShowCategoryModal(true)}
                            className="btn-secondary flex items-center justify-center gap-2"
                        >
                            <Settings size={18} /> Configurar Aportes
                        </button>
                    )}
                </div>
            </div>

            {/* Gradebook Grid */}
            {!selectedCourse || !selectedSubject ? (
                <div className="text-center py-20 bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200">
                    <Filter className="mx-auto h-12 w-12 text-slate-300 mb-4" />
                    <h3 className="text-lg font-medium text-slate-600">Comience seleccionando un curso y una materia</h3>
                    <p className="text-slate-400">Verá la lista de estudiantes y podrá ingresar notas.</p>
                </div>
            ) : categories.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 shadow-sm">
                    <div className="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Settings size={32} />
                    </div>
                    <h3 className="text-xl font-bold text-slate-800 mb-2">No hay aportes definidos</h3>
                    <p className="text-slate-500 max-w-md mx-auto mb-6">
                        Para ingresar notas, primero debe definir los aportes (ej. Tareas, Lecciones, Examen) y sus ponderaciones.
                    </p>
                    <button
                        onClick={() => setShowCategoryModal(true)}
                        className="btn-primary inline-flex items-center gap-2"
                    >
                        <Plus size={20} /> Crear Aportes
                    </button>
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
                                        <th className="p-4 border-b border-r border-slate-200 min-w-[250px] sticky left-0 bg-slate-50 z-10">Estudiante</th>
                                        {selectedTrimester === 'summary' ? (
                                            <>
                                                <th className="p-4 border-b border-slate-200 text-center min-w-[100px]">Trimestre 1</th>
                                                <th className="p-4 border-b border-slate-200 text-center min-w-[100px]">Trimestre 2</th>
                                                <th className="p-4 border-b border-slate-200 text-center min-w-[100px]">Trimestre 3</th>
                                                <th className="p-4 border-b border-l border-slate-200 text-center min-w-[100px] bg-indigo-50 font-bold text-indigo-700">Nota Final</th>
                                            </>
                                        ) : (
                                            <>
                                                {categories.map(cat => (
                                                    <th key={cat.id} className="p-4 border-b border-slate-200 text-center min-w-[120px]">
                                                        <div className="flex flex-col">
                                                            <span>{cat.name}</span>
                                                            <span className="text-[10px] text-indigo-600 bg-indigo-50 px-1 rounded self-center mt-1">{cat.weight}%</span>
                                                        </div>
                                                    </th>
                                                ))}
                                                <th className="p-4 border-b border-l border-slate-200 text-center min-w-[100px] bg-slate-50 font-bold text-slate-700">Promedio</th>
                                            </>
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {students.length === 0 ? (
                                        <tr><td colSpan={10} className="p-8 text-center text-slate-400">No hay estudiantes matriculados en este curso.</td></tr>
                                    ) : (
                                        students.map(studentEnrollment => {
                                            const globalData = selectedTrimester === 'summary' ? calculateGlobalAverage(studentEnrollment.id) : null;
                                            return (
                                                <tr key={studentEnrollment.id} className="hover:bg-slate-50/50 transition-colors">
                                                    <td className="p-4 border-r border-slate-100 font-medium text-slate-700 sticky left-0 bg-white group-hover:bg-slate-50/50 z-10">
                                                        {studentEnrollment.student_detail ?
                                                            `${studentEnrollment.student_detail.last_name} ${studentEnrollment.student_detail.first_name}` :
                                                            `ID: ${studentEnrollment.student}`
                                                        }
                                                    </td>
                                                    {selectedTrimester === 'summary' ? (
                                                        <>
                                                            <td className="p-4 text-center border-r border-slate-100">{globalData.t1}</td>
                                                            <td className="p-4 text-center border-r border-slate-100">{globalData.t2}</td>
                                                            <td className="p-4 text-center border-r border-slate-100">{globalData.t3}</td>
                                                            <td className="p-4 border-l border-slate-200 text-center font-bold text-indigo-800 bg-indigo-50/30">{globalData.final}</td>
                                                        </>
                                                    ) : (
                                                        <>
                                                            {categories.map(cat => {
                                                                const obs = getGradeObservation(studentEnrollment.id, cat.id);
                                                                return (
                                                                    <td key={cat.id} className="p-2 text-center border-r border-slate-50 relative group/cell">
                                                                        <div className="relative flex items-center justify-center gap-1">
                                                                            <input
                                                                                type="number"
                                                                                min="0"
                                                                                max="10"
                                                                                step="0.01"
                                                                                className="w-16 text-center p-2 rounded-md border-transparent hover:border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-all bg-transparent focus:bg-white font-medium text-slate-700"
                                                                                placeholder="-"
                                                                                defaultValue={getGradeValue(studentEnrollment.id, cat.id)}
                                                                                onBlur={(e) => saveGrade(studentEnrollment.id, cat.id, e.target.value)}
                                                                                onKeyDown={(e) => {
                                                                                    if (e.key === 'Enter') {
                                                                                        e.target.blur();
                                                                                    }
                                                                                }}
                                                                            />
                                                                            <button
                                                                                onClick={() => handleOpenComment(studentEnrollment.id, cat.id)}
                                                                                className={`p-1 rounded-full transition-colors ${obs ? 'text-indigo-500 bg-indigo-50 hover:bg-indigo-100' : 'text-slate-300 hover:text-slate-500 opacity-0 group-hover/cell:opacity-100'}`}
                                                                                title={obs || "Agregar comentario/detalle"}
                                                                            >
                                                                                <MessageSquare size={14} fill={obs ? "currentColor" : "none"} />
                                                                            </button>
                                                                        </div>
                                                                    </td>
                                                                );
                                                            })}
                                                            <td className="p-4 border-l border-slate-200 text-center font-bold text-slate-800 bg-slate-50/30">
                                                                {calculateFinalScore(studentEnrollment.id)}
                                                            </td>
                                                        </>
                                                    )}
                                                </tr>
                                            );
                                        })
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {/* Modal Gestionar Categorias (Simplificado para integración) */}
            {showCategoryModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl p-6 max-w-lg w-full shadow-2xl">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-slate-800">Aportes: {subjects.find(s => s.id === parseInt(selectedSubject))?.name}</h2>
                            <button onClick={() => setShowCategoryModal(false)} className="text-slate-400 hover:text-slate-600"><X size={24} /></button>
                        </div>

                        <form onSubmit={handleCategorySubmit} className="flex gap-2 items-end mb-6">
                            <div className="flex-1">
                                <label className="text-xs font-bold text-slate-500 uppercase">Nombre</label>
                                <input
                                    type="text"
                                    required
                                    className="input-modern w-full"
                                    placeholder="Ej. Tareas"
                                    value={categoryForm.name}
                                    onChange={e => setCategoryForm({ ...categoryForm, name: e.target.value })}
                                />
                            </div>
                            <div className="w-24">
                                <label className="text-xs font-bold text-slate-500 uppercase">Peso %</label>
                                <input
                                    type="number"
                                    required
                                    className="input-modern w-full"
                                    placeholder="30"
                                    value={categoryForm.weight}
                                    onChange={e => setCategoryForm({ ...categoryForm, weight: e.target.value })}
                                />
                            </div>
                            <button type="submit" className="btn-primary mb-0.5"><Plus size={20} /></button>
                        </form>

                        <div className="space-y-2 max-h-[300px] overflow-y-auto">
                            {categories.map(cat => (
                                <div key={cat.id} className="flex justify-between items-center bg-slate-50 p-3 rounded-lg border border-slate-100">
                                    <span className="font-medium">{cat.name}</span>
                                    <div className="flex items-center gap-3">
                                        <span className="text-sm bg-white px-2 py-1 rounded shadow-sm text-slate-600 font-bold">{cat.weight}%</span>
                                        <button onClick={() => handleCategoryDelete(cat.id)} className="text-red-400 hover:text-red-600"><X size={16} /></button>
                                    </div>
                                </div>
                            ))}
                            {categories.length === 0 && <p className="text-center text-slate-400 py-4">No hay aportes definidos.</p>}
                        </div>

                        <div className="mt-4 pt-4 border-t border-slate-50 text-xs text-slate-400">
                            La suma de pesos debería ser 100%. Actualmente: {categories.reduce((acc, c) => acc + parseFloat(c.weight), 0)}%
                        </div>
                    </div>
                </div>
            )}

            {/* Modal Comentario/Detalle */}
            {editingComment && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl p-6 max-w-sm w-full shadow-2xl animate-in zoom-in-95">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold text-slate-800">Detalle del Aporte</h3>
                            <button onClick={() => setEditingComment(null)} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
                        </div>
                        <div className="mb-4">
                            <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Comentario / Observación</label>
                            <textarea
                                autoFocus
                                className="input-modern w-full min-h-[100px]"
                                placeholder="Ej. Entrega tardía, Excelente trabajo, etc."
                                value={editingComment.text}
                                onChange={e => setEditingComment({ ...editingComment, text: e.target.value })}
                            ></textarea>
                        </div>
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setEditingComment(null)} className="btn-secondary">Cancelar</button>
                            <button onClick={handleSaveComment} className="btn-primary">Guardar</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GradesPage;
