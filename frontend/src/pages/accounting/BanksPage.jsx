import React, { useState, useEffect } from 'react';
import accountingService from '../../services/accountingService';
import { Plus, Pencil, Trash2, Building } from 'lucide-react';

const BanksPage = () => {
    const [banks, setBanks] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Minimalist modal state
    const [showModal, setShowModal] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        code: '',
        is_active: true
    });

    useEffect(() => {
        fetchBanks();
    }, []);

    const fetchBanks = async () => {
        try {
            const data = await accountingService.getBanks();
            setBanks(data);
        } catch (error) {
            console.error("Error fetching banks:", error);
        }
    };

    const handleOpenModal = (bank = null) => {
        if (bank) {
            setEditingId(bank.id);
            setFormData({
                name: bank.name,
                code: bank.code || '',
                is_active: bank.is_active
            });
        } else {
            setEditingId(null);
            setFormData({ name: '', code: '', is_active: true });
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
            if (editingId) {
                await accountingService.updateBank(editingId, formData);
            } else {
                await accountingService.createBank(formData);
            }
            await fetchBanks();
            handleCloseModal();
        } catch (error) {
            console.error("Error saving bank:", error);
            alert("Ocurrió un error guardando la entidad bancaria. Verifique que no exista ya otra con el mismo nombre.");
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (id, name) => {
        if (window.confirm(`¿Está seguro que desea eliminar a '${name}'?\nRecuerde que no podrá si ya tiene cuentas asociadas.`)) {
            try {
                await accountingService.deleteBank(id);
                setBanks(banks.filter(b => b.id !== id));
            } catch (error) {
                console.error("Error deleting:", error);
                alert("No se pudo eliminar el banco. Es probable que esté en uso en cuentas bancarias.");
            }
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                        <Building className="w-7 h-7 text-indigo-600" />
                        Catálogo de Bancos
                    </h1>
                    <p className="text-slate-500 text-sm mt-1">
                        Gestione las Instituciones Financieras (Bancos, Cooperativas) soportadas por su colegio.
                    </p>
                </div>
                <button
                    onClick={() => handleOpenModal()}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 font-medium flex items-center gap-2 shadow-sm"
                >
                    <Plus className="w-5 h-5" />
                    Registrar Entidad
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-x-auto">
                <table className="min-w-[800px] sm:min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Nombre de Institución</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Código (SRI)</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Registro</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Estado</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-200">
                        {banks.map((bank) => (
                            <tr key={bank.id} className="hover:bg-slate-50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-slate-800">
                                    {bank.name}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                                    {bank.code || <span className="text-slate-400 italic">No provisto</span>}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                                    {new Date(bank.created_at).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${bank.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                        {bank.is_active ? 'Activo' : 'Inactivo'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                    <button
                                        onClick={() => handleOpenModal(bank)}
                                        className="text-indigo-600 hover:text-indigo-900 mx-2"
                                        title="Editar"
                                    >
                                        <Pencil className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(bank.id, bank.name)}
                                        className="text-red-500 hover:text-red-700 mx-2"
                                        title="Borrar"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {banks.length === 0 && (
                            <tr>
                                <td colSpan="5" className="px-6 py-12 text-center text-slate-500">
                                    No se han registrado bancos todavía. Seleccione "Registrar Entidad" para empezar.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal de Creación/Edición */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden border border-slate-200">
                        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
                            <h3 className="text-lg font-bold text-slate-800">
                                {editingId ? 'Editar Institución' : 'Registrar Nuevo Banco'}
                            </h3>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6">
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Nombre Comercial *</label>
                                    <input
                                        type="text"
                                        name="name"
                                        value={formData.name}
                                        onChange={handleChange}
                                        required
                                        autoFocus
                                        placeholder="Ej: Banco del Pichincha"
                                        className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Código Contable (Opcional)</label>
                                    <input
                                        type="text"
                                        name="code"
                                        value={formData.code}
                                        onChange={handleChange}
                                        placeholder="Código interno o SRI"
                                        className="w-full border-slate-300 rounded-lg shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                                    />
                                </div>
                                <div className="flex items-center pt-2">
                                    <input
                                        id="is_active"
                                        name="is_active"
                                        type="checkbox"
                                        checked={formData.is_active}
                                        onChange={handleChange}
                                        className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-slate-300 rounded"
                                    />
                                    <label htmlFor="is_active" className="ml-2 block text-sm text-slate-700">
                                        Institución Activa
                                    </label>
                                </div>
                            </div>
                            <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-slate-100">
                                <button
                                    type="button"
                                    onClick={handleCloseModal}
                                    className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 font-medium"
                                    disabled={isSubmitting}
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium disabled:opacity-50"
                                    disabled={isSubmitting}
                                >
                                    {isSubmitting ? 'Guardando...' : 'Guardar Datos'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BanksPage;
