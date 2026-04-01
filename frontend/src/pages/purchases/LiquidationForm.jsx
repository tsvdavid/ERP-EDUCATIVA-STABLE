import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import purchaseService from '../../services/purchaseService';
import accountingService from '../../services/accountingService';

const LiquidationForm = () => {
    const navigate = useNavigate();
    const [suppliers, setSuppliers] = useState([]);
    const [accounts, setAccounts] = useState([]);

    // Header Data
    const [liquidationData, setLiquidationData] = useState({
        supplier: '',
        document_number: '',
        authorization_code: '',
        issue_date: new Date().toISOString().slice(0, 10),
        sustento_tributario: '01',
        payment_method: '20'
    });

    // Items
    const [items, setItems] = useState([
        { description: '', expense_account: '', quantity: 1, unit_price: 0, tax_rate: 0, subtotal: 0 }
    ]);

    useEffect(() => {
        const loadData = async () => {
            try {
                const supps = await purchaseService.getSuppliers();
                setSuppliers(supps);

                const accRes = await accountingService.getAccounts({ roots: false });
                const expenseAccounts = accRes.filter(a => a.account_type === 'EXPENSE');
                setAccounts(expenseAccounts);
            } catch (error) {
                console.error("Error loading form data", error);
            }
        };
        loadData();
    }, []);

    const handleHeaderChange = (e) => {
        setLiquidationData({ ...liquidationData, [e.target.name]: e.target.value });
    };

    const handleItemChange = (index, field, value) => {
        const newItems = [...items];
        newItems[index][field] = value;

        if (field === 'quantity' || field === 'unit_price') {
            const qty = parseFloat(newItems[index].quantity) || 0;
            const price = parseFloat(newItems[index].unit_price) || 0;
            newItems[index].subtotal = qty * price;
        }

        setItems(newItems);
    };

    const addItem = () => {
        setItems([...items, { description: '', expense_account: '', quantity: 1, unit_price: 0, tax_rate: 0, subtotal: 0 }]);
    };

    const removeItem = (index) => {
        const newItems = items.filter((_, i) => i !== index);
        if (newItems.length === 0) return;
        setItems(newItems);
    };

    const calculateTotals = () => {
        let sub0 = 0;
        let sub15 = 0;
        let iva = 0;

        items.forEach(item => {
            const val = parseFloat(item.subtotal) || 0;
            const rate = parseInt(item.tax_rate);

            if (rate === 0) sub0 += val;
            if (rate === 15) {
                sub15 += val;
                iva += val * 0.15;
            }
        });

        return { sub0, sub15, iva, total: sub0 + sub15 + iva };
    };

    const totals = calculateTotals();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!liquidationData.supplier) {
            alert("Seleccione un proveedor");
            return;
        }

        const payload = {
            ...liquidationData,
            items: items.map(i => ({
                description: i.description,
                expense_account: i.expense_account || null,
                quantity: i.quantity,
                unit_price: i.unit_price,
                tax_rate: i.tax_rate
            }))
        };

        try {
            await purchaseService.createLiquidation(payload);
            navigate('/dashboard/purchases/liquidations');
        } catch (error) {
            console.error("Error creating liquidation", error);
            alert("Error al guardar la liquidación de compra");
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">Nueva Liquidación de Compra</h1>

            <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
                {/* Header Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Cédula / Proveedor <span className="text-red-500">*</span></label>
                        <select
                            name="supplier"
                            className="block w-full border border-gray-300 rounded shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500"
                            value={liquidationData.supplier}
                            onChange={handleHeaderChange}
                            required
                        >
                            <option value="">-- Seleccionar --</option>
                            {suppliers.map(s => (
                                <option key={s.id} value={s.id}>{s.tax_id} - {s.legal_name}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Número de Liquidación <span className="text-red-500">*</span></label>
                        <input
                            type="text" name="document_number"
                            placeholder="001-001-000000001"
                            className="block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={liquidationData.document_number}
                            onChange={handleHeaderChange}
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Emisión <span className="text-red-500">*</span></label>
                        <input
                            type="date" name="issue_date"
                            className="block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={liquidationData.issue_date}
                            onChange={handleHeaderChange}
                            required
                        />
                    </div>
                    <div className="lg:col-span-3">
                        <label className="block text-sm font-medium text-gray-700 mb-1">Clave de Acceso / Autorización</label>
                        <input
                            type="text" name="authorization_code"
                            className="block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={liquidationData.authorization_code}
                            onChange={handleHeaderChange}
                            placeholder="Si es electrónica, ingrese los 49 dígitos."
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Sustento Tributario</label>
                        <select
                            name="sustento_tributario"
                            className="block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={liquidationData.sustento_tributario}
                            onChange={handleHeaderChange}
                        >
                            <option value="01">01 - Crédito Tributario para declaración de IVA</option>
                            <option value="02">02 - Costo o Gasto para declaración de Renta</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Método de Pago</label>
                        <select
                            name="payment_method"
                            className="block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={liquidationData.payment_method}
                            onChange={handleHeaderChange}
                        >
                            <option value="01">01 - Efectivo (Sin utilización del sist. financiero)</option>
                            <option value="19">19 - Tarjeta de crédito</option>
                            <option value="20">20 - Otros con utilización del sistema financiero</option>
                        </select>
                    </div>
                </div>

                <hr className="my-8 border-gray-100" />

                {/* Items Detail */}
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Bienes y Servicios Adquiridos</h3>
                    <button type="button" onClick={addItem} className="bg-blue-50 text-blue-700 hover:bg-blue-100 px-3 py-1.5 rounded text-sm font-medium transition-colors">
                        + Añadir Fila
                    </button>
                </div>

                <div className="overflow-x-auto border border-gray-200 rounded-lg">
                    <table className="min-w-[800px] sm:min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Concepto / Descripción</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-48">Cuenta Contable</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Cant.</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">P. Unitario ($)</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-24">Tarifa IVA</th>
                                <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider w-32">Total Disp.</th>
                                <th className="px-2 py-3 text-center w-12"></th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-100">
                            {items.map((item, idx) => (
                                <tr key={idx} className="hover:bg-gray-50/50">
                                    <td className="p-3">
                                        <input
                                            type="text"
                                            className="w-full border-gray-200 rounded p-2 text-sm focus:ring-blue-500 focus:border-blue-500"
                                            placeholder="Descripción del bien o servicio"
                                            value={item.description}
                                            onChange={(e) => handleItemChange(idx, 'description', e.target.value)}
                                            required
                                        />
                                    </td>
                                    <td className="p-3">
                                        <select
                                            className="w-full border-gray-200 rounded p-2 text-sm focus:ring-blue-500"
                                            value={item.expense_account}
                                            onChange={(e) => handleItemChange(idx, 'expense_account', e.target.value)}
                                        >
                                            <option value="">-- Opcional --</option>
                                            {accounts.map(acc => (
                                                <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                                            ))}
                                        </select>
                                    </td>
                                    <td className="p-3">
                                        <input
                                            type="number" step="0.01" min="0" required
                                            className="w-full border-gray-200 rounded p-2 text-sm focus:ring-blue-500"
                                            value={item.quantity}
                                            onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                                        />
                                    </td>
                                    <td className="p-3">
                                        <input
                                            type="number" step="0.0001" min="0" required
                                            className="w-full border-gray-200 rounded p-2 text-sm focus:ring-blue-500"
                                            value={item.unit_price}
                                            onChange={(e) => handleItemChange(idx, 'unit_price', e.target.value)}
                                        />
                                    </td>
                                    <td className="p-3">
                                        <select
                                            className="w-full border-gray-200 rounded p-2 text-sm focus:ring-blue-500"
                                            value={item.tax_rate}
                                            onChange={(e) => handleItemChange(idx, 'tax_rate', parseInt(e.target.value))}
                                        >
                                            <option value={0}>0%</option>
                                            <option value={15}>15%</option>
                                        </select>
                                    </td>
                                    <td className="p-3 text-right font-medium text-gray-700 bg-gray-50/50">
                                        ${item.subtotal.toFixed(2)}
                                    </td>
                                    <td className="p-3 text-center">
                                        <button type="button" onClick={() => removeItem(idx)} className="text-red-400 hover:text-red-600 bg-red-50 hover:bg-red-100 p-1.5 rounded transition-colors" title="Quitar ítem">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"></path><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex justify-end mt-6">
                    <div className="w-80 bg-gray-50 p-5 rounded-lg border border-gray-200 text-sm">
                        <div className="flex justify-between py-1.5 text-gray-600">
                            <span>Subtotal 15%:</span>
                            <span className="font-medium">${totals.sub15.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between py-1.5 text-gray-600">
                            <span>Subtotal 0%:</span>
                            <span className="font-medium">${totals.sub0.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between py-1.5 text-gray-600 border-b border-gray-200 mb-2">
                            <span>IVA (15%):</span>
                            <span className="font-medium">${totals.iva.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between py-2 text-xl font-bold text-gray-900">
                            <span>Total Liquidación:</span>
                            <span>${totals.total.toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end mt-8 gap-4 pt-4 border-t border-gray-100">
                    <button
                        type="button"
                        onClick={() => navigate('/dashboard/purchases/liquidations')}
                        className="bg-white border border-gray-300 text-gray-700 px-6 py-2.5 rounded hover:bg-gray-50 font-medium transition-colors"
                    >
                        Cancelar
                    </button>
                    <button
                        type="submit"
                        className="bg-indigo-600 text-white px-8 py-2.5 rounded hover:bg-indigo-700 font-medium shadow-sm transition-colors"
                    >
                        Guardar Liquidación
                    </button>
                </div>
            </form>
        </div>
    );
};

export default LiquidationForm;
