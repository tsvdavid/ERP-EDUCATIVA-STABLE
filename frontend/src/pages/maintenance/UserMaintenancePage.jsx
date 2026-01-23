import React, { useState, useEffect } from 'react';
import maintenanceService from '../../services/maintenanceService';
import { toast } from 'react-hot-toast';
import { Trash2, Search, RefreshCw, UserX } from 'lucide-react';

const UserMaintenancePage = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedUsers, setSelectedUsers] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const data = await maintenanceService.getUsersForMaintenance();
            setUsers(data);
        } catch (error) {
            console.error(error);
            toast.error('Error al cargar usuarios');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            setSelectedUsers(users.map(u => u.id));
        } else {
            setSelectedUsers([]);
        }
    };

    const handleSelectUser = (id) => {
        if (selectedUsers.includes(id)) {
            setSelectedUsers(selectedUsers.filter(uid => uid !== id));
        } else {
            setSelectedUsers([...selectedUsers, id]);
        }
    };

    const handleDelete = async () => {
        if (selectedUsers.length === 0) return;

        if (!window.confirm(`¿Está seguro de eliminar ${selectedUsers.length} usuarios? Esta acción no se puede deshacer.`)) {
            return;
        }

        try {
            setLoading(true);
            const response = await maintenanceService.deleteUsers(selectedUsers);
            toast.success(response.message);
            setSelectedUsers([]);
            fetchUsers();
        } catch (error) {
            console.error(error);
            toast.error('Error al eliminar usuarios');
        } finally {
            setLoading(false);
        }
    };

    const filteredUsers = users.filter(user =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Mantenimiento de Usuarios</h1>
                    <p className="text-slate-500">Gestión y eliminación masiva de cuentas de usuario.</p>
                </div>
                {selectedUsers.length > 0 && (
                    <button
                        onClick={handleDelete}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 shadow-lg shadow-red-500/30 transition-all"
                    >
                        <Trash2 size={18} />
                        Eliminar ({selectedUsers.length})
                    </button>
                )}
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row gap-4 justify-between items-center bg-slate-50/50">
                    <div className="relative w-full sm:w-96">
                        <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
                        <input
                            type="text"
                            placeholder="Buscar por nombre, usuario o email..."
                            className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 outline-none text-sm"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <button
                        onClick={fetchUsers}
                        className="p-2 text-slate-500 hover:bg-slate-200 rounded-lg transition-colors"
                        title="Recargar lista"
                    >
                        <RefreshCw size={20} />
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-500 uppercase bg-slate-50/80 border-b border-slate-200">
                            <tr>
                                <th className="p-4 w-4">
                                    <input
                                        type="checkbox"
                                        className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                                        checked={filteredUsers.length > 0 && selectedUsers.length === filteredUsers.length}
                                        onChange={handleSelectAll}
                                    />
                                </th>
                                <th className="px-6 py-3">Usuario</th>
                                <th className="px-6 py-3">Nombre Completo</th>
                                <th className="px-6 py-3">Rol</th>
                                <th className="px-6 py-3">Email</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {filteredUsers.length > 0 ? filteredUsers.map((user) => (
                                <tr key={user.id} className="hover:bg-slate-50/80 transition-colors">
                                    <td className="p-4">
                                        <input
                                            type="checkbox"
                                            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                                            checked={selectedUsers.includes(user.id)}
                                            onChange={() => handleSelectUser(user.id)}
                                        />
                                    </td>
                                    <td className="px-6 py-4 font-medium text-slate-900">{user.username}</td>
                                    <td className="px-6 py-4 text-slate-600">{user.first_name} {user.last_name}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold
                                            ${user.role === 'ADMIN' ? 'bg-purple-100 text-purple-700' :
                                                user.role === 'TEACHER' ? 'bg-blue-100 text-blue-700' :
                                                    user.role === 'STUDENT' ? 'bg-green-100 text-green-700' :
                                                        'bg-slate-100 text-slate-700'}`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-slate-500">{user.email}</td>
                                </tr>
                            )) : (
                                <tr>
                                    <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                                        {loading ? (
                                            <div className="flex justify-center"><RefreshCw className="animate-spin" /></div>
                                        ) : (
                                            <div className="flex flex-col items-center">
                                                <UserX size={48} className="text-slate-300 mb-2" />
                                                <p>No se encontraron usuarios</p>
                                            </div>
                                        )}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default UserMaintenancePage;
