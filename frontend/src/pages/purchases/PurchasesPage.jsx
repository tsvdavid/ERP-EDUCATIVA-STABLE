import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import purchaseService from '../../services/purchaseService';

const PurchasesPage = () => {
    const navigate = useNavigate();
    const [invoices, setInvoices] = useState([]);
    const [loading, setLoading] = useState(true);

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
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
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
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        {inv.status === 'DRAFT' && (
                                            <button onClick={() => handleValidate(inv.id)} className="text-blue-600 hover:text-blue-900 mr-4">Validar</button>
                                        )}
                                        <button className="text-indigo-600 hover:text-indigo-900">Ver</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default PurchasesPage;
