import React, { useState, useEffect } from 'react';
import privacyService from '../../services/privacyService';

const ConsentManager = () => {
    const [policies, setPolicies] = useState([]);
    const [consents, setConsents] = useState({}); // Map policyId -> boolean

    // ARCO State
    const [showArcoModal, setShowArcoModal] = useState(false);
    const [arcoData, setArcoData] = useState({ right_type: 'ACCESS', details: '' });
    const [arcoRequests, setArcoRequests] = useState([]);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [pRes, cRes, aRes] = await Promise.all([
                privacyService.getPolicies(),
                privacyService.getConsents(),
                privacyService.getARCORequests()
            ]);
            setPolicies(pRes);
            setArcoRequests(aRes);

            // Map user's existing consents
            const consentMap = {};
            cRes.forEach(c => {
                consentMap[c.policy] = c.accepted;
            });
            setConsents(consentMap);
        } catch (error) {
            console.error(error);
        }
    };

    const handleToggle = async (policyId, currentVal) => {
        try {
            await privacyService.recordConsent(policyId, !currentVal);
            setConsents(prev => ({ ...prev, [policyId]: !currentVal }));
        } catch (error) {
            alert("Error guardando consentimiento");
        }
    };

    const handleArcoSubmit = async (e) => {
        e.preventDefault();
        try {
            await privacyService.createARCORequest(arcoData);
            alert("Solicitud ARCO enviada exitosamente. Recibirá una respuesta en el plazo legal establecido.");
            setShowArcoModal(false);
            setArcoData({ right_type: 'ACCESS', details: '' });
            loadData(); // Refresh list
        } catch (error) {
            console.error(error);
            alert("Error al enviar solicitud ARCO");
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-2">Privacidad y Consumidor</h1>
            <p className="text-gray-600 mb-8">Administra tus preferencias de privacidad conforme a la LOPDP.</p>

            <div className="space-y-6">
                {policies.map(policy => (
                    <div key={policy.id} className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                        <div className="flex justify-between items-start">
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">{policy.name} <span className="text-xs font-normal text-gray-500">v{policy.version}</span></h3>
                                <p className="mt-2 text-gray-600 text-sm whitespace-pre-wrap max-h-40 overflow-y-auto bg-gray-50 p-2 rounded">
                                    {policy.content}
                                </p>
                            </div>

                            <div className="ml-4 flex items-center">
                                {policy.is_mandatory ? (
                                    <span className="text-xs font-bold text-gray-500 bg-gray-200 px-2 py-1 rounded">Obligatorio</span>
                                ) : (
                                    <label className="inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="form-checkbox h-6 w-6 text-blue-600"
                                            checked={!!consents[policy.id]}
                                            onChange={() => handleToggle(policy.id, !!consents[policy.id])}
                                        />
                                        <span className="ml-2 text-gray-700">Aceptar</span>
                                    </label>
                                )}
                            </div>
                        </div>
                        {policy.is_mandatory && (
                            <div className="mt-2 text-right">
                                <span className="text-sm text-green-600 font-medium">Aceptado (Esencial)</span>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <div className="mt-10 border-t pt-6">
                <h2 className="text-xl font-bold mb-4">Derechos ARCO</h2>
                <p className="text-gray-600 mb-4">Si deseas ejercer tus derechos de Acceso, Rectificación, Cancelación u Oposición, puedes iniciar una solicitud formal aquí.</p>
                <button
                    onClick={() => setShowArcoModal(true)}
                    className="bg-gray-800 text-white px-4 py-2 rounded hover:bg-gray-700"
                >
                    Iniciar Solicitud ARCO
                </button>

                {/* ARCO Requests List */}
                <div className="mt-8">
                    <h3 className="font-bold text-gray-700 mb-4">Mis Solicitudes</h3>
                    {arcoRequests.length === 0 ? (
                        <p className="text-gray-500 italic">No tienes solicitudes registradas.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="min-w-full bg-white border border-gray-200 rounded-lg">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Solicitante</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Derecho</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Detalles</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200">
                                    {arcoRequests.map(req => (
                                        <tr key={req.id}>
                                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                                                {new Date(req.created_at).toLocaleDateString()}
                                            </td>
                                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                                                <div className="font-medium">{req.requester_data?.first_name} {req.requester_data?.last_name}</div>
                                                <div className="text-xs text-gray-500">{req.requester_data?.username}</div>
                                            </td>
                                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                                                {req.right_type === 'ACCESS' && 'Acceso'}
                                                {req.right_type === 'RECTIFICATION' && 'Rectificación'}
                                                {req.right_type === 'CANCELLATION' && 'Cancelación'}
                                                {req.right_type === 'OPPOSITION' && 'Oposición'}
                                                {req.right_type === 'PORTABILITY' && 'Portabilidad'}
                                            </td>
                                            <td className="px-4 py-2 whitespace-nowrap">
                                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                                    ${req.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                                                        req.status === 'APPROVED' ? 'bg-green-100 text-green-800' :
                                                            req.status === 'REJECTED' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
                                                    {req.status === 'PENDING' && 'Pendiente'}
                                                    {req.status === 'IN_REVIEW' && 'En Revisión'}
                                                    {req.status === 'APPROVED' && 'Aprobado'}
                                                    {req.status === 'REJECTED' && 'Rechazado'}
                                                    {req.status === 'EXECUTED' && 'Ejecutado'}
                                                </span>
                                            </td>
                                            <td className="px-4 py-2 text-sm text-gray-500 truncate max-w-xs">
                                                {req.details}
                                                {req.response_content && (
                                                    <div className="mt-1 text-xs text-indigo-600 bg-indigo-50 p-1 rounded">
                                                        Resolución: {req.response_content}
                                                    </div>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* ARCO Modal */}
            {showArcoModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Nueva Solicitud ARCO</h2>
                        <form onSubmit={handleArcoSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Tipo de Derecho</label>
                                <select
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    value={arcoData.right_type}
                                    onChange={e => setArcoData({ ...arcoData, right_type: e.target.value })}
                                >
                                    <option value="ACCESS">Acceso</option>
                                    <option value="RECTIFICATION">Rectificación</option>
                                    <option value="CANCELLATION">Cancelación</option>
                                    <option value="OPPOSITION">Oposición</option>
                                    <option value="PORTABILITY">Portabilidad</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">Detalle de la Solicitud</label>
                                <textarea
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    rows="4"
                                    placeholder="Describa detalladamente su solicitud..."
                                    required
                                    value={arcoData.details}
                                    onChange={e => setArcoData({ ...arcoData, details: e.target.value })}
                                ></textarea>
                            </div>

                            <div className="flex justify-end gap-2 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowArcoModal(false)}
                                    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                >
                                    Enviar Solicitud
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ConsentManager;
