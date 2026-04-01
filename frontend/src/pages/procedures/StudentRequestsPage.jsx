import React, { useState, useEffect } from 'react';
import { FileText, Send, CheckCircle, XCircle, Clock, Download, AlertCircle } from 'lucide-react';
import { procedureService } from '../../services/procedureService';

const StudentRequestsPage = () => {
    const [requests, setRequests] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        template: '',
        details: ''
    });

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [reqRes, tempRes] = await Promise.all([
                procedureService.getRequests(),
                procedureService.getTemplates()
            ]);
            setRequests(reqRes);
            setTemplates(tempRes.filter(t => t.is_active));
        } catch (err) {
            setError('Error al cargar la información');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await procedureService.createRequest({
                template: parseInt(formData.template),
                details: formData.details
            });
            setShowModal(false);
            setFormData({ template: '', details: '' });
            loadData();
        } catch (err) {
            setError('Error al enviar la solicitud');
        }
    };

    const getStatusBadge = (status) => {
        switch (status) {
            case 'PENDING':
                return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium flex items-center gap-1"><Clock className="w-3 h-3" /> Pendiente</span>;
            case 'APPROVED':
                return <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Aprobado</span>;
            case 'REJECTED':
                return <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-medium flex items-center gap-1"><XCircle className="w-3 h-3" /> Rechazado</span>;
            default:
                return status;
        }
    };

    if (loading) return <div className="p-8 text-center text-slate-500">Cargando sus trámites...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Mis Trámites y Documentos</h1>
                    <p className="text-slate-600 mt-1">Solicita certificados, justificaciones o cartas a la institución.</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                    <Send className="w-4 h-4" />
                    Nueva Solicitud
                </button>
            </div>

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[600px] sm:min-w-full">
                    <thead>
                        <tr className="bg-slate-50 border-b border-slate-200">
                            <th className="p-4 font-semibold text-sm text-slate-700">Trámite / Plantilla</th>
                            <th className="p-4 font-semibold text-sm text-slate-700">Fecha</th>
                            <th className="p-4 font-semibold text-sm text-slate-700">Estado</th>
                            <th className="p-4 font-semibold text-sm text-slate-700 text-right">Documento</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                        {requests.length === 0 ? (
                            <tr>
                                <td colSpan="4" className="p-8 text-center text-slate-500">
                                    No has realizado ninguna solicitud todavía.
                                </td>
                            </tr>
                        ) : (
                            requests.map(req => (
                                <tr key={req.id} className="hover:bg-slate-50">
                                    <td className="p-4">
                                        <div className="font-medium text-slate-800">{req.template_name}</div>
                                        <div className="text-xs text-slate-500 truncate max-w-xs">{req.details || 'Sin justificación'}</div>
                                    </td>
                                    <td className="p-4 text-sm text-slate-600">
                                        {new Date(req.request_date).toLocaleDateString()}
                                    </td>
                                    <td className="p-4">
                                        {getStatusBadge(req.status)}
                                        {req.status === 'REJECTED' && req.response_notes && (
                                            <div className="text-xs text-red-500 mt-1">Motivo: {req.response_notes}</div>
                                        )}
                                    </td>
                                    <td className="p-4 text-right">
                                        {req.status === 'APPROVED' && req.generated_file ? (
                                            <a
                                                href={req.generated_file}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
                                            >
                                                <Download className="w-4 h-4" />
                                                Descargar PDF
                                            </a>
                                        ) : (
                                            <span className="text-sm text-slate-400">-</span>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal Nueva Solicitud */}
            {showModal && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                            <h2 className="text-xl font-bold text-slate-800">Solicitar Trámite</h2>
                            <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">&times;</button>
                        </div>

                        <div className="p-6">
                            <form id="requestForm" onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Trámite</label>
                                    <select
                                        required
                                        value={formData.template}
                                        onChange={e => setFormData({ ...formData, template: e.target.value })}
                                        className="w-full border-slate-200 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                                    >
                                        <option value="">Seleccione una opción...</option>
                                        {templates.map(t => (
                                            <option key={t.id} value={t.id}>{t.name}</option>
                                        ))}
                                    </select>
                                    {formData.template && (
                                        <p className="text-xs text-slate-500 mt-2 p-2 bg-slate-50 rounded">
                                            {templates.find(t => t.id === parseInt(formData.template))?.description}
                                        </p>
                                    )}
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Motivo o Detalles Adicionales</label>
                                    <textarea
                                        rows="3"
                                        value={formData.details}
                                        onChange={e => setFormData({ ...formData, details: e.target.value })}
                                        className="w-full border-slate-200 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                                        placeholder="Ej. Requiero el permiso médico correspondiente a fecha..."
                                    />
                                </div>
                            </form>
                        </div>

                        <div className="p-6 border-t border-slate-100 bg-slate-50 rounded-b-xl flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setShowModal(false)}
                                className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-100"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                form="requestForm"
                                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                            >
                                <Send className="w-4 h-4" />
                                Enviar Solicitud
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default StudentRequestsPage;
