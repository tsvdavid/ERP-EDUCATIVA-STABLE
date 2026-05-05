import React, { useState, useEffect } from 'react';
import { Search, ShoppingCart, DollarSign, User, FileText, Check, AlertCircle, Download, Trash2, X, Send } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import treasuryService from '../../services/treasuryService';
import userService from '../../services/userService';

const PaymentsPage = () => {
    // Search State
    const [searchTerm, setSearchTerm] = useState('');
    const [customers, setCustomers] = useState([]);
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [searching, setSearching] = useState(false);

    // Cart State
    const [concepts, setConcepts] = useState([]); // Available concepts
    const [charges, setCharges] = useState([]); // Pending charges (Debts)
    const [cart, setCart] = useState([]); // [{concept, quantity, charge_id, is_debt}]
    const [paymentMethods, setPaymentMethods] = useState([]);
    const [selectedMethod, setSelectedMethod] = useState('');

    // Billing Info State
    const [billingInfo, setBillingInfo] = useState({
        client_name: '',
        client_ruc: '',
        client_address: '',
        client_email: ''
    });

    const [processing, setProcessing] = useState(false);
    const [lastInvoice, setLastInvoice] = useState(null);
    const [studentInvoices, setStudentInvoices] = useState([]);

    useEffect(() => {
        loadResources();
    }, []);

    const loadResources = async () => {
        try {
            const [cData, mData] = await Promise.all([
                treasuryService.getConcepts(),
                treasuryService.getMethods()
            ]);
            setConcepts(cData);
            setPaymentMethods(mData);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando configuración");
        }
    };

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!searchTerm) return;
        setSearching(true);
        try {
            const lower = searchTerm.toLowerCase();
            const found = await treasuryService.getCustomers({ search: lower });
            setCustomers(found);
            if (found.length === 0) toast('No se encontraron clientes', { icon: '🔍' });
        } catch (error) {
            toast.error("Error buscando");
        } finally {
            setSearching(false);
        }
    };

    const selectStudent = async (customer) => {
        setSelectedCustomer(customer);
        setCustomers([]); // Clear search results
        setSearchTerm('');
        setCart([]); // Reset cart
        setLastInvoice(null);
        setStudentInvoices([]);
        
        // Cargar Datos de Facturación por defecto
        setBillingInfo({
            client_name: customer.business_name || `${customer.first_name} ${customer.last_name}`,
            client_ruc: customer.identification,
            client_address: customer.address || 'Sin dirección',
            client_email: customer.email || ''
        });

        // Load Charges (Solo si es estudiante)
        if (customer.student) {
            try {
                const pendingCharges = await treasuryService.getCharges({ student_id: customer.student, pending: 'true' });
                setCharges(pendingCharges);
            } catch (error) {
                console.error(error);
                toast.error("Error cargando deudas del estudiante");
            }
        } else {
            setCharges([]);
        }

        // Load Invoices
        try {
            const invoices = await treasuryService.getInvoices({ customer_id: customer.id });
            setStudentInvoices(invoices || []);
        } catch (error) {
            console.error("Could not load invoices", error);
        }
    };

    const handleSendToSri = async (invoice) => {
        const toastId = toast.loading("Enviando al SRI...");
        try {
            const result = await treasuryService.sendToSri(invoice.id);
            if (result.status === 'AUTHORIZED') {
                toast.success("¡Factura Autorizada!", { id: toastId });
            } else {
                toast.error(`Estado: ${result.status}. ${result.message}`, { id: toastId, duration: 5000 });
            }
            // Refresh invoices
            if (selectedCustomer) {
                const invoices = await treasuryService.getInvoices({ customer_id: selectedCustomer.id });
                setStudentInvoices(invoices || []);
            }
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.error || error.response?.data?.message || "Error al enviar al SRI";
            toast.error(msg, { id: toastId });
        }
    };

    const addToCart = (concept, charge = null) => {
        // Prepare Cart Item
        // If it's a Charge (Debt), quantity is fixed at 1 and we track charge_id
        // If it's a generic Concept, quantity can aggregate

        if (charge) {
            // Check if already in cart
            if (cart.find(item => item.charge_id === charge.id)) {
                return toast("Esta deuda ya está en el carrito", { icon: '🛒' });
            }
            // Add Debt
            // We mock the concept structure if needed or use the nested one
            const cartItem = {
                concept: charge.concept_detail,
                quantity: 1,
                charge_id: charge.id,
                is_debt: true,
                price: parseFloat(charge.amount) // Use the frozen price from debt
            };
            setCart([...cart, cartItem]);
        } else {
            // Check if exists (Generic)
            const exists = cart.find(item => item.concept.id === concept.id && !item.is_debt);
            if (exists) {
                setCart(cart.map(item =>
                    item.concept.id === concept.id && !item.is_debt
                        ? { ...item, quantity: item.quantity + 1 }
                        : item
                ));
            } else {
                setCart([...cart, {
                    concept,
                    quantity: 1,
                    is_debt: false,
                    price: parseFloat(concept.price)
                }]);
            }
        }
    };

    const removeFromCart = (index) => {
        const newCart = [...cart];
        newCart.splice(index, 1);
        setCart(newCart);
    };

    const calculateTotal = () => {
        return cart.reduce((acc, item) => {
            const tax = parseFloat(item.concept.iva_rate);
            const price = item.price;
            const subtotal = price * item.quantity;
            const total = subtotal * (1 + tax);
            return acc + total;
        }, 0);
    };

    const handleProcessPayment = async () => {
        if (!selectedMethod) return toast.error("Seleccione forma de pago");
        if (cart.length === 0) return toast.error("Carrito vacío");

        setProcessing(true);
        try {
            const isPending = selectedMethod === 'PENDING';

            const payload = {
                customer_id: selectedCustomer.id,
                payment_method_id: isPending ? null : selectedMethod,
                is_pending: isPending,
                client_name: billingInfo.client_name,
                client_ruc: billingInfo.client_ruc,
                client_address: billingInfo.client_address,
                client_email: billingInfo.client_email,
                concepts: cart.map(item => ({
                    concept_id: item.concept.id,
                    quantity: item.quantity,
                    charge_id: item.charge_id // Send if exists
                }))
            };

            const invoice = await treasuryService.processPayment(payload);
            setLastInvoice(invoice);
            setCart([]);
            // Reload Pending Charges (some might be paid or added now)
            if (selectedCustomer.student) {
                const pendingCharges = await treasuryService.getCharges({ student_id: selectedCustomer.student, pending: 'true' });
                setCharges(pendingCharges);
            }
        } catch (error) {
            console.error(error);
            toast.error("Error al procesar pago");
        } finally {
            setProcessing(false);
        }
    };

    const handleDownloadPDF = async () => {
        if (!lastInvoice) return;
        try {
            const blob = await treasuryService.downloadInvoice(lastInvoice.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Factura_${lastInvoice.number}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            toast.error("Error al descargar PDF");
        }
    };

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />

            <h1 className="text-2xl font-bold text-slate-800">Facturación y Cobros</h1>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Student Selection & Concepts */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Student Search */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                        <h2 className="font-bold text-slate-700 mb-4 flex items-center gap-2">
                            <User size={20} /> 1. Seleccionar Cliente
                        </h2>

                        {!selectedCustomer ? (
                            <form onSubmit={handleSearch} className="relative">
                                <Search className="absolute left-3 top-3 text-slate-400" size={20} />
                                <input
                                    type="text"
                                    className="input-modern pl-10 w-full"
                                    placeholder="Buscar por nombre, cédula o RUC..."
                                    value={searchTerm}
                                    onChange={e => setSearchTerm(e.target.value)}
                                />
                                <button type="submit" disabled={searching} className="absolute right-2 top-2 btn-primary py-1 px-3 text-sm">
                                    {searching ? '...' : 'Buscar'}
                                </button>

                                {customers.length > 0 && (
                                    <ul className="absolute z-10 w-full bg-white border border-slate-200 rounded-lg mt-1 shadow-xl max-h-60 overflow-y-auto">
                                        {customers.map(c => (
                                            <li key={c.id}
                                                onClick={() => selectStudent(c)}
                                                className="p-3 hover:bg-indigo-50 cursor-pointer border-b border-slate-50 last:border-0"
                                            >
                                                <div className="font-bold text-slate-800">
                                                    {c.customer_type === 'INDEPENDENT' && c.business_name ? c.business_name : `${c.first_name} ${c.last_name}`}
                                                    {c.customer_type === 'INDEPENDENT' && <span className="ml-2 text-[10px] bg-slate-100 text-slate-500 px-1 rounded">EXTERNO</span>}
                                                </div>
                                                <div className="text-xs text-slate-500">ID: {c.identification}</div>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </form>
                        ) : (
                            <div className="flex justify-between items-center bg-indigo-50 p-4 rounded-lg border border-indigo-100">
                                <div>
                                    <p className="text-sm text-indigo-600 font-bold uppercase">Cliente Seleccionado</p>
                                    <p className="text-lg font-bold text-slate-800">
                                        {selectedCustomer.customer_type === 'INDEPENDENT' && selectedCustomer.business_name ? selectedCustomer.business_name : `${selectedCustomer.first_name} ${selectedCustomer.last_name}`}
                                    </p>
                                    <p className="text-sm text-slate-500">{selectedCustomer.identification}</p>
                                </div>
                                <button onClick={() => setSelectedCustomer(null)} className="text-indigo-600 hover:text-indigo-800 text-sm font-medium underline">
                                    Cambiar
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Debts Section */}
                    {selectedCustomer && (
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                            <h2 className="font-bold text-slate-700 mb-4 flex items-center gap-2 text-red-600">
                                <AlertCircle size={20} /> Deudas Pendientes ({charges.length})
                            </h2>
                            {charges.length === 0 ? (
                                <p className="text-slate-400 italic">No hay deudas pendientes.</p>
                            ) : (
                                <div className="space-y-3">
                                    {charges.map(charge => (
                                        <div key={charge.id} className="flex justify-between items-center p-3 bg-red-50 border border-red-100 rounded-lg">
                                            <div>
                                                <p className="font-bold text-slate-800">{charge.concept_detail.name}</p>
                                                <p className="text-xs text-red-500">Vence: {charge.due_date}</p>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <span className="font-bold text-slate-700">${parseFloat(charge.amount).toFixed(2)}</span>
                                                <button
                                                    onClick={() => addToCart(null, charge)}
                                                    className="px-3 py-1 bg-white border border-red-200 text-red-600 rounded-md text-sm font-medium hover:bg-red-600 hover:text-white transition-colors"
                                                >
                                                    Pagar
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Concepts Grid */}
                    {selectedCustomer && (
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                            <h2 className="font-bold text-slate-700 mb-4 flex items-center gap-2">
                                <ShoppingCart size={20} /> 2. Servicios Adicionales
                            </h2>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                {concepts.map(concept => (
                                    <button
                                        key={concept.id}
                                        onClick={() => addToCart(concept)}
                                        className="p-3 text-left border border-slate-200 rounded-lg hover:border-indigo-500 hover:bg-indigo-50 transition-all group"
                                    >
                                        <p className="font-bold text-slate-700 group-hover:text-indigo-700 text-sm mb-1">{concept.name}</p>
                                        <p className="text-green-600 font-bold">${concept.price}</p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Right Column: Cart & Summary */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 h-full flex flex-col">
                        <h2 className="font-bold text-slate-700 mb-4 flex items-center gap-2">
                            <DollarSign size={20} /> 3. Detalle de Pago
                        </h2>

                        <div className="flex-1 overflow-y-auto mb-4 space-y-3 min-h-[200px]">
                            {cart.length === 0 ? (
                                <div className="text-center text-slate-400 py-10 italic">
                                    Carrito vacío
                                </div>
                            ) : (
                                cart.map((item, idx) => (
                                    <div key={idx} className={`flex justify-between items-center text-sm p-3 rounded-lg border ${item.is_debt ? 'bg-red-50 border-red-100' : 'bg-slate-50 border-slate-100'}`}>
                                        <div>
                                            <p className="font-medium text-slate-800">
                                                {item.concept.name} {item.is_debt && <span className="text-[10px] bg-red-200 text-red-800 px-1 rounded ml-1">DEUDA</span>}
                                            </p>
                                            <p className="text-xs text-slate-500">x{item.quantity}</p>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <span className="font-bold text-slate-600">
                                                ${(item.price * item.quantity).toFixed(2)}
                                            </span>
                                            <button onClick={() => removeFromCart(idx)} className="text-slate-400 hover:text-red-500">
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="border-t border-slate-100 pt-4 space-y-4">
                            <div className="flex justify-between items-end">
                                <span className="text-slate-500">Total a Pagar:</span>
                                <span className="text-3xl font-bold text-slate-800">${calculateTotal().toFixed(2)}</span>
                            </div>

                        </div>

                        {/* Billing Info Section */}
                        <div className="border-t border-slate-100 pt-4">
                            <h3 className="font-bold text-slate-700 mb-2 flex items-center gap-2 text-sm">
                                <FileText size={16} /> Datos de Facturación
                            </h3>
                            <div className="space-y-2">
                                <input
                                    type="text"
                                    className="input-modern w-full text-sm"
                                    placeholder="Razón Social / Nombre"
                                    value={billingInfo.client_name}
                                    onChange={e => setBillingInfo({ ...billingInfo, client_name: e.target.value })}
                                />
                                <input
                                    type="text"
                                    className="input-modern w-full text-sm"
                                    placeholder="RUC / Cédula"
                                    value={billingInfo.client_ruc}
                                    onChange={e => setBillingInfo({ ...billingInfo, client_ruc: e.target.value })}
                                    maxLength={13}
                                />
                                <input
                                    type="text"
                                    className="input-modern w-full text-sm"
                                    placeholder="Dirección"
                                    value={billingInfo.client_address}
                                    onChange={e => setBillingInfo({ ...billingInfo, client_address: e.target.value })}
                                />
                                <input
                                    type="email"
                                    className="input-modern w-full text-sm"
                                    placeholder="Email"
                                    value={billingInfo.client_email}
                                    onChange={e => setBillingInfo({ ...billingInfo, client_email: e.target.value })}
                                />
                            </div>
                        </div>

                        <div>
                            <label className="label-modern mb-1 block">Forma de Pago</label>
                            <select
                                className="input-modern w-full"
                                value={selectedMethod}
                                onChange={e => setSelectedMethod(e.target.value)}
                            >
                                <option value="">-- Seleccione --</option>
                                <option value="PENDING" className="font-bold text-red-600">Dejar como Pendiente (Saldos por Cobrar)</option>
                                {paymentMethods.map(m => (
                                    <option key={m.id} value={m.id}>{m.name}</option>
                                ))}
                            </select>
                        </div>

                        <button
                            onClick={handleProcessPayment}
                            disabled={processing || cart.length === 0 || !selectedMethod}
                            className="btn-primary w-full py-3 text-lg shadow-lg shadow-indigo-200"
                        >
                            {processing ? 'Procesando...' : 'Confirmar Pago'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Success Invoice Modal */}
            {lastInvoice && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-8 text-center relative animate-in zoom-in-95">
                        <button onClick={() => { setLastInvoice(null); loadResources(); if (selectedCustomer) selectStudent(selectedCustomer); }} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
                            <X size={24} />
                        </button>

                        <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Check size={32} />
                        </div>

                        <h2 className="text-2xl font-bold text-slate-800 mb-2">¡Pago Exitoso!</h2>
                        <p className="text-slate-500 mb-6">Se ha generado la factura #{lastInvoice.number}</p>

                        <div className="bg-slate-50 p-4 rounded-lg mb-6 text-left text-sm space-y-2">
                            <div className="flex justify-between">
                                <span className="text-slate-500">Cliente:</span>
                                <span className="font-bold">{lastInvoice.client_name}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-slate-500">Total:</span>
                                <span className="font-bold text-green-600">${lastInvoice.total}</span>
                            </div>
                        </div>

                        <div className="flex gap-2 flex-col">
                            <div className="flex gap-2">
                                <button onClick={handleDownloadPDF} className="flex-1 btn-primary flex items-center justify-center gap-2">
                                    <Download size={18} /> PDF
                                </button>
                                <button
                                    onClick={() => handleSendToSri(lastInvoice)}
                                    className="flex-1 bg-indigo-600 text-white rounded-lg flex items-center justify-center gap-2 hover:bg-indigo-700 font-bold transition-colors"
                                >
                                    <Send size={18} /> Enviar SRI
                                </button>
                            </div>
                            <button onClick={() => { setLastInvoice(null); loadResources(); if (selectedCustomer) selectStudent(selectedCustomer); }} className="btn-secondary w-full">
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* INVOICE HISTORY SECTION */}
            {selectedCustomer && studentInvoices.length > 0 && (
                <div className="lg:col-span-3 bg-white p-6 rounded-xl shadow-sm border border-slate-200 mt-6">
                    <h2 className="font-bold text-slate-700 mb-4 flex items-center gap-2">
                        <FileText size={20} /> Historial de Facturas (Últimas 10)
                    </h2>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100">
                                <tr>
                                    <th className="px-4 py-3">Número</th>
                                    <th className="px-4 py-3">Fecha</th>
                                    <th className="px-4 py-3">Total</th>
                                    <th className="px-4 py-3">Estado SRI</th>
                                    <th className="px-4 py-3 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50">
                                {studentInvoices.slice(0, 10).map(inv => (
                                    <tr key={inv.id} className="hover:bg-slate-50">
                                        <td className="px-4 py-3 font-medium text-slate-800">{inv.number}</td>
                                        <td className="px-4 py-3">{new Date(inv.issue_date).toLocaleDateString()}</td>
                                        <td className="px-4 py-3 font-bold">${inv.total}</td>
                                        <td className="px-4 py-3">
                                            {inv.sri_status === 'AUTHORIZED' ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold">
                                                    <Check size={12} /> AUTORIZADO
                                                </span>
                                            ) : inv.sri_status === 'SENT' ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs font-bold">
                                                    Enviado
                                                </span>
                                            ) : inv.sri_status === 'REJECTED' ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-bold">
                                                    <AlertCircle size={12} /> Rechazado
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-slate-100 text-slate-500 text-xs font-bold">
                                                    Pendiente
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 text-right flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => { setLastInvoice(inv); handleDownloadPDF(); }}
                                                className="p-1.5 hover:bg-slate-200 rounded text-slate-500"
                                                title="Descargar PDF"
                                            >
                                                <Download size={16} />
                                            </button>
                                            {inv.sri_status !== 'AUTHORIZED' && (
                                                <button
                                                    onClick={() => handleSendToSri(inv)}
                                                    className="p-1.5 hover:bg-indigo-100 rounded text-indigo-600"
                                                    title="Enviar al SRI"
                                                >
                                                    <Send size={16} />
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PaymentsPage;
