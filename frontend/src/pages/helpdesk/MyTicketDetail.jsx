import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import helpdeskService from '../../services/helpdeskService';

const MyTicketDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [ticket, setTicket] = useState(null);
    const [loading, setLoading] = useState(true);
    const [newComment, setNewComment] = useState('');
    const [newFile, setNewFile] = useState(null);
    const [ratingScore, setRatingScore] = useState(5);
    const [ratingComment, setRatingComment] = useState('');

    useEffect(() => {
        loadTicket();
    }, [id]);

    const loadTicket = async () => {
        try {
            const res = await helpdeskService.getTicket(id);
            setTicket(res.data);
        } catch (error) {
            alert("No se pudo cargar el ticket");
            navigate(-1);
        } finally {
            setLoading(false);
        }
    };

    const handleAddComment = async () => {
        if (!newComment.trim()) return;
        try {
            await helpdeskService.addComment({
                ticket: id,
                content: newComment
            });
            setNewComment('');
            loadTicket(); // Reload to see new comment
        } catch (error) {
            alert("Error al añadir comentario");
        }
    };

    const handleUpload = async () => {
        if (!newFile) return;
        try {
            await helpdeskService.addAttachment({
                ticket: id,
                file: newFile
            });
            setNewFile(null);
            alert("Archivo adjuntado");
            loadTicket();
        } catch (error) {
            alert("Error al subir archivo");
        }
    };

    const handleRate = async () => {
        try {
            await helpdeskService.rateTicket(id, ratingScore, ratingComment);
            alert("¡Gracias por su calificación!");
            loadTicket();
        } catch (error) {
            alert("Error al enviar calificación");
        }
    };

    if (loading) return <div>Cargando...</div>;
    if (!ticket) return <div>Ticket no encontrado</div>;

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <button onClick={() => navigate(-1)} className="text-blue-600 mb-4 hover:underline">← Volver a Mis Tickets</button>

            <div className="bg-white shadow rounded-lg p-6 mb-6">
                <div className="flex justify-between items-start border-b pb-4 mb-4">
                    <div>
                        <h1 className="text-2xl font-bold">#{ticket.id} {ticket.title}</h1>
                        <p className="text-gray-500">{ticket.category_name}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-bold 
                        ${ticket.status === 'OPEN' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                        {ticket.status}
                    </span>
                </div>

                <div className="mb-6">
                    <h3 className="font-bold text-gray-700 mb-2">Descripción Original</h3>
                    <p className="p-4 bg-gray-50 rounded text-gray-800 whitespace-pre-wrap">{ticket.description}</p>
                </div>

                {/* Rating Section - Only if Resolved/Closed */}
                {(ticket.status === 'RESOLVED' || ticket.status === 'CLOSED') && (
                    <div className="mb-6 bg-blue-50 p-4 rounded border border-blue-200">
                        <h3 className="font-bold text-blue-800 mb-2">Encuesta de Satisfacción</h3>

                        {ticket.survey ? (
                            <div>
                                <div className="text-2xl text-yellow-500 font-bold mb-1">
                                    {'★'.repeat(ticket.survey.rating)}{'☆'.repeat(5 - ticket.survey.rating)}
                                </div>
                                {ticket.survey.comment && <p className="text-gray-700 italic">"{ticket.survey.comment}"</p>}
                                <p className="text-xs text-gray-500 mt-2">Gracias por su feedback.</p>
                            </div>
                        ) : (
                            <div>
                                <p className="text-sm text-gray-700 mb-3">Por favor califique la atención recibida para cerrar este ticket.</p>
                                <div className="flex gap-2 mb-3">
                                    {[1, 2, 3, 4, 5].map(star => (
                                        <button
                                            key={star}
                                            onClick={() => setRatingScore(star)}
                                            className={`text-3xl focus:outline-none ${star <= ratingScore ? 'text-yellow-400' : 'text-gray-300'}`}
                                        >
                                            ★
                                        </button>
                                    ))}
                                </div>
                                <textarea
                                    className="w-full border rounded p-2 mb-2 text-sm"
                                    rows="2"
                                    placeholder="Comentario sobre el servicio (opcional)..."
                                    value={ratingComment}
                                    onChange={e => setRatingComment(e.target.value)}
                                ></textarea>
                                <button
                                    onClick={handleRate}
                                    className="bg-blue-600 text-white px-4 py-1.5 rounded text-sm hover:bg-blue-700"
                                >
                                    Enviar Calificación
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {/* Attachments Section */}
                <div className="mb-6">
                    <h3 className="font-bold text-gray-700 mb-2">Archivos Adjuntos</h3>
                    {ticket.attachments && ticket.attachments.length > 0 ? (
                        <ul className="list-disc list-inside">
                            {ticket.attachments.map(att => (
                                <li key={att.id} className="text-blue-600">
                                    <a href={att.file} target="_blank" rel="noopener noreferrer" className="hover:underline">
                                        {att.filename || 'Archivo'}
                                    </a>
                                    <span className="text-xs text-gray-400 ml-2">({new Date(att.created_at).toLocaleString()})</span>
                                </li>
                            ))}
                        </ul>
                    ) : <p className="text-gray-400 italic">No hay adjuntos.</p>}

                    <div className="mt-2 flex gap-2 items-center">
                        <input
                            type="file"
                            className="text-sm"
                            onChange={e => setNewFile(e.target.files[0])}
                        />
                        <button
                            onClick={handleUpload}
                            disabled={!newFile}
                            className="text-xs bg-gray-200 px-3 py-1 rounded hover:bg-gray-300 disabled:opacity-50"
                        >
                            Subir
                        </button>
                    </div>
                </div>

                {/* Comments Section */}
                <div>
                    <h3 className="font-bold text-gray-700 mb-4">Actividad y Comentarios</h3>
                    <div className="space-y-4 mb-6">
                        {ticket.comments && ticket.comments.length > 0 ? (
                            ticket.comments.map(comment => (
                                <div key={comment.id} className="bg-gray-50 p-3 rounded">
                                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                                        <span className="font-bold">{comment.author_name}</span>
                                        <span>{new Date(comment.created_at).toLocaleString()}</span>
                                    </div>
                                    <p className="text-sm text-gray-800 whitespace-pre-wrap">{comment.content}</p>
                                </div>
                            ))
                        ) : <p className="text-gray-400 italic">No hay comentarios aún.</p>}
                    </div>

                    <div className="flex flex-col gap-2">
                        <textarea
                            className="border p-2 rounded w-full"
                            placeholder="Escribir un comentario..."
                            rows="3"
                            value={newComment}
                            onChange={e => setNewComment(e.target.value)}
                        ></textarea>
                        <div className="text-right">
                            <button
                                onClick={handleAddComment}
                                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                            >
                                Enviar Comentario
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MyTicketDetail;
