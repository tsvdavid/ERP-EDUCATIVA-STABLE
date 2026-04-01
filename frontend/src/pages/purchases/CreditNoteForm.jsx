import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import purchaseService from '../../services/purchaseService';

const CreditNoteForm = () => {
    const navigate = useNavigate();
    const [invoices, setInvoices] = useState([]);

    const [formData, setFormData] = useState({
        invoice: '',
        document_number: '',
        authorization_code: '',
        issue_date: new Date().toISOString().split('T')[0],
        reason: '',
        subtotal_0: 0,
        subtotal_15: 0,
        subtotal_no_obj: 0,
        tax_rate: '15'
    });

    useEffect(() => {
        const fetchInvoices = async () => {
            try {
                const invs = await purchaseService.getInvoices();
                // Solo cargar facturas validadas para aplicar notas de credito
                const validatedInvs = invs.filter(inv => inv.status === 'VALIDATED');
                setInvoices(validatedInvs);
            } catch (error) {
                console.error("Error loading invoices", error);
            }
        };
        fetchInvoices();
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubtotalChange = (e) => {
        const value = parseFloat(e.target.value) || 0;
        const taxRate = formData.tax_rate;

        let newSubtotal0 = 0;
        let newSubtotal15 = 0;

        if (taxRate === '0') {
            newSubtotal0 = value;
            newSubtotal15 = 0;
        } else if (taxRate === '15') {
            newSubtotal15 = value;
            newSubtotal0 = 0;
        }

        setFormData(prev => ({
            ...prev,
            subtotal_0: newSubtotal0,
            subtotal_15: newSubtotal15
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Preparar payload para evitar issues con drf decimals
        const taxRate = formData.tax_rate;
        const subtotal = taxRate === '0' ? parseFloat(formData.subtotal_0) : parseFloat(formData.subtotal_15);
        const iva = taxRate === '15' ? (subtotal * 0.15).toFixed(2) : '0.00';

        const payload = {
            invoice: parseInt(formData.invoice),
            document_number: formData.document_number,
            authorization_code: formData.authorization_code,
            issue_date: formData.issue_date,
            reason: formData.reason,
            subtotal_0: formData.subtotal_0.toString(),
            subtotal_15: formData.subtotal_15.toString(),
            subtotal_no_obj: formData.subtotal_no_obj.toString(),
            iva: iva.toString()
        };

        try {
            await purchaseService.createCreditNote(payload);
            navigate('/dashboard/purchases/credit-notes');
        } catch (error) {
            console.error("Error al registrar", error);
            alert("Error al guardar la Nota de Crédito. Verifique que el Secuencial no esté repetido o falten campos.");
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Nueva Nota de Crédito</h1>
                <button
                    onClick={() => navigate('/dashboard/purchases/credit-notes')}
                    className="text-slate-500 hover:text-slate-700 font-medium"
                >
                    Volver
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Selector de Factura Padre */}
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-slate-700 mb-1">Factura Base a Modificar *</label>
                            <select
                                name="invoice"
                                value={formData.invoice}
                                onChange={handleChange}
                                required
                                className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            >
                                <option value="">Seleccione una factura validada...</option>
                                {invoices.map(inv => (
                                    <option key={inv.id} value={inv.id}>
                                        {inv.supllier_name || `Prov. #${inv.supplier}`} - {inv.document_number} - Total: ${inv.total}
                                    </option>
                                ))}
                            </select>
                            <p className="text-xs text-slate-500 mt-1">Sólo se muestran facturas en estado VALIDATED.</p>
                        </div>

                        {/* Datos de Comprobante NC */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Nro. de Documento (Secuencial completo) *</label>
                            <input
                                type="text"
                                name="document_number"
                                placeholder="001-002-000000001"
                                value={formData.document_number}
                                onChange={handleChange}
                                required
                                maxLength="17"
                                className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Clave de Acceso SRI</label>
                            <input
                                type="text"
                                name="authorization_code"
                                value={formData.authorization_code}
                                onChange={handleChange}
                                maxLength="49"
                                className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Fecha Emisión *</label>
                            <input
                                type="date"
                                name="issue_date"
                                value={formData.issue_date}
                                onChange={handleChange}
                                required
                                className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1">Motivo de la Emisión *</label>
                            <input
                                type="text"
                                name="reason"
                                placeholder="Ej: Devolución Mercadería"
                                value={formData.reason}
                                onChange={handleChange}
                                required
                                maxLength="255"
                                className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                        </div>

                        {/* Calculadora Moneda */}
                        <div className="md:col-span-2 mt-4 pt-4 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Valor a Afectar (Subtotal sin Imp) *</label>
                                <div className="relative">
                                    <span className="absolute left-3 top-2 text-slate-500">$</span>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        placeholder="0.00"
                                        value={formData.tax_rate === '0' ? formData.subtotal_0 : formData.subtotal_15}
                                        onChange={handleSubtotalChange}
                                        required
                                        className="w-full pl-8 border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Tarifa IVA de la devolución *</label>
                                <select
                                    name="tax_rate"
                                    value={formData.tax_rate}
                                    onChange={(e) => {
                                        handleChange(e);
                                        // Reset subtotales on tax rate change to force user to re-input correctly
                                        setFormData(prev => ({ ...prev, tax_rate: e.target.value, subtotal_0: 0, subtotal_15: 0 }));
                                    }}
                                    className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                >
                                    <option value="15">IVA (15%)</option>
                                    <option value="0">TARIFA 0%</option>
                                </select>
                            </div>
                        </div>

                        <div className="md:col-span-2 pt-4 flex gap-4 items-center justify-end border-t border-slate-100 mt-2">
                            <div className="text-right mr-4 text-slate-600">
                                <p className="text-sm">Subtotal 15%: ${formData.subtotal_15}</p>
                                <p className="text-sm">Subtotal 0%: ${formData.subtotal_0}</p>
                                <p className="text-sm">IVA Calculado: ${(formData.tax_rate === '15' ? (formData.subtotal_15 * 0.15) : 0).toFixed(2)}</p>
                                <p className="text-lg font-bold text-slate-800 mt-1">Total: $
                                    {(
                                        parseFloat(formData.subtotal_0) +
                                        parseFloat(formData.subtotal_15) +
                                        (formData.tax_rate === '15' ? formData.subtotal_15 * 0.15 : 0)
                                    ).toFixed(2)}
                                </p>
                            </div>
                        </div>


                    </div>

                    <div className="flex justify-end gap-3 pt-6 border-t border-slate-200">
                        <button
                            type="button"
                            onClick={() => navigate('/dashboard/purchases/credit-notes')}
                            className="px-6 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 font-medium"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className="px-6 py-2 bg-indigo-600 rounded-lg text-white hover:bg-indigo-700 font-medium"
                        >
                            Guardar Nota
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default CreditNoteForm;
