import React, { useEffect, useState, useMemo } from 'react';
import userService from '../services/userService';
import academicService from '../services/academicService';
import { useAuthStore } from '../context/authStore';
import { Plus, UserPlus, BookOpen, Search, Filter, MoreHorizontal, Mail, Shield, Edit, Trash2, X, Save, Phone } from 'lucide-react';

const StudentsPage = () => {
    const [students, setStudents] = useState([]);
    const [courses, setCourses] = useState([]);
    const [enrollments, setEnrollments] = useState([]);
    const [loading, setLoading] = useState(true);

    // Modals
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showEnrollModal, setShowEnrollModal] = useState(false);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [isEditing, setIsEditing] = useState(false);

    // Filters
    const [showFilters, setShowFilters] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterCourse, setFilterCourse] = useState('');

    // Form data for creating/editing student
    const [studentData, setStudentData] = useState({
        id: null,
        username: '',
        password: '',
        first_name: '',
        last_name: '',
        email: '',
        birth_date: '',
        gender: '',
        notes: '',
        role: 'STUDENT',
        representative_name: '',
        phone: '',
        secondary_phone: ''
    });

    // Form data for enrolling
    const [enrollData, setEnrollData] = useState({ course: '' });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [studentsData, coursesData, enrollmentsData] = await Promise.all([
                userService.getUsers('STUDENT'),
                academicService.getCourses(),
                academicService.getEnrollments()
            ]);
            setStudents(Array.isArray(studentsData) ? studentsData : []);
            setCourses(Array.isArray(coursesData) ? coursesData : []);
            setEnrollments(Array.isArray(enrollmentsData) ? enrollmentsData : []);
        } catch (error) {
            console.error("Error loading data", error);
        } finally {
            setLoading(false);
        }
    };

    // Helper to find student's course
    const getStudentCourse = (studentId) => {
        const enrollment = enrollments.find(e => e.student === studentId);
        if (!enrollment) return null;
        return courses.find(c => c.id === enrollment.course);
    };

    const { user, activeInstitution } = useAuthStore();

    const handleCreateOrUpdateStudent = async (e) => {
        e.preventDefault();

        let targetInstitution = activeInstitution || user?.institution;

        // Fallback: If no institution in context, try to fetch it (for Admins/Single Tenant)
        if (!targetInstitution) {
            try {
                const insts = await userService.getInstitutions();
                if (insts && insts.length > 0) {
                    targetInstitution = insts[0].id;
                    // Optionally update store/localstorage? skipping for now to strict local scope.
                }
            } catch (err) {
                console.error("Failed to fallback fetch institution:", err);
            }
        }

        if (!targetInstitution) {
            alert("No se pudo determinar la institución. Asegúrese de que existe una institución creada.");
            return;
        }

        try {
            const payload = { ...studentData, institution: targetInstitution };
            if (isEditing && !payload.password) {
                delete payload.password;
            }
            if (!payload.birth_date) payload.birth_date = null;

            if (isEditing) {
                await userService.updateUser(payload.id, payload);
                alert('Estudiante actualizado exitosamente');
            } else {
                await userService.createUser(payload);
                alert('Estudiante creado exitosamente');
            }
            setShowCreateModal(false);
            resetForm();
            loadData();
        } catch (error) {
            console.error("Error saving student:", error);
            let msg = "Error al guardar.";
            if (error.response?.data) {
                if (typeof error.response.data === 'string') {
                    msg = error.response.data;
                } else if (typeof error.response.data === 'object') {
                    // Extract first error usually
                    const entries = Object.entries(error.response.data);
                    if (entries.length > 0) {
                        msg = `${entries[0][0]}: ${entries[0][1]}`;
                    } else {
                        msg = JSON.stringify(error.response.data);
                    }
                }
            }
            alert(msg);
        }
    };

    const handleDeleteStudent = async (id) => {
        if (!window.confirm('¿Seguro de eliminar este estudiante? Se perderán sus calificaciones.')) return;
        try {
            await userService.deleteUser(id);
            loadData();
        } catch (error) {
            console.error(error);
            alert("Error al eliminar.");
        }
    };

    const handleEnrollStudent = async (e) => {
        e.preventDefault();
        if (!selectedStudent || !enrollData.course) return;

        try {
            await academicService.createEnrollment({
                student: selectedStudent.id,
                course: enrollData.course
            });
            setShowEnrollModal(false);
            alert(`Estudiante matriculado exitosamente.`);
            setEnrollData({ course: '' });
            loadData(); // Reload to update list
        } catch (error) {
            // Enhanced error logic
            if (error.response && error.response.data && error.response.data[0]) {
                alert(`Error: ${error.response.data[0]}`);
            } else {
                alert('No se pudo matricular. Verifique si el estudiante ya pertenece a un curso.');
            }
        }
    };

    const openEnrollModal = (student) => {
        setSelectedStudent(student);
        setShowEnrollModal(true);
    };

    const openCreateModal = () => {
        resetForm();
        setIsEditing(false);
        setShowCreateModal(true);
    };

    const openEditModal = (student) => {
        setStudentData({
            id: student.id,
            username: student.username,
            password: '',
            first_name: student.first_name,
            last_name: student.last_name,
            email: student.email,
            birth_date: student.birth_date || '',
            gender: student.gender || '',
            notes: student.notes || '',
            role: 'STUDENT',
            representative_name: student.representative_name || '',
            phone: student.phone || '',
            secondary_phone: student.secondary_phone || ''
        });
        setIsEditing(true);
        setShowCreateModal(true);
    };

    const resetForm = () => {
        setStudentData({
            id: null,
            username: '',
            password: '',
            first_name: '',
            last_name: '',
            email: '',
            birth_date: '',
            gender: '',
            notes: '',
            role: 'STUDENT',
            representative_name: '',
            phone: '',
            secondary_phone: ''
        });
    };

    // Filter Logic
    const filteredStudents = useMemo(() => {
        return students.filter(student => {
            const fullName = `${student.first_name} ${student.last_name}`.toLowerCase();
            const username = student.username.toLowerCase();
            const searchLower = searchTerm.toLowerCase();

            const matchesSearch = fullName.includes(searchLower) || username.includes(searchLower);

            if (!matchesSearch) return false;

            if (filterCourse) {
                const course = getStudentCourse(student.id);
                if (!course || course.id !== parseInt(filterCourse)) return false;
            }

            return true;
        });
    }, [students, enrollments, courses, searchTerm, filterCourse]);

    if (loading) return <div className="p-8 flex justify-center"><div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div></div>;

    const getAvatarColor = (name) => {
        const colors = ['bg-blue-500', 'bg-indigo-500', 'bg-purple-500', 'bg-pink-500', 'bg-emerald-500', 'bg-orange-500'];
        let hash = 0;
        for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
        return colors[Math.abs(hash) % colors.length];
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Directorio de Estudiantes</h1>
                    <p className="text-slate-500 mt-1">Administra el acceso y matrícula del alumnado.</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className={`btn-secondary flex items-center gap-2 ${showFilters ? 'bg-indigo-50 text-indigo-600 border-indigo-200' : ''}`}
                    >
                        <Filter size={18} /> <span>Filtrar</span>
                    </button>
                    <button
                        onClick={openCreateModal}
                        className="btn-primary flex items-center gap-2 shadow-indigo-500/20"
                    >
                        <UserPlus size={18} /> Nuevo Estudiante
                    </button>
                </div>
            </div>

            {showFilters && (
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4 animate-in fade-in slide-in-from-top-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Buscar por nombre o usuario..."
                            className="input-modern pl-10 w-full"
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="w-full md:w-64">
                        <select
                            className="input-modern w-full"
                            value={filterCourse}
                            onChange={e => setFilterCourse(e.target.value)}
                        >
                            <option value="">-- Todos los Cursos --</option>
                            {courses.map(c => (
                                <option key={c.id} value={c.id}>{c.name} {c.parallel}</option>
                            ))}
                        </select>
                    </div>
                </div>
            )}

            <div className="card-premium overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-50 border-b border-slate-100 text-xs uppercase text-slate-500 font-semibold tracking-wider">
                        <tr>
                            <th className="p-5">Estudiante</th>
                            <th className="p-5">Curso Matriculado</th>
                            <th className="p-5">Contacto</th>
                            <th className="p-5 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                        {filteredStudents.length === 0 ? (
                            <tr><td colSpan="4" className="p-12 text-center text-slate-400">No se encontraron estudiantes.</td></tr>
                        ) : (
                            filteredStudents.map(student => {
                                const course = getStudentCourse(student.id);
                                return (
                                    <tr key={student.id} className="hover:bg-slate-50/50 transition-colors group">
                                        <td className="p-5">
                                            <div className="flex items-center gap-4">
                                                <div className={`w-10 h-10 rounded-full ${getAvatarColor(student.first_name)} flex items-center justify-center text-white font-bold shadow-md`}>
                                                    {student.first_name.charAt(0)}
                                                </div>
                                                <div>
                                                    <div className="font-semibold text-slate-700 group-hover:text-indigo-600 transition-colors">
                                                        {student.first_name} {student.last_name}
                                                    </div>
                                                    <div className="text-xs text-slate-400">@{student.username}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-5">
                                            {course ? (
                                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                                                    <BookOpen size={12} />
                                                    {course.name} "{course.parallel}"
                                                </span>
                                            ) : (
                                                <span className="text-slate-400 text-sm italic">Sin matrícula</span>
                                            )}
                                        </td>
                                        <td className="p-5">
                                            <div className="flex flex-col gap-1">
                                                {student.representative_name && (
                                                    <div className="flex items-center gap-2 text-slate-700 font-medium text-sm">
                                                        <Shield size={14} className="text-indigo-500" />
                                                        {student.representative_name}
                                                    </div>
                                                )}
                                                {student.phone && (
                                                    <div className="flex items-center gap-2 text-slate-500 text-xs">
                                                        <Phone size={14} />
                                                        {student.phone}
                                                    </div>
                                                )}
                                                <div className="flex items-center gap-2 text-slate-400 text-xs">
                                                    <Mail size={14} />
                                                    {student.email || 'No email'}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-5 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => openEnrollModal(student)}
                                                    className="text-sm font-medium text-emerald-600 bg-emerald-50 hover:bg-emerald-100 p-2 rounded-lg transition-colors inline-flex items-center"
                                                    title="Matricular / Cambiar Curso"
                                                >
                                                    <BookOpen size={16} />
                                                </button>
                                                <button
                                                    onClick={() => openEditModal(student)}
                                                    className="text-sm font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 p-2 rounded-lg transition-colors inline-flex items-center"
                                                    title="Editar"
                                                >
                                                    <Edit size={16} />
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteStudent(student.id)}
                                                    className="text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 p-2 rounded-lg transition-colors inline-flex items-center"
                                                    title="Eliminar"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )
                            })
                        )}
                    </tbody>
                </table>
            </div>

            {showCreateModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl animate-in fade-in zoom-in">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-2xl font-bold text-slate-800">
                                {isEditing ? 'Editar Estudiante' : 'Nuevo Estudiante'}
                            </h2>
                            <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600">
                                <X size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleCreateOrUpdateStudent} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
                                    <input type="text" placeholder="Nombre" required className="input-modern p-3 w-full"
                                        value={studentData.first_name} onChange={e => setStudentData({ ...studentData, first_name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Apellido</label>
                                    <input type="text" placeholder="Apellido" required className="input-modern p-3 w-full"
                                        value={studentData.last_name} onChange={e => setStudentData({ ...studentData, last_name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Usuario</label>
                                    <input type="text" placeholder="Usuario" required className="input-modern p-3 w-full"
                                        value={studentData.username} onChange={e => setStudentData({ ...studentData, username: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                                    <input type="email" placeholder="Email" required className="input-modern p-3 w-full"
                                        value={studentData.email} onChange={e => setStudentData({ ...studentData, email: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Fecha de Nacimiento</label>
                                    <input type="date" className="input-modern p-3 w-full"
                                        value={studentData.birth_date} onChange={e => setStudentData({ ...studentData, birth_date: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Sexo</label>
                                    <select className="input-modern p-3 w-full"
                                        value={studentData.gender} onChange={e => setStudentData({ ...studentData, gender: e.target.value })}>
                                        <option value="">Seleccione...</option>
                                        <option value="M">Masculino</option>
                                        <option value="F">Femenino</option>
                                        <option value="O">Otro</option>
                                    </select>
                                </div>
                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Nombre del Representante</label>
                                    <input type="text" placeholder="Nombre completo del representante" className="input-modern p-3 w-full"
                                        value={studentData.representative_name} onChange={e => setStudentData({ ...studentData, representative_name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Celular / Teléfono</label>
                                    <input type="text" placeholder="Número de contacto" className="input-modern p-3 w-full"
                                        value={studentData.phone} onChange={e => setStudentData({ ...studentData, phone: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Celular de Respaldo</label>
                                    <input type="text" placeholder="Otro número de contacto" className="input-modern p-3 w-full"
                                        value={studentData.secondary_phone} onChange={e => setStudentData({ ...studentData, secondary_phone: e.target.value })} />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Notas</label>
                                <textarea placeholder="Notas adicionales..." className="input-modern p-3 w-full" rows="3"
                                    value={studentData.notes} onChange={e => setStudentData({ ...studentData, notes: e.target.value })}></textarea>
                            </div>

                            <div className="relative">
                                <label className="block text-sm font-medium text-slate-700 mb-1">Contraseña</label>
                                <input type="password" placeholder={isEditing ? "Contraseña (dejar en blanco para no cambiar)" : "Contraseña"}
                                    required={!isEditing}
                                    className="input-modern p-3 w-full"
                                    value={studentData.password} onChange={e => setStudentData({ ...studentData, password: e.target.value })} />
                            </div>

                            <div className="flex justify-end gap-3 mt-8 pt-4 border-t border-slate-50">
                                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">Cancelar</button>
                                <button type="submit" className="btn-primary flex items-center gap-2">
                                    <Save size={18} /> {isEditing ? 'Actualizar' : 'Guardar'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showEnrollModal && selectedStudent && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-2xl">
                        <h2 className="text-xl font-bold mb-2 text-slate-800">Matricular Estudiante</h2>
                        <p className="text-slate-500 mb-6">{selectedStudent.first_name} {selectedStudent.last_name}</p>
                        <form onSubmit={handleEnrollStudent} className="space-y-4">
                            <select
                                required
                                className="input-modern p-3"
                                value={enrollData.course}
                                onChange={e => setEnrollData({ ...enrollData, course: e.target.value })}
                            >
                                <option value="">-- Seleccione Curso --</option>
                                {courses.map(course => (
                                    <option key={course.id} value={course.id}>{course.name} ({course.level} - {course.parallel})</option>
                                ))}
                            </select>
                            <div className="flex justify-end gap-3 mt-8">
                                <button type="button" onClick={() => setShowEnrollModal(false)} className="btn-secondary">Cancelar</button>
                                <button type="submit" className="btn-primary">Confirmar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StudentsPage;
