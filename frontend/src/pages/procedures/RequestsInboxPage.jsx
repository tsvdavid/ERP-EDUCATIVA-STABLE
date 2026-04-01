import React, { useState, useEffect } from 'react';
import { FileText, Check, X, AlertCircle } from 'lucide-react';
import { procedureService } from '../../services/procedureService';

const RequestsInboxPage = () => {
    const [requests, setRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [resolvingId, setResolvingId] = useState(null);

    // Modal state for resolving (mainly for rejection notes)
    const [showResolveModal, setShowResolveModal] = useState(false);
    const [resolveData, setResolveData] = useState({ id: null, action: '', notes: '' });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const data = await procedureService.getRequests();
            // Typically inbox only focuses on PENDING, we display all but sort logic helps
            setRequests(data);
        } catch (err) {
            setError('Error al cargar la bandeja de solicitudes');
        } finally {
            setLoading(false);
        }
    };

    const handleResolveClick = (id, action) => {
        if (action === 'APPROVE') {
            // Confirm approval immediately or could use modal
            if (window.confirm("¿Está seguro de APROBAR esta solicitud y generar el PDF automáticamente?")) {
                submitResolve(id, 'APPROVE', '');
            }
        } else {
            // Reject needs notes
            setResolveData({ id, action: 'REJECT', notes: '' });
            setShowResolveModal(true);
        }
    };

    const submitResolve = async (id, action, notes) => {
        try {
            setResolvingId(id);
            await procedureService.resolveRequest(id, { action, notes });
            setShowResolveModal(false);
            loadData();
        } catch (err) {
            setError('Error al procesar la solicitud');
        } finally {
            setResolvingId(null);
        }
    };

    const pendingRequests = requests.filter(r => r.status === 'PENDING');
    const processedRequests = requests.filter(r => r.status !== 'PENDING');

    if (loading) return <div className="p-8 text-center text-slate-500">Cargando bandeja...</div>;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Bandeja de Trámites y Solicitudes</h1>
                <p className="text-slate-600 mt-1">Aprueba o rechaza los documentos solicitados por los estudiantes.</p>
            </div>

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            {/* PENDING TICKETS */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200">
                <div className="p-4 border-b border-slate-200 bg-slate-50">
                    <h2 className="text-lg font-semibold text-slate-800">Pendientes de Aprobación ({pendingRequests.length})</h2>
                </div>
                {pendingRequests.length === 0 ? (
                    <div className="p-8 text-center text-slate-500">No hay solicitudes pendientes.</div>
                ) : (
                    <ul className="divide-y divide-slate-100">
                        {pendingRequests.map(req => (
                            <li key={req.id} className="p-6 hover:bg-slate-50 transition-colors">
                                <div className="flex justify-between items-start">
                                    <div className="space-y-1">
                                        <div className="flex items-center gap-2">
                                            <h3 className="text-md font-bold text-slate-800">{req.template_name}</h3>
                                            <span className="text-xs font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                                                {new Date(req.request_date).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-indigo-600 font-medium">Solicitado por: {req.student_name}</p>
                                        <div className="text-sm text-slate-600 bg-white p-3 border border-slate-200 rounded-lg mt-2 italic shadow-sm">
                                            "{req.details || 'Sin observaciones adicionales proporcionadas'}"
                                        </div>
                                    </div>

                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleResolveClick(req.id, 'APPROVE')}
                                            disabled={resolvingId === req.id}
                                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 text-sm font-medium disabled:opacity-50"
                                        >
                                            <Check className="w-4 h-4" /> Aprobar y Emitir
                                        </button>
                                        <button
                                            onClick={() => handleResolveClick(req.id, 'REJECT')}
                                            disabled={resolvingId === req.id}
                                            className="px-4 py-2 border border-red-200 text-red-600 rounded-lg hover:bg-red-50 flex items-center gap-2 text-sm font-medium disabled:opacity-50"
                                        >
                                            <X className="w-4 h-4" /> Rechazar
                                        </button>
                                    </div>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* RESOLVE MODAL */}
            {showResolveModal && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
                        <div className="p-6 border-b border-slate-100">
                            <h2 className="text-xl font-bold text-slate-800">Rechazar Solicitud</h2>
                        </div>
                        <div className="p-6">
                            <label className="block text-sm font-medium text-slate-700 mb-1">Motivo del Rechazo (Visible para el estudiante)</label>
                            <textarea
                                rows="3"
                                value={resolveData.notes}
                                onChange={e => setResolveData({ ...resolveData, notes: e.target.value })}
                                className="w-full border-slate-200 rounded-lg focus:ring-red-500 focus:border-red-500"
                                placeholder="Indique la razón para que el estudiante pueda corregirlo..."
                                required
                            />
                        </div>
                        <div className="p-6 border-t border-slate-100 bg-slate-50 rounded-b-xl flex justify-end gap-3">
                            <button onClick={() => setShowResolveModal(false)} className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-100">
                                Cancelar
                            </button>
                            <button
                                onClick={() => submitResolve(resolveData.id, resolveData.action, resolveData.notes)}
                                disabled={!resolveData.notes.trim() || resolvingId === resolveData.id}
                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                            >
                                Confirmar Rechazo
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* HISTORIAL */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 mt-8">
                <div className="p-4 border-b border-slate-200 bg-slate-50">
                    <h2 className="text-lg font-semibold text-slate-800">Historial Procesado</h2>
                </div>
                <ul className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                    {processedRequests.length === 0 ? (
                        <div className="p-8 text-center text-slate-500">Ningún trámite procesado aún.</div>
                    ) : (
                        processedRequests.map(req => (
                            <li key={req.id} className="p-4 flex justify-between items-center hover:bg-slate-50">
                                <div>
                                    <div className="font-medium text-slate-800">{req.template_name} - {req.student_name}</div>
                                    <div className="text-xs text-slate-500 mt-0.5">Atendido por: {req.approver_name} el {new Date(req.approval_date).toLocaleDateString()}</div>
                                </div>
                                <div>
                                    {req.status === 'APPROVED' ? (
                                        <div className="flex items-center gap-3">
                                            {req.generated_file && (
                                                <a
                                                    href={req.generated_file}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="inline-flex items-center gap-1 text-indigo-600 hover:text-indigo-800 text-sm font-medium transition-colors"
                                                >
                                                    <FileText className="w-4 h-4" />
                                                    Ver PDF
                                                </a>
                                            )}
                                            <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-1 rounded-full">APROBADO</span>
                                        </div>
                                    ) : (
                                        <span className="text-xs font-medium text-red-700 bg-red-100 px-2 py-1 rounded-full">RECHAZADO</span>
                                    )}
                                </div>
                            </li>
                        ))
                    )}
                </ul>
            </div>
        </div>
    );
};

export default RequestsInboxPage;
