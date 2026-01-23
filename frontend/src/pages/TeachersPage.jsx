import React, { useState, useEffect } from 'react';
import userService from '../services/userService';
import { Plus, Edit, Trash2, Search, X, UserCheck } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import { useAuthStore } from '../context/authStore';

const TeachersPage = () => {
    const [teachers, setTeachers] = useState([]);
    const [filteredTeachers, setFilteredTeachers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);

    const { activeInstitution, user } = useAuthStore();
    const [institutions, setInstitutions] = useState([]);
    const [editingId, setEditingId] = useState(null);

    // Form State for Teachers
    const initialFormState = {
        username: '',
        email: '',
        password: '',
        first_name: '',
        second_name: '',
        last_name: '',
        second_surname: '',
        cedula: '',
        role: 'TEACHER', // Hardcoded
        phone: '',
        address: '',
        birth_date: '',

        photo: null,
        institution: activeInstitution || ''
    };
    const [formData, setFormData] = useState(initialFormState);

    useEffect(() => {
        loadTeachers();
    }, []);

    useEffect(() => {
        filterTeachers();
    }, [searchTerm, teachers]);

    const loadTeachers = async () => {
        setLoading(true);
        try {
            // Fetch ONLY teachers
            const data = await userService.getUsers('TEACHER');
            setTeachers(data);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar profesores");
        } finally {
            setLoading(false);
        }
    };

    const filterTeachers = () => {
        let result = teachers;
        if (searchTerm) {
            const lower = searchTerm.toLowerCase();
            result = result.filter(u =>
                (u.first_name || '').toLowerCase().includes(lower) ||
                (u.last_name || '').toLowerCase().includes(lower) ||
                (u.username || '').toLowerCase().includes(lower) ||
                (u.email || '').toLowerCase().includes(lower)
            );
        }
        setFilteredTeachers(result);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = new FormData();
            data.append('username', formData.username);
            data.append('email', formData.email);
            data.append('first_name', formData.first_name);
            data.append('last_name', formData.last_name);
            data.append('role', 'TEACHER'); // Force Role

            if (formData.institution) {
                data.append('institution', formData.institution);
            } else if (activeInstitution) {
                data.append('institution', activeInstitution);
            }

            if (formData.second_name) data.append('second_name', formData.second_name);
            if (formData.second_surname) data.append('second_surname', formData.second_surname);
            if (formData.cedula) data.append('cedula', formData.cedula);
            if (formData.birth_date) data.append('birth_date', formData.birth_date);
            if (formData.phone) data.append('phone', formData.phone);
            if (formData.address) data.append('address', formData.address);
            if (formData.photo instanceof File) {
                data.append('photo', formData.photo);
            }

            if (editingId) {
                if (formData.password) data.append('password', formData.password);
                await userService.updateUser(editingId, data);
                toast.success("Profesor actualizado");
            } else {
                data.append('password', formData.password);
                await userService.createUser(data);
                toast.success("Profesor registrado");
            }

            closeModal();
            loadTeachers();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.detail || "Error al guardar";
            toast.error(msg);
        }
    };

    const handleEdit = (user) => {
        setEditingId(user.id);
        const safeValue = (val) => val || '';
        setFormData({
            username: user.username,
            email: safeValue(user.email),
            password: '',
            first_name: user.first_name,
            second_name: safeValue(user.second_name),
            last_name: user.last_name,
            second_surname: safeValue(user.second_surname),
            cedula: safeValue(user.cedula),
            role: 'TEACHER',
            phone: safeValue(user.phone),
            address: safeValue(user.address),
            birth_date: safeValue(user.birth_date),

            photo: null,
            institution: user.institution || ''
        });
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {
        if (window.confirm('¿Eliminar este profesor?')) {
            try {
                await userService.deleteUser(id);
                toast.success("Profesor eliminado");
                loadTeachers();
            } catch (error) {
                toast.error("Error al eliminar");
            }
        }
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setFormData({ ...initialFormState, institution: activeInstitution || '' });
        setEditingId(null);
    };

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />

            <div className="flex flex-wrap justify-between items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Gestión de Profesores</h1>
                    <p className="text-slate-500">Administra el personal docente de la institución.</p>
                </div>
                <button
                    onClick={() => { setEditingId(null); setFormData(initialFormState); setIsModalOpen(true); }}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={18} /> Nuevo Profesor
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
                <div className="relative">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Buscar profesor..."
                        className="input-modern pl-10 w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <div className="col-span-full text-center py-10 text-slate-400">Cargando...</div>
                ) : filteredTeachers.length === 0 ? (
                    <div className="col-span-full text-center py-10 text-slate-400 bg-white rounded-xl border border-dashed border-slate-300">
                        <UserCheck size={48} className="mx-auto mb-2 opacity-50" />
                        <p>No se encontraron profesores.</p>
                    </div>
                ) : (
                    filteredTeachers.map(teacher => (
                        <div key={teacher.id} className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex flex-col gap-4 hover:shadow-md transition-shadow">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 bg-indigo-50 text-indigo-600 rounded-full flex items-center justify-center font-bold text-lg">
                                        {teacher.first_name[0]}{teacher.last_name[0]}
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-slate-800">{teacher.first_name} {teacher.last_name}</h3>
                                        <p className="text-xs text-slate-500">@{teacher.username}</p>
                                    </div>
                                </div>
                                <span className="bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-1 rounded-full uppercase">Profesor</span>
                            </div>

                            <div className="space-y-2 text-sm text-slate-600">
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Cédula:</span>
                                    <span>{teacher.cedula || '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Email:</span>
                                    <span className="truncate max-w-[150px]" title={teacher.email}>{teacher.email || '-'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-slate-400">Teléfono:</span>
                                    <span>{teacher.phone || '-'}</span>
                                </div>
                            </div>

                            <div className="pt-4 mt-auto border-t border-slate-50 flex justify-end gap-2">
                                <button onClick={() => handleEdit(teacher)} className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
                                    <Edit size={18} />
                                </button>
                                <button onClick={() => handleDelete(teacher.id)} className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50 sticky top-0">
                            <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Editar Profesor' : 'Nuevo Profesor'}</h2>
                            <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                                <X size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="label-modern">Nombres *</label>
                                    <input type="text" required className="input-modern w-full" placeholder="Ej. Juan Carlos" value={formData.first_name} onChange={e => setFormData({ ...formData, first_name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Apellidos *</label>
                                    <input type="text" required className="input-modern w-full" placeholder="Ej. Pérez López" value={formData.last_name} onChange={e => setFormData({ ...formData, last_name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Cédula</label>
                                    <input type="text" className="input-modern w-full" value={formData.cedula} onChange={e => setFormData({ ...formData, cedula: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Teléfono</label>
                                    <input type="text" className="input-modern w-full" value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Usuario (Login) *</label>
                                    <input type="text" required className="input-modern w-full" value={formData.username} onChange={e => setFormData({ ...formData, username: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Email</label>
                                    <input type="email" className="input-modern w-full" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
                                </div>
                                <div className="col-span-full">
                                    <label className="label-modern">Contraseña {editingId && '(Dejar vacío para no cambiar)'}</label>
                                    <input type="password" className="input-modern w-full" value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} />
                                </div>
                                {/* Institution Selector for Admin */}
                                {user?.role === 'ADMIN' && (
                                    <div className="col-span-full mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                                        <label className="label-modern">Institución Asignada</label>
                                        <select
                                            className="input-modern w-full"
                                            value={formData.institution}
                                            onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
                                        >
                                            <option value="">-- Seleccione Institución --</option>
                                            {institutions.map(inst => (
                                                <option key={inst.id} value={inst.id}>{inst.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                )}
                            </div>
                            <div className="flex justify-end gap-3 pt-4">
                                <button type="button" onClick={closeModal} className="px-4 py-2 text-slate-600">Cancelar</button>
                                <button type="submit" className="btn-primary">Guardar Profesor</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TeachersPage;
