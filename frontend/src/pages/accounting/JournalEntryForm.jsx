import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, X, Plus, Trash2, ArrowLeft } from 'lucide-react';
import { toast } from 'react-hot-toast';
import accountingService from '../../services/accountingService';

const JournalEntryForm = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [accounts, setAccounts] = useState([]);

    const [formData, setFormData] = useState({
        date: new Date().toISOString().split('T')[0],
        description: '',
        reference: ''
    });

    const [items, setItems] = useState([
        { id: Date.now(), account: '', description: '', debit: 0, credit: 0 },
        { id: Date.now() + 1, account: '', description: '', debit: 0, credit: 0 }
    ]);

    useEffect(() => {
        const loadAccounts = async () => {
            try {
                // Fetch low-level accounts (children/transactional level)
                const data = await accountingService.getAccounts({});
                // We should ideally filter to only leaf accounts or 'transactional' accounts if there's a flag,
                // but for now we list all.
                setAccounts(data);
            } catch (error) {
                toast.error("Error al cargar las cuentas contables");
            }
        };
        loadAccounts();
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleItemChange = (id, field, value) => {
        setItems(items.map(item => {
            if (item.id === id) {
                return { ...item, [field]: value };
            }
            return item;
        }));
    };

    const addItem = () => {
        setItems([...items, { id: Date.now(), account: '', description: '', debit: 0, credit: 0 }]);
    };

    const removeItem = (id) => {
        if (items.length <= 2) {
            toast.error("El asiento debe tener al menos dos líneas.");
            return;
        }
        setItems(items.filter(item => item.id !== id));
    };

    const calculateTotals = () => {
        const totalDebit = items.reduce((sum, item) => sum + parseFloat(item.debit || 0), 0);
        const totalCredit = items.reduce((sum, item) => sum + parseFloat(item.credit || 0), 0);
        return { totalDebit, totalCredit, isBalanced: Math.abs(totalDebit - totalCredit) < 0.01 };
    };

    const { totalDebit, totalCredit, isBalanced } = calculateTotals();

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!formData.date || !formData.description) {
            toast.error("La fecha y la glosa son obligatorias.");
            return;
        }

        // Validate items
        const invalidItems = items.filter(i => !i.account || (parseFloat(i.debit) === 0 && parseFloat(i.credit) === 0));
        if (invalidItems.length > 0) {
            toast.error("Todas las líneas deben tener una cuenta seleccionada y un valor mayor a cero.");
            return;
        }

        if (!isBalanced) {
            if (!window.confirm("El asiento está descuadrado. ¿Desea guardarlo como borrador de todos modos?")) {
                return;
            }
        }

        setLoading(true);
        try {
            const payload = {
                ...formData,
                items: items.map(i => ({
                    account: parseInt(i.account),
                    description: i.description,
                    debit: parseFloat(i.debit || 0),
                    credit: parseFloat(i.credit || 0)
                }))
            };

            await accountingService.createEntry(payload);
            toast.success("Asiento contable creado exitosamente");
            navigate('/dashboard/accounting/entries');
        } catch (error) {
            toast.error(error.response?.data?.error || "Error al crear el asiento");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center items-start gap-4 border-b border-slate-200 pb-4">
                <button
                    onClick={() => navigate('/dashboard/accounting/entries')}
                    className="p-2 text-slate-500 hover:text-slate-700 bg-slate-100 rounded-full hover:bg-slate-200"
                >
                    <ArrowLeft size={20} />
                </button>
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Nuevo Asiento Contable</h1>
                    <p className="text-sm text-slate-500 mt-1">
                        Crea un comprobante de diario manualmente.
                    </p>
                </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Header Info */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Fecha <span className="text-red-500">*</span></label>
                        <input
                            type="date"
                            name="date"
                            required
                            className="input-modern w-full"
                            value={formData.date}
                            onChange={handleChange}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Referencia</label>
                        <input
                            type="text"
                            name="reference"
                            placeholder="Ej. Cheque, Fac #123"
                            className="input-modern w-full"
                            value={formData.reference}
                            onChange={handleChange}
                        />
                    </div>
                    <div className="md:col-span-3">
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Concepto / Glosa General <span className="text-red-500">*</span></label>
                        <textarea
                            name="description"
                            required
                            rows="2"
                            placeholder="Explicación del asiento contable"
                            className="input-modern w-full"
                            value={formData.description}
                            onChange={handleChange}
                        ></textarea>
                    </div>
                </div>

                {/* Journal Items */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                    <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-0">
                        <h3 className="font-bold text-slate-800">Detalle del Asiento</h3>
                        <button
                            type="button"
                            onClick={addItem}
                            className="text-sm font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                        >
                            <Plus size={16} /> Agregar Línea
                        </button>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-500 bg-slate-100 uppercase border-b border-slate-200">
                                <tr>
                                    <th className="px-4 py-3 min-w-[300px]">Cuenta Contable <span className="text-red-500">*</span></th>
                                    <th className="px-4 py-3 min-w-[200px]">Detalle Línea (Opcional)</th>
                                    <th className="px-4 py-3 w-36 text-right">Debe ($)</th>
                                    <th className="px-4 py-3 w-36 text-right">Haber ($)</th>
                                    <th className="px-4 py-3 w-16 text-center"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                {items.map((item, index) => (
                                    <tr key={item.id} className="hover:bg-slate-50">
                                        <td className="px-4 py-3">
                                            <select
                                                required
                                                className="input-modern w-full text-sm p-2"
                                                value={item.account}
                                                onChange={(e) => handleItemChange(item.id, 'account', e.target.value)}
                                            >
                                                <option value="">Seleccione una cuenta</option>
                                                {accounts.map(acc => (
                                                    <option key={acc.id} value={acc.id}>
                                                        {acc.code} - {acc.name}
                                                    </option>
                                                ))}
                                            </select>
                                        </td>
                                        <td className="px-4 py-3">
                                            <input
                                                type="text"
                                                placeholder="..."
                                                className="input-modern w-full text-sm p-2"
                                                value={item.description}
                                                onChange={(e) => handleItemChange(item.id, 'description', e.target.value)}
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <input
                                                type="number"
                                                min="0"
                                                step="0.01"
                                                className="input-modern w-full text-sm p-2 text-right"
                                                value={item.debit}
                                                onChange={(e) => {
                                                    const val = e.target.value;
                                                    handleItemChange(item.id, 'debit', val);
                                                    if (parseFloat(val) > 0) handleItemChange(item.id, 'credit', 0);
                                                }}
                                            />
                                        </td>
                                        <td className="px-4 py-3">
                                            <input
                                                type="number"
                                                min="0"
                                                step="0.01"
                                                className="input-modern w-full text-sm p-2 text-right"
                                                value={item.credit}
                                                onChange={(e) => {
                                                    const val = e.target.value;
                                                    handleItemChange(item.id, 'credit', val);
                                                    if (parseFloat(val) > 0) handleItemChange(item.id, 'debit', 0);
                                                }}
                                            />
                                        </td>
                                        <td className="px-4 py-3 text-center">
                                            <button
                                                type="button"
                                                onClick={() => removeItem(item.id)}
                                                className="text-slate-400 hover:text-red-500 transition-colors p-1"
                                                title="Eliminar fila"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot className="bg-slate-50 font-bold border-t border-slate-200">
                                <tr>
                                    <td colSpan="2" className="px-4 py-4 text-right text-slate-600">
                                        TOTALES:
                                    </td>
                                    <td className="px-4 py-4 text-right text-indigo-700 bg-indigo-50/50">
                                        ${totalDebit.toFixed(2)}
                                    </td>
                                    <td className="px-4 py-4 text-right text-indigo-700 bg-indigo-50/50">
                                        ${totalCredit.toFixed(2)}
                                    </td>
                                    <td></td>
                                </tr>
                                {!isBalanced && (
                                    <tr>
                                        <td colSpan="5" className="px-4 py-2 text-center text-red-500 bg-red-50 text-xs font-medium">
                                            ⚠ El comprobante está descuadrado por diferencial de ${(Math.abs(totalDebit - totalCredit)).toFixed(2)}. Será guardado en estado borrador.
                                        </td>
                                    </tr>
                                )}
                            </tfoot>
                        </table>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col-reverse sm:flex-row justify-end gap-3 pt-4 border-t border-slate-200">
                    <button
                        type="button"
                        onClick={() => navigate('/dashboard/accounting/entries')}
                        className="btn-secondary flex items-center gap-2"
                        disabled={loading}
                    >
                        <X size={18} /> Cancelar
                    </button>
                    <button
                        type="submit"
                        className="btn-primary flex items-center gap-2"
                        disabled={loading}
                    >
                        {loading ? (
                            <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        ) : (
                            <Save size={18} />
                        )}
                        Guardar Asiento
                    </button>
                </div>
            </form>
        </div>
    );
};

export default JournalEntryForm;
