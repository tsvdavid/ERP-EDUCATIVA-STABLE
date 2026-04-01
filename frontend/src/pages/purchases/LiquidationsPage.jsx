import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { XCircle } from 'lucide-react';
import purchaseService from '../../services/purchaseService';

const LiquidationsPage = () => {
    const navigate = useNavigate();
    const [liquidations, setLiquidations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedLiquidation, setSelectedLiquidation] = useState(null);

    useEffect(() => {
        loadLiquidations();
    }, []);

    const loadLiquidations = async () => {
        try {
            const data = await purchaseService.getLiquidations();
            setLiquidations(data);
        } catch (error) {
            console.error("Error loading liquidations", error);
        } finally {
            setLoading(false);
        }
    };

    const handleValidate = async (id) => {
        if (window.confirm('¿Validar liquidación? Se generará el asiento contable correspondiente.')) {
            try {
                // Same pattern as invoice: assuming there is a /validate/ action in the ViewSet.
                await purchaseService.api.post(`/purchases/liquidations/${id}/validate/`);
                loadLiquidations();
            } catch (error) {
                console.error("Error validating", error);
                alert("Error al validar la liquidación");
            }
        }
    };

    const handleCancelLiquidation = async (id) => {
        if (!window.confirm("¿Está seguro de anular esta liquidación de compra?")) return;

        try {
            await purchaseService.cancelLiquidation(id);
            loadLiquidations();
        } catch (error) {
            console.error("Error cancelling", error);
            alert("Error al anular la liquidación");
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Liquidaciones de Compra</h1>
                <button
                    onClick={() => navigate('/dashboard/purchases/liquidations/new')}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 shadow-sm"
                >
                    Nueva Liquidación
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
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Emisión</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Monto Total</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {liquidations.map(liq => (
                                <tr key={liq.id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{liq.document_number}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{liq.supplier_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{liq.issue_date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">${parseFloat(liq.total).toFixed(2)}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                            ${liq.status === 'VALIDATED' ? 'bg-green-100 text-green-800' :
                                                liq.status === 'CANCELLED' ? 'bg-red-100 text-red-800' :
                                                    'bg-yellow-100 text-yellow-800'}`}>
                                            {liq.status === 'VALIDATED' ? 'VALIDADA' : liq.status === 'CANCELLED' ? 'ANULADA' : 'BORRADOR'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium flex justify-end items-center gap-3">
                                        {liq.status === 'DRAFT' && (
                                            <>
                                                <button onClick={() => handleValidate(liq.id)} className="text-blue-600 hover:text-blue-900 font-semibold border border-blue-200 px-2 py-1 rounded bg-blue-50">Validar</button>
                                                <button onClick={() => handleCancelLiquidation(liq.id)} className="text-red-500 hover:text-red-700" title="Anular"><XCircle size={18} /></button>
                                            </>
                                        )}
                                        <button onClick={() => setSelectedLiquidation(liq)} className="text-indigo-600 hover:text-indigo-900 font-semibold px-2">Ver Detalles</button>
                                    </td>
                                </tr>
                            ))}
                            {liquidations.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                                        No se encontraron liquidaciones de compra.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}

            {/* View Details Modal */}
            {selectedLiquidation && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-xl max-w-4xl w-full overflow-hidden border border-slate-200 flex flex-col max-h-[90vh]">
                        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
                            <h3 className="text-lg font-bold text-slate-800">
                                Liquidación de Compra: {selectedLiquidation.document_number}
                            </h3>
                            <button onClick={() => setSelectedLiquidation(null)} className="text-slate-400 hover:text-slate-600 font-bold text-xl">&times;</button>
                        </div>
                        <div className="p-6 overflow-y-auto">
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-sm bg-slate-50 p-4 rounded-lg border border-slate-100">
                                <div className="col-span-2"><span className="text-slate-500 block text-xs uppercase mb-1">Proveedor</span> <span className="font-semibold text-slate-800">{selectedLiquidation.supplier_name}</span></div>
                                <div><span className="text-slate-500 block text-xs uppercase mb-1">Fecha Emisión</span> <span className="font-medium text-slate-700">{selectedLiquidation.issue_date}</span></div>
                                <div><span className="text-slate-500 block text-xs uppercase mb-1">Estado</span> <span className={`font-semibold ${selectedLiquidation.status === 'VALIDATED' ? 'text-green-600' : selectedLiquidation.status === 'CANCELLED' ? 'text-red-600' : 'text-yellow-600'}`}>{selectedLiquidation.status}</span></div>

                                <div className="col-span-2"><span className="text-slate-500 block text-xs uppercase mb-1">Autorización</span> <span className="font-medium text-slate-700">{selectedLiquidation.authorization_code || '-'}</span></div>
                                <div className="col-span-2"><span className="text-slate-500 block text-xs uppercase mb-1">Método de Pago</span> <span className="font-medium text-slate-700">{selectedLiquidation.payment_method}</span></div>
                            </div>

                            <h4 className="font-bold text-slate-700 mb-3">Detalle de Bienes y Servicios</h4>
                            {selectedLiquidation.items && selectedLiquidation.items.length > 0 ? (
                                <div className="overflow-x-auto border border-slate-200 rounded-lg mb-6">
                                    <table className="min-w-[700px] w-full text-sm text-left">
                                        <thead className="text-xs text-slate-500 bg-slate-50 border-b border-slate-200">
                                            <tr>
                                                <th className="px-4 py-3">Descripción / Cuenta de Gasto</th>
                                                <th className="px-4 py-3 text-right">Cant.</th>
                                                <th className="px-4 py-3 text-right">Precio Unit.</th>
                                                <th className="px-4 py-3 text-right">Subtotal</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-100">
                                            {selectedLiquidation.items.map(item => (
                                                <tr key={item.id} className="hover:bg-slate-50">
                                                    <td className="px-4 py-3">
                                                        <span className="font-medium text-slate-800 block">{item.description}</span>
                                                        <span className="text-xs text-slate-500 mt-1 block">
                                                            {item.expense_account_name ? `Cuenta: ${item.expense_account_name}` : 'Sin cuenta vinculada'} | IVA: {item.tax_rate}%
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3 text-right text-slate-700">{parseFloat(item.quantity).toFixed(2)}</td>
                                                    <td className="px-4 py-3 text-right text-slate-700">${parseFloat(item.unit_price).toFixed(2)}</td>
                                                    <td className="px-4 py-3 text-right font-medium text-slate-900">${parseFloat(item.subtotal).toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p className="text-slate-500 italic text-sm text-center py-4 bg-slate-50 rounded-lg border border-dashed border-slate-200 mb-6">
                                    No hay detalles registrados para esta liquidación.
                                </p>
                            )}

                            <div className="flex justify-end pr-4">
                                <div className="w-64 space-y-2 text-sm bg-slate-50 p-4 rounded-lg border border-slate-100">
                                    <div className="flex justify-between text-slate-600"><span>Subtotal 15%:</span> <span className="font-medium">${parseFloat(selectedLiquidation.subtotal_15 || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-slate-600"><span>Subtotal 0%:</span> <span className="font-medium">${parseFloat(selectedLiquidation.subtotal_0 || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-slate-600"><span>Subtotal No Objeto:</span> <span className="font-medium">${parseFloat(selectedLiquidation.subtotal_no_obj || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between text-slate-600 border-b border-slate-200 pb-2 mb-2"><span>IVA 15%:</span> <span className="font-medium">${parseFloat(selectedLiquidation.iva || 0).toFixed(2)}</span></div>
                                    <div className="flex justify-between font-bold text-lg text-slate-800 pt-2"><span>Total General:</span> <span>${parseFloat(selectedLiquidation.total).toFixed(2)}</span></div>
                                </div>
                            </div>
                        </div>
                        <div className="px-6 py-4 border-t border-slate-100 bg-slate-50 flex justify-end">
                            <button onClick={() => setSelectedLiquidation(null)} className="px-5 py-2 border border-slate-300 rounded-lg text-slate-700 shadow-sm hover:bg-slate-100 font-medium transition-colors">
                                Cerrar Ventana
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LiquidationsPage;
