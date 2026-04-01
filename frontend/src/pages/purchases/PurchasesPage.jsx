import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { XCircle } from 'lucide-react';
import purchaseService from '../../services/purchaseService';

const PurchasesPage = () => {
    const navigate = useNavigate();
    const [invoices, setInvoices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedInvoice, setSelectedInvoice] = useState(null);

    useEffect(() => {
        loadInvoices();
    }, []);

    const loadInvoices = async () => {
        try {
            const data = await purchaseService.getInvoices();
            setInvoices(data);
        } catch (error) {
            console.error("Error loading invoices", error);
        } finally {
            setLoading(false);
        }
    };

    const handleValidate = async (id) => {
        if (window.confirm('¿Validar factura? Se generará el asiento contable.')) {
            try {
                await purchaseService.validateInvoice(id);
                loadInvoices();
            } catch (error) {
                console.error("Error validating", error);
                alert("Error al validar factura");
            }
        }
    };

    const handleCancelInvoice = async (id) => {
        if (!window.confirm("¿Está seguro de anular esta factura? El estado pasará a Anulado.")) return;

        try {
            await purchaseService.cancelInvoice(id);
            loadInvoices();
        } catch (error) {
            console.error("Error cancelling", error);
            alert("Error al anular la factura");
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Facturas de Compra</h1>
                <button
                    onClick={() => navigate('/dashboard/purchases/invoices/new')}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                >
                    Nueva Compra
                </button>
            </div>

            {loading ? (
                <div>Cargando...</div>
            ) : (
                <div className="bg-white rounded-lg shadow overflow-x-auto">
                    <table className="min-w-[800px] sm:min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nro.</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Proveedor</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {invoices.map(inv => (
                                <tr key={inv.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">{inv.document_number}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{inv.supplier_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{inv.issue_date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">${inv.total}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${inv.status === 'VALIDATED' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                                            }`}>
                                            {inv.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end items-center gap-2">
                                        {inv.status === 'DRAFT' && (
                                            <>
                                                <button onClick={() => handleValidate(inv.id)} className="text-blue-600 hover:text-blue-900">Validar</button>
                                                <button onClick={() => handleCancelInvoice(inv.id)} className="text-red-500 hover:text-red-700 mx-2" title="Anular"><XCircle size={18} /></button>
                                            </>
                                        )}
                                        <button onClick={() => setSelectedInvoice(inv)} className="text-indigo-600 hover:text-indigo-900">Ver</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* View Details Modal */}
            {selectedInvoice && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">
                        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
                            <h3 className="text-lg font-bold text-slate-800">
                                Factura de Compra: {selectedInvoice.document_number}
                            </h3>
                            <button onClick={() => setSelectedInvoice(null)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">&times;</button>
                        </div>
                        <div className="p-6 overflow-y-auto">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-sm bg-slate-50 p-4 rounded-lg border border-slate-100">
                                <div><span className="text-slate-500 block text-xs uppercase mb-1">Proveedor</span> <span className="font-semibold text-slate-800">{selectedInvoice.supplier_name}</span></div>
                                <div><span className="text-slate-500 block text-xs uppercase mb-1">Cédula/RUC</span> <span className="font-medium text-slate-700">{selectedInvoice.supplier_tax_id || '-'}</span></div>
                                <div><span className="text-slate-500 block text-xs uppercase mb-1">Fecha Emisión</span> <span className="font-medium text-slate-700">{selectedInvoice.issue_date}</span></div>
                                <div><span className="text-slate-500 block text-xs uppercase mb-1">Estado</span> <span className={`font-semibold ${selectedInvoice.status === 'VALIDATED' ? 'text-green-600' : 'text-yellow-600'}`}>{selectedInvoice.status}</span></div>

                                <div className="col-span-2"><span className="text-slate-500 block text-xs uppercase mb-1">Autorización SRI</span> <span className="font-medium text-slate-700">{selectedInvoice.authorization_number || '-'}</span></div>
                                <div className="col-span-2"><span className="text-slate-500 block text-xs uppercase mb-1">Sustento Tributario</span> <span className="font-medium text-slate-700">{selectedInvoice.tax_support_code || '-'}</span></div>
                            </div>

                            <h4 className="font-bold text-slate-700 mb-3">Detalle de Productos/Servicios</h4>
                            {selectedInvoice.items && selectedInvoice.items.length > 0 ? (
                                <div className="overflow-x-auto border border-slate-200 rounded-lg mb-6">
                                    <table className="w-full text-sm text-left">
                                        <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200">
                                            <tr>
                                                <th className="px-4 py-3">Descripción</th>
                                                <th className="px-4 py-3 text-right">Cant.</th>
                                                <th className="px-4 py-3 text-right">Precio Unit.</th>
                                                <th className="px-4 py-3 text-right">Desc.</th>
                                                <th className="px-4 py-3 text-right">Subtotal</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {selectedInvoice.items.map(item => (
                                                <tr key={item.id} className="hover:bg-slate-50">
                                                    <td className="px-4 py-3 font-medium text-slate-800">
                                                        {item.description}
                                                        <div className="text-xs text-slate-400">IVA: {item.tax_percentage}%</div>
                                                    </td>
                                                    <td className="px-4 py-3 text-right">{parseFloat(item.quantity).toFixed(2)}</td>
                                                    <td className="px-4 py-3 text-right">${parseFloat(item.unit_price).toFixed(2)}</td>
                                                    <td className="px-4 py-3 text-right">${parseFloat(item.discount || 0).toFixed(2)}</td>
                                                    <td className="px-4 py-3 text-right font-medium">${parseFloat(item.subtotal).toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p className="text-slate-500 italic text-sm text-center py-4 bg-slate-50 rounded-lg border border-dashed border-slate-200 mb-6">
                                    Esta factura no tiene detalles de ítems registrados o no están disponibles en esta vista.
                                </p>
                            )}

                            <div className="flex justify-end">
                                <div className="w-64 space-y-2 text-sm">
                                    <div className="flex justify-between text-slate-600"><span>Subtotal 12%:</span> <span>${parseFloat(selectedInvoice.subtotal_taxable || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-slate-600"><span>Subtotal 0%:</span> <span>${parseFloat(selectedInvoice.subtotal_zero_tax || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-slate-600"><span>Descuento:</span> <span>${parseFloat(selectedInvoice.total_discount || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-slate-600"><span>IVA 12%:</span> <span>${parseFloat(selectedInvoice.total_tax || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between font-bold text-lg text-slate-800 pt-2 border-t mt-2"><span>Total:</span> <span>${parseFloat(selectedInvoice.total).toFixed(2)}</span></div>
                                </div>
                            </div>
                        </div>
                        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end">
                            <button onClick={() => setSelectedInvoice(null)} className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 font-medium">
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PurchasesPage;
