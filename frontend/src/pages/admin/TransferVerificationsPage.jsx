import React, { useState, useEffect } from 'react';
import {
    CheckCircle, XCircle, Search, FileText,
    Eye, ExternalLink, Calendar, User, DollarSign,
    Clock
} from 'lucide-react';
import api from '../../services/api';

const TransferVerificationsPage = () => {
    const [transfers, setTransfers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [processingId, setProcessingId] = useState(null);

    useEffect(() => {
        fetchTransfers();
    }, []);

    const fetchTransfers = async () => {
        try {
            setLoading(true);
            const res = await api.get('/payments/pending_transfers/');
            setTransfers(res.data);
            setError(null);
        } catch (err) {
            console.error('Error fetching transfers:', err);
            setError('Error al cargar las transferencias pendientes.');
        } finally {
            setLoading(false);
        }
    };

    const handleVerification = async (id, action) => {
        if (!window.confirm(`¿Estás seguro que deseas ${action === 'approve' ? 'APROBAR' : 'RECHAZAR'} esta transferencia?`)) return;

        try {
            setProcessingId(id);
            await api.post(`payments/${id}/verify_transfer/`, { action });
            // Quitar de la lista
            setTransfers(transfers.filter(t => t.id !== id));
        } catch (err) {
            console.error(`Error procesando transferencia ${id}:`, err);
            alert(`Error al intentar ${action} la transferencia.`);
        } finally {
            setProcessingId(null);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm(`¿Estás seguro que deseas ELIMINAR esta solicitud de transferencia? Esta acción no se puede deshacer.`)) return;

        try {
            setProcessingId(id);
            await api.delete(`payments/${id}/delete_transfer/`);
            setTransfers(transfers.filter(t => t.id !== id));
        } catch (err) {
            console.error(`Error eliminando transferencia ${id}:`, err);
            alert(`Error al intentar eliminar la transferencia.`);
        } finally {
            setProcessingId(null);
        }
    };

    if (loading) return <div className="p-8 text-center text-slate-500">Cargando transferencias pendientes...</div>;

    if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Verificación de Transferencias</h1>
                <p className="text-slate-500">Revisa los comprobantes de depósito subidos por los usuarios y aproba o rechaza el pago.</p>
            </div>

            {/* Listado */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-600">
                        <thead className="bg-slate-50 text-slate-700 uppercase font-semibold border-b border-slate-200">
                            <tr>
                                <th className="px-6 py-4">ID Trans.</th>
                                <th className="px-6 py-4">Fecha</th>
                                <th className="px-6 py-4">Monto</th>
                                <th className="px-6 py-4">Detalle</th>
                                <th className="px-6 py-4 text-center">Comprobante</th>
                                <th className="px-6 py-4 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {transfers.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-8 text-center text-slate-500">
                                        <div className="flex flex-col items-center justify-center gap-2">
                                            <CheckCircle size={32} className="text-green-400" />
                                            <p>No hay transferencias pendientes de verificación.</p>
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                transfers.map((txn) => (
                                    <tr key={txn.id} className="hover:bg-slate-50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-xs text-slate-500">
                                            #{txn.id}
                                            <div className="mt-1 flex items-center gap-1 text-[10px] bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full w-max">
                                                <Clock size={10} /> {txn.status}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <Calendar size={14} className="text-slate-400" />
                                                <span>{new Date(txn.created_at).toLocaleString()}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="font-bold text-slate-800">${txn.amount}</div>
                                            <div className="text-xs text-slate-400">{txn.currency}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="max-w-[200px] truncate text-sm" title={txn.description}>
                                                {txn.description || 'Sin detalle'}
                                            </div>
                                            <div className="text-xs text-slate-400 font-mono mt-1">Ref: {txn.reference_id || 'N/A'}</div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {txn.voucher_file ? (
                                                <a
                                                    href={txn.voucher_file}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-md transition-colors text-xs font-medium"
                                                >
                                                    <ExternalLink size={14} /> Ver Archivo
                                                </a>
                                            ) : (
                                                <span className="text-xs text-red-500 bg-red-50 px-2 py-1 rounded">Sin archivo</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => handleVerification(txn.id, 'reject')}
                                                    disabled={processingId === txn.id}
                                                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                                                    title="Rechazar"
                                                >
                                                    <XCircle size={20} />
                                                </button>
                                                <button
                                                    onClick={() => handleVerification(txn.id, 'approve')}
                                                    disabled={processingId === txn.id}
                                                    className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
                                                    title="Aprobar Pago"
                                                >
                                                    <CheckCircle size={20} />
                                                </button>
                                                <button
                                                    onClick={() => handleDelete(txn.id)}
                                                    disabled={processingId === txn.id}
                                                    className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                                                    title="Eliminar Registro"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path></svg>
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default TransferVerificationsPage;
