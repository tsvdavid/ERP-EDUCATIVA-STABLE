import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import purchaseService from '../../services/purchaseService';
import userService from '../../services/userService'; // Assuming we might need generic lookups, but lets stick to purchaseService for now
// We need accounts for the select. 
import axios from 'axios'; // Direct call for accounts or use service if available. 
// Let's assume we need an accountingService or similar. 
// For now I'll create a quick fetch in useEffect or add to purchaseService if suitable? 
// Actually accounting accounts are in accountingService (not created yet for frontend).
// I'll make a direct fetch to /api/accounting/accounts/ for now or add getAccounts to purchaseService as a helper.

const PurchaseForm = () => {
    const navigate = useNavigate();
    const [suppliers, setSuppliers] = useState([]);
    const [accounts, setAccounts] = useState([]);

    // Header Data
    const [invoiceData, setInvoiceData] = useState({
        supplier: '',
        document_number: '',
        authorization_code: '',
        issue_date: new Date().toISOString().slice(0, 10),
        sustento_tributario: '01',
        payment_method: '20'
    });

    // Items
    const [items, setItems] = useState([
        { description: '', expense_account: '', quantity: 1, unit_price: 0, tax_rate: 15, subtotal: 0 }
    ]);

    useEffect(() => {
        // Load Suppliers and Accounts
        const loadData = async () => {
            try {
                const supps = await purchaseService.getSuppliers();
                setSuppliers(supps);

                // Fetch Expense Accounts
                const token = localStorage.getItem('token');
                const accRes = await axios.get('http://localhost:8000/api/accounting/accounts/?roots=false', {
                    headers: { Authorization: `Bearer ${token}` }
                });
                // Filter only expenses if possible on frontend or backend
                const expenseAccounts = accRes.data.filter(a => a.account_type === 'EXPENSE');
                setAccounts(expenseAccounts);
            } catch (error) {
                console.error("Error loading form data", error);
            }
        };
        loadData();
    }, []);

    const handleHeaderChange = (e) => {
        setInvoiceData({ ...invoiceData, [e.target.name]: e.target.value });
    };

    const handleItemChange = (index, field, value) => {
        const newItems = [...items];
        newItems[index][field] = value;

        // Recalc subtotal
        if (field === 'quantity' || field === 'unit_price') {
            const qty = parseFloat(newItems[index].quantity) || 0;
            const price = parseFloat(newItems[index].unit_price) || 0;
            newItems[index].subtotal = qty * price;
        }

        setItems(newItems);
    };

    const addItem = () => {
        setItems([...items, { description: '', expense_account: '', quantity: 1, unit_price: 0, tax_rate: 15, subtotal: 0 }]);
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
        if (!invoiceData.supplier) {
            alert("Seleccione un proveedor");
            return;
        }

        const payload = {
            ...invoiceData,
            items: items.map(i => ({
                description: i.description,
                expense_account: i.expense_account || null,
                quantity: i.quantity,
                unit_price: i.unit_price,
                tax_rate: i.tax_rate
            }))
        };

        try {
            await purchaseService.createInvoice(payload);
            navigate('/dashboard/purchases/invoices');
        } catch (error) {
            console.error("Error creating invoice", error);
            alert("Error al crear factura");
        }
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">Nueva Factura de Compra</h1>

            <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6">
                {/* Header */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Proveedor</label>
                        <select
                            name="supplier"
                            className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={invoiceData.supplier}
                            onChange={handleHeaderChange}
                            required
                        >
                            <option value="">-- Seleccionar --</option>
                            {suppliers.map(s => (
                                <option key={s.id} value={s.id}>{s.legal_name}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Número Comprobante</label>
                        <input
                            type="text" name="document_number"
                            placeholder="001-001-000000001"
                            className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={invoiceData.document_number}
                            onChange={handleHeaderChange}
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Fecha Emisión</label>
                        <input
                            type="date" name="issue_date"
                            className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={invoiceData.issue_date}
                            onChange={handleHeaderChange}
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Autorización</label>
                        <input
                            type="text" name="authorization_code"
                            className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={invoiceData.authorization_code}
                            onChange={handleHeaderChange}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Sustento Tributario</label>
                        <select
                            name="sustento_tributario"
                            className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                            value={invoiceData.sustento_tributario}
                            onChange={handleHeaderChange}
                        >
                            <option value="01">01 - Crédito Tributario para declaración de IVA</option>
                            <option value="02">02 - Costo o Gasto para declaración de Renta</option>
                        </select>
                    </div>
                </div>

                <hr className="my-6" />

                {/* Items */}
                <h3 className="text-lg font-medium text-gray-900 mb-4">Detalle de Gastos</h3>
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead>
                            <tr>
                                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Descripción</th>
                                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-48">Cuenta Gasto</th>
                                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">Cant.</th>
                                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">P. Unit</th>
                                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-24">IVA %</th>
                                <th className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Subtotal</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item, idx) => (
                                <tr key={idx}>
                                    <td className="p-2">
                                        <input
                                            type="text"
                                            className="w-full border-gray-300 rounded shadow-sm p-1 border"
                                            value={item.description}
                                            onChange={(e) => handleItemChange(idx, 'description', e.target.value)}
                                            required
                                        />
                                    </td>
                                    <td className="p-2">
                                        <select
                                            className="w-full border-gray-300 rounded shadow-sm p-1 border"
                                            value={item.expense_account}
                                            onChange={(e) => handleItemChange(idx, 'expense_account', e.target.value)}
                                        >
                                            <option value="">-- Cuenta --</option>
                                            {accounts.map(acc => (
                                                <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                                            ))}
                                        </select>
                                    </td>
                                    <td className="p-2">
                                        <input
                                            type="number" step="0.01"
                                            className="w-full border-gray-300 rounded shadow-sm p-1 border"
                                            value={item.quantity}
                                            onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                                        />
                                    </td>
                                    <td className="p-2">
                                        <input
                                            type="number" step="0.0001"
                                            className="w-full border-gray-300 rounded shadow-sm p-1 border"
                                            value={item.unit_price}
                                            onChange={(e) => handleItemChange(idx, 'unit_price', e.target.value)}
                                        />
                                    </td>
                                    <td className="p-2">
                                        <select
                                            className="w-full border-gray-300 rounded shadow-sm p-1 border"
                                            value={item.tax_rate}
                                            onChange={(e) => handleItemChange(idx, 'tax_rate', parseInt(e.target.value))}
                                        >
                                            <option value={0}>0%</option>
                                            <option value={15}>15%</option>
                                        </select>
                                    </td>
                                    <td className="p-2 text-right">
                                        ${item.subtotal.toFixed(2)}
                                    </td>
                                    <td className="p-2">
                                        <button type="button" onClick={() => removeItem(idx)} className="text-red-500 hover:text-red-700">X</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <button type="button" onClick={addItem} className="mt-2 text-sm text-blue-600 hover:text-blue-800">+ Agregar Item</button>

                <div className="flex justify-end mt-6">
                    <div className="w-64">
                        <div className="flex justify-between py-1">
                            <span>Subtotal 15%:</span>
                            <span>${totals.sub15.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between py-1">
                            <span>Subtotal 0%:</span>
                            <span>${totals.sub0.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between py-1 font-bold">
                            <span>IVA (15%):</span>
                            <span>${totals.iva.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between py-2 border-t border-gray-300 text-lg font-bold">
                            <span>Total:</span>
                            <span>${totals.total.toFixed(2)}</span>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end mt-8 gap-4">
                    <button
                        type="button"
                        onClick={() => navigate('/dashboard/purchases/invoices')}
                        className="bg-gray-200 text-gray-700 px-6 py-2 rounded shadow-sm hover:bg-gray-300"
                    >
                        Cancelar
                    </button>
                    <button
                        type="submit"
                        className="bg-indigo-600 text-white px-6 py-2 rounded shadow-sm hover:bg-indigo-700"
                    >
                        Guardar Compra
                    </button>
                </div>

            </form>
        </div>
    );
};

export default PurchaseForm;
