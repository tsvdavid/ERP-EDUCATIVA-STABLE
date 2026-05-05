import React, { useState, useEffect } from 'react';
import { Save, Shield, Clock, Bell, Zap, RefreshCw } from 'lucide-react';
import { toast, Toaster } from 'react-hot-toast';
import subscriptionService from '../../services/subscriptionService';

const SaaSSettingsPage = () => {
    const [settings, setSettings] = useState({
        default_trial_days: 30,
        grace_period_days: 5,
        auto_suspend: true,
        reminder_days: [30, 15, 7, 3, 1]
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const data = await subscriptionService.getGlobalSettings();
            setSettings(data);
        } catch (error) {
            toast.error("Error al cargar configuración global.");
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            await subscriptionService.updateGlobalSettings(settings);
            toast.success("Configuración SaaS actualizada correctamente.");
        } catch (error) {
            toast.error("Error al guardar cambios.");
        }
    };

    const handleReminderToggle = (day) => {
        const newReminders = settings.reminder_days.includes(day)
            ? settings.reminder_days.filter(d => d !== day)
            : [...settings.reminder_days, day].sort((a, b) => b - a);
        setSettings({ ...settings, reminder_days: newReminders });
    };

    if (loading) return <div className="p-8 text-center text-slate-500 font-bold">Cargando parámetros globales...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <Toaster position="top-right" />
            <div>
                <h1 className="text-3xl font-black text-slate-800 tracking-tight">Parámetros Globales <span className="text-indigo-600">SaaS</span></h1>
                <p className="text-slate-500">Configura el comportamiento automático de suscripciones, pruebas y mora.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* General Policy */}
                <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm space-y-6">
                    <div className="flex items-center gap-3 text-indigo-600">
                        <Shield size={24} strokeWidth={3} />
                        <h3 className="font-black uppercase tracking-widest text-sm">Política de Activación</h3>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Días de Prueba (Default)</label>
                            <input 
                                type="number" className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700"
                                value={settings.default_trial_days} onChange={e => setSettings({...settings, default_trial_days: parseInt(e.target.value)})}
                            />
                        </div>
                        <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-2xl">
                            <input 
                                type="checkbox" id="auto_suspend" className="w-5 h-5 rounded-lg text-indigo-600 border-slate-300"
                                checked={settings.auto_suspend} onChange={e => setSettings({...settings, auto_suspend: e.target.checked})}
                            />
                            <label htmlFor="auto_suspend" className="text-sm font-bold text-slate-700">Suspensión automática tras vencimiento</label>
                        </div>
                    </div>
                </div>

                {/* Grace & Reminders */}
                <div className="bg-white p-8 rounded-[2rem] border border-slate-100 shadow-sm space-y-6">
                    <div className="flex items-center gap-3 text-amber-500">
                        <Clock size={24} strokeWidth={3} />
                        <h3 className="font-black uppercase tracking-widest text-sm">Mora y Notificaciones</h3>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Días de Gracia</label>
                            <input 
                                type="number" className="w-full bg-slate-50 border-none rounded-2xl px-5 py-4 font-bold text-slate-700"
                                value={settings.grace_period_days} onChange={e => setSettings({...settings, grace_period_days: parseInt(e.target.value)})}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Alertas de Vencimiento (Días antes)</label>
                            <div className="flex flex-wrap gap-2">
                                {[30, 15, 7, 5, 3, 1].map(day => (
                                    <button
                                        key={day}
                                        onClick={() => handleReminderToggle(day)}
                                        className={`px-4 py-2 rounded-xl text-xs font-black transition-all ${
                                            settings.reminder_days.includes(day)
                                            ? 'bg-amber-500 text-white shadow-lg shadow-amber-100'
                                            : 'bg-slate-100 text-slate-400 hover:bg-slate-200'
                                        }`}
                                    >
                                        {day}d
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex justify-end">
                <button 
                    onClick={handleSave}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-2xl font-black shadow-xl shadow-indigo-100 transition-all active:scale-95"
                >
                    <Save size={20} />
                    Guardar Configuración
                </button>
            </div>
        </div>
    );
};

export default SaaSSettingsPage;
