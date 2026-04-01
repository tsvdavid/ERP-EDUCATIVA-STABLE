import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import purchaseService from '../../services/purchaseService';

const DebitNotesPage = () => {
    const navigate = useNavigate();
    const [notes, setNotes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedNote, setSelectedNote] = useState(null);

    useEffect(() => {
        loadNotes();
    }, []);

    const loadNotes = async () => {
        try {
            const data = await purchaseService.getDebitNotes();
            setNotes(data);
        } catch (error) {
            console.error("Error loading debit notes", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Notas de Débito (Proveedores)</h1>
                <button
                    onClick={() => navigate('/dashboard/purchases/debit-notes/new')}
                    className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
                >
                    Nueva Nota de Débito
                </button>
            </div>

            {loading ? (
                <div>Cargando...</div>
            ) : (
                <div className="bg-white rounded-lg shadow overflow-x-auto">
                    <table className="min-w-[800px] sm:min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nro. ND</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proveedor</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Factura Base</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Motivo</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {notes.length === 0 ? (
                                <tr><td colSpan="6" className="px-6 py-4 text-center text-gray-500">No hay notas de débito registradas.</td></tr>
                            ) : notes.map(note => (
                                <tr key={note.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">{note.document_number}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{note.supplier_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{note.invoice_number}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{note.issue_date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">${note.total}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{note.reason}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button onClick={() => setSelectedNote(note)} className="text-indigo-600 hover:text-indigo-900">Ver</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* View Modal */}
            {selectedNote && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
                    <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-lg">
                        <div className="flex justify-between items-center mb-4 pb-2 border-b">
                            <h2 className="text-xl font-bold text-gray-800">Detalles Nota de Débito</h2>
                            <button onClick={() => setSelectedNote(null)} className="text-gray-500 hover:text-gray-700 text-2xl font-bold">&times;</button>
                        </div>
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-md">
                                <div>
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide">Proveedor</p>
                                    <p className="text-sm font-medium text-gray-900">{selectedNote.supplier_name}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide">Factura Base</p>
                                    <p className="text-sm font-medium text-gray-900">{selectedNote.invoice_number}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide">Nro. de Documento</p>
                                    <p className="text-sm font-medium text-gray-900">{selectedNote.document_number}</p>
                                </div>
                                <div>
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide">Fecha Emisión</p>
                                    <p className="text-sm font-medium text-gray-900">{selectedNote.issue_date}</p>
                                </div>
                                <div className="col-span-2">
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide">Código de Autorización</p>
                                    <p className="text-sm font-medium text-gray-900">{selectedNote.authorization_code || '-'}</p>
                                </div>
                                <div className="col-span-2">
                                    <p className="text-xs text-gray-500 font-bold uppercase tracking-wide">Motivo</p>
                                    <p className="text-sm font-medium text-gray-900">{selectedNote.reason}</p>
                                </div>
                            </div>

                            <div className="bg-slate-50 p-4 rounded-md mt-4">
                                <h3 className="text-sm font-bold text-gray-800 mb-2 border-b pb-1">Montos</h3>
                                <div className="space-y-1 text-sm">
                                    <div className="flex justify-between text-gray-600"><span>Subtotal 0%:</span> <span>${parseFloat(selectedNote.subtotal_0 || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-gray-600"><span>Subtotal 15%:</span> <span>${parseFloat(selectedNote.subtotal_15 || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-gray-600"><span>IVA 15%:</span> <span>${parseFloat(selectedNote.iva || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between font-bold text-gray-800 pt-1 border-t mt-1"><span>Total:</span> <span>${parseFloat(selectedNote.total || 0).toFixed(2)}</span></div>
                                </div>
                            </div>
                        </div>
                        <div className="mt-6 flex justify-end">
                            <button onClick={() => setSelectedNote(null)} className="bg-gray-100 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-200">
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DebitNotesPage;
