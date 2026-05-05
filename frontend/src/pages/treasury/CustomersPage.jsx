import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Search, User, X, Mail, Phone, MapPin, CreditCard, Building } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import treasuryService from '../../services/treasuryService';
import userService from '../../services/userService';
import { useAuthStore } from '../../context/authStore';

const CustomersPage = () => {
    const { activeInstitution, user } = useAuthStore();
    const [customers, setCustomers] = useState([]);
    const [institutions, setInstitutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    const initialFormState = {
        customer_type: 'INDIVIDUAL',
        identification: '',
        first_name: '',
        last_name: '',
        business_name: '',
        email: '',
        phone: '',
        address: '',
        institution: ''
    };

    const [formData, setFormData] = useState(initialFormState);

    useEffect(() => {
        loadCustomers();
        if (user?.role === 'ADMIN') {
            loadInstitutions();
        }
    }, [user, searchTerm]);

    const loadInstitutions = async () => {
        try {
            const data = await userService.getInstitutions();
            setInstitutions(data);
        } catch (error) {
            console.error(error);
        }
    };

    const loadCustomers = async () => {
        setLoading(true);
        try {
            const params = {};
            if (searchTerm) params.search = searchTerm;
            const data = await treasuryService.getCustomers(params);
            setCustomers(data);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar clientes");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!activeInstitution && !formData.institution) {
            toast.error("No hay una institución activa seleccionada.");
            return;
        }

        try {
            const payload = {
                ...formData,
                institution: parseInt(formData.institution || activeInstitution)
            };

            if (editingId) {
                await treasuryService.updateCustomer(editingId, payload);
                toast.success("Cliente actualizado");
            } else {
                await treasuryService.createCustomer(payload);
                toast.success("Cliente creado");
            }
            setIsModalOpen(false);
            setFormData(initialFormState);
            setEditingId(null);
            loadCustomers();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data
                ? Object.entries(error.response.data).map(([k, v]) => `${k}: ${v}`).join(', ')
                : "Error al guardar";
            toast.error(msg);
        }
    };

    const handleEdit = (item) => {
        setEditingId(item.id);
        setFormData({
            customer_type: item.customer_type,
            identification: item.identification,
            first_name: item.first_name,
            last_name: item.last_name || '',
            business_name: item.business_name || '',
            email: item.email,
            phone: item.phone || '',
            address: item.address,
            institution: item.institution
        });
        setIsModalOpen(true);
    };

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />

            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Base de Clientes</h1>
                    <p className="text-slate-500">Gestiona clientes académicos e independientes para facturación.</p>
                </div>
                <button
                    onClick={() => { setEditingId(null); setFormData(initialFormState); setIsModalOpen(true); }}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={18} /> Nuevo Cliente Individual / Empresa
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 text-slate-400" size={20} />
                    <input
                        type="text"
                        placeholder="Buscar por nombre, RUC o identificación..."
                        className="input-modern pl-10 w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {customers.map(item => (
                    <div key={item.id} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-4">
                            <div className={`p-3 rounded-lg ${item.customer_type === 'STUDENT' ? 'bg-indigo-50 text-indigo-600' : 'bg-green-50 text-green-600'}`}>
                                {item.customer_type === 'STUDENT' ? <User size={24} /> : <Building size={24} />}
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => handleEdit(item)} className="text-slate-400 hover:text-indigo-600">
                                    <Edit size={18} />
                                </button>
                            </div>
                        </div>
                        
                        <div className="mb-4">
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                                item.customer_type === 'STUDENT' ? 'bg-indigo-100 text-indigo-700' : 
                                item.customer_type === 'COMPANY' ? 'bg-amber-100 text-amber-700' :
                                item.customer_type === 'WALKIN' ? 'bg-slate-100 text-slate-700' :
                                'bg-green-100 text-green-700'
                            }`}>
                                {item.customer_type === 'STUDENT' ? 'Académico (Estudiante)' : 
                                 item.customer_type === 'COMPANY' ? 'Empresa / RUC' :
                                 item.customer_type === 'WALKIN' ? 'Consumidor Final' :
                                 'Individual'}
                            </span>
                        </div>

                        <h3 className="font-bold text-lg text-slate-800 mb-1">
                            {item.business_name || `${item.first_name} ${item.last_name}`}
                        </h3>
                        <p className="text-sm text-slate-500 flex items-center gap-2 mb-3">
                            <CreditCard size={14} /> {item.identification}
                        </p>

                        <div className="space-y-2 pt-3 border-t border-slate-50 text-sm text-slate-600">
                            <div className="flex items-center gap-2">
                                <Mail size={14} className="text-slate-400" /> {item.email}
                            </div>
                            {item.phone && (
                                <div className="flex items-center gap-2">
                                    <Phone size={14} className="text-slate-400" /> {item.phone}
                                </div>
                            )}
                            <div className="flex items-start gap-2">
                                <MapPin size={14} className="text-slate-400 mt-1 shrink-0" /> 
                                <span className="line-clamp-2">{item.address}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center sticky top-0 bg-white z-10">
                            <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Editar' : 'Nuevo'} Cliente</h2>
                            <button onClick={() => setIsModalOpen(false)}><X size={24} className="text-slate-400" /></button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                                <div>
                                    <label className="label-modern">Tipo de Cliente</label>
                                    <select
                                        className="input-modern w-full"
                                        value={formData.customer_type}
                                        onChange={(e) => setFormData({ ...formData, customer_type: e.target.value })}
                                        disabled={editingId && formData.customer_type === 'STUDENT'}
                                    >
                                        <option value="INDIVIDUAL">Individual (Persona Natural)</option>
                                        <option value="COMPANY">Empresa / RUC</option>
                                        <option value="WALKIN">Consumidor Final</option>
                                        {formData.customer_type === 'STUDENT' && <option value="STUDENT">Académico (Estudiante)</option>}
                                    </select>
                                </div>

                            {/* Institution Selector for Admin */}
                            {user?.role === 'ADMIN' && (
                                <div>
                                    <label className="label-modern">Institución</label>
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

                            <div className="grid grid-cols-2 gap-4">
                                <div className="col-span-2 md:col-span-1">
                                    <label className="label-modern">Identificación (RUC/Cédula)</label>
                                    <input type="text" required className="input-modern w-full" 
                                        value={formData.identification} onChange={e => setFormData({ ...formData, identification: e.target.value })} />
                                </div>
                                <div className="col-span-2 md:col-span-1">
                                    <label className="label-modern">Nombre Comercial / Empresa (Opcional)</label>
                                    <input type="text" className="input-modern w-full" 
                                        value={formData.business_name} onChange={e => setFormData({ ...formData, business_name: e.target.value })} />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label-modern">Nombres</label>
                                    <input type="text" required className="input-modern w-full" 
                                        value={formData.first_name} onChange={e => setFormData({ ...formData, first_name: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Apellidos</label>
                                    <input type="text" className="input-modern w-full" 
                                        value={formData.last_name} onChange={e => setFormData({ ...formData, last_name: e.target.value })} />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label-modern">Correo Electrónico</label>
                                    <input type="email" required className="input-modern w-full" 
                                        value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Teléfono</label>
                                    <input type="text" className="input-modern w-full" 
                                        value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} />
                                </div>
                            </div>

                            <div>
                                <label className="label-modern">Dirección de Facturación</label>
                                <textarea rows="2" required className="input-modern w-full" 
                                    value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })}></textarea>
                            </div>

                            <button type="submit" className="btn-primary w-full mt-4 py-3">
                                {editingId ? 'Actualizar Cliente' : 'Registrar Cliente'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CustomersPage;
