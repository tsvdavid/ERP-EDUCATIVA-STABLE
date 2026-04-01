import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import treasuryService from '../../services/treasuryService';
import toast from 'react-hot-toast';

const TreasuryDebitNoteForm = () => {
    const navigate = useNavigate();
    const [invoices, setInvoices] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [formData, setFormData] = useState({
        invoice: '',
        reason: '',
        amount: '',
        status: 'ISSUED'
    });

    useEffect(() => {
        loadInvoices();
    }, []);

    const loadInvoices = async () => {
        try {
            const data = await treasuryService.getInvoices();
            const issuedInvoices = data.filter(inv => inv.status !== 'CANCELLED' && inv.status !== 'DRAFT');
            setInvoices(issuedInvoices);
        } catch (error) {
            toast.error('Error al cargar facturas');
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.invoice || !formData.amount || !formData.reason) {
            toast.error('Por favor complete todos los campos');
            return;
        }

        try {
            setIsSubmitting(true);
            await treasuryService.createDebitNote(formData);
            toast.success('Nota de Débito generada exitosamente');
            navigate('/dashboard/treasury/debit-notes');
        } catch (error) {
            toast.error(error.response?.data?.error || 'Error al crear la nota de débito');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Nueva Nota de Débito (Ventas)</h1>
            </div>

            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Factura de Referencia <span className="text-red-500">*</span>
                        </label>
                        <select
                            required
                            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                            value={formData.invoice}
                            onChange={(e) => setFormData({ ...formData, invoice: e.target.value })}
                        >
                            <option value="">Seleccione una factura</option>
                            {invoices.map((inv) => (
                                <option key={inv.id} value={inv.id}>
                                    {inv.number} - {inv.student_name} (${inv.total})
                                </option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Motivo de Recargo <span className="text-red-500">*</span>
                        </label>
                        <textarea
                            required
                            rows={3}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                            value={formData.reason}
                            onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                            placeholder="Ej. Cheque protestado, recargo por mora..."
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Monto Adicional ($) <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="number"
                            required
                            step="0.01"
                            min="0.01"
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                            value={formData.amount}
                            onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        />
                    </div>

                    <div className="flex justify-end pt-4 space-x-3">
                        <button
                            type="button"
                            onClick={() => navigate('/dashboard/treasury/debit-notes')}
                            className="bg-white dark:bg-gray-700 py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="bg-indigo-600 border border-transparent rounded-md shadow-sm py-2 px-4 inline-flex justify-center text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                        >
                            {isSubmitting ? 'Guardando...' : 'Generar Nota de Débito'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default TreasuryDebitNoteForm;
