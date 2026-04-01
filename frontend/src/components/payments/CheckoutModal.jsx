import React, { useState, useEffect } from 'react';
import { X, CreditCard, CheckCircle, AlertCircle, ShoppingCart, UploadCloud } from 'lucide-react';
import api from '../../services/api';

const CheckoutModal = ({ isOpen, onClose, cartPayload, onPaymentSuccess }) => {
    const [gateways, setGateways] = useState([]);
    const [selectedGateway, setSelectedGateway] = useState('');
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState(null);
    const [voucherFile, setVoucherFile] = useState(null);
    const [loadingGateways, setLoadingGateways] = useState(false);

    // Fetch gateways dynamically
    useEffect(() => {
        if (isOpen) {
            fetchGateways();
        }
    }, [isOpen]);

    const fetchGateways = async () => {
        setLoadingGateways(true);
        try {
            const res = await api.get('/payments/payment-gateway-configs/');
            const activeGateways = res.data.map(gw => {
                let icon = '💳';
                let name = gw.gateway_name;

                switch (gw.gateway_name) {
                    case 'stripe': name = 'Tarjeta de Crédito / Débito (Stripe)'; icon = '💳'; break;
                    case 'paypal': name = 'PayPal'; icon = '🌐'; break;
                    case 'mercadopago': name = 'MercadoPago'; icon = '🤝'; break;
                    case 'payphone': name = 'PayPhone (Ecuador)'; icon = '📱'; break;
                    case 'kushki': name = 'Kushki'; icon = '🛡️'; break;
                    case 'datafast': name = 'Datafast'; icon = '⚡'; break;
                    case 'bank_transfer': name = 'Transferencia Bancaria'; icon = '🏦'; break;
                    default: break;
                }
                return { ...gw, id: gw.gateway_name, name, icon };
            });
            setGateways(activeGateways);
        } catch (err) {
            console.error(err);
            setError('Error al cargar los métodos de pago.');
        } finally {
            setLoadingGateways(false);
        }
    };

    if (!isOpen) return null;

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setVoucherFile(e.target.files[0]);
        }
    };

    const handleCheckout = async () => {
        if (!selectedGateway) {
            setError('Por favor selecciona un método de pago.');
            return;
        }

        if (selectedGateway === 'bank_transfer' && !voucherFile) {
            setError('Por favor adjunta el comprobante de transferencia.');
            return;
        }

        setProcessing(true);
        setError(null);

        try {
            // Este payload asume que ya trae el "amount", "currency", "description"
            let response;

            if (selectedGateway === 'bank_transfer') {
                // Multipark Form Data para enviar archivo
                const formData = new FormData();
                formData.append('gateway_name', selectedGateway);
                formData.append('amount', cartPayload.amount);
                formData.append('currency', cartPayload.currency || 'USD');
                if (cartPayload.description) formData.append('description', cartPayload.description);
                if (cartPayload.reference_id) formData.append('reference_id', cartPayload.reference_id);
                formData.append('voucher_file', voucherFile);

                response = await api.post('/payments/checkout/', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });
            } else {
                const payload = {
                    ...cartPayload,
                    gateway_name: selectedGateway
                };
                response = await api.post('/payments/checkout/', payload);
            }

            const { checkout_data, transaction_id } = response.data;

            // Manejo dinámico según la pasarela
            switch (selectedGateway) {
                case 'bank_transfer':
                    if (onPaymentSuccess) {
                        onPaymentSuccess({ status: 'verifying', message: checkout_data.message });
                    } else {
                        alert(checkout_data.message || 'Comprobante subido exitosamente.');
                        onClose();
                    }
                    break;
                case 'stripe':
                    // Ejemplo: Redirigir a ventana de Stripe o renderizar elemento
                    // Ideal usar @stripe/react-stripe-js con el client_secret
                    alert(`Iniciando Stripe Modal con secret: ${checkout_data.client_secret}`);
                    break;
                case 'payphone':
                    if (checkout_data.pay_url) {
                        window.location.href = checkout_data.pay_url;
                    }
                    break;
                case 'paypal':
                    if (checkout_data.approve_url) {
                        window.location.href = checkout_data.approve_url;
                    }
                    break;
                case 'mercadopago':
                    if (checkout_data.init_point) {
                        window.location.href = checkout_data.init_point;
                    }
                    break;
                case 'datafast':
                    if (checkout_data.process_url) {
                        window.location.href = checkout_data.process_url;
                    }
                    break;
                case 'kushki':
                    alert('Mostrar formulario de Kushki Cajita usando public_key');
                    break;
                default:
                    setError('Pasarela no soportada o estructurada.');
            }

        } catch (err) {
            console.error(err);
            setError(err.response?.data?.error || 'Error al iniciar el pago.');
        } finally {
            setProcessing(false);
        }
    };

    const selectedGatewayObj = gateways.find(gw => gw.id === selectedGateway);

    return (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in-95 relative max-h-[90vh] overflow-y-auto">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 focus:outline-none"
                    disabled={processing}
                >
                    <X size={24} />
                </button>

                <div className="flex items-center gap-3 border-b border-slate-100 pb-4 mb-6">
                    <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center">
                        <ShoppingCart size={20} />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-slate-800">Finalizar Pago</h2>
                        <p className="text-sm text-slate-500">Total a pagar: <span className="font-bold text-slate-700">${cartPayload.amount}</span> {cartPayload.currency || 'USD'}</p>
                    </div>
                </div>

                {error && (
                    <div className="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm flex items-start gap-2">
                        <AlertCircle size={16} className="mt-0.5 shrink-0" />
                        <span>{error}</span>
                    </div>
                )}

                <div className="space-y-3 mb-6">
                    <label className="block text-sm font-bold text-slate-700 mb-2">Selecciona un método de pago</label>
                    {loadingGateways ? (
                        <div className="text-center p-4 text-slate-500">Cargando métodos disponibles...</div>
                    ) : gateways.length === 0 ? (
                        <div className="text-center p-4 text-orange-600 bg-orange-50 rounded-lg">No hay métodos de pago configurados por la institución.</div>
                    ) : (
                        <div className="grid grid-cols-1 gap-2 max-h-60 overflow-y-auto pr-2">
                            {gateways.map(gw => (
                                <button
                                    key={gw.id}
                                    onClick={() => setSelectedGateway(gw.id)}
                                    className={`flex items-center gap-3 p-3 rounded-lg border text-left transition-all ${selectedGateway === gw.id
                                        ? 'border-indigo-600 bg-indigo-50 ring-1 ring-indigo-600'
                                        : 'border-slate-200 hover:border-indigo-300'
                                        }`}
                                >
                                    <span className="text-2xl">{gw.icon}</span>
                                    <span className={`font-medium ${selectedGateway === gw.id ? 'text-indigo-800' : 'text-slate-700'}`}>
                                        {gw.name}
                                    </span>
                                    {selectedGateway === gw.id && <CheckCircle size={18} className="text-indigo-600 ml-auto shrink-0" />}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {selectedGateway === 'bank_transfer' && (
                    <div className="mb-6 bg-slate-50 p-4 rounded-xl border border-slate-200">
                        <h3 className="font-bold text-slate-700 mb-2 text-sm">Instrucciones de Transferencia</h3>
                        {selectedGatewayObj?.credentials?.bank_name ? (
                            <div className="text-sm text-slate-600 mb-4 space-y-1">
                                <p><strong>Banco:</strong> {selectedGatewayObj.credentials.bank_name}</p>
                                <p><strong>Tipo de Cuenta:</strong> {selectedGatewayObj.credentials.account_type}</p>
                                <p><strong>Identificación (Cédula/RUC):</strong> {selectedGatewayObj.credentials.owner_id}</p>
                                <p><strong>Correo Electrónico:</strong> {selectedGatewayObj.credentials.email}</p>
                            </div>
                        ) : (
                            <div className="text-sm text-orange-600 mb-4">
                                Configuración bancaria incompleta por parte de la institución.
                            </div>
                        )}

                        <div className="mt-2">
                            <label className="block text-sm font-bold text-slate-700 mb-2">Comprobante de Depósito</label>
                            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-lg cursor-pointer bg-white hover:bg-slate-50 transition-colors">
                                <div className="flex flex-col items-center justify-center pt-5 pb-6 px-4 text-center">
                                    <UploadCloud className="w-8 h-8 mb-2 text-slate-400" />
                                    {voucherFile ? (
                                        <p className="text-sm text-green-600 font-semibold truncate max-w-[200px]">{voucherFile.name}</p>
                                    ) : (
                                        <>
                                            <p className="mb-1 text-sm text-slate-500"><span className="font-semibold">Click para subir</span> o arrastra y suelta</p>
                                            <p className="text-xs text-slate-400">PDF, JPG o PNG (Max. 5MB)</p>
                                        </>
                                    )}
                                </div>
                                <input type="file" className="hidden" accept=".pdf,image/*" onChange={handleFileChange} />
                            </label>
                        </div>
                    </div>
                )}

                <div className="pt-4 border-t border-slate-100">
                    <button
                        onClick={handleCheckout}
                        disabled={processing || !selectedGateway || (selectedGateway === 'bank_transfer' && !voucherFile)}
                        className="w-full btn-primary py-3 text-lg font-bold flex justify-center items-center gap-2"
                    >
                        {processing ? 'Procesando...' : (
                            <>
                                {selectedGateway === 'bank_transfer' ? `Enviar Comprobante de $${cartPayload.amount}` : `Pagar $${cartPayload.amount}`}
                                {selectedGateway !== 'bank_transfer' && <CreditCard size={20} />}
                            </>
                        )}
                    </button>
                    {selectedGateway !== 'bank_transfer' && (
                        <p className="text-center text-xs text-slate-400 mt-4 flex items-center justify-center gap-1">
                            Paga de forma segura y encriptada
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CheckoutModal;
