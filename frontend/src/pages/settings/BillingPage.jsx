import React, { useState, useEffect } from 'react';
import { CreditCard, AlertTriangle, CheckCircle, Calendar, Package } from 'lucide-react';
import { toast, Toaster } from 'react-hot-toast';
import subscriptionService from '../../services/subscriptionService';

const BillingPage = () => {
    const [info, setInfo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadInfo = async () => {
            try {
                const data = await subscriptionService.getMyBillingInfo();
                setInfo(data);
            } catch (error) {
                if (error.response?.status === 404) {
                    setInfo({ no_subscription: true });
                } else {
                    toast.error("Error al cargar la información de facturación.");
                }
            } finally {
                setLoading(false);
            }
        };
        loadInfo();
    }, []);

    if (loading) return <div className="p-8 text-center text-slate-500">Cargando detalles de facturación...</div>;

    if (info?.no_subscription) {
        return (
            <div className="p-8 max-w-2xl mx-auto bg-white rounded-xl border border-slate-200 text-center">
                <CreditCard size={48} className="mx-auto text-slate-300 mb-4" />
                <h2 className="text-xl font-bold text-slate-800 mb-2">Sin suscripción activa</h2>
                <p className="text-slate-500">No hemos detectado una suscripción configurada para su institución. Por favor contacte con soporte para activar su plan.</p>
            </div>
        );
    }

    // Guard against missing info (e.g., API error 400)
    if (!info) {
        return (
            <div className="p-8 max-w-2xl mx-auto bg-white rounded-xl border border-slate-200 text-center">
                <AlertTriangle size={48} className="mx-auto text-rose-300 mb-4" />
                <h2 className="text-xl font-bold text-slate-800 mb-2">Error de facturación</h2>
                <p className="text-slate-500">No se pudo cargar la información de facturación. Por favor contacte al soporte.</p>
            </div>
        );
    }

    const isSuspended = info?.status === 'SUSPENDED';
    const isGrace = info?.status === 'GRACE';
    const isExpiring = info?.status === 'EXPIRING';

    return (
        <div className="space-y-6 max-w-4xl mx-auto">
            <Toaster position="top-right" />
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Mi Facturación y Suscripción</h1>
                <p className="text-slate-500">Gestione su plan, módulos activos y pagos de Eduka360.</p>
            </div>

            {/* Status Alert */}
            {isSuspended && (
                <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-xl flex items-start gap-3">
                    <AlertTriangle className="shrink-0 mt-0.5" />
                    <div>
                        <h3 className="font-bold">Servicio Suspendido</h3>
                        <p className="text-sm">Su suscripción se encuentra suspendida por falta de pago. Por favor, regularice su saldo pendiente de <strong>${info.monthly_fee}</strong> para reactivar el servicio inmediatamente.</p>
                    </div>
                </div>
            )}
            
            {isGrace && (
                <div className="bg-amber-50 border border-amber-200 text-amber-800 p-4 rounded-xl flex items-start gap-3">
                    <AlertTriangle className="shrink-0 mt-0.5" />
                    <div>
                        <h3 className="font-bold">Pago Atrasado (Período de Gracia)</h3>
                        <p className="text-sm">Su fecha de corte fue el {info.next_billing_date}. Tiene hasta el <strong>{info.grace_until}</strong> para registrar su pago antes de que el servicio sea suspendido.</p>
                    </div>
                </div>
            )}
            
            {isExpiring && (
                <div className="bg-blue-50 border border-blue-200 text-blue-800 p-4 rounded-xl flex items-start gap-3">
                    <Clock className="shrink-0 mt-0.5" />
                    <div>
                        <h3 className="font-bold">Próximo Vencimiento</h3>
                        <p className="text-sm">Su próxima factura de <strong>${info.monthly_fee}</strong> se generará el <strong>{info.next_billing_date}</strong>. ¡Asegúrese de realizar el pago a tiempo!</p>
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Plan Details */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2 mb-4"><Package size={20} className="text-indigo-500" /> Plan Actual</h2>
                    <div className="space-y-4">
                        <div>
                            <p className="text-sm text-slate-500">Nombre del Plan</p>
                            <p className="font-bold text-lg">{info.plan_name}</p>
                        </div>
                        <div>
                            <p className="text-sm text-slate-500">Módulos Contratados</p>
                            <ul className="mt-1 space-y-1">
                                {info.modules?.length > 0 ? info.modules.map((m, i) => (
                                    <li key={i} className="flex items-center gap-2 text-sm text-slate-700">
                                        <CheckCircle size={14} className="text-emerald-500" /> {m}
                                    </li>
                                )) : <li className="text-sm text-slate-400">Ningún módulo adicional</li>}
                            </ul>
                        </div>
                    </div>
                </div>

                {/* Billing Summary */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2 mb-4"><Calendar size={20} className="text-emerald-500" /> Resumen de Cobro</h2>
                    <div className="space-y-4">
                        <div className="flex justify-between items-end border-b border-slate-100 pb-3">
                            <div>
                                <p className="text-sm text-slate-500">Cuota Fija</p>
                                <p className="text-2xl font-bold text-slate-800">${info.monthly_fee}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-slate-500">Próximo Corte</p>
                                <p className="font-bold text-slate-700">{info.next_billing_date}</p>
                            </div>
                        </div>
                        
                        <div className="bg-slate-50 p-4 rounded-lg text-sm text-slate-600">
                            <p className="font-bold text-slate-700 mb-1">Instrucciones de Pago</p>
                            <p>{info.payment_instructions}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BillingPage;
