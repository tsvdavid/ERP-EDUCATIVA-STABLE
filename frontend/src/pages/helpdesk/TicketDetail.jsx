import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import helpdeskService from '../../services/helpdeskService';
import userService from '../../services/userService';

const TicketDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [ticket, setTicket] = useState(null);
    const [loading, setLoading] = useState(true);
    const [agents, setAgents] = useState([]);

    // Editable fields
    const [status, setStatus] = useState('');
    const [priority, setPriority] = useState('');
    const [assignedTo, setAssignedTo] = useState('');
    const [response, setResponse] = useState(''); // Just a placeholder for now if we had comments

    useEffect(() => {
        loadTicket();
        loadAgents();
    }, [id]);

    const loadTicket = async () => {
        try {
            const res = await helpdeskService.getTicket(id);
            setTicket(res.data);
            setStatus(res.data.status);
            setPriority(res.data.priority);
            setAssignedTo(res.data.assigned_to || '');
        } catch (error) {
            console.error(error);
            alert("Error cargando ticket");
            navigate(-1);
        } finally {
            setLoading(false);
        }
    };

    const loadAgents = async () => {
        // Fetch users who can be agents (Admin/Rector)
        // Ideally backend should provide this list. 
        // For now, we might skip this or implement a fetch if userService allows.
        // Assuming userService.getUsers exists or similar.
    };

    const handleSave = async () => {
        try {
            await helpdeskService.updateTicket(id, {
                status,
                priority,
                assigned_to: assignedTo || null
            });
            alert("Ticket actualizado");
            loadTicket();
        } catch (error) {
            alert("Error actualizando ticket");
        }
    };

    if (loading) return <div>Cargando...</div>;
    if (!ticket) return <div>Ticket no encontrado</div>;

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <button onClick={() => navigate(-1)} className="text-blue-600 mb-4 hover:underline">← Volver</button>

            <div className="bg-white shadow rounded-lg p-6 mb-6">
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-800">#{ticket.id} {ticket.title}</h1>
                        <p className="text-gray-500">{ticket.category_name}</p>
                    </div>
                    <div className="text-right">
                        <span className="text-sm text-gray-500">Solicitado por:</span>
                        <p className="font-medium">{ticket.requester_data?.username}</p>
                        <p className="text-xs text-gray-400">{new Date(ticket.created_at).toLocaleString()}</p>
                    </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg border mb-6">
                    <h3 className="font-bold text-gray-700 mb-2">Descripción</h3>
                    <p className="whitespace-pre-wrap text-gray-800">{ticket.description}</p>
                </div>

                {/* Rating Display for Agents */}
                {ticket.survey && (
                    <div className="mb-6 bg-yellow-50 p-4 rounded border border-yellow-200">
                        <h3 className="font-bold text-yellow-800 mb-1">Calificación del Usuario</h3>
                        <div className="flex items-center gap-2">
                            <div className="text-2xl text-yellow-500 font-bold">
                                {'★'.repeat(ticket.survey.rating)}{'☆'.repeat(5 - ticket.survey.rating)}
                            </div>
                            <span className="text-yellow-800 font-bold">({ticket.survey.rating}/5)</span>
                        </div>
                        {ticket.survey.comment && (
                            <div className="mt-2 text-sm text-gray-700 italic border-l-4 border-yellow-300 pl-2">
                                "{ticket.survey.comment}"
                            </div>
                        )}
                    </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 border-t pt-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Estado</label>
                        <select
                            value={status}
                            onChange={e => setStatus(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                        >
                            <option value="OPEN">Abierto</option>
                            <option value="IN_PROGRESS">En Progreso</option>
                            <option value="PENDING_APPROVAL">Pendiente Aprobación</option>
                            <option value="RESOLVED">Resuelto</option>
                            <option value="CLOSED">Cerrado</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">Prioridad</label>
                        <select
                            value={priority}
                            onChange={e => setPriority(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                        >
                            <option value="LOW">Baja</option>
                            <option value="MEDIUM">Media</option>
                            <option value="HIGH">Alta</option>
                            <option value="CRITICAL">Crítica</option>
                        </select>
                    </div>

                    {/* Placeholder for Agent Assign if we had the list */}
                    {/* <div>
                        <label className="block text-sm font-medium text-gray-700">Asignar a</label>
                        <select className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border">
                            <option value="">-- Sin Asignar --</option>
                        </select>
                    </div> */}
                </div>

                <div className="mt-8 flex justify-end">
                    <button
                        onClick={handleSave}
                        className="bg-blue-600 text-white px-6 py-2 rounded shadow hover:bg-blue-700"
                    >
                        Guardar Cambios
                    </button>
                </div>
            </div>

            {/* Future Comment Section Placeholder */}
            {/* <div className="bg-white shadow rounded-lg p-6">
                <h3 className="text-lg font-bold mb-4">Comentarios</h3>
                <p className="text-gray-500 italic">No hay comentarios aún.</p>
             </div> */}
        </div>
    );
};

export default TicketDetail;
