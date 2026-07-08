import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../context/authStore';
import api from '../../services/api';

const SetupWizard = () => {
    const { user } = useAuthStore();
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [statusLoading, setStatusLoading] = useState(true);
    const [statusError, setStatusError] = useState(null);
    const [completeError, setCompleteError] = useState(null);
    const [checklist, setChecklist] = useState(null);
    
    const [formData, setFormData] = useState({
        logo: null,
        ruc: '',
        establishment_code: '001',
        emission_point: '001',
        bank_name: '',
        account_number: '',
        account_type: 'CHECKING',
        obligado_contabilidad: false,
    });

    useEffect(() => {
        if (user?.institution) {
            fetchStatus();
        }
    }, [user]);

    const fetchStatus = async () => {
        setStatusLoading(true);
        setStatusError(null);
        try {
            const res = await api.get(`/users/institutions/${user.institution}/setup-status/`);
            setChecklist(res.data);
            if (res.data.wizard_completed) {
                navigate('/dashboard');
            }
        } catch (err) {
            console.error("Error fetching setup status", err);
            setStatusError("No se pudo cargar configuración inicial");
        } finally {
            setStatusLoading(false);
        }
    };

    const handleNext = () => setStep(prev => prev + 1);
    const handleBack = () => setStep(prev => prev - 1);

    const handleComplete = async () => {
        setLoading(true);
        setCompleteError(null);
        try {
            // 1. Update institution fields that are editable through regular PATCH.
            await api.patch(`/users/institutions/${user.institution}/`, {
                ruc: formData.ruc,
                establishment_code: formData.establishment_code,
                emission_point: formData.emission_point,
                obligado_contabilidad: formData.obligado_contabilidad,
            });

            // 2. Complete wizard through dedicated controlled endpoint.
            const completeRes = await api.post(`/users/institutions/${user.institution}/complete-wizard/`);
            if (!completeRes?.data?.success || !completeRes?.data?.wizard_completed) {
                throw new Error('No se pudo completar el wizard');
            }

            // 3. Reflect completion in local auth state to prevent guard redirect loop.
            useAuthStore.setState((state) => ({
                user: state.user ? { ...state.user, wizard_completed: true } : state.user,
            }));
            
            navigate('/dashboard');
        } catch (err) {
            setCompleteError(err.response?.data?.error || err.message || 'No se pudo completar la configuración');
        } finally {
            setLoading(false);
        }
    };

    if (statusLoading) return <div className="p-10 text-center">Cargando configuración inicial...</div>;

    if (statusError) {
        return (
            <div className="p-10 text-center">
                <p className="text-red-600 font-medium mb-4">{statusError}</p>
                <button
                    onClick={fetchStatus}
                    className="px-6 py-2.5 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-all"
                >
                    Reintentar
                </button>
            </div>
        );
    }

    if (!checklist) return <div className="p-10 text-center">No se pudo cargar configuración inicial</div>;

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
            <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
                <div className="bg-indigo-600 p-8 text-white">
                    <h1 className="text-2xl font-bold">Bienvenido a Eduka360</h1>
                    <p className="text-indigo-100 mt-1">Configuración inicial de tu institución</p>
                    
                    <div className="flex mt-6 gap-2">
                        {[1, 2, 3, 4].map(s => (
                            <div key={s} className={`h-1.5 flex-1 rounded-full ${s <= step ? 'bg-white' : 'bg-indigo-400'}`} />
                        ))}
                    </div>
                </div>

                <div className="p-8">
                    {step === 1 && (
                        <div className="space-y-6">
                            <h2 className="text-xl font-semibold text-slate-800">Paso 1: Identificación Institucional</h2>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">RUC de la Institución</label>
                                <input 
                                    type="text" 
                                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                                    placeholder="179XXXXXXX001"
                                    value={formData.ruc}
                                    onChange={e => setFormData({...formData, ruc: e.target.value})}
                                />
                            </div>
                            <div className="flex gap-4">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Cód. Establecimiento</label>
                                    <input 
                                        type="text" 
                                        className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg"
                                        maxLength={3}
                                        value={formData.establishment_code}
                                        onChange={e => setFormData({...formData, establishment_code: e.target.value})}
                                    />
                                </div>
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Punto de Emisión</label>
                                    <input 
                                        type="text" 
                                        className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg"
                                        maxLength={3}
                                        value={formData.emission_point}
                                        onChange={e => setFormData({...formData, emission_point: e.target.value})}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="space-y-6">
                            <h2 className="text-xl font-semibold text-slate-800">Paso 2: Firma Electrónica</h2>
                            <p className="text-sm text-slate-500">Eduka360 requiere tu firma (.p12) para emitir facturas electrónicas autorizadas por el SRI.</p>
                            <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-indigo-400 transition-colors cursor-pointer bg-slate-50">
                                <span className="text-slate-400 block mb-2">Próximamente: Subir archivo .p12</span>
                                <p className="text-xs text-slate-400">Puedes saltar este paso y configurarlo después en "Institución".</p>
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="space-y-6">
                            <h2 className="text-xl font-semibold text-slate-800">Paso 3: Cuenta Bancaria Principal</h2>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Nombre del Banco</label>
                                <input 
                                    type="text" 
                                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg"
                                    placeholder="Ej: Banco Pichincha"
                                    value={formData.bank_name}
                                    onChange={e => setFormData({...formData, bank_name: e.target.value})}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Número de Cuenta</label>
                                <input 
                                    type="text" 
                                    className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg"
                                    value={formData.account_number}
                                    onChange={e => setFormData({...formData, account_number: e.target.value})}
                                />
                            </div>
                        </div>
                    )}

                    {step === 4 && (
                        <div className="space-y-6">
                            <h2 className="text-xl font-semibold text-slate-800">Paso 4: Resumen y Finalización</h2>
                            <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 space-y-3">
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Plan de Cuentas:</span>
                                    <span className={checklist.chart_accounts ? "text-green-600 font-medium" : "text-amber-600"}>
                                        {checklist.chart_accounts ? "Listo ✓" : "Pendiente"}
                                    </span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Configuración Contable:</span>
                                    <span className={checklist.configs ? "text-green-600 font-medium" : "text-amber-600"}>
                                        {checklist.configs ? "Listo ✓" : "Pendiente"}
                                    </span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-slate-500">Año Fiscal:</span>
                                    <span className={checklist.fiscal_year ? "text-green-600 font-medium" : "text-amber-600"}>
                                        {checklist.fiscal_year ? "Listo ✓" : "Pendiente"}
                                    </span>
                                </div>
                            </div>
                            <div className="p-4 bg-indigo-50 text-indigo-700 text-sm rounded-lg border border-indigo-100">
                                Al hacer clic en <strong>Finalizar</strong>, tu institución será marcada como lista para operar.
                            </div>
                        </div>
                    )}

                    <div className="mt-10 flex justify-between">
                        {step > 1 ? (
                            <button 
                                onClick={handleBack}
                                className="px-6 py-2.5 text-slate-600 font-medium hover:bg-slate-100 rounded-lg transition-colors"
                            >
                                Atrás
                            </button>
                        ) : <div />}

                        {step < 4 ? (
                            <button 
                                onClick={handleNext}
                                className="px-8 py-2.5 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 shadow-md transition-all active:scale-95"
                            >
                                Siguiente
                            </button>
                        ) : (
                            <div className="flex flex-col items-end gap-2">
                                {completeError && (
                                    <p className="text-sm text-red-600 font-medium">{completeError}</p>
                                )}
                                <button 
                                    onClick={handleComplete}
                                    disabled={loading}
                                    className="px-8 py-2.5 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 shadow-md transition-all active:scale-95 disabled:bg-slate-400"
                                >
                                    {loading ? "Procesando..." : "Finalizar Configuración"}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SetupWizard;
