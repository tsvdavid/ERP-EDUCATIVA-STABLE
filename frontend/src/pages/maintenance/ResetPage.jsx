import React, { useState } from 'react';
import maintenanceService from '../../services/maintenanceService';
import { toast } from 'react-hot-toast';
import { RefreshCw, AlertTriangle, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../context/authStore';

const ResetPage = () => {
    const [loading, setLoading] = useState(false);
    const [confirmText, setConfirmText] = useState('');
    const navigate = useNavigate();
    const logout = useAuthStore(state => state.logout);

    const handleReset = async () => {
        if (confirmText !== 'RESETEAR') {
            toast.error('Por favor escriba "RESETEAR" para confirmar.');
            return;
        }

        if (!window.confirm('¡ATENCIÓN! ¿Está ABSOLUTAMENTE SEGURO? Esta acción borrará TODOS los datos de la base de datos de forma permanente. No se puede deshacer.')) {
            return;
        }

        try {
            setLoading(true);
            await maintenanceService.resetApplication();
            toast.success('Aplicación reseteada correctamente.');

            // Clear auth state properly
            logout();

            // Short delay to ensure toast is seen and state is cleared
            setTimeout(() => {
                navigate('/login');
            }, 1000);

        } catch (error) {
            console.error("Reset Error:", error);
            const errorMessage = error.response?.data?.error || error.message || 'Error desconocido';
            toast.error('Error al resetear: ' + errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-8 py-10">
            <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-red-100 rounded-full mb-4 ring-8 ring-red-50">
                    <AlertTriangle className="text-red-600" size={40} />
                </div>
                <h1 className="text-3xl font-extrabold text-slate-900">Reseteo de Aplicación (Danger Zone)</h1>
                <p className="text-slate-500 max-w-lg mx-auto">
                    Esta herramienta permite restablecer la base de datos al estado inicial.
                    <span className="block font-bold text-red-600 mt-1">¡Esta acción es destructiva e irreversible!</span>
                </p>
            </div>

            <div className="bg-white rounded-2xl shadow-xl border border-red-100 overflow-hidden">
                <div className="bg-red-50 p-6 border-b border-red-100 flex items-start gap-4">
                    <ShieldAlert className="text-red-500 mt-1 shrink-0" size={24} />
                    <div className="space-y-2">
                        <h3 className="font-bold text-red-800 text-lg">Advertencia de Seguridad</h3>
                        <p className="text-red-700 text-sm leading-relaxed">
                            Al ejecutar esta acción, se eliminarán permanentemente:
                        </p>
                        <ul className="list-disc list-inside text-red-700 text-sm ml-2 space-y-1">
                            <li>Todos los usuarios (excepto superusuarios en algunos casos).</li>
                            <li>Todos los registros académicos (notas, asistencias).</li>
                            <li>Datos contables y de facturación.</li>
                            <li>Información de tickets y auditoría.</li>
                        </ul>
                    </div>
                </div>

                <div className="p-8 space-y-6">
                    <div className="space-y-4">
                        <label className="block text-sm font-medium text-slate-700">
                            Para confirmar, escriba <span className="font-mono font-bold select-all bg-slate-100 rounded px-1 text-slate-900">RESETEAR</span> en el campo de abajo:
                        </label>
                        <input
                            type="text"
                            value={confirmText}
                            onChange={(e) => setConfirmText(e.target.value)}
                            className="block w-full rounded-lg border-slate-300 shadow-sm focus:border-red-500 focus:ring-red-500 sm:text-lg p-3 text-center tracking-widest uppercase font-bold placeholder:font-normal placeholder:normal-case placeholder:text-slate-400 placeholder:tracking-normal"
                            placeholder='Escribe "RESETEAR" aquí'
                        />
                    </div>

                    <button
                        onClick={handleReset}
                        disabled={loading || confirmText !== 'RESETEAR'}
                        className="w-full flex items-center justify-center gap-3 px-6 py-4 bg-red-600 text-white font-bold rounded-xl hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-500/30 transition-all transform active:scale-[0.98]"
                    >
                        {loading ? (
                            <>
                                <RefreshCw className="animate-spin" /> Procesando Reseteo...
                            </>
                        ) : (
                            <>
                                <AlertTriangle /> BORRAR TODOS LOS DATOS
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ResetPage;
