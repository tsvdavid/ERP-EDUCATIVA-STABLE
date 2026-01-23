import React, { useState } from 'react';
import maintenanceService from '../../services/maintenanceService';
import { toast } from 'react-hot-toast';
import { Download, Upload, AlertTriangle, FileJson } from 'lucide-react';

const BackupRestorePage = () => {
    const [loading, setLoading] = useState(false);
    const [file, setFile] = useState(null);

    const handleBackup = async () => {
        try {
            setLoading(true);
            const data = await maintenanceService.downloadBackup();

            // Create blob and download link
            const url = window.URL.createObjectURL(new Blob([data]));
            const link = document.createElement('a');
            link.href = url;
            const date = new Date().toISOString().split('T')[0];
            link.setAttribute('download', `erp_backup_${date}.json`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);

            toast.success('Backup generado correctamente');
        } catch (error) {
            console.error(error);
            toast.error('Error al generar el backup');
        } finally {
            setLoading(false);
        }
    };

    const handleRestore = async () => {
        if (!file) {
            toast.error('Por favor seleccione un archivo');
            return;
        }

        if (!window.confirm('¿Está seguro de restaurar la base de datos? Esto sobrescribirá los datos actuales.')) {
            return;
        }

        try {
            setLoading(true);
            await maintenanceService.restoreBackup(file);
            toast.success('Restauración completada con éxito');
            setFile(null);
            // Optional: force logout or reload
            setTimeout(() => window.location.reload(), 2000);
        } catch (error) {
            console.error(error);
            toast.error('Error en la restauración: ' + (error.response?.data?.error || 'Error desconocido'));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Copia de Seguridad y Restauración</h1>
                <p className="text-slate-500">Gestione los backups de la base de datos del sistema.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Backup Card */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
                        <Download className="text-indigo-600" size={24} />
                    </div>
                    <h2 className="text-lg font-bold text-slate-800 mb-2">Descargar Backup</h2>
                    <p className="text-sm text-slate-500 mb-6">
                        Genere un archivo JSON con toda la información actual de la base de datos.
                        Guarde este archivo en un lugar seguro.
                    </p>
                    <button
                        onClick={handleBackup}
                        disabled={loading}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                    >
                        {loading ? 'Procesando...' : (
                            <>
                                <Download size={18} /> Generar Copia de Seguridad
                            </>
                        )}
                    </button>
                </div>

                {/* Restore Card */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                    <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4">
                        <Upload className="text-orange-600" size={24} />
                    </div>
                    <h2 className="text-lg font-bold text-slate-800 mb-2">Restaurar Información</h2>
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-4 flex gap-2">
                        <AlertTriangle className="text-orange-500 shrink-0" size={18} />
                        <p className="text-xs text-orange-700">
                            <strong>Advertencia:</strong> Esta acción sobrescribirá los datos actuales con los del archivo de respaldo.
                        </p>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-center w-full">
                            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-300 border-dashed rounded-lg cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <FileJson className="w-8 h-8 mb-3 text-slate-400" />
                                    <p className="mb-2 text-sm text-slate-500">
                                        <span className="font-semibold">Click para subir</span>
                                    </p>
                                    <p className="text-xs text-slate-500">Archivo .JSON</p>
                                </div>
                                <input
                                    type="file"
                                    className="hidden"
                                    accept=".json"
                                    onChange={(e) => setFile(e.target.files[0])}
                                />
                            </label>
                        </div>

                        {file && (
                            <div className="flex items-center gap-2 text-sm text-slate-600 bg-slate-100 px-3 py-2 rounded-lg">
                                <FileJson size={16} />
                                <span className="truncate">{file.name}</span>
                            </div>
                        )}

                        <button
                            onClick={handleRestore}
                            disabled={loading || !file}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors font-medium"
                        >
                            {loading ? 'Restaurando...' : 'Restaurar Base de Datos'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BackupRestorePage;
