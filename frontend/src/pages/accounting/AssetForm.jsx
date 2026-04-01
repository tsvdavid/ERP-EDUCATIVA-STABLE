import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import accountingService from '../../services/accountingService';

const AssetForm = () => {
    const navigate = useNavigate();
    const [accounts, setAccounts] = useState([]);

    const [formData, setFormData] = useState({
        name: '',
        code: '',
        purchase_date: new Date().toISOString().slice(0, 10),
        purchase_price: '',
        salvage_value: '0',
        useful_life_years: 5,
        account_asset: '',
        account_depreciation: '',
        account_expense: ''
    });

    useEffect(() => {
        const loadAccounts = async () => {
            try {
                // Fetch all accounts to let user choose the appropriate ones
                const data = await accountingService.getAccounts({ roots: false });
                setAccounts(data);
            } catch (error) {
                console.error("Error loading accounts", error);
            }
        };
        loadAccounts();
    }, []);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({ ...formData, [name]: value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                useful_life_years: parseInt(formData.useful_life_years, 10),
                account_asset: parseInt(formData.account_asset, 10),
                account_expense: parseInt(formData.account_expense, 10),
                account_depreciation: parseInt(formData.account_depreciation, 10),
                purchase_price: parseFloat(formData.purchase_price),
                salvage_value: parseFloat(formData.salvage_value)
            };
            await accountingService.createAsset(payload);
            navigate('/dashboard/accounting/assets');
        } catch (error) {
            console.error("Error creating asset", error);
            alert("Error al registrar el activo fijo. Revise los campos requeridos.");
        }
    };

    return (
        <div className="p-6 max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">Registrar Activo Fijo</h1>
                <button
                    type="button"
                    onClick={() => navigate('/dashboard/accounting/assets')}
                    className="bg-gray-200 text-gray-700 px-4 py-2 rounded shadow hover:bg-gray-300"
                >
                    Volver al Listado
                </button>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
                <div>
                    <h3 className="text-lg font-medium text-gray-900 border-b pb-2 mb-4">Información del Bien</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Nombre / Descripción *</label>
                            <input
                                type="text" name="name" required
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.name} onChange={handleChange}
                                placeholder="Ej. Mac G5 16GB"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Código / Etiqueta</label>
                            <input
                                type="text" name="code"
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.code} onChange={handleChange}
                                placeholder="Ej. CMP-001"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Fecha de Adquisición *</label>
                            <input
                                type="date" name="purchase_date" required
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.purchase_date} onChange={handleChange}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Valor de Adquisición ($) *</label>
                            <input
                                type="number" step="0.01" name="purchase_price" required min="0"
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.purchase_price} onChange={handleChange}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Valor de Salvamento ($) *</label>
                            <input
                                type="number" step="0.01" name="salvage_value" required min="0"
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.salvage_value} onChange={handleChange}
                            />
                            <p className="text-xs text-gray-500 mt-1">Valor residual esperado al final de la vida útil.</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Vida Útil (Años) *</label>
                            <input
                                type="number" name="useful_life_years" required min="1"
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.useful_life_years} onChange={handleChange}
                            />
                            <p className="text-xs text-gray-500 mt-1">Base para cálculo de depreciación por línea recta.</p>
                        </div>
                    </div>
                </div>

                <div>
                    <h3 className="text-lg font-medium text-gray-900 border-b pb-2 mb-4">Configuración Contable</h3>
                    <p className="text-sm text-gray-500 mb-4">Seleccione las cuentas para los asientos automatizados de depreciación.</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Cuenta de Activo *</label>
                            <select
                                name="account_asset" required
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.account_asset} onChange={handleChange}
                            >
                                <option value="">-- Seleccionar --</option>
                                {accounts.filter(a => a.account_type === 'ASSET').map(acc => (
                                    <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Cuenta Gasto por Depreciación *</label>
                            <select
                                name="account_expense" required
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.account_expense} onChange={handleChange}
                            >
                                <option value="">-- Seleccionar --</option>
                                {accounts.filter(a => a.account_type === 'EXPENSE').map(acc => (
                                    <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Cuenta Depreciación Acumulada *</label>
                            <select
                                name="account_depreciation" required
                                className="mt-1 block w-full border border-gray-300 rounded shadow-sm p-2"
                                value={formData.account_depreciation} onChange={handleChange}
                            >
                                <option value="">-- Seleccionar --</option>
                                {accounts.filter(a => a.account_type === 'ASSET' || a.account_type === 'LIABILITY').map(acc => (
                                    <option key={acc.id} value={acc.id}>{acc.code} - {acc.name} ({acc.account_type})</option>
                                ))}
                            </select>
                            <p className="text-xs text-gray-500 mt-1">Usualmente una cuenta reguladora de activo (se acredita mes a mes).</p>
                        </div>
                    </div>
                </div>

                <div className="flex justify-end pt-4 border-t">
                    <button
                        type="submit"
                        className="bg-indigo-600 text-white px-6 py-2 rounded shadow hover:bg-indigo-700"
                    >
                        Guardar Activo Fijo
                    </button>
                </div>
            </form>
        </div>
    );
};

export default AssetForm;
