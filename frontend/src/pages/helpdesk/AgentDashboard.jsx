import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import helpdeskService from '../../services/helpdeskService';

const AgentDashboard = () => {
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusUpdating, setStatusUpdating] = useState(null);
    const [showCatModal, setShowCatModal] = useState(false);

    // Category Management
    const [categories, setCategories] = useState([]);
    const [newCatName, setNewCatName] = useState('');
    const [newCatParent, setNewCatParent] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [tRes, cRes] = await Promise.all([
                helpdeskService.getTickets(),
                helpdeskService.getCatalog()
            ]);
            setTickets(tRes);
            setCategories(cRes);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const updateTicket = async (id, data) => {
        setStatusUpdating(id);
        try {
            await helpdeskService.updateTicket(id, data);

            // Optimistic update locally
            setTickets(prev => prev.map(t =>
                t.id === id ? { ...t, ...data } : t
            ));
        } catch (error) {
            alert("Error actualizando ticket");
        } finally {
            setStatusUpdating(null);
        }
    };

    const handleCreateCategory = async () => {
        try {
            await helpdeskService.createCategory({
                name: newCatName,
                parent: newCatParent || null
            });
            setNewCatName('');
            setNewCatParent('');
            setShowCatModal(false);
            alert("Categoría creada");
            // Reload categories
            const cRes = await helpdeskService.getCatalog();
            setCategories(cRes);
        } catch (error) {
            alert("Error creando categoría");
        }
    };

    if (loading) return <div>Cargando tablero...</div>;

    return (
        <div className="p-6">
            <div className="flex justify-between mb-6">
                <h1 className="text-2xl font-bold">Tablero de Agente</h1>
                <button
                    onClick={() => setShowCatModal(true)}
                    className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700"
                >
                    + Nueva Categoría
                </button>
            </div>

            {showCatModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
                    <div className="bg-white p-6 rounded shadow-lg">
                        <h2 className="text-lg font-bold mb-4">Crear Categoría de Servicio</h2>

                        <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                        <input
                            className="border p-2 w-full mb-4 rounded"
                            placeholder="Ej. Soporte Hardware"
                            value={newCatName}
                            onChange={e => setNewCatName(e.target.value)}
                        />

                        <label className="block text-sm font-medium text-gray-700 mb-1">Categoría Padre (Opcional)</label>
                        <select
                            className="border p-2 w-full mb-6 rounded"
                            value={newCatParent}
                            onChange={e => setNewCatParent(e.target.value)}
                        >
                            <option value="">-- Ninguna (Categoría Principal) --</option>
                            {categories.filter(c => !c.parent).map(parent => (
                                <React.Fragment key={parent.id}>
                                    <option value={parent.id} className="font-bold">{parent.name}</option>
                                    {/* Only show parents as potential parents for now? Or allow nesting? Assuming generic list for now if creating subcat */}
                                </React.Fragment>
                            ))}
                        </select>
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setShowCatModal(false)} className="px-4 py-2 text-gray-600">Cancelar</button>
                            <button onClick={handleCreateCategory} className="px-4 py-2 bg-blue-600 text-white rounded">Guardar</button>
                        </div>
                    </div>
                </div>
            )}

            <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200 shadow-sm rounded-lg">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Asunto</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Solicitante</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoría</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prioridad</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                        {tickets.map((ticket) => (
                            <tr key={ticket.id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <Link to={`/dashboard/helpdesk/tickets/agent/${ticket.id}`} className="text-blue-600 hover:text-blue-800 font-bold">
                                        #{ticket.id}
                                    </Link>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{ticket.title}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {ticket.requester_data ? ticket.requester_data.username : 'N/A'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {ticket.category_name}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    <select
                                        disabled={statusUpdating === ticket.id}
                                        value={ticket.priority}
                                        onChange={(e) => updateTicket(ticket.id, { priority: e.target.value })}
                                        className={`text-xs border-gray-300 rounded shadow-sm focus:ring focus:ring-opacity-50
                                            ${ticket.priority === 'CRITICAL' ? 'text-red-600 font-bold' :
                                                ticket.priority === 'HIGH' ? 'text-orange-600' : 'text-gray-600'}`}
                                    >
                                        <option value="LOW">Baja</option>
                                        <option value="MEDIUM">Media</option>
                                        <option value="HIGH">Alta</option>
                                        <option value="CRITICAL">Crítica</option>
                                    </select>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full mb-1
                                        ${ticket.status === 'OPEN' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                        {ticket.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                    <select
                                        disabled={statusUpdating === ticket.id}
                                        value={ticket.status}
                                        onChange={(e) => updateTicket(ticket.id, { status: e.target.value })}
                                        className="text-sm border-gray-300 rounded shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                                    >
                                        <option value="OPEN">Abierto</option>
                                        <option value="IN_PROGRESS">En Progreso</option>
                                        <option value="PENDING_APPROVAL">Pendiente Aprobación</option>
                                        <option value="RESOLVED">Resuelto</option>
                                        <option value="CLOSED">Cerrado</option>
                                    </select>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div >
    );
};

export default AgentDashboard;
