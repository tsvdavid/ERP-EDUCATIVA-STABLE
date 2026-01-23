import React, { useState, useEffect } from 'react';
import maintenanceService from '../../services/maintenanceService';
import { toast } from 'react-hot-toast';
import { FileText, RefreshCw, AlertCircle } from 'lucide-react';

const LogPage = () => {
    const [logContent, setLogContent] = useState('');
    const [loading, setLoading] = useState(false);

    const fetchLog = async () => {
        try {
            setLoading(true);
            const data = await maintenanceService.getLog();
            setLogContent(data.log || 'El archivo de registro está vacío.');
        } catch (error) {
            console.error(error);
            toast.error('Error al cargar los registros');
            setLogContent('Error al intentar leer el archivo de log.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLog();
    }, []);

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Registro de Errores (Logs)</h1>
                    <p className="text-slate-500">Visualización del archivo de registro del sistema para depuración.</p>
                </div>
                <button
                    onClick={fetchLog}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors font-medium border border-indigo-200"
                >
                    <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
                    Actualizar
                </button>
            </div>

            <div className="flex-1 bg-slate-900 rounded-xl overflow-hidden shadow-lg border border-slate-700 flex flex-col">
                <div className="bg-slate-800 px-4 py-2 flex items-center justify-between border-b border-slate-700">
                    <span className="text-xs text-slate-400 font-mono">django.log</span>
                    <div className="flex gap-1.5">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500"></div>
                        <div className="w-2.5 h-2.5 rounded-full bg-green-500"></div>
                    </div>
                </div>
                <div className="flex-1 p-4 overflow-auto custom-scrollbar">
                    {loading && !logContent ? (
                        <div className="text-slate-500 text-center py-10">Cargando registros...</div>
                    ) : (
                        <pre className="font-mono text-xs text-green-400 whitespace-pre-wrap leading-relaxed">
                            {logContent}
                        </pre>
                    )}
                    {!loading && logContent.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-2">
                            <AlertCircle size={32} />
                            <p>Archivo de log vacío</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LogPage;
