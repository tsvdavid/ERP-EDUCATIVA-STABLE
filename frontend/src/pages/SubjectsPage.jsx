import React, { useEffect, useState } from 'react';
import academicService from '../services/academicService';
import userService from '../services/userService';
import { Plus, Edit, Trash2, BookOpen, Save, X } from 'lucide-react';
import { useAuthStore } from '../context/authStore';

const SubjectsPage = () => {
    const { user } = useAuthStore();
    const [subjects, setSubjects] = useState([]);
    const [courses, setCourses] = useState([]);
    const [teachers, setTeachers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [isEditing, setIsEditing] = useState(false);

    // El modelo Subject requiere: name, course (ID), teacher (ID), grading_type
    const [formData, setFormData] = useState({ id: null, name: '', course: '', teacher: '', grading_type: 'INHERIT' });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [subjectsData, coursesData, teachersData] = await Promise.all([
                academicService.getSubjects(),
                academicService.getCourses(),
                userService.getUsers('TEACHER')
            ]);
            setSubjects(subjectsData);
            setCourses(coursesData);
            setTeachers(Array.isArray(teachersData) ? teachersData : []);
        } catch (error) {
            console.error("Error loading data", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFormSubmit = async (e) => {
        e.preventDefault();
        try {
            if (isEditing) {
                await academicService.updateSubject(formData.id, formData);
                alert('Materia actualizada con éxito');
            } else {
                await academicService.createSubject(formData);
                alert('Materia creada con éxito');
            }
            setShowModal(false);
            setFormData({ id: null, name: '', course: '', teacher: '', grading_type: 'INHERIT' });
            loadData();
        } catch (error) {
            console.error(error);
            if (error.response && error.response.data && error.response.data.non_field_errors) {
                alert("Error: Ya existe esta materia en el curso seleccionado.");
            } else {
                alert("Error al guardar la materia.");
            }
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm('¿Seguro de eliminar esta materia?')) return;
        try {
            await academicService.deleteSubject(id);
            loadData();
        } catch (error) {
            console.error(error);
            alert("Error al eliminar materia.");
        }
    };

    const openCreateModal = () => {
        setFormData({ id: null, name: '', course: '', teacher: '', grading_type: 'INHERIT' });
        setIsEditing(false);
        setShowModal(true);
    };

    const openEditModal = (subject) => {
        setFormData({
            id: subject.id,
            name: subject.name,
            course: subject.course,
            teacher: subject.teacher || '',
            grading_type: subject.grading_type || 'INHERIT'
        });
        setIsEditing(true);
        setShowModal(true);
    };

    if (loading) return <div className="p-8">Cargando materias...</div>;

    const getCourseName = (courseId) => {
        const course = courses.find(c => c.id === courseId);
        return course ? course.name : 'Desconocido';
    };

    const getTeacherName = (teacherId) => {
        if (!teacherId) return 'Sin docente';
        const teacher = teachers.find(t => t.id === teacherId);
        return teacher ? `${teacher.first_name} ${teacher.last_name}` : 'Desconocido';
    };

    return (
        <div className="p-6 space-y-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 flex items-center gap-2">
                        <BookOpen className="text-indigo-600" /> Gestión de Materias
                    </h1>
                    <p className="text-slate-500 mt-1">Administra las asignaturas del plan de estudios.</p>
                </div>
                {user?.role !== 'TEACHER' && (
                    <button
                        onClick={openCreateModal}
                        className="btn-primary flex items-center gap-2"
                    >
                        <Plus size={20} /> Nueva Materia
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {subjects.map(subject => (
                    <div key={subject.id} className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-2">
                            <h3 className="text-xl font-bold text-slate-800">{subject.name}</h3>
                            <span className="text-xs font-semibold bg-indigo-50 text-indigo-700 px-2 py-1 rounded-full">
                                {getCourseName(subject.course)}
                            </span>
                        </div>
                        <p className="text-sm text-slate-500 mb-4 flex items-center gap-2">
                            Docente: <span className="font-medium text-slate-700">{getTeacherName(subject.teacher)}</span>
                        </p>
                        {user?.role !== 'TEACHER' && (
                            <div className="mt-4 pt-4 border-t border-slate-50 flex justify-end gap-2">
                                <button
                                    onClick={() => openEditModal(subject)}
                                    className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-full transition-colors"
                                    title="Editar"
                                >
                                    <Edit size={18} />
                                </button>
                                <button
                                    onClick={() => handleDelete(subject.id)}
                                    className="p-2 text-red-600 hover:bg-red-50 rounded-full transition-colors"
                                    title="Eliminar"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl animate-in fade-in zoom-in">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-2xl font-bold text-slate-800">
                                {isEditing ? 'Editar Materia' : 'Nueva Materia'}
                            </h2>
                            <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                                <X size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleFormSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Nombre de la Materia</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={e => setFormData({ ...formData, name: e.target.value })}
                                    className="input-modern w-full"
                                    placeholder="Ej. Álgebra, Historia..."
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Asignar a Curso</label>
                                <select
                                    value={formData.course}
                                    onChange={e => setFormData({ ...formData, course: e.target.value })}
                                    className="input-modern w-full"
                                    required
                                >
                                    <option value="">Seleccione un curso...</option>
                                    {courses.map(course => (
                                        <option key={course.id} value={course.id}>
                                            {course.name} - {course.level} {course.parallel}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Asignar Docente</label>
                                <select
                                    value={formData.teacher}
                                    onChange={e => setFormData({ ...formData, teacher: e.target.value })}
                                    className="input-modern w-full"
                                >
                                    <option value="">Sin docente asignado</option>
                                    {teachers.map(teacher => (
                                        <option key={teacher.id} value={teacher.id}>
                                            {teacher.first_name} {teacher.last_name}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Calificación</label>
                                <select
                                    value={formData.grading_type}
                                    onChange={e => setFormData({ ...formData, grading_type: e.target.value })}
                                    className="input-modern w-full"
                                >
                                    <option value="INHERIT">Heredar del Curso</option>
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
                                    <Save size={18} /> {isEditing ? 'Actualizar' : 'Guardar'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SubjectsPage;
