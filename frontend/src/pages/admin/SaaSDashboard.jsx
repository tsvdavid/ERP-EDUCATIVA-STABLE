import React, { useState, useEffect } from 'react';
import { DollarSign, Users, AlertCircle, Clock, CheckCircle } from 'lucide-react';
import { toast, Toaster } from 'react-hot-toast';
import subscriptionService from '../../services/subscriptionService';

const SaaSDashboard = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedSub, setSelectedSub] = useState(null);
    const [paymentData, setPaymentData] = useState({ amount: '', months_to_extend: 1, notes: '' });

    const loadDashboard = async () => {
        try {
            setLoading(true);
            const res = await subscriptionService.getDashboard();
            setData(res);
        } catch (error) {
            toast.error("Error al cargar el panel de suscripciones.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDashboard();
    }, []);

    const handleConfirmPayment = async (e) => {
        e.preventDefault();
        try {
            await subscriptionService.confirmPayment(selectedSub.id, paymentData);
            toast.success("Pago confirmado exitosamente.");
            setIsModalOpen(false);
            loadDashboard(); // Refresh data
        } catch (error) {
            toast.error("Error al procesar el pago.");
        }
    };

    const openPaymentModal = (sub) => {
        setSelectedSub(sub);
        setPaymentData({ amount: sub.monthly_fee, months_to_extend: 1, notes: '' });
        setIsModalOpen(true);
    };

    if (loading) return <div className="p-8 text-center text-slate-500">Cargando panel SaaS...</div>;

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Panel Global SaaS (Owner)</h1>
                <p className="text-slate-500">Resumen de ingresos recurrentes y estado de clientes.</p>
            </div>

            {/* KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-4 bg-emerald-100 rounded-lg text-emerald-600"><DollarSign size={24} /></div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">MRR (Ingreso Mensual)</p>
                        <p className="text-2xl font-bold text-slate-800">${data?.mrr?.toFixed(2)}</p>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-4 bg-blue-100 rounded-lg text-blue-600"><Users size={24} /></div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Clientes Activos</p>
                        <p className="text-2xl font-bold text-slate-800">{data?.active_customers}</p>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-4 bg-amber-100 rounded-lg text-amber-600"><Clock size={24} /></div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Vencen pronto (15 días)</p>
                        <p className="text-2xl font-bold text-slate-800">{data?.expiring_soon}</p>
                    </div>
                </div>
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <div className="p-4 bg-rose-100 rounded-lg text-rose-600"><AlertCircle size={24} /></div>
                    <div>
                        <p className="text-sm text-slate-500 font-medium">Cuentas en Mora / Suspendidas</p>
                        <p className="text-2xl font-bold text-slate-800">{data?.overdue}</p>
                    </div>
                </div>
            </div>

            {/* Overdue Accounts */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 bg-rose-50/50">
                    <h2 className="font-bold text-rose-800 flex items-center gap-2"><AlertCircle size={18} /> Requieren Atención Inmediata (Mora)</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50 text-slate-600">
                            <tr>
                                <th className="px-6 py-3">Institución</th>
                                <th className="px-6 py-3">Estado</th>
                                <th className="px-6 py-3">Fecha de Vencimiento</th>
                                <th className="px-6 py-3">Cuota ($)</th>
                                <th className="px-6 py-3 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {data?.overdue_list?.length === 0 ? (
                                <tr><td colSpan="5" className="px-6 py-4 text-center text-slate-500">No hay cuentas en mora.</td></tr>
                            ) : data?.overdue_list?.map(sub => (
                                <tr key={sub.id}>
                                    <td className="px-6 py-4 font-medium">{sub.institution_name}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${sub.status === 'SUSPENDED' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'}`}>
                                            {sub.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">{sub.next_billing_date}</td>
                                    <td className="px-6 py-4">${sub.monthly_fee}</td>
                                    <td className="px-6 py-4 text-right">
                                        <button onClick={() => openPaymentModal(sub)} className="text-emerald-600 hover:text-emerald-800 font-medium text-sm flex items-center justify-end gap-1 w-full">
                                            <CheckCircle size={16} /> Confirmar Pago
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Expiring Soon */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                    <h2 className="font-bold text-slate-800 flex items-center gap-2"><Clock size={18} className="text-amber-500" /> Próximos Vencimientos (15 días)</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50 text-slate-600">
                            <tr>
                                <th className="px-6 py-3">Institución</th>
                                <th className="px-6 py-3">Plan</th>
                                <th className="px-6 py-3">Fecha de Vencimiento</th>
                                <th className="px-6 py-3 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {data?.expiring_list?.length === 0 ? (
                                <tr><td colSpan="4" className="px-6 py-4 text-center text-slate-500">No hay cuentas por vencer en los próximos 15 días.</td></tr>
                            ) : data?.expiring_list?.map(sub => (
                                <tr key={sub.id}>
                                    <td className="px-6 py-4 font-medium">{sub.institution_name}</td>
                                    <td className="px-6 py-4 text-slate-500">{sub.plan_name}</td>
                                    <td className="px-6 py-4 font-medium text-amber-600">{sub.next_billing_date}</td>
                                    <td className="px-6 py-4 text-right">
                                        <button onClick={() => openPaymentModal(sub)} className="text-emerald-600 hover:text-emerald-800 font-medium text-sm">
                                            Confirmar Pago
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Payment Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                        <h3 className="text-xl font-bold mb-4">Confirmar Pago Manual</h3>
                        <p className="text-sm text-slate-500 mb-4">Registra el pago para <strong>{selectedSub?.institution_name}</strong>. Esto reactivará su cuenta (si estaba suspendida) y extenderá la fecha de su próximo corte.</p>
                        
                        <form onSubmit={handleConfirmPayment} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Monto Pagado ($)</label>
                                <input type="number" step="0.01" required className="w-full border border-slate-300 rounded-lg px-3 py-2" 
                                    value={paymentData.amount} onChange={e => setPaymentData({...paymentData, amount: e.target.value})} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Meses a Extender</label>
                                <input type="number" min="1" required className="w-full border border-slate-300 rounded-lg px-3 py-2" 
                                    value={paymentData.months_to_extend} onChange={e => setPaymentData({...paymentData, months_to_extend: e.target.value})} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Notas / Referencia (Opcional)</label>
                                <textarea className="w-full border border-slate-300 rounded-lg px-3 py-2" rows="2" placeholder="# Transferencia, Banco..."
                                    value={paymentData.notes} onChange={e => setPaymentData({...paymentData, notes: e.target.value})}></textarea>
                            </div>
                            <div className="flex gap-3 justify-end pt-4">
                                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-slate-600 bg-slate-100 rounded-lg hover:bg-slate-200 font-medium">Cancelar</button>
                                <button type="submit" className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-medium">Confirmar Pago</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SaaSDashboard;
