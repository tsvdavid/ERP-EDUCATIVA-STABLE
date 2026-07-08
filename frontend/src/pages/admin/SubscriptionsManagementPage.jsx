import React, { useState, useEffect } from 'react';
import { 
    Search, 
    Filter, 
    MoreVertical, 
    Pause, 
    Play, 
    XCircle, 
    Calendar, 
    History, 
    Layout, 
    CreditCard,
    ChevronRight,
    AlertTriangle,
    CheckCircle2,
    Plus,
    DollarSign,
    Zap
} from 'lucide-react';
import { toast, Toaster } from 'react-hot-toast';
import subscriptionService from '../../services/subscriptionService';
import ChangePlanModal from '../../components/ChangePlanModal';

const SubscriptionsManagementPage = () => {
    const [subscriptions, setSubscriptions] = useState([]);
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [institutionsWithoutSub, setInstitutionsWithoutSub] = useState([]);
    
    // Modal states
    const [selectedSub, setSelectedSub] = useState(null);
    const [isDetailOpen, setIsDetailOpen] = useState(false);
    const [isActionOpen, setIsActionOpen] = useState(false);
    const [isNewSubModalOpen, setIsNewSubModalOpen] = useState(false);
    const [isChangePlanOpen, setIsChangePlanOpen] = useState(false);
    const [changePlanLoading, setChangePlanLoading] = useState(false);
    const [actionType, setActionType] = useState(''); 
    const [actionData, setActionData] = useState({ date: '', plan_id: '' });
    const [changePlanData, setChangePlanData] = useState({ plan_id: '' });

    const loadData = async () => {
        try {
            setLoading(true);
            const [subsRes, plansRes, noSubRes] = await Promise.all([
                subscriptionService.getSubscriptions(),
                subscriptionService.getPlans(),
                subscriptionService.getInstitutionsWithoutSubscription()
            ]);
            setSubscriptions(subsRes);
            setPlans(plansRes);
            setInstitutionsWithoutSub(noSubRes);
        } catch (error) {
            toast.error("Error al cargar datos del sistema.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const openDetail = async (sub) => {
        try {
            const detail = await subscriptionService.getSubscription(sub.id);
            setSelectedSub(detail);
            setIsDetailOpen(true);
        } catch (error) {
            toast.error("Error al cargar el detalle de la suscripción.");
        }
    };

    const handleAction = async (type, sub) => {
        setActionType(type);
        setSelectedSub(sub);
        if (type === 'edit-dates') {
            setActionData({ date: sub.next_billing_date });
        } else if (type === 'confirm-payment') {
            setActionData({ amount: sub.monthly_fee, months_to_extend: 1, notes: '' });
        }
        setIsActionOpen(true);
    };

    const submitAction = async (e) => {
        e.preventDefault();
        try {
            if (actionType === 'edit-dates') {
                await subscriptionService.editDates(selectedSub.id, actionData.date);
            } else if (actionType === 'confirm-payment') {
                await subscriptionService.confirmPayment(selectedSub.id, actionData);
            }
            toast.success("Operación completada con éxito.");
            setIsActionOpen(false);
            loadData();
        } catch (error) {
            toast.error("Error al ejecutar la acción.");
        }
    };

    const openChangePlanModal = async (sub) => {
        try {
            const detail = await subscriptionService.getSubscription(sub.id);
            setSelectedSub(detail);
            setChangePlanData({
                plan_id: String(sub.plan || ''),
            });
            setIsChangePlanOpen(true);
        } catch (error) {
            toast.error('Error al cargar detalle para cambio de plan.');
        }
    };

    const submitChangePlan = async () => {
        if (!selectedSub?.id || !changePlanData.plan_id) {
            toast.error('Debe seleccionar un plan.');
            return;
        }

        if (!window.confirm('¿Está seguro de cambiar el plan de esta institución?')) {
            return;
        }

        try {
            setChangePlanLoading(true);
            await subscriptionService.changePlan(
                selectedSub.id,
                changePlanData.plan_id
            );
            toast.success('Plan actualizado correctamente.');
            setIsChangePlanOpen(false);
            loadData();
        } catch (error) {
            toast.error(error?.response?.data?.message || 'Error al cambiar el plan.');
        } finally {
            setChangePlanLoading(false);
        }
    };

    const runStatusAction = async (id, action) => {
        if (!window.confirm(`¿Seguro que deseas ejecutar ${action} sobre esta suscripción?`)) return;
        try {
            if (action === 'suspend') await subscriptionService.suspendSubscription(id, "Suspensión manual");
            if (action === 'reactivate') await subscriptionService.reactivateSubscription(id);
            if (action === 'cancel') await subscriptionService.cancelSubscription(id);
            toast.success("Estado actualizado.");
            loadData();
        } catch (error) {
            toast.error("Error al actualizar el estado.");
        }
    };

    const handleCreateSub = async (e) => {
        e.preventDefault();
        try {
            await subscriptionService.createSubscription(actionData);
            toast.success("Suscripción creada manualmente.");
            setIsNewSubModalOpen(false);
            loadData();
        } catch (error) {
            toast.error("Error al crear suscripción.");
        }
    };

    const filteredSubs = subscriptions.filter(s => 
        s.institution_name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) return <div className="p-8 text-center text-slate-500 font-bold">Cargando ecosistema de suscripciones...</div>;

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-black text-slate-800 tracking-tight">Gestión de <span className="text-indigo-600">Suscripciones</span></h1>
                    <p className="text-slate-500">Administra planes, fechas de corte y accesos de instituciones.</p>
                </div>
                <div className="bg-white p-1 rounded-2xl shadow-sm border border-slate-100 flex gap-1">
                    <button className="px-4 py-2 bg-indigo-50 text-indigo-700 rounded-xl text-xs font-black uppercase tracking-widest">Todos</button>
                    <button className="px-4 py-2 text-slate-400 hover:bg-slate-50 rounded-xl text-xs font-black uppercase tracking-widest">En Mora</button>
                    <button className="px-4 py-2 text-slate-400 hover:bg-slate-50 rounded-xl text-xs font-black uppercase tracking-widest">Suspendidos</button>
                </div>
                <button 
                    onClick={() => setIsNewSubModalOpen(true)}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-3 rounded-2xl font-bold shadow-lg shadow-indigo-100 transition-all active:scale-95 ml-4"
                >
                    <Plus size={20} strokeWidth={3} />
                    Nueva Suscripción
                </button>
            </div>

            {/* Search Bar */}
            <div className="bg-white p-4 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                    <input 
                        type="text" placeholder="Buscar por institución..."
                        className="w-full pl-12 pr-4 py-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-indigo-500 text-slate-700 font-bold"
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
                    />
                </div>
                <button className="p-3 bg-slate-50 text-slate-400 rounded-xl hover:bg-slate-100 transition-colors"><Filter size={20} /></button>
            </div>

            {/* Subscriptions Table */}
            <div className="bg-white rounded-3xl shadow-sm border border-slate-100">
                <div className="overflow-x-auto">
                    <table className="w-full min-w-[980px] text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50/50 border-b border-slate-100">
                                <th className="px-6 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Institución</th>
                                <th className="px-6 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Plan Actual</th>
                                <th className="px-6 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Estado</th>
                                <th className="px-6 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Vencimiento / Corte</th>
                                <th className="px-6 py-4 text-xs font-black text-slate-400 uppercase tracking-widest">Días Libres</th>
                                <th className="px-6 py-4 min-w-[260px] text-xs font-black text-slate-400 uppercase tracking-widest text-right sticky right-0 bg-slate-50/95 z-10">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                            {filteredSubs.map(sub => (
                                <tr key={sub.id} className="hover:bg-slate-50/50 transition-colors group">
                                    <td className="px-6 py-5">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center text-slate-400 font-bold">
                                                {sub.institution_name.charAt(0)}
                                            </div>
                                            <div>
                                                <p className="font-bold text-slate-800">{sub.institution_name}</p>
                                                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest">ID: #{sub.id}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <span className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-bold">{sub.plan_name || 'Personalizado'}</span>
                                        <p className="text-[10px] text-slate-400 font-bold mt-1 uppercase">{sub.billing_cycle_display} - ${sub.monthly_fee}</p>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className="flex items-center gap-2">
                                            <div className={`w-2 h-2 rounded-full ${
                                                sub.status === 'ACTIVE' || sub.status === 'TRIAL_ACTIVE' ? 'bg-emerald-500' : 
                                                sub.status === 'SUSPENDED' ? 'bg-rose-500' : 'bg-amber-500'
                                            }`}></div>
                                            <span className={`text-xs font-black uppercase tracking-widest ${
                                                sub.status === 'ACTIVE' || sub.status === 'TRIAL_ACTIVE' ? 'text-emerald-600' : 
                                                sub.status === 'SUSPENDED' ? 'text-rose-600' : 'text-amber-600'
                                            }`}>{sub.status}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-5">
                                        <p className="text-sm font-bold text-slate-700">{sub.next_billing_date}</p>
                                        <p className="text-[10px] text-slate-400 font-bold uppercase">Exp: {sub.expiration_date || 'N/A'}</p>
                                    </td>
                                    <td className="px-6 py-5">
                                        <div className={`text-sm font-black ${sub.days_remaining < 7 ? 'text-rose-600 animate-pulse' : 'text-slate-700'}`}>
                                            {sub.days_remaining} días
                                        </div>
                                    </td>
                                    <td className="px-6 py-5 text-right min-w-[260px] sticky right-0 bg-white z-10">
                                        <div className="flex justify-end gap-2 flex-nowrap">
                                            <button onClick={() => openDetail(sub)} className="p-2 text-slate-400 hover:text-indigo-600 bg-slate-100 rounded-lg" title="Auditoría/Detalle"><History size={16} /></button>
                                            {sub.status === 'TRIAL_ACTIVE' && (
                                                <button onClick={async () => {
                                                    if(window.confirm('¿Convertir prueba a suscripción activa de pago?')) {
                                                        await subscriptionService.convertTrial(sub.id);
                                                        toast.success('Suscripción activada.');
                                                        loadData();
                                                    }
                                                }} className="p-2 text-slate-400 hover:text-emerald-600 bg-slate-100 rounded-lg" title="Convertir a Pago"><Zap size={16} /></button>
                                            )}
                                            {sub.status !== 'SUSPENDED' ? (
                                                <button onClick={() => runStatusAction(sub.id, 'suspend')} className="p-2 text-slate-400 hover:text-amber-600 bg-slate-100 rounded-lg" title="Suspender"><Pause size={16} /></button>
                                            ) : (
                                                <button onClick={() => runStatusAction(sub.id, 'reactivate')} className="p-2 text-slate-400 hover:text-emerald-600 bg-slate-100 rounded-lg" title="Reactivar"><Play size={16} /></button>
                                            )}
                                            <button onClick={() => handleAction('confirm-payment', sub)} className="p-2 text-slate-400 hover:text-emerald-600 bg-slate-100 rounded-lg" title="Confirmar Pago (Renovar)"><DollarSign size={16} /></button>
                                            <button onClick={() => openChangePlanModal(sub)} className="p-2 text-slate-400 hover:text-indigo-600 bg-slate-100 rounded-lg" title="Cambiar Plan"><CreditCard size={16} /></button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Detail Modal (Audit/History) */}
            {isDetailOpen && selectedSub && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-[2rem] shadow-2xl max-w-4xl w-full max-h-[85vh] overflow-hidden flex flex-col">
                        <div className="p-8 border-b border-slate-100 flex justify-between items-center">
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center text-2xl font-black">
                                    {selectedSub?.institution_name?.charAt(0) || '?'}
                                </div>
                                <div>
                                    <h2 className="text-2xl font-black text-slate-800">{selectedSub?.institution_name || '-'}</h2>
                                    <p className="text-slate-500 font-medium">Historial y Auditoría de Suscripción</p>
                                </div>
                            </div>
                            <button onClick={() => setIsDetailOpen(false)} className="p-3 hover:bg-slate-50 rounded-full transition-colors"><XCircle size={24} className="text-slate-300" /></button>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto p-8 grid grid-cols-1 md:grid-cols-3 gap-8">
                            {/* Stats */}
                            <div className="md:col-span-1 space-y-6">
                                <div className="p-6 bg-slate-50 rounded-3xl">
                                    <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Resumen Actual</p>
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-slate-500">Plan</span>
                                            <span className="text-sm font-bold text-slate-800">{selectedSub?.plan_name || '-'}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-slate-500">Desde</span>
                                            <span className="text-sm font-bold text-slate-800">{selectedSub?.start_date || '-'}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-slate-500">Monto Mensual</span>
                                            <span className="text-sm font-bold text-indigo-600">${selectedSub?.monthly_fee || '0'}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="p-6 bg-slate-50 rounded-3xl">
                                    <p className="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Módulos Activos</p>
                                    <div className="flex flex-wrap gap-2">
                                        {(selectedSub?.modules_detail || []).length > 0 ? (
                                            selectedSub.modules_detail.map(m => (
                                                <span key={m.id} className="px-3 py-1 bg-white text-slate-600 rounded-lg text-[10px] font-black uppercase border border-slate-100">{m.module_name}</span>
                                            ))
                                        ) : (
                                            <p className="text-[10px] text-slate-400 font-bold uppercase italic">No hay módulos asignados</p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Logs */}
                            <div className="md:col-span-2 space-y-4">
                                <h3 className="text-sm font-black text-slate-400 uppercase tracking-widest flex items-center gap-2"><History size={16} /> Auditoría de Eventos</h3>
                                <div className="space-y-3">
                                    {(selectedSub?.audit_logs || []).length > 0 ? (
                                        selectedSub.audit_logs.map(log => (
                                            <div key={log.id} className="p-4 bg-white border border-slate-100 rounded-2xl flex gap-4 items-start shadow-sm">
                                                <div className={`p-2 rounded-lg ${log.event_type === 'PAYMENT_CONFIRMED' ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-500'}`}>
                                                    {log.event_type === 'PAYMENT_CONFIRMED' ? <CheckCircle2 size={16} /> : <Layout size={16} />}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="flex justify-between">
                                                        <p className="text-sm font-bold text-slate-800">{log.event_display}</p>
                                                        <p className="text-[10px] font-bold text-slate-400">{log.created_at}</p>
                                                    </div>
                                                    <p className="text-xs text-slate-500 mt-1">{JSON.stringify(log.metadata_json)}</p>
                                                    <p className="text-[10px] text-slate-400 font-bold mt-2 uppercase tracking-widest">Por: {log.user_name || 'System'}</p>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="p-8 text-center bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200">
                                            <p className="text-xs font-black text-slate-400 uppercase tracking-widest">No hay registros de auditoría disponibles</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Action Modals */}
            {isActionOpen && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-[2rem] shadow-2xl max-w-md w-full p-8">
                        <h3 className="text-2xl font-black text-slate-800 mb-2">
                               {actionType === 'edit-dates' ? 'Ajustar Fecha' : 'Confirmar Pago'}
                        </h3>
                        <p className="text-slate-500 text-sm mb-6">Realizando cambios para <strong>{selectedSub?.institution_name}</strong>.</p>
                        
                        <form onSubmit={submitAction} className="space-y-6">
                            {actionType === 'confirm-payment' && (
                                <>
                                    <div>
                                        <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Monto Pagado ($)</label>
                                        <input type="number" step="0.01" required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700"
                                            value={actionData.amount} onChange={e => setActionData({...actionData, amount: e.target.value})} />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Meses a Extender</label>
                                        <input type="number" min="1" required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700"
                                            value={actionData.months_to_extend} onChange={e => setActionData({...actionData, months_to_extend: e.target.value})} />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Notas / Referencia</label>
                                        <textarea className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700" rows="2"
                                            value={actionData.notes} onChange={e => setActionData({...actionData, notes: e.target.value})}></textarea>
                                    </div>
                                </>
                            )}
                            {actionType === 'edit-dates' && (
                                <div>
                                    <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Nueva Fecha de Corte</label>
                                    <input 
                                        type="date" required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700"
                                        value={actionData.date} onChange={e => setActionData({...actionData, date: e.target.value})}
                                    />
                                </div>
                            )}
                            <div className="flex gap-4">
                                <button type="button" onClick={() => setIsActionOpen(false)} className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-bold">Cancelar</button>
                                <button type="submit" className="flex-1 py-4 bg-indigo-600 text-white rounded-2xl font-bold shadow-lg shadow-indigo-100">Aplicar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            <ChangePlanModal
                isOpen={isChangePlanOpen}
                subscription={selectedSub}
                plans={plans}
                loading={changePlanLoading}
                planId={changePlanData.plan_id}
                onPlanChange={(plan_id) => setChangePlanData(prev => ({ ...prev, plan_id }))}
                onClose={() => setIsChangePlanOpen(false)}
                onConfirm={submitChangePlan}
            />
            {/* New Subscription Modal */}
            {isNewSubModalOpen && (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-[2rem] shadow-2xl max-w-md w-full p-8">
                        <h3 className="text-2xl font-black text-slate-800 mb-2">Nueva Suscripción</h3>
                        <p className="text-slate-500 text-sm mb-6">Asigna un plan a una institución sin suscripción activa.</p>
                        
                        <form onSubmit={handleCreateSub} className="space-y-6">
                            <div>
                                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Institución</label>
                                <select 
                                    required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700"
                                    value={actionData.institution} onChange={e => setActionData({...actionData, institution: e.target.value})}
                                >
                                    <option value="">-- Seleccionar Institución --</option>
                                    {institutionsWithoutSub.map(inst => <option key={inst.id} value={inst.id}>{inst.name}</option>)}
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Plan Inicial</label>
                                <select 
                                    required className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700"
                                    value={actionData.plan} onChange={e => setActionData({...actionData, plan: e.target.value})}
                                >
                                    <option value="">-- Seleccionar Plan --</option>
                                    {plans.map(p => <option key={p.id} value={p.id}>{p.name} - ${p.base_price_monthly}/mes</option>)}
                                </select>
                            </div>

                            <div className="flex gap-4">
                                <button type="button" onClick={() => setIsNewSubModalOpen(false)} className="flex-1 py-4 bg-slate-100 text-slate-600 rounded-2xl font-bold">Cancelar</button>
                                <button type="submit" className="flex-1 py-4 bg-indigo-600 text-white rounded-2xl font-bold">Crear</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SubscriptionsManagementPage;
