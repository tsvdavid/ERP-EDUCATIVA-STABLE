import React, { useState, useEffect } from 'react';
import api from '../../services/api';
import { Save, AlertCircle, CircleCheckBig } from 'lucide-react';

function PaymentGatewaysConfigPage() {
    const [configs, setConfigs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState('');

    const API_URL = '/payments/config/';

    // Pasarelas soportadas iniciales hardcodeadas para la UI
    const defaultGateways = [
        { name: 'bank_transfer', title: 'Transferencia Bancaria', fields: [{ key: 'bank_name', label: 'Nombre del Banco' }, { key: 'account_type', label: 'Tipo de Cuenta (Ej: Corriente)' }, { key: 'owner_id', label: 'Identificación (Cédula/RUC)' }, { key: 'email', label: 'Correo Electrónico' }] },
        { name: 'stripe', title: 'Stripe', fields: [{ key: 'secret_key', label: 'Secret Key' }, { key: 'publishable_key', label: 'Publishable Key' }, { key: 'webhook_secret', label: 'Webhook Secret' }] },
        { name: 'paypal', title: 'PayPal', fields: [{ key: 'client_id', label: 'Client ID' }, { key: 'client_secret', label: 'Client Secret' }] },
        { name: 'mercadopago', title: 'MercadoPago', fields: [{ key: 'access_token', label: 'Access Token' }] },
        { name: 'payphone', title: 'PayPhone', fields: [{ key: 'token', label: 'Token de Autenticación' }] },
        { name: 'kushki', title: 'Kushki', fields: [{ key: 'public_merchant_id', label: 'Public Merchant ID' }, { key: 'private_merchant_id', label: 'Private Merchant ID' }] },
        { name: 'datafast', title: 'Datafast', fields: [{ key: 'merchant_id', label: 'Merchant ID' }, { key: 'terminal_id', label: 'Terminal ID' }] }
    ];

    useEffect(() => {
        fetchConfigs();
    }, []);

    const fetchConfigs = async () => {
        setLoading(true);
        try {
            const res = await api.get(API_URL);
            // Mezclamos la respuesta del backend con las plantillas por defecto
            const existing = res.data;
            const merged = defaultGateways.map(gw => {
                const found = existing.find(c => c.gateway_name === gw.name);
                if (found) {
                    return { ...gw, ...found, id: found.id, credentials: found.credentials || {} };
                }
                return { ...gw, is_active: false, is_test_mode: true, credentials: {} };
            });
            setConfigs(merged);
        } catch (err) {
            console.error(err);
            setError('Error al cargar la configuración de las pasarelas.');
        } finally {
            setLoading(false);
        }
    };

    const handleFieldChange = (index, field, value) => {
        const newConfigs = [...configs];
        if (field === 'is_active' || field === 'is_test_mode') {
            newConfigs[index][field] = value;
        } else {
            newConfigs[index].credentials[field] = value;
        }
        setConfigs(newConfigs);
    };

    const handleSave = async (config) => {
        setError(null);
        setSuccessMsg('');
        try {
            const payload = {
                gateway_name: config.name,
                is_active: config.is_active,
                is_test_mode: config.is_test_mode,
                credentials: config.credentials
            };

            if (config.id) {
                // Update
                await api.put(`${API_URL}${config.id}/`, payload);
            } else {
                // Create
                const res = await api.post(API_URL, payload);
                // Actualizar id local
                const newConfigs = [...configs];
                const idx = newConfigs.findIndex(c => c.name === config.name);
                newConfigs[idx].id = res.data.id;
                setConfigs(newConfigs);
            }
            setSuccessMsg(`Configuración de ${config.title} guardada exitosamente.`);
            setTimeout(() => setSuccessMsg(''), 3000);
        } catch (err) {
            console.error(err);
            setError(`Error guardando ${config.title}.`);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
            <h1 className="text-2xl font-bold text-slate-800 mb-6">Configuración de Pasarelas de Pago</h1>

            {error && (
                <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-md flex items-center gap-3">
                    <AlertCircle className="text-red-500" size={20} />
                    <p className="text-red-700">{error}</p>
                </div>
            )}

            {successMsg && (
                <div className="mb-6 bg-green-50 border-l-4 border-green-500 p-4 rounded-md flex items-center gap-3">
                    <CircleCheckBig className="text-green-500" size={20} />
                    <p className="text-green-700">{successMsg}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {configs.map((config, idx) => (
                    <div key={config.name} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-semibold text-slate-800">{config.title}</h2>
                                <label className="flex items-center cursor-pointer">
                                    <div className="relative">
                                        <input
                                            type="checkbox"
                                            className="sr-only"
                                            checked={config.is_active}
                                            onChange={(e) => handleFieldChange(idx, 'is_active', e.target.checked)}
                                        />
                                        <div className={`block w-10 h-6 rounded-full transition-colors ${config.is_active ? 'bg-indigo-500' : 'bg-slate-300'}`}></div>
                                        <div className={`dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${config.is_active ? 'transform translate-x-4' : ''}`}></div>
                                    </div>
                                    <span className="ml-3 text-sm font-medium text-slate-600">Activo</span>
                                </label>
                            </div>

                            <div className="space-y-4">
                                <label className="flex items-center cursor-pointer mb-4">
                                    <div className="relative">
                                        <input
                                            type="checkbox"
                                            className="sr-only"
                                            checked={config.is_test_mode}
                                            onChange={(e) => handleFieldChange(idx, 'is_test_mode', e.target.checked)}
                                        />
                                        <div className={`block w-10 h-6 rounded-full transition-colors ${config.is_test_mode ? 'bg-amber-500' : 'bg-slate-300'}`}></div>
                                        <div className={`dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${config.is_test_mode ? 'transform translate-x-4' : ''}`}></div>
                                    </div>
                                    <span className="ml-3 text-sm font-medium text-slate-600">
                                        {config.name === 'bank_transfer' ? 'Requiere Revisión Manual (Voucher)' : 'Modo Pruebas (Sandbox)'}
                                    </span>
                                </label>

                                {config.fields.map(fieldObj => (
                                    <div key={fieldObj.key}>
                                        <label className="block text-sm font-medium text-slate-700 mb-1">
                                            {fieldObj.label}
                                        </label>
                                        <input
                                            type={config.name === 'bank_transfer' ? 'text' : 'password'}
                                            className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-indigo-100 focus:border-indigo-400 outline-none transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                            value={config.credentials[fieldObj.key] || ''}
                                            onChange={(e) => handleFieldChange(idx, fieldObj.key, e.target.value)}
                                            disabled={!config.is_active}
                                            placeholder={`Ingrese ${fieldObj.label}`}
                                        />
                                    </div>
                                ))}
                            </div>

                            <div className="mt-6 flex justify-end">
                                <button
                                    onClick={() => handleSave(config)}
                                    disabled={!config.is_active && !config.id}
                                    className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                                >
                                    <Save size={16} />
                                    Guardar Configuración
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default PaymentGatewaysConfigPage;
