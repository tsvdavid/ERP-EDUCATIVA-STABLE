import React, { useState, useEffect } from 'react';
import accountingService from '../../services/accountingService';
import { Plus, Pencil, Trash2, Wallet, Building2 } from 'lucide-react';

const BankAccountsPage = () => {
    const [accounts, setAccounts] = useState([]);
    const [banks, setBanks] = useState([]);
    const [accountingAccounts, setAccountingAccounts] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Minimalist modal state
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({
        bank: '',
        account_number: '',
        account_type: 'CHECKING',
        linked_account: '',
        initial_balance: 0,
        is_active: true
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [accsData, bnkData, accPlanData] = await Promise.all([
                accountingService.getBankAccounts(),
                accountingService.getBanks(),
                accountingService.getAccounts({ roots: true }) // Adjust if needed based on API
            ]);
            setAccounts(accsData);
            setBanks(bnkData.filter(b => b.is_active)); // Only active banks

            // Flatten accounting plan or filter to just ASSET types if desired
            setAccountingAccounts(accPlanData);
        } catch (error) {
            console.error("Error fetching data:", error);
        }
    };

    const handleOpenModal = (account = null) => {
        if (account) {
            setEditingId(account.id);
            setFormData({
                bank: account.bank,
                account_number: account.account_number,
                account_type: account.account_type,
                linked_account: account.linked_account || '',
                initial_balance: account.initial_balance,
                is_active: account.is_active
            });
        } else {
            setEditingId(null);
            setFormData({
                bank: banks.length > 0 ? banks[0].id : '',
                account_number: '',
                account_type: 'CHECKING',
                linked_account: '',
                initial_balance: 0,
                is_active: true
            });
        }
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingId(null);
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            // Nullify linked_account if empty string
            const payload = { ...formData };
            if (!payload.linked_account) payload.linked_account = null;

            if (editingId) {
                await accountingService.updateBankAccount(editingId, payload);
            } else {
                await accountingService.createBankAccount(payload);
            }
            await fetchData();
            handleCloseModal();
        } catch (error) {
            console.error("Error saving bank account:", error);
            alert("No se pudo guardar la cuenta. Asegúrese que el número de cuenta no esté duplicado en el mismo banco.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (id, number) => {
        if (window.confirm(`¿Está seguro que desea borrar la cuenta terminada en '${number}'?`)) {
            try {
                await accountingService.deleteBankAccount(id);
                setAccounts(accounts.filter(a => a.id !== id));
            } catch (error) {
                console.error("Error deleting:", error);
                alert("No se pudo eliminar la cuenta bancaria. Es probable que tenga movimientos registrados.");
            }
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        <Wallet className="w-7 h-7 text-indigo-600" />
                        Cuentas Bancarias Operativas
                    </h1>
                    <p className="text-slate-500 text-sm mt-1">
                        Registre y administre las cuentas usadas para recepción de pagos y tesorería.
                    </p>
                </div>
                <button
                    onClick={() => handleOpenModal()}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 font-medium flex items-center gap-2 shadow-sm"
                    disabled={banks.length === 0}
                    title={banks.length === 0 ? "Debe registrar al menos un Banco primero" : ""}
                >
                    <Plus className="w-5 h-5" />
                    Aperturar Cuenta
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-x-auto">
                <table className="min-w-[900px] sm:min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Banco y Tipo</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Número</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Cuenta Contable</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Saldo Registrado</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                        {accounts.map((acc) => (
                            <tr key={acc.id} className="hover:bg-slate-50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <Building2 className="flex-shrink-0 h-5 w-5 text-slate-400 mr-2" />
                                        <div>
                                            <div className="text-sm font-semibold text-slate-800">{acc.bank_name}</div>
                                            <div className="text-xs text-slate-500">{acc.account_type_display}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-700">
                                    {acc.account_number}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                    {acc.linked_account_code ? (
                                        <span className="bg-slate-100 text-slate-800 px-2 py-1 rounded text-xs">
                                            {acc.linked_account_code} - {acc.linked_account_name}
                                        </span>
                                    ) : (
                                        <span className="text-slate-400 italic">No Enlazada</span>
                                    )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-emerald-600">
                                    ${parseFloat(acc.initial_balance).toFixed(2)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                    <button
                                        onClick={() => handleOpenModal(acc)}
                                        className="text-indigo-600 hover:text-indigo-900 mx-2"
                                        title="Editar"
                                    >
                                        <Pencil className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(acc.id, acc.account_number.slice(-4))}
                                        className="text-red-500 hover:text-red-700 mx-2"
                                        title="Borrar"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {accounts.length === 0 && (
                            <tr>
                                <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                                    No hay cuentas bancarias operativas ingresadas.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal de Creación/Edición */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-slate-200">
                        <div className="flex px-6 py-4 border-b border-slate-100 bg-slate-50 justify-between items-center">
                            <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                                <Wallet className="w-5 h-5 text-indigo-600" />
                                {editingId ? 'Gestionar Cuenta Bancaria' : 'Nueva Cuenta Bancaria'}
                            </h3>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Banco Pertinente *</label>
                                    <select
                                        name="bank"
                                        value={formData.bank}
                                        onChange={handleChange}
                                        required
                                        className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    >
                                        <option value="" disabled>Seleccione el Banco...</option>
                                        {banks.map(b => (
                                            <option key={b.id} value={b.id}>{b.name}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Cuenta *</label>
                                    <select
                                        name="account_type"
                                        value={formData.account_type}
                                        onChange={handleChange}
                                        required
                                        className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    >
                                        <option value="CHECKING">Corriente</option>
                                        <option value="SAVINGS">Ahorros</option>
                                        <option value="VIRTUAL">Billetera Virtual</option>
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Número de Cuenta *</label>
                                    <input
                                        type="text"
                                        name="account_number"
                                        value={formData.account_number}
                                        onChange={handleChange}
                                        required
                                        placeholder="Ej: 2200113344"
                                        className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    />
                                </div>

                                <div className="col-span-2">
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Cuenta Contable (Enlace Opcional)</label>
                                    <select
                                        name="linked_account"
                                        value={formData.linked_account}
                                        onChange={handleChange}
                                        className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                                    >
                                        <option value="">Ninguna - Sin Enlace al Libro Mayor</option>
                                        {/* Simplification: Just listing roots here for assignment demo */}
                                        {accountingAccounts.map(acc => (
                                            <option key={acc.id} value={acc.id}>
                                                Mapear contra: {acc.code} - {acc.name}
                                            </option>
                                        ))}
                                    </select>
                                    <p className="text-xs text-slate-500 mt-1">Este enlace automatiza libros diarios en el Módulo de Tesorería.</p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Saldo Conciliado ($)</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        name="initial_balance"
                                        value={formData.initial_balance}
                                        onChange={handleChange}
                                        className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    />
                                </div>

                                <div className="flex items-center pt-6 pl-2">
                                    <input
                                        id="is_active_acc"
                                        name="is_active"
                                        type="checkbox"
                                        checked={formData.is_active}
                                        onChange={handleChange}
                                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                                    />
                                    <label htmlFor="is_active_acc" className="ml-2 block text-sm font-medium text-slate-700">
                                        Cuenta Habilitada
                                    </label>
                                </div>
                            </div>

                            <div className="mt-6 flex justify-end gap-3 pt-5 border-t border-slate-100">
                                <button
                                    type="button"
                                    onClick={handleCloseModal}
                                    className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 font-medium"
                                    disabled={isSubmitting}
                                >
                                    Cerrar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium disabled:opacity-50"
                                    disabled={isSubmitting}
                                >
                                    {isSubmitting ? 'Guardando...' : 'Guardar Cuenta'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BankAccountsPage;
