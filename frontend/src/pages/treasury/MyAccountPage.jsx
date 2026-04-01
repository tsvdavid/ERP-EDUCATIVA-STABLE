import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../../context/authStore';
import api from '../../services/api';
import treasuryService from '../../services/treasuryService';
import { Users, FileText, Check, AlertCircle, Download, Send, DollarSign, Wallet } from 'lucide-react';
import { toast } from 'react-hot-toast';
import CheckoutModal from '../../components/payments/CheckoutModal';

const MyAccountPage = () => {
    const { user } = useAuthStore();
    const [children, setChildren] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [loading, setLoading] = useState(true);

    const [charges, setCharges] = useState([]);
    const [invoices, setInvoices] = useState([]);
    const [verifyingPayments, setVerifyingPayments] = useState([]);
    const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
    const [cartPayload, setCartPayload] = useState(null);

    // Initialization: load children if PARENT, or self if STUDENT
    useEffect(() => {
        const initData = async () => {
            setLoading(true);
            try {
                if (user?.role === 'PARENT') {
                    if (user?.children && user.children.length > 0) {
                        setChildren(user.children);
                        setSelectedStudent(user.children[0]);
                    } else {
                        const response = await api.get(`/users/${user.id}/`);
                        if (response.data.children) {
                            setChildren(response.data.children);
                            setSelectedStudent(response.data.children[0]);
                        }
                    }
                } else if (user?.role === 'STUDENT') {
                    setSelectedStudent(user);
                }
            } catch (error) {
                console.error("Error fetching user data", error);
                toast.error("Error al cargar los datos del usuario.");
            } finally {
                setLoading(false);
            }
        };

        initData();
    }, [user]);

    // Fetch invoices and charges when student changes
    useEffect(() => {
        if (selectedStudent) {
            loadFinancialData(selectedStudent.id);
        }
    }, [selectedStudent]);

    const loadFinancialData = async (studentId) => {
        try {
            const [chargesData, invoicesData, paymentsRes] = await Promise.all([
                treasuryService.getCharges({ student_id: studentId, pending: 'true' }),
                treasuryService.getInvoices({ student_id: studentId }),
                api.get('/payments/')
            ]);

            const allTxns = paymentsRes.data || [];
            const verifyingTxns = allTxns.filter(t => t.status === 'VERIFYING');
            const verifyingIds = verifyingTxns.map(t => parseInt(t.reference_id)).filter(id => !isNaN(id));

            const filteredCharges = (chargesData || []).filter(c => !verifyingIds.includes(c.id));

            setCharges(filteredCharges);
            setInvoices(invoicesData || []);
            setVerifyingPayments(verifyingTxns);
        } catch (error) {
            console.error("Error loading financial data", error);
        }
    };

    const handlePayDebt = (charge) => {
        const payload = {
            student_id: selectedStudent.id,
            amount: parseFloat(charge.amount),
            currency: 'USD',
            description: `Pago de: ${charge.concept_detail?.name || 'Deuda'}`,
            reference_id: charge.id,
            concepts: [
                {
                    concept_id: charge.concept_detail?.id,
                    quantity: 1,
                    charge_id: charge.id
                }
            ]
        };
        setCartPayload(payload);
        setIsCheckoutOpen(true);
    };

    const onPaymentSuccess = () => {
        setIsCheckoutOpen(false);
        if (selectedStudent) {
            loadFinancialData(selectedStudent.id);
        }
    };

    const handleDownloadPDF = async (invoice) => {
        try {
            const blob = await treasuryService.downloadInvoice(invoice.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Factura_${invoice.number}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            toast.error("Error al descargar PDF");
        }
    };

    if (loading) return <div className="p-8 text-center">Cargando...</div>;

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Mi Cuenta</h1>
                    <p className="text-slate-500">Historial de pagos y facturación</p>
                </div>

                {user?.role === 'PARENT' && children.length > 1 && (
                    <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm border border-slate-200">
                        <Users size={18} className="text-indigo-600" />
                        <select
                            className="bg-transparent border-none text-slate-700 font-medium focus:ring-0"
                            value={selectedStudent?.id || ''}
                            onChange={(e) => {
                                const child = children.find(c => c.id === parseInt(e.target.value));
                                setSelectedStudent(child);
                            }}
                        >
                            {children.map(child => (
                                <option key={child.id} value={child.id}>{child.first_name} {child.last_name}</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>

            {selectedStudent ? (
                <>
                    {/* Debts Section */}
                    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                        <div className="p-5 border-b border-slate-100 flex items-center gap-2 bg-red-50/50">
                            <Wallet className="text-red-500" size={20} />
                            <h2 className="font-bold text-slate-800">Saldos Pendientes</h2>
                        </div>
                        <div className="p-5 p-0">
                            {charges.length === 0 ? (
                                <p className="text-slate-500 p-5 italic">No hay deudas pendientes registradas.</p>
                            ) : (
                                <div className="divide-y divide-slate-100">
                                    {charges.map(charge => (
                                        <div key={charge.id} className="flex flex-col md:flex-row md:justify-between md:items-center p-5 bg-white gap-4 md:gap-0 hover:bg-slate-50 transition-colors">
                                            <div>
                                                <p className="font-bold text-slate-800">{charge.concept_detail?.name || 'Deuda'}</p>
                                                <p className="text-sm text-red-500 flex items-center gap-1">
                                                    <AlertCircle size={14} /> Vence: {charge.due_date}
                                                </p>
                                            </div>
                                            <div className="flex items-center justify-between md:justify-end gap-6 w-full md:w-auto">
                                                <span className="font-bold text-slate-700 text-lg">${parseFloat(charge.amount).toFixed(2)}</span>
                                                <button
                                                    onClick={() => handlePayDebt(charge)}
                                                    className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 transition-colors flex items-center justify-center gap-2 shadow-sm"
                                                >
                                                    <DollarSign size={18} /> Pagar Ahora
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Verifying Payments Section */}
                    {verifyingPayments.length > 0 && (
                        <div className="bg-white rounded-xl shadow-sm border border-orange-100 overflow-hidden mt-6">
                            <div className="p-5 border-b border-orange-100 flex items-center gap-2 bg-orange-50/50">
                                <AlertCircle className="text-orange-500" size={20} />
                                <h2 className="font-bold text-slate-800">Pagos en Proceso (Verificación Bancaria)</h2>
                            </div>
                            <div className="p-0">
                                <div className="divide-y divide-orange-50">
                                    {verifyingPayments.map(txn => (
                                        <div key={txn.id} className="flex flex-col md:flex-row md:justify-between md:items-center p-5 bg-white gap-4 md:gap-0 hover:bg-orange-50 transition-colors">
                                            <div>
                                                <p className="font-bold text-slate-800">{txn.description || 'Transferencia Bancaria'}</p>
                                                <p className="text-sm text-orange-500 flex items-center gap-1">
                                                    Ref: {txn.reference_id} | Fecha: {new Date(txn.created_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                            <div className="flex items-center justify-between md:justify-end gap-6 w-full md:w-auto">
                                                <span className="font-bold text-slate-700 text-lg">${parseFloat(txn.amount).toFixed(2)}</span>
                                                <span className="px-4 py-1.5 bg-orange-100 text-orange-700 rounded-full text-xs font-bold uppercase tracking-wide">
                                                    En Revisión
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Invoices History Section */}
                    <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                        <div className="p-5 border-b border-slate-100 flex items-center gap-2">
                            <FileText className="text-indigo-500" size={20} />
                            <h2 className="font-bold text-slate-800">Historial de Facturas Automáticas</h2>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100">
                                    <tr>
                                        <th className="px-5 py-4 font-medium">Factura</th>
                                        <th className="px-5 py-4 font-medium">Fecha</th>
                                        <th className="px-5 py-4 font-medium">Total</th>
                                        <th className="px-5 py-4 font-medium">Estado</th>
                                        <th className="px-5 py-4 text-right font-medium">Descargar</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {invoices.length === 0 ? (
                                        <tr>
                                            <td colSpan="5" className="px-5 py-8 text-center text-slate-400 italic">
                                                No hay historial de facturación disponible.
                                            </td>
                                        </tr>
                                    ) : (
                                        invoices.map(inv => (
                                            <tr key={inv.id} className="hover:bg-slate-50 transition-colors">
                                                <td className="px-5 py-4 font-medium text-slate-800">{inv.number}</td>
                                                <td className="px-5 py-4 text-slate-600">{new Date(inv.issue_date).toLocaleDateString()}</td>
                                                <td className="px-5 py-4 font-bold text-slate-700">${inv.total}</td>
                                                <td className="px-5 py-4">
                                                    {inv.sri_status === 'AUTHORIZED' ? (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold">
                                                            <Check size={12} /> Pagada
                                                        </span>
                                                    ) : inv.sri_status === 'REJECTED' ? (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-100 text-red-700 text-xs font-bold">
                                                            <AlertCircle size={12} /> Rechazada
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-bold">
                                                            Pendiente SRI
                                                        </span>
                                                    )}
                                                </td>
                                                <td className="px-5 py-4 text-right">
                                                    <button
                                                        onClick={() => handleDownloadPDF(inv)}
                                                        className="p-2 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors inline-block"
                                                        title="Descargar Comprobante PDF"
                                                    >
                                                        <Download size={18} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Payment Modal */}
                    {cartPayload && (
                        <CheckoutModal
                            isOpen={isCheckoutOpen}
                            onClose={() => setIsCheckoutOpen(false)}
                            cartPayload={cartPayload}
                            onPaymentSuccess={onPaymentSuccess}
                        />
                    )}
                </>
            ) : null}
        </div>
    );
};

export default MyAccountPage;
