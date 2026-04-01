import React, { useEffect, useState } from 'react';
import academicService from '../services/academicService';
import userService from '../services/userService';
import { useAuthStore } from '../context/authStore';
import { Plus, Edit, Trash2, Book, GraduationCap, Calendar, MoreVertical, X, Save } from 'lucide-react';

const CoursesPage = () => {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({ id: null, name: '', description: '', level: '', parallel: 'A', year: new Date().getFullYear(), grading_type: 'QUANTITATIVE' });

    const [institutionId, setInstitutionId] = useState(null);
    const { user } = useAuthStore();

    useEffect(() => {
        loadData();
    }, [user]);

    const loadData = async () => {
        console.log("CoursesPage: Loading data...");
        try {
            // 1. Load Courses
            try {
                const coursesData = await academicService.getCourses();
                setCourses(coursesData);
            } catch (courseError) {
                console.error("Error loading courses:", courseError);
            }

            // 2. Load Institution Context (if authorized)
            let currentInstitution = user?.institution;

            if (!currentInstitution && (user?.role === 'ADMIN' || user?.role === 'RECTOR')) {
                try {
                    const instData = await userService.getInstitutions();
                    if (instData && instData.length > 0) {
                        currentInstitution = instData[0].id;
                    }
                } catch (instError) {
                    console.error("Error loading institutions:", instError);
                }
            }

            if (currentInstitution) {
                console.log("Setting Institution ID:", currentInstitution);
                setInstitutionId(currentInstitution);
            }

        } catch (error) {
            console.error("Fatal error in loadData:", error);
        } finally {
            setLoading(false);
        }
    };

    // Kept loadCourses for refresh actions
    const loadCourses = async () => {
        try {
            const data = await academicService.getCourses();
            setCourses(data);
        } catch (error) {
            console.error("Error loading courses", error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Final safety check
        const targetInstitution = institutionId || user?.institution;

        if (!targetInstitution) {
            alert("No hay una institución configurada. Por favor configure la institución primero.");
            return;
        }

        try {
            const payload = { ...formData, institution: targetInstitution };
            if (isEditing) {
                await academicService.updateCourse(formData.id, payload);
                alert('Curso actualizado exitosamente');
            } else {
                await academicService.createCourse(payload);
                alert('Curso creado exitosamente');
            }
            setShowModal(false);
            loadCourses();
            resetForm();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data ? JSON.stringify(error.response.data) : 'Error al guardar curso.';
            alert(msg);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('¿Estás seguro de eliminar este curso? Se eliminarán también las materias asociadas.')) return;
        try {
            await academicService.deleteCourse(id);
            loadCourses();
        } catch (error) {
            console.error(error);
            alert('Error al eliminar curso.');
        }
    };

    const openCreateModal = () => {
        resetForm();
        setIsEditing(false);
        setShowModal(true);
    };

    const openEditModal = (course) => {
        setFormData({
            id: course.id,
            name: course.name,
            description: course.description,
            level: course.level,
            parallel: course.parallel,
            year: course.year,
            grading_type: course.grading_type || 'QUANTITATIVE'
        });
        setIsEditing(true);
        setShowModal(true);
    };

    const resetForm = () => {
        setFormData({ id: null, name: '', description: '', level: '', parallel: 'A', year: new Date().getFullYear(), grading_type: 'QUANTITATIVE' });
    };

    const canManageCourses = user?.role === 'ADMIN' || user?.role === 'RECTOR';

    if (loading) return <div className="p-8 flex justify-center"><div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div></div>;

    const getGradient = (id) => {
        const gradients = [
            'from-blue-500 to-cyan-400',
            'from-indigo-500 to-purple-500',
            'from-rose-500 to-pink-500',
            'from-emerald-500 to-teal-400',
            'from-orange-500 to-amber-400',
        ];
        return gradients[id % gradients.length];
    };

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Cursos Académicos</h1>
                    <p className="text-slate-500 mt-1">Gestiona los grados y niveles educativos.</p>
                </div>
                {canManageCourses && (
                    <button
                        onClick={openCreateModal}
                        className="btn-primary flex items-center gap-2 shadow-indigo-500/20"
                    >
                        <Plus size={20} />
                        <span>Crear Curso</span>
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {courses.map((course) => (
                    <div key={course.id} className="group relative bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 border border-slate-100">
                        <div className={`h-24 bg-gradient-to-r ${getGradient(course.id)} p-4 relative`}>
                            {canManageCourses && (
                                <div className="absolute top-4 right-4 flex gap-2">
                                    <button
                                        onClick={() => openEditModal(course)}
                                        className="bg-white/20 backdrop-blur-sm p-1.5 rounded-lg text-white hover:bg-white/30 cursor-pointer transition-colors"
                                        title="Editar"
                                    >
                                        <Edit size={16} />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(course.id)}
                                        className="bg-red-500/20 backdrop-blur-sm p-1.5 rounded-lg text-white hover:bg-red-500/40 cursor-pointer transition-colors"
                                        title="Eliminar"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            )}
                            <div className="absolute -bottom-6 left-6">
                                <div className="w-12 h-12 bg-white rounded-xl shadow-md flex items-center justify-center text-indigo-600">
                                    <GraduationCap size={24} />
                                </div>
                            </div>
                        </div>

                        <div className="pt-8 p-6">
                            <div className="mb-4">
                                <h3 className="text-xl font-bold text-slate-800 mb-1 group-hover:text-indigo-600 transition-colors">{course.name}</h3>
                                <p className="text-slate-500 text-sm line-clamp-2">{course.description || 'Sin descripción disponible.'}</p>
                            </div>

                            <div className="flex items-center gap-4 text-sm text-slate-500 border-t border-slate-50 pt-4">
                                <div className="flex items-center gap-1.5 bg-slate-50 px-2 py-1 rounded-md">
                                    <Book size={14} className="text-indigo-400" />
                                    <span>{course.level} - {course.parallel}</span>
                                </div>
                                <div className="flex items-center gap-1.5 bg-slate-50 px-2 py-1 rounded-md">
                                    <Calendar size={14} className="text-indigo-400" />
                                    <span>{course.year}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

                {canManageCourses && (
                    <button
                        onClick={openCreateModal}
                        className="flex flex-col items-center justify-center p-8 rounded-2xl border-2 border-dashed border-slate-200 text-slate-400 hover:border-indigo-400 hover:text-indigo-500 hover:bg-indigo-50/10 transition-all gap-3 min-h-[280px]"
                    >
                        <div className="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center group-hover:bg-indigo-100 transition-colors">
                            <Plus size={32} />
                        </div>
                        <span className="font-medium">Agregar Nuevo Curso</span>
                    </button>
                )}
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
                        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                            <h2 className="text-xl font-bold text-slate-800">
                                {isEditing ? 'Editar Curso' : 'Nuevo Curso'}
                            </h2>
                            <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                                <X size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1">Nombre del Curso</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    className="input-modern"
                                    placeholder="Ej. Matemática Avanzada"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1">Descripción</label>
                                <textarea
                                    value={formData.description}
                                    onChange={e => setFormData({ ...formData, description: e.target.value })}
                                    className="input-modern"
                                    rows="3"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold text-slate-700 mb-1">Nivel</label>
                                    <input
                                        type="text"
                                        value={formData.level}
                                        onChange={e => setFormData({ ...formData, level: e.target.value })}
                                        className="input-modern"
                                        placeholder="Ej. Secundaria"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 mb-1">Paralelo</label>
                                        <input
                                            type="text"
                                            value={formData.parallel}
                                            onChange={e => setFormData({ ...formData, parallel: e.target.value })}
                                            className="input-modern"
                                            placeholder="A"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-semibold text-slate-700 mb-1">Año</label>
                                        <input
                                            type="number"
                                            value={formData.year}
                                            onChange={e => setFormData({ ...formData, year: e.target.value })}
                                            className="input-modern"
                                        />
                                    </div>
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-slate-700 mb-1">Tipo de Calificación</label>
                                <select
                                    value={formData.grading_type}
                                    onChange={e => setFormData({ ...formData, grading_type: e.target.value })}
                                    className="input-modern"
                                >
                                    <option value="QUANTITATIVE">Cuantitativa (0-10)</option>
                                    <option value="QUALITATIVE_DESTREZAS">Cualitativa - Destrezas (DA, EP, I, NE)</option>
                                    <option value="QUALITATIVE_PROYECTOS">Cualitativa - Proyectos (EX, MB, B, R)</option>
                                    <option value="QUALITATIVE_COMPORTAMIENTO">Cualitativa - Comportamiento (A, B, C, D, E)</option>
                                </select>
                            </div>
                            <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-slate-50">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="btn-secondary"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="btn-primary flex items-center gap-2"
                                >
                                    <Save size={18} />
                                    {isEditing ? 'Actualizar' : 'Crear Curso'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CoursesPage;
