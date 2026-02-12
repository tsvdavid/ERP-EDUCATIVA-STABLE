import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import helpdeskService from '../../services/helpdeskService';

const TicketPortal = () => {
    const [tickets, setTickets] = useState([]);
    const [catalog, setCatalog] = useState([]);
    const [showModal, setShowModal] = useState(false);

    // Rating State
    const [showRatingModal, setShowRatingModal] = useState(false);
    const [ratingData, setRatingData] = useState({ ticketId: null, score: 5, comment: '' });

    const [newTicket, setNewTicket] = useState({
        title: '',
        description: '',
        category: '',
        priority: 'MEDIUM',
        file: null
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [ticketsRes, catalogRes] = await Promise.all([
                helpdeskService.getTickets(),
                helpdeskService.getCatalog()
            ]);
            setTickets(ticketsRes);
            setCatalog(catalogRes);
        } catch (error) {
            console.error("Error fetching helpdesk data", error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // 1. Create Ticket
            const res = await helpdeskService.createTicket(newTicket);
            const ticketId = res.data.id;

            // 2. Upload Attachment if exists
            if (newTicket.file) {
                await helpdeskService.addAttachment({
                    ticket: ticketId,
                    file: newTicket.file
                });
            }

            setShowModal(false);
            fetchData();
            setNewTicket({ title: '', description: '', category: '', priority: 'MEDIUM', file: null });
            alert("Ticket creado exitosamente");
        } catch (error) {
            console.error(error);
            alert("Error creando ticket");
        }
    };

    const handleRateClick = (ticket) => {
        setRatingData({ ticketId: ticket.id, score: 5, comment: '' });
        setShowRatingModal(true);
    };

    const submitRating = async () => {
        try {
            await helpdeskService.rateTicket(ratingData.ticketId, ratingData.score, ratingData.comment);
            alert("¡Gracias por su calificación!");
            setShowRatingModal(false);
            fetchData(); // Refresh to potentially show updated status or hide button
        } catch (error) {
            console.error(error);
            alert("Error al enviar calificación");
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'OPEN': return 'bg-blue-100 text-blue-800';
            case 'RESOLVED': return 'bg-green-100 text-green-800';
            case 'CLOSED': return 'bg-gray-100 text-gray-800';
            default: return 'bg-yellow-100 text-yellow-800';
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Mesa de Ayuda</h1>
                <button
                    onClick={() => setShowModal(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                    + Nuevo Ticket
                </button>
            </div>

            {/* Ticket List */}
            <div className="grid gap-4">
                {tickets.map(ticket => (
                    <div key={ticket.id} className="bg-white p-4 rounded-lg shadow border border-gray-200 flex justify-between items-center">
                        <div>
                            <div className="flex items-center gap-2">
                                <Link to={`/dashboard/helpdesk/tickets/${ticket.id}`} className="font-bold text-lg hover:underline text-blue-600">
                                    #{ticket.id} {ticket.title}
                                </Link>
                                <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(ticket.status)}`}>
                                    {ticket.status}
                                </span>
                            </div>
                            <p className="text-gray-600 mt-1">{ticket.category_name}</p>
                            <p className="text-sm text-gray-500 mt-2">Actualizado: {new Date(ticket.updated_at).toLocaleDateString()}</p>
                        </div>

                        <div className="text-right">
                            {(ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') && !ticket.survey && (
                                <button
                                    onClick={() => handleRateClick(ticket)}
                                    className="text-sm text-blue-600 hover:underline border border-blue-600 px-3 py-1 rounded hover:bg-blue-50"
                                >
                                    Calificar Atención
                                </button>
                            )}
                            {ticket.survey && (
                                <span className="text-sm text-yellow-600 font-bold">
                                    ★ {ticket.survey.rating}/5
                                </span>
                            )}
                        </div>
                    </div>
                ))}

                {tickets.length === 0 && (
                    <p className="text-center text-gray-500 py-10">No tienes tickets registrados.</p>
                )}
            </div>

            {/* Create Ticket Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold mb-4">Nuevo Ticket</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700">Categoría</label>
                                <select
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    required
                                    value={newTicket.category}
                                    onChange={e => setNewTicket({ ...newTicket, category: e.target.value })}
                                >
                                    <option value="">Seleccione...</option>
                                    {catalog.filter(c => !c.parent).map(parent => {
                                        const children = catalog.filter(c => c.parent === parent.id);
                                        return (
                                            <React.Fragment key={parent.id}>
                                                <option value={parent.id} className="font-bold">{parent.name}</option>
                                                {children.map(child => (
                                                    <option key={child.id} value={child.id}>
                                                        &nbsp;&nbsp;-- {child.name}
                                                    </option>
                                                ))}
                                            </React.Fragment>
                                        );
                                    })}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">Asunto</label>
                                <input
                                    type="text"
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    required
                                    value={newTicket.title}
                                    onChange={e => setNewTicket({ ...newTicket, title: e.target.value })}
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">Descripción</label>
                                <textarea
                                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border"
                                    rows="3"
                                    required
                                    value={newTicket.description}
                                    onChange={e => setNewTicket({ ...newTicket, description: e.target.value })}
                                ></textarea>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700">Adjuntar Archivo (Opcional)</label>
                                <input
                                    type="file"
                                    className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                                    onChange={e => setNewTicket({ ...newTicket, file: e.target.files[0] })}
                                />
                            </div>

                            <div className="flex justify-end gap-2 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                >
                                    Crear Ticket
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Rating Modal */}
            {showRatingModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-sm text-center">
                        <h3 className="text-xl font-bold mb-4">Calificar Atención</h3>
                        <p className="text-gray-600 mb-4">¿Cómo calificaría el servicio recibido?</p>

                        <div className="flex justify-center gap-2 mb-4">
                            {[1, 2, 3, 4, 5].map(star => (
                                <button
                                    key={star}
                                    onClick={() => setRatingData({ ...ratingData, score: star })}
                                    className={`text-3xl focus:outline-none ${star <= ratingData.score ? 'text-yellow-400' : 'text-gray-300'}`}
                                >
                                    ★
                                </button>
                            ))}
                        </div>

                        <textarea
                            className="w-full border rounded p-2 mb-4 text-sm"
                            rows="3"
                            placeholder="Comentario opcional..."
                            value={ratingData.comment}
                            onChange={e => setRatingData({ ...ratingData, comment: e.target.value })}
                        ></textarea>

                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => setShowRatingModal(false)}
                                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={submitRating}
                                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                                Enviar Calificación
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TicketPortal;
