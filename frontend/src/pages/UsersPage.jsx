import React, { useState, useEffect } from 'react';
import userService from '../services/userService';
import { Plus, Edit, Trash2, Search, Filter, X } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import { useAuthStore } from '../context/authStore';

const UsersPage = () => {
    const [users, setUsers] = useState([]);
    const [filteredUsers, setFilteredUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState('ALL');
    const [isModalOpen, setIsModalOpen] = useState(false);

    const { activeInstitution, user } = useAuthStore();
    const [institutions, setInstitutions] = useState([]);
    const [editingId, setEditingId] = useState(null);

    // Form State
    const initialFormState = {
        username: '',
        email: '',
        password: '',
        first_name: '',
        second_name: '',
        last_name: '',
        second_surname: '',
        cedula: '',
        role: 'STUDENT',
        phone: '',
        address: '',
        birth_date: '',
        gender: '',
        nationality: 'Ecuatoriana',
        civil_status: '',
        notes: '',
        photo: null,
        institution: activeInstitution || ''
    };
    const [formData, setFormData] = useState(initialFormState);

    useEffect(() => {
        loadUsers();
    }, []);

    useEffect(() => {
        filterUsers();
    }, [searchTerm, roleFilter, users]);

    const loadUsers = async () => {
        setLoading(true);
        try {
            const data = await userService.getUsers();
            setUsers(data);
            if (user?.role === 'ADMIN') {
                try {
                    const insts = await userService.getInstitutions();
                    setInstitutions(insts);
                } catch (err) { console.error("Error loading institutions", err); }
            }
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.detail || error.message || "Error al cargar usuarios";
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    const filterUsers = () => {
        let result = users;
        // Filter by Role
        if (roleFilter !== 'ALL') {
            result = result.filter(u => u.role === roleFilter);
        }
        // Filter by Search
        if (searchTerm) {
            const lower = searchTerm.toLowerCase();
            result = result.filter(u =>
                u.username.toLowerCase().includes(lower) ||
                (u.first_name || '').toLowerCase().includes(lower) ||
                (u.last_name || '').toLowerCase().includes(lower) ||
                (u.email || '').toLowerCase().includes(lower)
            );
        }
        setFilteredUsers(result);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = new FormData();
            // Basic fields
            data.append('username', formData.username);
            data.append('email', formData.email);
            data.append('first_name', formData.first_name);
            data.append('last_name', formData.last_name);
            data.append('role', formData.role);

            // Institution Context
            if (formData.institution) {
                data.append('institution', formData.institution);
            } else if (activeInstitution) {
                data.append('institution', activeInstitution);
            }

            // New fields
            if (formData.second_name) data.append('second_name', formData.second_name);
            if (formData.second_surname) data.append('second_surname', formData.second_surname);
            if (formData.cedula) data.append('cedula', formData.cedula);
            if (formData.birth_date) data.append('birth_date', formData.birth_date);
            if (formData.gender) data.append('gender', formData.gender);
            if (formData.nationality) data.append('nationality', formData.nationality);
            if (formData.civil_status) data.append('civil_status', formData.civil_status);
            if (formData.notes) data.append('notes', formData.notes);
            if (formData.phone) data.append('phone', formData.phone);
            if (formData.address) data.append('address', formData.address);

            if (formData.photo && formData.photo instanceof File) {
                data.append('photo', formData.photo);
            }

            if (editingId) {
                // Update
                if (formData.password) data.append('password', formData.password);

                await userService.updateUser(editingId, data);
                toast.success("Usuario actualizado exitosamente");
            } else {
                // Create
                data.append('password', formData.password);
                await userService.createUser(data);
                toast.success("Usuario creado exitosamente");
            }

            closeModal();
            loadUsers();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.detail || error.message || "Error al guardar usuario";

            // Should we show complex validation errors?
            if (error.response?.data && typeof error.response.data === 'object' && !error.response.data.detail) {
                const validationMsg = Object.entries(error.response.data)
                    .map(([k, v]) => {
                        const val = Array.isArray(v) ? v.join(' ') : v;
                        return `${k}: ${val}`;
                    })
                    .join('\n');
                toast.error(validationMsg, { duration: 6000 });
            } else {
                toast.error(msg, { duration: 6000 });
            }
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFormData({ ...formData, photo: e.target.files[0] });
        }
    };

    const handleEdit = (user) => {
        setEditingId(user.id);
        setFormData({
            username: user.username,
            email: user.email || '',
            password: '',
            first_name: user.first_name,
            second_name: user.second_name || '',
            last_name: user.last_name,
            second_surname: user.second_surname || '',
            cedula: user.cedula || '',
            role: user.role,
            phone: user.phone || '',
            address: user.address || '',
            birth_date: user.birth_date || '',
            gender: user.gender || '',
            nationality: user.nationality || 'Ecuatoriana',
            civil_status: user.civil_status || '',
            notes: user.notes || '',
            photo: null,
            institution: user.institution || ''
        });
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setFormData({ ...initialFormState, institution: activeInstitution || '' });
        setEditingId(null);
    };

    const handleDelete = async (id) => {
        if (window.confirm('¿Está seguro de eliminar este usuario?')) {
            try {
                await userService.deleteUser(id);
                toast.success("Usuario eliminado");
                loadUsers();
            } catch (error) {
                toast.error("Error al eliminar");
            }
        }
    };

    const getRoleBadge = (role) => {
        const styles = {
            'ADMIN': 'bg-purple-100 text-purple-700',
            'LOCAL_ADMIN': 'bg-fuchsia-100 text-fuchsia-700',
            'ACCOUNTANT': 'bg-emerald-100 text-emerald-700',
            'RECTOR': 'bg-pink-100 text-pink-700',
            'TEACHER': 'bg-blue-100 text-blue-700',
            'PARENT': 'bg-orange-100 text-orange-700',
            'STUDENT': 'bg-green-100 text-green-700',
            'DECE': 'bg-teal-100 text-teal-700',
            'MEDICO': 'bg-cyan-100 text-cyan-700',
        };
        return styles[role] || 'bg-slate-100 text-slate-700';
    };

    const getRoleName = (role) => {
        const names = {
            'ADMIN': 'Administrador',
            'LOCAL_ADMIN': 'Administrador Local',
            'ACCOUNTANT': 'Contabilidad',
            'RECTOR': 'Rector/Supervisor',
            'TEACHER': 'Profesor',
            'PARENT': 'Padre',
            'STUDENT': 'Estudiante',
            'DECE': 'Consejero DECE',
            'MEDICO': 'Médico Dispensario',
        };
        return names[role] || role;
    };

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />

            <div className="flex flex-wrap justify-between items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Gestión de Usuarios</h1>
                    <p className="text-slate-500">Administra profesores, estudiantes y personal.</p>
                </div>
                <button
                    onClick={() => { setEditingId(null); setFormData(initialFormState); setIsModalOpen(true); }}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={18} /> Nuevo Usuario
                </button>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap gap-4 bg-white p-4 rounded-xl shadow-sm border border-slate-200">
                <div className="flex-1 min-w-[200px] relative">
                    <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Buscar por nombre, email..."
                        className="input-modern pl-10 w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Filter size={18} className="text-slate-400" />
                    <select
                        className="input-modern"
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                    >
                        <option value="ALL">Todos los Roles</option>
                        <option value="ADMIN">Administrador Superior</option>
                        <option value="LOCAL_ADMIN">Administrador Local</option>
                        <option value="ACCOUNTANT">Contabilidad</option>
                        <option value="RECTOR">Supervisor/Rector</option>
                        <option value="TEACHER">Profesor</option>
                        <option value="PARENT">Padre/Representante</option>
                        <option value="STUDENT">Estudiante</option>
                        <option value="DECE">Consejero DECE</option>
                        <option value="MEDICO">Médico</option>
                    </select>
                </div>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50 text-slate-500 font-medium">
                            <tr>
                                <th className="p-4">Usuario</th>
                                <th className="p-4">Rol</th>
                                <th className="p-4">Email / Info</th>
                                <th className="p-4 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {loading ? (
                                <tr>
                                    <td colSpan="4" className="p-8 text-center text-slate-400">Cargando usuarios...</td>
                                </tr>
                            ) : filteredUsers.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="p-8 text-center text-slate-400">No se encontraron usuarios.</td>
                                </tr>
                            ) : filteredUsers.map((u) => (
                                <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs">
                                                {u.first_name?.[0] || u.username[0]}
                                            </div>
                                            <div>
                                                <p className="font-semibold text-slate-800">{u.first_name} {u.last_name}</p>
                                                <p className="text-xs text-slate-500">@{u.username}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getRoleBadge(u.role)}`}>
                                            {getRoleName(u.role)}
                                        </span>
                                    </td>
                                    <td className="p-4 text-slate-600">
                                        <p>{u.email}</p>
                                        <p className="text-xs text-slate-400">{u.phone}</p>
                                    </td>
                                    <td className="p-4 text-right">
                                        <button
                                            onClick={() => handleEdit(u)}
                                            className="text-indigo-400 hover:text-indigo-600 p-2 hover:bg-indigo-50 rounded-lg transition-colors mr-2"
                                            title="Editar"
                                        >
                                            <Edit size={18} />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(u.id)}
                                            className="text-red-400 hover:text-red-600 p-2 hover:bg-red-50 rounded-lg transition-colors"
                                            title="Eliminar"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50 sticky top-0">
                            <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Editar Usuario' : 'Crear Nuevo Usuario'}</h2>
                            <button onClick={closeModal} className="text-slate-400 hover:text-slate-600">
                                <X size={24} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6 space-y-6">
                            {/* Personal Info */}
                            <div>
                                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Información Personal</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {/* Campos Básicos */}
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Primer Nombre</label>
                                        <input type="text" required className="input-modern w-full" value={formData.first_name} onChange={(e) => setFormData({ ...formData, first_name: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Segundo Nombre</label>
                                        <input type="text" className="input-modern w-full" value={formData.second_name} onChange={(e) => setFormData({ ...formData, second_name: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Primer Apellido</label>
                                        <input type="text" required className="input-modern w-full" value={formData.last_name} onChange={(e) => setFormData({ ...formData, last_name: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Segundo Apellido</label>
                                        <input type="text" className="input-modern w-full" value={formData.second_surname} onChange={(e) => setFormData({ ...formData, second_surname: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Cédula</label>
                                        <input type="text" className="input-modern w-full" value={formData.cedula} onChange={(e) => setFormData({ ...formData, cedula: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Sexo</label>
                                        <select className="input-modern w-full" value={formData.gender} onChange={e => setFormData({ ...formData, gender: e.target.value })}>
                                            <option value="">Seleccione...</option>
                                            <option value="M">Masculino</option>
                                            <option value="F">Femenino</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Nacionalidad</label>
                                        <input type="text" className="input-modern w-full" value={formData.nationality} onChange={(e) => setFormData({ ...formData, nationality: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Estado Civil</label>
                                        <select className="input-modern w-full" value={formData.civil_status} onChange={e => setFormData({ ...formData, civil_status: e.target.value })}>
                                            <option value="">Seleccione...</option>
                                            <option value="SOLTERO">Soltero/a</option>
                                            <option value="CASADO">Casado/a</option>
                                            <option value="DIVORCIADO">Divorciado/a</option>
                                            <option value="VIUDO">Viudo/a</option>
                                            <option value="UNION_LIBRE">Unión Libre</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Fecha de Nacimiento</label>
                                        <input type="date" className="input-modern w-full" value={formData.birth_date} onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })} />
                                    </div>
                                </div>
                            </div>

                            {/* Account Info */}
                            <div className="pt-4 border-t border-slate-100">
                                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Cuenta de Usuario</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Usuario (Login)</label>
                                        <input type="text" required className="input-modern w-full" value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                                        <input type="email" className="input-modern w-full" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Rol</label>
                                        <select className="input-modern w-full" value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })}>
                                            <option value="STUDENT">Estudiante</option>
                                            <option value="TEACHER">Profesor</option>
                                            <option value="PARENT">Padre/Representante</option>
                                            <option value="DECE">Consejero DECE</option>
                                            <option value="MEDICO">Médico Dispensario</option>
                                            <option value="ACCOUNTANT">Contabilidad</option>
                                            <option value="RECTOR">Supervisor/Rector</option>
                                            {(user?.role === 'ADMIN' || user?.role === 'LOCAL_ADMIN') && <option value="LOCAL_ADMIN">Administrador Local</option>}
                                            {user?.role === 'ADMIN' && <option value="ADMIN">Administrador Superior</option>}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Contraseña {editingId && <span className="font-normal text-xs text-slate-400">(Opcional)</span>}</label>
                                        <input type="password" className="input-modern w-full" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} />
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
                                            <p className="text-xs text-slate-500 mt-1">Si se deja vacío, se usará la institución activa actual.</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Contact & Extra */}
                            <div className="pt-4 border-t border-slate-100">
                                <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Contacto y Otros</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Teléfono</label>
                                        <input type="text" className="input-modern w-full" value={formData.phone} onChange={(e) => setFormData({ ...formData, phone: e.target.value })} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Foto de Perfil</label>
                                        <input type="file" accept="image/*" className="input-modern w-full text-sm file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" onChange={handleFileChange} />
                                    </div>
                                </div>
                                <div className="mt-4">
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Dirección</label>
                                    <textarea rows="2" className="input-modern w-full" value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })}></textarea>
                                </div>
                                <div className="mt-4">
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Observaciones</label>
                                    <textarea rows="2" className="input-modern w-full" value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })}></textarea>
                                </div>
                            </div>

                            <div className="pt-4 flex justify-end gap-3 border-t border-slate-100">
                                <button type="button" onClick={closeModal} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                                <button type="submit" className="btn-primary flex items-center gap-2">
                                    <Plus size={18} /> {editingId ? 'Actualizar' : 'Crear Usuario'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UsersPage;
