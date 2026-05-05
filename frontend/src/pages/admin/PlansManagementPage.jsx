import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Check, X, Shield, Package } from 'lucide-react';
import { toast, Toaster } from 'react-hot-toast';
import subscriptionService from '../../services/subscriptionService';

const PlansManagementPage = () => {
    const [plans, setPlans] = useState([]);
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingPlan, setEditingPlan] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        base_price_monthly: '',
        base_price_yearly: '',
        is_active: true,
        included_modules: []
    });

    const loadData = async () => {
        try {
            setLoading(true);
            const [plansRes, modulesRes] = await Promise.all([
                subscriptionService.getPlans(),
                subscriptionService.getModules()
            ]);
            setPlans(plansRes);
            setModules(modulesRes);
        } catch (error) {
            toast.error("Error al cargar planes o módulos.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const openModal = (plan = null) => {
        if (plan) {
            setEditingPlan(plan);
            setFormData({
                name: plan.name,
                base_price_monthly: plan.base_price_monthly,
                base_price_yearly: plan.base_price_yearly,
                is_active: plan.is_active,
                included_modules: plan.included_modules || []
            });
        } else {
            setEditingPlan(null);
            setFormData({
                name: '',
                base_price_monthly: '',
                base_price_yearly: '',
                is_active: true,
                included_modules: []
            });
        }
        setIsModalOpen(true);
    };

    const handleModuleToggle = (moduleId) => {
        setFormData(prev => ({
            ...prev,
            included_modules: prev.included_modules.includes(moduleId)
                ? prev.included_modules.filter(id => id !== moduleId)
                : [...prev.included_modules, moduleId]
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingPlan) {
                await subscriptionService.updatePlan(editingPlan.id, formData);
                toast.success("Plan actualizado correctamente.");
            } else {
                await subscriptionService.createPlan(formData);
                toast.success("Plan creado correctamente.");
            }
            setIsModalOpen(false);
            loadData();
        } catch (error) {
            toast.error("Error al guardar el plan.");
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("¿Estás seguro de eliminar este plan?")) return;
        try {
            await subscriptionService.deletePlan(id);
            toast.success("Plan eliminado.");
            loadData();
        } catch (error) {
            toast.error("Error al eliminar el plan.");
        }
    };

    if (loading) return <div className="p-8 text-center text-slate-500 font-bold">Cargando catálogo comercial...</div>;

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-black text-slate-800 tracking-tight">Catálogo de <span className="text-indigo-600">Planes</span></h1>
                    <p className="text-slate-500">Define los paquetes comerciales y módulos incluidos.</p>
                </div>
                <button 
                    onClick={() => openModal()}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-2xl font-bold shadow-lg shadow-indigo-200 transition-all active:scale-95"
                >
                    <Plus size={20} strokeWidth={3} />
                    Nuevo Plan
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {plans.map(plan => (
                    <div key={plan.id} className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm hover:shadow-xl transition-all duration-300 relative overflow-hidden group">
                        <div className={`absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 rounded-full ${plan.is_active ? 'bg-emerald-50' : 'bg-slate-50'} group-hover:scale-150 transition-transform duration-500 opacity-50`}></div>
                        
                        <div className="relative">
                            <div className="flex justify-between items-start mb-4">
                                <div className={`p-3 rounded-2xl ${plan.is_active ? 'bg-indigo-50 text-indigo-600' : 'bg-slate-100 text-slate-400'}`}>
                                    <Package size={24} />
                                </div>
                                <div className="flex gap-1">
                                    <button onClick={() => openModal(plan)} className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-xl transition-colors"><Edit size={18} /></button>
                                    <button onClick={() => handleDelete(plan.id)} className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"><Trash2 size={18} /></button>
                                </div>
                            </div>

                            <h3 className="text-xl font-bold text-slate-800">{plan.name}</h3>
                            <div className="mt-4 flex items-baseline gap-1">
                                <span className="text-3xl font-black text-slate-900">${plan.base_price_monthly}</span>
                                <span className="text-slate-500 text-sm font-medium">/mes</span>
                            </div>
                            <p className="text-xs text-slate-400 font-bold uppercase tracking-widest mt-1">${plan.base_price_yearly} anual</p>

                            <div className="mt-6 space-y-2">
                                <p className="text-xs font-black text-slate-400 uppercase tracking-widest">Módulos Incluidos</p>
                                <div className="flex flex-wrap gap-2">
                                    {plan.included_modules_names?.length > 0 ? plan.included_modules_names.map(m => (
                                        <span key={m} className="px-3 py-1 bg-slate-100 text-slate-600 rounded-lg text-xs font-bold">{m}</span>
                                    )) : <span className="text-xs text-slate-400 italic">Sin módulos definidos</span>}
                                </div>
                            </div>

                            <div className="mt-6 flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${plan.is_active ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'}`}></div>
                                <span className={`text-xs font-black uppercase tracking-widest ${plan.is_active ? 'text-emerald-600' : 'text-slate-400'}`}>
                                    {plan.is_active ? 'Activo' : 'Inactivo'}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal Plan Form */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-[2rem] shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
                        <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                            <div>
                                <h2 className="text-2xl font-black text-slate-800">{editingPlan ? 'Editar Plan' : 'Nuevo Plan Comercial'}</h2>
                                <p className="text-slate-500 text-sm">Configura precios y accesos del paquete.</p>
                            </div>
                            <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-white rounded-full transition-colors"><X size={24} /></button>
                        </div>
                        
                        <form onSubmit={handleSubmit} className="p-8 space-y-6 overflow-y-auto flex-1">
                            <div className="grid grid-cols-2 gap-6">
                                <div className="col-span-2">
                                    <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Nombre del Plan</label>
                                    <input 
                                        type="text" required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-indigo-500 font-bold text-slate-700"
                                        placeholder="Ej: Plan Administrativo, Full, Académico"
                                        value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Precio Mensual ($)</label>
                                    <input 
                                        type="number" step="0.01" required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-indigo-500 font-bold text-slate-700"
                                        value={formData.base_price_monthly} onChange={e => setFormData({...formData, base_price_monthly: e.target.value})}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Precio Anual ($)</label>
                                    <input 
                                        type="number" step="0.01" required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 focus:ring-2 focus:ring-indigo-500 font-bold text-slate-700"
                                        value={formData.base_price_yearly} onChange={e => setFormData({...formData, base_price_yearly: e.target.value})}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Módulos Incluidos</label>
                                <div className="grid grid-cols-2 gap-3">
                                    {modules.map(mod => (
                                        <button
                                            key={mod.id}
                                            type="button"
                                            onClick={() => handleModuleToggle(mod.id)}
                                            className={`flex items-center justify-between px-5 py-3 rounded-2xl border-2 transition-all font-bold text-sm ${
                                                formData.included_modules.includes(mod.id)
                                                ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                                                : 'border-slate-100 bg-slate-50 text-slate-400 hover:border-slate-200'
                                            }`}
                                        >
                                            {mod.name}
                                            {formData.included_modules.includes(mod.id) && <Check size={16} strokeWidth={3} />}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
                                <input 
                                    type="checkbox" id="is_active" className="w-5 h-5 rounded-lg text-indigo-600 border-slate-300 focus:ring-indigo-500"
                                    checked={formData.is_active} onChange={e => setFormData({...formData, is_active: e.target.checked})}
                                />
                                <label htmlFor="is_active" className="text-sm font-bold text-slate-700">Plan activo y disponible para asignación</label>
                            </div>

                            <div className="flex gap-4 pt-4">
                                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 px-6 py-4 bg-slate-100 text-slate-600 rounded-2xl font-bold hover:bg-slate-200 transition-all">Cancelar</button>
                                <button type="submit" className="flex-1 px-6 py-4 bg-indigo-600 text-white rounded-2xl font-bold shadow-lg shadow-indigo-100 hover:bg-indigo-700 transition-all">Guardar Plan</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PlansManagementPage;
