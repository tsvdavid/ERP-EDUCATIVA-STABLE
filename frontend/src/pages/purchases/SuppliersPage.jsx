import React, { useState, useEffect } from 'react';
import purchaseService from '../../services/purchaseService';

const SuppliersPage = () => {
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingSupplier, setEditingSupplier] = useState(null);
    const [formData, setFormData] = useState({
        tax_id: '',
        legal_name: '',
        trade_name: '',
        address: '',
        email: '',
        phone: '',
        tax_id_type: 'RUC'
    });

    useEffect(() => {
        loadSuppliers();
    }, []);

    const loadSuppliers = async () => {
        try {
            const data = await purchaseService.getSuppliers();
            setSuppliers(data);
        } catch (error) {
            console.error("Error loading suppliers", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingSupplier) {
                await purchaseService.updateSupplier(editingSupplier.id, formData);
            } else {
                await purchaseService.createSupplier(formData);
            }
            setShowModal(false);
            setEditingSupplier(null);
            setFormData({ tax_id: '', legal_name: '', trade_name: '', address: '', email: '', phone: '', tax_id_type: 'RUC' });
            loadSuppliers();
        } catch (error) {
            console.error("Error saving supplier", error);
            alert("Error al guardar proveedor");
        }
    };

    const handleEdit = (supplier) => {
        setEditingSupplier(supplier);
        setFormData({
            tax_id: supplier.tax_id,
            legal_name: supplier.legal_name,
            trade_name: supplier.trade_name,
            address: supplier.address,
            email: supplier.email,
            phone: supplier.phone,
            tax_id_type: supplier.tax_id_type
        });
        setShowModal(true);
    };

    const handleDelete = async (id) => {
        if (window.confirm('¿Está seguro de eliminar este proveedor?')) {
            try {
                await purchaseService.deleteSupplier(id);
                loadSuppliers();
            } catch (error) {
                console.error("Error deleting supplier", error);
            }
        }
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Proveedores</h1>
                <button
                    onClick={() => {
                        setEditingSupplier(null);
                        setFormData({ tax_id: '', legal_name: '', trade_name: '', address: '', email: '', phone: '', tax_id_type: 'RUC' });
                        setShowModal(true);
                    }}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                    Nuevo Proveedor
                </button>
            </div>

            {loading ? (
                <div>Cargando...</div>
            ) : (
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Identificación</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Razón Social</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre Comercial</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {suppliers.map(sup => (
                                <tr key={sup.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">{sup.tax_id} ({sup.tax_id_type})</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{sup.legal_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">{sup.trade_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button onClick={() => handleEdit(sup)} className="text-indigo-600 hover:text-indigo-900 mr-4">Editar</button>
                                        <button onClick={() => handleDelete(sup.id)} className="text-red-600 hover:text-red-900">Eliminar</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center">
                    <div className="bg-white p-8 rounded-md shadow-xl w-96">
                        <h2 className="text-xl font-bold mb-4">{editingSupplier ? 'Editar' : 'Nuevo'} Proveedor</h2>
                        <form onSubmit={handleSubmit}>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700">Tipo ID</label>
                                <select
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                                    value={formData.tax_id_type}
                                    onChange={(e) => setFormData({ ...formData, tax_id_type: e.target.value })}
                                >
                                    <option value="RUC">RUC</option>
                                    <option value="CEDULA">Cédula</option>
                                    <option value="PASAPORTE">Pasaporte</option>
                                </select>
                            </div>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700">Identificación</label>
                                <input
                                    type="text"
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                                    value={formData.tax_id}
                                    onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700">Razón Social</label>
                                <input
                                    type="text"
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                                    value={formData.legal_name}
                                    onChange={(e) => setFormData({ ...formData, legal_name: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700">Nombre Comercial</label>
                                <input
                                    type="text"
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                                    value={formData.trade_name}
                                    onChange={(e) => setFormData({ ...formData, trade_name: e.target.value })}
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700">Email</label>
                                <input
                                    type="email"
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                />
                            </div>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-700">Dirección</label>
                                <input
                                    type="text"
                                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                                    value={formData.address}
                                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                />
                            </div>

                            <div className="flex justify-end mt-6">
                                <button
                                    type="button"
                                    onClick={() => setShowModal(false)}
                                    className="bg-gray-300 text-gray-700 px-4 py-2 rounded mr-2"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="bg-blue-600 text-white px-4 py-2 rounded"
                                >
                                    Guardar
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SuppliersPage;
