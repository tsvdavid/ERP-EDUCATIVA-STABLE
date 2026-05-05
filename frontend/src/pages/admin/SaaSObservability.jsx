import React, { useState, useEffect } from 'react';
import { 
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { 
    Activity, AlertTriangle, ShieldAlert, History, UserX, Info 
} from 'lucide-react';
import { toast, Toaster } from 'react-hot-toast';
import subscriptionService from '../../services/subscriptionService';

const SaaSObservability = () => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadMonitoring = async () => {
        try {
            setLoading(true);
            const res = await subscriptionService.getObservability();
            setData(res);
        } catch (error) {
            toast.error("Error al cargar monitoreo de facturación.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadMonitoring();
    }, []);

    if (loading) return <div className="p-8 text-center text-slate-500 italic">Analizando salud del sistema SaaS...</div>;

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />
            
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                        <Activity className="text-indigo-600" /> Observabilidad de Facturación
                    </h1>
                    <p className="text-slate-500">Monitoreo en tiempo real de ingresos, anomalías y logs de auditoría.</p>
                </div>
                <button 
                    onClick={loadMonitoring}
                    className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors"
                >
                    Actualizar Datos
                </button>
            </div>

            {/* Main Trend Chart */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                    <History size={18} className="text-slate-400" /> Tendencia de Ingresos (MRR)
                </h2>
                <div className="h-[300px] w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data?.trend_chart || []}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                            <XAxis dataKey="date" stroke="#64748b" fontSize={12} tickMargin={10} />
                            <YAxis stroke="#64748b" fontSize={12} />
                            <Tooltip 
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                            />
                            <Legend />
                            <Line 
                                type="monotone" 
                                dataKey="mrr" 
                                name="MRR ($)" 
                                stroke="#4f46e5" 
                                strokeWidth={3} 
                                dot={{ r: 4, fill: '#4f46e5' }} 
                                activeDot={{ r: 6 }} 
                            />
                            <Line 
                                type="monotone" 
                                dataKey="active" 
                                name="Clientes Activos" 
                                stroke="#10b981" 
                                strokeWidth={2} 
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* 1. Alerts & Anomalies */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="px-5 py-4 border-b border-slate-100 bg-rose-50/50 flex justify-between items-center">
                            <h2 className="font-bold text-rose-800 flex items-center gap-2 text-sm">
                                <ShieldAlert size={16} /> Alertas Críticas
                            </h2>
                            <span className="bg-rose-100 text-rose-700 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">Anomalías</span>
                        </div>
                        <div className="p-5 space-y-4">
                            {data?.alerts?.length === 0 ? (
                                <p className="text-slate-400 text-sm italic text-center py-4">No se detectaron anomalías.</p>
                            ) : data?.alerts?.map((alert, idx) => (
                                <div key={idx} className="flex gap-3 p-3 bg-slate-50 rounded-lg border-l-4 border-rose-500">
                                    <AlertTriangle className="text-rose-500 shrink-0" size={18} />
                                    <div>
                                        <p className="text-xs font-bold text-slate-800">{alert.event}</p>
                                        <p className="text-[10px] text-slate-500 mb-1">{alert.created_at}</p>
                                        <p className="text-[10px] font-mono bg-white p-1 border border-slate-200 rounded text-slate-600 truncate max-w-[200px]">
                                            {JSON.stringify(alert.metadata)}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 2. Suspended Customers */}
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="px-5 py-4 border-b border-slate-100 flex justify-between items-center">
                            <h2 className="font-bold text-slate-800 flex items-center gap-2 text-sm">
                                <UserX size={16} className="text-rose-500" /> Clientes Suspendidos
                            </h2>
                            <span className="text-slate-400 font-bold text-xs">{data?.suspended_customers?.length}</span>
                        </div>
                        <div className="divide-y divide-slate-100 max-h-[300px] overflow-y-auto">
                            {data?.suspended_customers?.length === 0 ? (
                                <p className="p-8 text-center text-slate-400 text-sm">Todo al día.</p>
                            ) : data?.suspended_customers?.map((sub, idx) => (
                                <div key={idx} className="p-4 flex justify-between items-center hover:bg-slate-50 transition-colors">
                                    <div>
                                        <p className="text-sm font-medium text-slate-800">{sub.institution}</p>
                                        <p className="text-[10px] text-slate-500">Venció: {sub.next_billing_date}</p>
                                    </div>
                                    <p className="text-xs font-bold text-rose-600">${sub.monthly_fee}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 3. Recent Activity (Audit Logs) */}
                <div className="lg:col-span-2">
                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden h-full">
                        <div className="px-5 py-4 border-b border-slate-100 flex justify-between items-center">
                            <h2 className="font-bold text-slate-800 flex items-center gap-2 text-sm">
                                <History size={16} className="text-indigo-500" /> Actividad Reciente (Auditoría)
                            </h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs">
                                <thead className="bg-slate-50 text-slate-500 border-b border-slate-100 uppercase tracking-tighter font-bold">
                                    <tr>
                                        <th className="px-5 py-3">Evento</th>
                                        <th className="px-5 py-3">Institución</th>
                                        <th className="px-5 py-3">Fecha / Hora</th>
                                        <th className="px-5 py-3">Responsable</th>
                                        <th className="px-5 py-3 text-right">Info</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {data?.audit_logs?.map((log) => (
                                        <tr key={log.id} className="hover:bg-slate-50 transition-colors">
                                            <td className="px-5 py-3 font-medium">
                                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                                    log.event_code === 'PAYMENT_CONFIRMED' ? 'bg-emerald-100 text-emerald-700' :
                                                    log.event_code === 'SUSPENDED' ? 'bg-rose-100 text-rose-700' :
                                                    log.event_code === 'EMAIL_SENT' ? 'bg-blue-100 text-blue-700' :
                                                    'bg-slate-100 text-slate-700'
                                                }`}>
                                                    {log.event}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 text-slate-600">{log.institution}</td>
                                            <td className="px-5 py-3 text-slate-500">{log.created_at}</td>
                                            <td className="px-5 py-3 text-slate-500">{log.user}</td>
                                            <td className="px-5 py-3 text-right">
                                                <button 
                                                    className="text-slate-300 hover:text-indigo-500 transition-colors"
                                                    title={JSON.stringify(log.metadata)}
                                                >
                                                    <Info size={14} />
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SaaSObservability;
