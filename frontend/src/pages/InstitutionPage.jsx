import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import userService from '../services/userService';
import { Building, Save, ArrowLeft, Globe, ShieldCheck, Mail, MapPin, Phone, Hash, Link as LinkIcon, FileCheck } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../context/authStore';

const InstitutionPage = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuthStore();
    const [loading, setLoading] = useState(true);
    const [formData, setFormData] = useState({
        name: '',
        address: '',
        phone: '',
        email: '',
        website: '',
        logo: null,
        ruc: '',
        establishment_code: '001',
        emission_point: '001',
        special_taxpayer_number: '',
        obligado_contabilidad: false,
        sri_environment: 1
    });
    const [exists, setExists] = useState(false);
    const isNew = !id && window.location.pathname.includes('/new');

    useEffect(() => {
        if (!isNew) {
            loadInstitution();
        } else {
            setLoading(false);
            setExists(false);
        }
    }, [id]);

    const loadInstitution = async () => {
        setLoading(true);
        try {
            if (id) {
                // Admin Global editing specific institution
                const data = await userService.getInstitutionById(id);
                setFormData(data);
                setExists(true);
            } else {
                // Rector loading their own institution (fallback list filtered by backend)
                const data = await userService.getInstitutions();
                if (data && data.length > 0) {
                    // Logic: The backend already filters this for the user. We take the first one available.
                    setFormData(data[0]);
                    setExists(true);
                } else {
                    setExists(false);
                }
            }
        } catch (error) {
            console.error("Error loading institution", error);
            toast.error("Error al cargar información institucional");
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFormData({ ...formData, logo: e.target.files[0] });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const toastId = toast.loading('Guardando configuración...');
        try {
            const data = new FormData();
            
            // Clonamos el estado para poder forzar campos vacíos u opcionales
            const payload = { ...formData };
            if (!payload.address) payload.address = "No especificado";
            if (!payload.phone) payload.phone = "0000000000";
            if (!payload.email) payload.email = "admin@institucion.local";

            Object.keys(payload).forEach(key => {
                if (key === 'logo') {
                    if (payload.logo instanceof File) {
                        data.append('logo', payload.logo);
                    }
                } else if (payload[key] !== null && payload[key] !== undefined) {
                    data.append(key, payload[key]);
                }
            });

            if (exists && !isNew) {
                const targetId = id || formData.id;
                await userService.updateInstitution(targetId, data);
                toast.success('Institución actualizada con éxito', { id: toastId });
            } else {
                await userService.createInstitution(data);
                toast.success('Institución creada con éxito', { id: toastId });
                if (user.role === 'ADMIN') {
                    navigate('/dashboard/admin/institutions');
                }
            }
            if (!isNew) loadInstitution();
        } catch (error) {
            console.error(error);
            toast.error('Error al guardar: ' + (error.response?.data?.detail || 'Algo salió mal'), { id: toastId });
        }
    };

    const canEdit = user?.role === 'ADMIN' || user?.role === 'RECTOR';

    if (loading) return (
        <div className="flex flex-col items-center justify-center p-20 space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            <p className="text-slate-500 font-bold tracking-widest animate-pulse">SINCRONIZANDO ECOSISTEMA...</p>
        </div>
    );

    return (
        <div className="max-w-6xl mx-auto space-y-8 pb-12">
            {/* Header / Toolbar */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-white p-8 rounded-[2rem] shadow-sm border border-slate-100 gap-6">
                <div className="flex items-center gap-6">
                    <button 
                        onClick={() => navigate(-1)}
                        className="p-4 bg-slate-50 hover:bg-slate-100 text-slate-500 rounded-2xl transition-all active:scale-95"
                    >
                        <ArrowLeft size={24} />
                    </button>
                    <div>
                        <div className="flex items-center gap-3">
                             <h1 className="text-3xl font-black text-slate-800 tracking-tight">
                                {isNew ? 'Nueva Institución' : formData.name || 'Configuración'}
                            </h1>
                            {exists && (
                                <span className="bg-emerald-100 text-emerald-700 text-[10px] px-3 py-1 rounded-full font-black uppercase tracking-tighter shadow-sm shadow-emerald-100">Activa</span>
                            )}
                        </div>
                        <p className="text-slate-400 text-xs font-black uppercase tracking-[0.2em] mt-1">
                            {id ? `ID NODO: #${id}` : 'Perfil Institucional Operativo'}
                        </p>
                    </div>
                </div>
                
                <div className="flex items-center gap-4 py-2 px-6 bg-indigo-50/50 rounded-2xl border border-indigo-100">
                    <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center text-indigo-600">
                        <Building size={20} />
                    </div>
                    <div>
                        <p className="text-[10px] font-black text-indigo-600 uppercase tracking-tighter">Modo de Administración</p>
                        <p className="text-sm font-bold text-slate-700">
                            {user.role === 'ADMIN' ? 'Control de Plataforma' : 'Gestión Local'}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Lateral: Brand & Summary */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-white rounded-[2.5rem] p-8 border border-slate-100 shadow-sm text-center relative overflow-hidden group">
                        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <Building size={160} />
                        </div>
                        
                        <div className="relative inline-block mb-8">
                            <div className="w-48 h-48 bg-slate-50 rounded-[3rem] flex items-center justify-center overflow-hidden border-8 border-white shadow-2xl relative z-10">
                                {formData.logo && typeof formData.logo === 'string' ? (
                                    <img src={formData.logo} alt="Logo" className="w-full h-full object-contain" />
                                ) : (
                                    <Building size={80} className="text-slate-200" />
                                )}
                            </div>
                            {canEdit && (
                                <label className="absolute -bottom-2 -right-2 p-4 bg-indigo-600 text-white rounded-[1.5rem] shadow-xl cursor-pointer hover:bg-indigo-700 transition-all active:scale-90 hover:rotate-6 z-20">
                                    <Globe size={24} />
                                    <input type="file" accept="image/*" className="hidden" onChange={handleFileChange} />
                                </label>
                            )}
                        </div>
                        <h2 className="text-2xl font-black text-slate-800 leading-tight mb-2 line-clamp-2">{formData.name || 'Nombre Entidad'}</h2>
                        <div className="flex flex-col items-center gap-1 mb-8">
                             <div className="flex items-center gap-2 text-slate-400 font-bold text-xs uppercase tracking-widest">
                                <Hash size={14} />
                                RUC: {formData.ruc || 'Pendiente'}
                             </div>
                        </div>

                        <div className="grid grid-cols-1 gap-3 pt-6 border-t border-slate-50">
                            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl text-left">
                                <Mail size={16} className="text-indigo-600" />
                                <span className="text-xs font-bold text-slate-600 truncate">{formData.email || 'Sin correo'}</span>
                            </div>
                            <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-2xl text-left">
                                <Phone size={16} className="text-indigo-600" />
                                <span className="text-xs font-bold text-slate-600">{formData.phone || 'Sin teléfono'}</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-[2.5rem] p-8 text-white shadow-2xl shadow-indigo-200 relative overflow-hidden group">
                        <ShieldCheck className="absolute -right-8 -bottom-8 text-indigo-800/30 w-48 h-48 group-hover:scale-110 transition-transform duration-700" />
                        <div className="relative z-10">
                            <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center mb-4">
                                <FileCheck size={24} className="text-indigo-300" />
                            </div>
                            <h4 className="font-black text-indigo-300 text-xs uppercase tracking-[0.2em] mb-3">Integridad SaaS</h4>
                            <p className="text-sm text-indigo-50 leading-relaxed font-medium">
                                Los cambios en esta sección son estructurales. La correcta configuración del RUC y puntos de emisión es vital para la interoperabilidad con el SRI y pasarelas de pago.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Main: Detailed Form */}
                <div className="lg:col-span-8 bg-white rounded-[2.5rem] p-10 lg:p-12 border border-slate-100 shadow-sm">
                    <form onSubmit={handleSubmit} className="space-y-10">
                        {/* Section 1: Identificación */}
                        <div>
                            <div className="flex justify-between items-center mb-8 border-b border-slate-50 pb-4">
                                <h3 className="text-xl font-black text-slate-800 flex items-center gap-4">
                                    <span className="w-10 h-10 bg-indigo-600 text-white rounded-xl flex items-center justify-center shadow-lg shadow-indigo-100">1</span>
                                    Identificación de Entidad
                                </h3>
                                <div className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Información Fiscal</div>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Razón Social</label>
                                    <input required readOnly={!canEdit} type="text" placeholder="Nombre completo comercial..." className="input-modern w-full font-bold md:text-lg focus:shadow-xl focus:shadow-indigo-50 transition-all border-slate-100" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Registro Único (RUC)</label>
                                    <div className="relative">
                                        <Hash className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                                        <input required readOnly={!canEdit} type="text" placeholder="1790000000001" className="input-modern w-full pl-12 font-bold tracking-widest border-slate-100" value={formData.ruc} onChange={e => setFormData({ ...formData, ruc: e.target.value })} />
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Cód. Establecimiento</label>
                                    <input readOnly={!canEdit} type="text" maxLength={3} placeholder="001" className="input-modern w-full font-bold text-center border-slate-100" value={formData.establishment_code} onChange={e => setFormData({ ...formData, establishment_code: e.target.value })} />
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Punto de Emisión</label>
                                    <input readOnly={!canEdit} type="text" maxLength={3} placeholder="001" className="input-modern w-full font-bold text-center border-slate-100" value={formData.emission_point} onChange={e => setFormData({ ...formData, emission_point: e.target.value })} />
                                </div>
                            </div>
                        </div>

                        {/* Section 2: Conectividad */}
                        <div>
                            <div className="flex justify-between items-center mb-8 border-b border-slate-50 pb-4">
                                <h3 className="text-xl font-black text-slate-800 flex items-center gap-4">
                                    <span className="w-10 h-10 bg-indigo-600 text-white rounded-xl flex items-center justify-center shadow-lg shadow-indigo-100">2</span>
                                    Canales de Conectividad
                                </h3>
                                <div className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Global Reach</div>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Correo Corporativo</label>
                                    <div className="relative group">
                                        <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-indigo-600 transition-colors" size={18} />
                                        <input readOnly={!canEdit} type="email" placeholder="admin@institucion.edu.ec" className="input-modern w-full pl-12 border-slate-100" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Teléfono Central</label>
                                    <div className="relative group">
                                        <Phone className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-indigo-600 transition-colors" size={18} />
                                        <input readOnly={!canEdit} type="text" placeholder="+593 9 000 0000" className="input-modern w-full pl-12 border-slate-100" value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} />
                                    </div>
                                </div>
                                <div className="md:col-span-2 space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Dirección Matriz</label>
                                    <div className="relative group">
                                        <MapPin className="absolute left-4 top-4 text-slate-300 group-focus-within:text-indigo-600 transition-colors" size={18} />
                                        <textarea readOnly={!canEdit} rows="3" placeholder="Calle principal, número y referencia..." className="input-modern w-full pl-12 pt-4 border-slate-100" value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} />
                                    </div>
                                </div>
                                <div className="md:col-span-2 space-y-3">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] ml-1">Presencia Digital (Website)</label>
                                    <div className="relative group">
                                        <LinkIcon className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-indigo-600 transition-colors" size={18} />
                                        <input readOnly={!canEdit} type="url" placeholder="https://www.misitioschool.edu.ec" className="input-modern w-full pl-12 border-slate-100" value={formData.website} onChange={e => setFormData({ ...formData, website: e.target.value })} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {canEdit && (
                            <div className="pt-8 flex justify-end">
                                <button type="submit" className="group relative bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-4 px-12 py-5 rounded-[2rem] text-xl font-black shadow-2xl shadow-indigo-200 transition-all active:scale-95">
                                    <div className="absolute inset-0 bg-white/10 rounded-[2rem] scale-x-0 group-hover:scale-x-100 transition-transform origin-left duration-500"></div>
                                    <Save size={24} strokeWidth={3} className="relative z-10" />
                                    <span className="relative z-10">{isNew ? 'CREAR ENTIDAD' : 'ACTUALIZAR NODO'}</span>
                                </button>
                            </div>
                        )}
                    </form>
                </div>
            </div>
        </div>
    );
};

export default InstitutionPage;
