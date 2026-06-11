import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, CheckCircle, XCircle, Clock, AlertTriangle, Send, FileCode, Download, ExternalLink } from 'lucide-react';
import { toast } from 'react-hot-toast';
import treasuryService from '../../services/treasuryService';

const SriMonitoringPage = () => {
    const [data, setData] = useState({ metrics: {}, invoices: [] });
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [filter, setFilter] = useState('');

    const loadData = async (isManual = false) => {
        if (isManual) setRefreshing(true);
        try {
            const result = await treasuryService.getSriMonitoring({ status: filter });
            setData(result);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando monitoreo SRI");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(() => loadData(), 20000); // Auto refresh 20s
        return () => clearInterval(interval);
    }, [filter]);

    const handleRetry = async (invoiceId) => {
        const toastId = toast.loading("Encolando reintento...");
        try {
            await treasuryService.sendToSri(invoiceId);
            toast.success("Reintento iniciado", { id: toastId });
            loadData();
        } catch (error) {
            toast.error("Error al reintentar", { id: toastId });
        }
    };

    const handlePreflight = async (invoiceId) => {
        const toastId = toast.loading("Validando estructura...");
        try {
            const result = await treasuryService.preflightCheck(invoiceId);
            if (result.valid) {
                toast.success(result.message, { id: toastId });
            } else {
                toast.error(result.error, { id: toastId });
            }
        } catch (error) {
            const msg = error.response?.data?.error || "Error en validación previa";
            toast.error(msg, { id: toastId });
        }
    };

    const handleDownloadXML = async (invoiceId, number) => {
        try {
            const blob = await treasuryService.downloadInvoiceXml(invoiceId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Factura_${number}.xml`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            toast.error("Error al descargar XML");
        }
    };

    if (loading) return <div className="p-10 text-center">Cargando monitoreo...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <Activity className="text-indigo-600" /> Monitoreo Operativo SRI
                </h1>
                <div className="flex items-center gap-4">
                    <span className="text-xs text-slate-400 italic">Auto-refresh cada 30s</span>
                    <button 
                        onClick={() => loadData(true)} 
                        className="p-2 hover:bg-indigo-50 text-indigo-600 rounded-lg transition-colors"
                    >
                        <RefreshCw size={20} className={refreshing ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <MetricCard 
                    title="Pendientes (Draft)" 
                    value={data.metrics.pending_sri} 
                    icon={<Clock className="text-slate-500" />}
                    color="bg-slate-50 border-slate-200"
                />
                <MetricCard 
                    title="Cola de Reintento" 
                    value={data.metrics.retry_queue} 
                    icon={<AlertTriangle className="text-orange-500" />}
                    color="bg-orange-50 border-orange-200"
                />
                <MetricCard 
                    title="Autorizadas Hoy" 
                    value={data.metrics.authorized_today} 
                    icon={<CheckCircle className="text-green-500" />}
                    color="bg-green-50 border-green-200"
                />
                <MetricCard 
                    title="Rechazadas Hoy" 
                    value={data.metrics.rejected_today} 
                    icon={<XCircle className="text-red-500" />}
                    color="bg-red-50 border-red-200"
                />
            </div>

            {/* Invoices Table */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
                    <h3 className="font-bold text-slate-700">Últimos Movimientos SRI</h3>
                    <select 
                        className="input-modern py-1 text-xs" 
                        value={filter} 
                        onChange={(e) => setFilter(e.target.value)}
                    >
                        <option value="">Todos los estados</option>
                        <option value="SIGNED">Firmados</option>
                        <option value="PENDING_SRI">En Reintento</option>
                        <option value="RECEIVED">Recibidos</option>
                        <option value="AUTHORIZED">Autorizados</option>
                        <option value="REJECTED">Rechazados</option>
                    </select>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left text-slate-600">
                        <thead className="bg-slate-50 text-[10px] uppercase font-bold text-slate-400">
                            <tr>
                                <th className="px-6 py-3">Factura / Cliente</th>
                                <th className="px-6 py-3">Estado Actual</th>
                                <th className="px-6 py-3">Cód. Error</th>
                                <th className="px-6 py-3">Intentos</th>
                                <th className="px-6 py-3">Última Respuesta SRI</th>
                                <th className="px-6 py-3">Último Evento</th>
                                <th className="px-6 py-3 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {data.invoices.map(inv => (
                                <React.Fragment key={inv.id}>
                                    <tr className="hover:bg-slate-50/50 transition-colors cursor-pointer" onClick={() => {
                                        if (inv.messages?.length > 0) {
                                            const row = document.getElementById(`msg-${inv.id}`);
                                            row.classList.toggle('hidden');
                                        }
                                    }}>
                                        <td className="px-6 py-4">
                                            <div className="font-bold text-slate-800">{inv.number}</div>
                                            <div className="text-[11px] text-slate-500">{inv.client_name}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <StatusBadge status={inv.status} />
                                        </td>
                                        <td className="px-6 py-4 font-mono text-[11px] font-bold text-rose-600">
                                            {inv.messages?.[0]?.code || '-'}
                                        </td>
                                        <td className="px-6 py-4 font-mono text-xs">
                                            {inv.attempts}
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="max-w-xs truncate text-[11px] font-mono bg-slate-100 p-1 rounded" title={inv.last_response}>
                                                {inv.last_response}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-[11px]">
                                            {new Date(inv.updated_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                                                {inv.status !== 'AUTHORIZED' && (
                                                    <>
                                                        <button 
                                                            onClick={() => handlePreflight(inv.id)}
                                                            className="p-1.5 hover:bg-slate-100 text-slate-500 rounded transition-colors"
                                                            title="Validación Previa (Pre-flight)"
                                                        >
                                                            <FileCode size={16} />
                                                        </button>
                                                        <button 
                                                            onClick={() => handleRetry(inv.id)}
                                                            className="p-1.5 hover:bg-indigo-100 text-indigo-600 rounded transition-colors"
                                                            title="Reintentar YA"
                                                        >
                                                            <Send size={16} />
                                                        </button>
                                                    </>
                                                )}
                                                {inv.status !== 'DRAFT' && (
                                                    <button 
                                                        onClick={() => handleDownloadXML(inv.id, inv.number)}
                                                        className="p-1.5 hover:bg-green-100 text-green-600 rounded transition-colors"
                                                        title="Descargar XML"
                                                    >
                                                        <Download size={16} />
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                    {inv.messages?.length > 0 && (
                                        <tr id={`msg-${inv.id}`} className="hidden bg-slate-50 border-x-4 border-indigo-500">
                                            <td colSpan="7" className="px-6 py-4">
                                                <div className="space-y-3">
                                                    <h5 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Detalles de Errores / Alertas SRI</h5>
                                                    <div className="grid grid-cols-1 gap-2">
                                                        {inv.messages.map((m, idx) => (
                                                            <div key={idx} className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm flex items-start gap-3">
                                                                <div className="bg-rose-100 text-rose-700 px-2 py-0.5 rounded text-[10px] font-bold font-mono">
                                                                    {m.code}
                                                                </div>
                                                                <div className="flex-1">
                                                                    <p className="text-[12px] font-bold text-slate-700">{m.message}</p>
                                                                    {m.additional_info && (
                                                                        <p className="text-[11px] text-slate-500 mt-1 italic">{m.additional_info}</p>
                                                                    )}
                                                                </div>
                                                                <div className="text-[9px] font-black text-slate-300 uppercase">
                                                                    {m.type}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const MetricCard = ({ title, value, icon, color }) => (
    <div className={`p-6 rounded-2xl border shadow-sm ${color} flex items-center justify-between`}>
        <div>
            <p className="text-xs font-bold text-slate-500 uppercase mb-1">{title}</p>
            <h4 className="text-2xl font-black text-slate-800">{value || 0}</h4>
        </div>
        <div className="p-3 bg-white/50 rounded-xl">
            {icon}
        </div>
    </div>
);

const StatusBadge = ({ status }) => {
    const config = {
        'AUTHORIZED': { class: 'bg-green-100 text-green-700', text: 'AUTORIZADO' },
        'RECEIVED': { class: 'bg-blue-100 text-blue-700', text: 'RECIBIDO' },
        'PENDING_SRI': { class: 'bg-orange-100 text-orange-700', text: 'REINTENTO' },
        'REJECTED': { class: 'bg-red-100 text-red-700', text: 'RECHAZADO' },
        'SIGNED': { class: 'bg-indigo-100 text-indigo-700', text: 'FIRMADO' },
        'DRAFT': { class: 'bg-slate-100 text-slate-500', text: 'BORRADOR' },
    };
    const s = config[status] || config['DRAFT'];
    return (
        <span className={`px-2 py-0.5 rounded-full text-[10px] font-black border border-current ${s.class}`}>
            {s.text}
        </span>
    );
};

export default SriMonitoringPage;
