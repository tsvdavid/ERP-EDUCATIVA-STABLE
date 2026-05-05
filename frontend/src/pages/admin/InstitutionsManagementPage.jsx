import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import userService from '../../services/userService';
import { 
    Building, 
    Plus, 
    Edit, 
    Trash2, 
    Search, 
    Globe, 
    Phone, 
    Mail,
    ArrowRight,
    MapPin,
    AlertCircle
} from 'lucide-react';
import { toast } from 'react-hot-toast';

const InstitutionsManagementPage = () => {
    const navigate = useNavigate();
    const [institutions, setInstitutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadInstitutions();
    }, []);

    const loadInstitutions = async () => {
        setLoading(true);
        try {
            const data = await userService.getInstitutions();
            setInstitutions(data);
        } catch (error) {
            console.error("Error loading institutions", error);
            toast.error("Error al cargar el listado de instituciones");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id, name) => {
        const isHardDelete = window.confirm(`¿Deseas realizar un BORRADO FORZADO de "${name}"?\n\nESTO ELIMINARÁ PERMANENTEMENTE:\n- Todos los usuarios\n- Registros contables\n- Calificaciones y asistencia\n- Configuración de facturación\n\nPresiona ACEPTAR para BORRADO PERMANENTE, o CANCELAR para intentar un borrado normal.`);
        
        if (isHardDelete) {
            try {
                toast.loading("Ejecutando borrado forzado cascada...");
                await userService.hardDeleteInstitution(id);
                toast.dismiss();
                toast.success("Institución y todos sus datos han sido purgados del sistema.");
                loadInstitutions();
            } catch (error) {
                toast.dismiss();
                console.error("Error hard deleting institution", error);
                const errorMsg = error.response?.data?.error || "Error en el borrado forzado";
                toast.error(errorMsg);
            }
            return;
        }

        if (!window.confirm(`¿Estás seguro de que deseas desactivar la institución "${name}"?`)) {
            return;
        }

        try {
            await userService.deleteInstitution(id);
            toast.success("Institución desactivada correctamente");
            loadInstitutions();
        } catch (error) {
            console.error("Error deleting institution", error);
            const errorMsg = error.response?.data?.error || "Error al desactivar la institución";
            toast.error(errorMsg);
        }
    };

    const filteredInstitutions = institutions.filter(inst => 
        inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inst.ruc?.includes(searchTerm)
    );

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                <p className="text-slate-500 font-medium">Cargando ecosistema institucional...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header section with Stats */}
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-black text-slate-800 tracking-tight">
                        Gestión Institucional <span className="text-indigo-600">Global</span>
                    </h1>
                    <p className="text-slate-500 mt-1">Administración centralizada de todos los tenants de la plataforma.</p>
                </div>
                <button 
                    onClick={() => navigate('/dashboard/admin/institutions/new')}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-xl font-bold shadow-lg shadow-indigo-200 transition-all active:scale-95"
                >
                    <Plus size={20} strokeWidth={3} />
                    Nueva Institución
                </button>
            </div>

            {/* Search/Filter Bar */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                    <input 
                        type="text" 
                        placeholder="Buscar por nombre o RUC..."
                        className="w-full pl-12 pr-4 py-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-indigo-500 text-slate-700 font-medium"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-lg text-sm font-bold">
                    {filteredInstitutions.length} Entidades registradas
                </div>
            </div>

            {/* Grid of Institutions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {filteredInstitutions.map((inst) => (
                    <div key={inst.id} className="group bg-white rounded-3xl p-6 border border-slate-100 shadow-sm hover:shadow-xl transition-all duration-300 relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-2 h-full bg-indigo-500 group-hover:w-3 transition-all"></div>
                        
                        <div className="flex gap-6">
                            {/* Logo context */}
                            <div className="w-24 h-24 bg-slate-100 rounded-2xl flex-shrink-0 overflow-hidden flex items-center justify-center p-2">
                                {inst.logo ? (
                                    <img src={inst.logo} alt={inst.name} className="w-full h-full object-contain" />
                                ) : (
                                    <Building className="text-slate-300" size={40} />
                                )}
                            </div>

                            <div className="flex-1 space-y-3">
                                <div>
                                    <div className="flex justify-between items-start">
                                        <h3 className="text-xl font-bold text-slate-800 leading-tight line-clamp-1">{inst.name}</h3>
                                        <div className="flex gap-1">
                                            <button 
                                                onClick={() => navigate(`/dashboard/admin/institutions/${inst.id}`)}
                                                className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                                title="Editar"
                                            >
                                                <Edit size={18} />
                                            </button>
                                            <button 
                                                onClick={() => handleDelete(inst.id, inst.name)}
                                                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                                                title="Eliminar"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    </div>
                                    <p className="text-indigo-600 text-xs font-black uppercase tracking-widest mt-1">
                                        RUC: {inst.ruc || 'No definido'}
                                    </p>
                                </div>

                                <div className="grid grid-cols-2 gap-y-2 text-sm text-slate-500">
                                    <div className="flex items-center gap-2">
                                        <Phone size={14} className="text-slate-400" />
                                        {inst.phone || 'N/A'}
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <Mail size={14} className="text-slate-400" />
                                        <span className="truncate">{inst.email || 'N/A'}</span>
                                    </div>
                                    <div className="flex items-center gap-2 col-span-2">
                                        <MapPin size={14} className="text-slate-400" />
                                        <span className="truncate">{inst.address || 'Sin dirección registrada'}</span>
                                    </div>
                                </div>

                                <div className="pt-2 flex justify-between items-center border-t border-slate-50">
                                    <span className="text-[10px] text-slate-400">ID SISTEMA: #{inst.id}</span>
                                    <button 
                                        className="text-xs font-bold text-indigo-600 flex items-center gap-1 hover:gap-2 transition-all p-1"
                                        onClick={() => navigate(`/dashboard/admin/institutions/${inst.id}`)}
                                    >
                                        Detalles Completos <ArrowRight size={14} />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {inst.ruc === '' && (
                            <div className="mt-4 flex items-center gap-2 p-2 bg-yellow-50 text-yellow-700 text-[10px] font-bold rounded-lg uppercase">
                                <AlertCircle size={14} />
                                Configuración incompleta: RUC faltante
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {filteredInstitutions.length === 0 && (
                <div className="text-center py-20 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                    <Building className="mx-auto text-slate-300 mb-4" size={60} />
                    <p className="text-slate-500 font-medium">No se encontraron instituciones que coincidan con tu búsqueda.</p>
                </div>
            )}
        </div>
    );
};

export default InstitutionsManagementPage;
