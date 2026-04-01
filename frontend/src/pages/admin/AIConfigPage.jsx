import React, { useState, useEffect } from 'react';
import aiService from '../../services/aiService';
import { Save, AlertCircle, CircleCheckBig, Sparkles, Activity } from 'lucide-react';

function AIConfigPage() {
    const [configs, setConfigs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [testing, setTesting] = useState(false);
    const [error, setError] = useState(null);
    const [successMsg, setSuccessMsg] = useState('');

    const providers = [
        { 
            id: 'anthropic', 
            name: 'Anthropic (Claude)', 
            defaultModel: 'claude-3-haiku-20240307',
            fields: [
                { key: 'api_key', label: 'Anthropic API Key', type: 'password' },
                { key: 'model_name', label: 'Modelo (ej: claude-3-haiku)', type: 'text' }
            ]
        },
        { 
            id: 'openai', 
            name: 'OpenAI (GPT)', 
            defaultModel: 'gpt-4o-mini',
            fields: [
                { key: 'api_key', label: 'OpenAI API Key', type: 'password' },
                { key: 'model_name', label: 'Modelo (ej: gpt-4o)', type: 'text' }
            ]
        },
        { 
            id: 'local', 
            name: 'Local / Custom (Ollama)', 
            defaultModel: 'llama3',
            fields: [
                { key: 'api_base_url', label: 'API Base URL (ej: http://localhost:11434/v1)', type: 'text' },
                { key: 'api_key', label: 'API Key (Opcional)', type: 'password' },
                { key: 'model_name', label: 'Modelo (ej: llama3)', type: 'text' }
            ]
        }
    ];

    useEffect(() => {
        fetchConfigs();
    }, []);

    const fetchConfigs = async () => {
        setLoading(true);
        try {
            const existingConfigs = await aiService.getConfigs();
            const merged = providers.map(p => {
                const found = existingConfigs.find(c => c.provider === p.id);
                if (found) {
                    return { ...p, ...found, api_key: '' }; // No mostramos la clave anterior por seguridad
                }
                return { ...p, is_active: false, api_key: '', model_name: p.defaultModel, api_base_url: p.id === 'local' ? 'http://localhost:11434/v1' : '' };
            });
            setConfigs(merged);
        } catch (err) {
            console.error(err);
            setError('Error al cargar la configuración de IA.');
        } finally {
            setLoading(false);
        }
    };

    const handleFieldChange = (idx, field, value) => {
        const newConfigs = [...configs];
        newConfigs[idx][field] = value;
        setConfigs(newConfigs);
    };

    const handleSave = async (config) => {
        setError(null);
        setSuccessMsg('');
        try {
            const payload = {
                provider: config.id,
                api_key: config.api_key,
                model_name: config.model_name,
                api_base_url: config.api_base_url,
                is_active: config.is_active,
                institution: 1 // TODO: Obtener del contexto si es necesario, el backend lo maneja usualmente
            };

            if (config.pk) { // Usamos pk o id dependiendo de cómo venga del backend
                await aiService.updateConfig(config.pk, payload);
            } else if (config.id && typeof config.id === 'number') {
                 await aiService.updateConfig(config.id, payload);
            } else {
                await aiService.createConfig(payload);
            }
            
            setSuccessMsg(`Configuración de ${config.name} guardada exitosamente.`);
            fetchConfigs(); // Recargar para obtener IDs
            setTimeout(() => setSuccessMsg(''), 3000);
        } catch (err) {
            console.error(err);
            setError(`Error al guardar ${config.name}. Asegúrate de completar los campos obligatorios.`);
        }
    };

    const handleTest = async () => {
        setTesting(true);
        setError(null);
        setSuccessMsg('');
        try {
            const res = await aiService.testConnection();
            if (res.status === 'success') {
                setSuccessMsg(`Conexión exitosa: IA respondió "${res.response}"`);
            } else {
                setError(`Error en la prueba: ${res.message}`);
            }
        } catch (err) {
            setError(`Error de conexión: ${err.response?.data?.message || err.message}`);
        } finally {
            setTesting(false);
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-indigo-600 border-solid"></div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto p-6 lg:p-12">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        <Sparkles className="text-indigo-600" size={32} />
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight">Configuración Eduka IA</h1>
                    </div>
                    <p className="text-slate-500 font-medium">Gestiona los modelos de lenguaje que potencian tu plataforma.</p>
                </div>
                <button 
                    onClick={handleTest}
                    disabled={testing}
                    className="flex items-center justify-center gap-2 px-8 py-4 bg-slate-900 text-white rounded-[2rem] font-black hover:bg-indigo-600 transition-all shadow-xl shadow-slate-200 disabled:opacity-50"
                >
                    {testing ? <Activity className="animate-spin" size={20} /> : <Activity size={20} />}
                    Probar Conexión Activa
                </button>
            </header>

            {error && (
                <div className="mb-8 bg-red-50 border-2 border-red-100 p-6 rounded-[2rem] flex items-center gap-4 animate-shake">
                    <div className="bg-red-500 p-2 rounded-xl text-white">
                        <AlertCircle size={20} />
                    </div>
                    <p className="text-red-700 font-bold">{error}</p>
                </div>
            )}

            {successMsg && (
                <div className="mb-8 bg-emerald-50 border-2 border-emerald-100 p-6 rounded-[2rem] flex items-center gap-4 animate-bounce-subtle">
                    <div className="bg-emerald-500 p-2 rounded-xl text-white">
                        <CircleCheckBig size={20} />
                    </div>
                    <p className="text-emerald-700 font-bold">{successMsg}</p>
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {configs.map((config, idx) => (
                    <div key={config.id} className={`bg-white rounded-[3rem] shadow-sm border-2 transition-all overflow-hidden ${config.is_active ? 'border-indigo-500 ring-4 ring-indigo-50' : 'border-slate-100 hover:border-slate-200'}`}>
                        <div className="p-8 lg:p-10">
                            <div className="flex justify-between items-center mb-8">
                                <h2 className="text-2xl font-black text-slate-900 tracking-tight">{config.name}</h2>
                                <label className="relative inline-flex items-center cursor-pointer">
                                    <input 
                                        type="checkbox" 
                                        className="sr-only peer"
                                        checked={config.is_active}
                                        onChange={(e) => handleFieldChange(idx, 'is_active', e.target.checked)}
                                    />
                                    <div className="w-14 h-8 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[4px] after:start-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-indigo-600"></div>
                                    <span className="ms-3 text-sm font-black text-slate-400 uppercase tracking-widest leading-none">Activar</span>
                                </label>
                            </div>

                            <div className="space-y-6">
                                {config.fields.map(field => (
                                    <div key={field.key} className="space-y-2">
                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">{field.label}</label>
                                        <input
                                            type={field.type}
                                            className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all"
                                            value={config[field.key] || ''}
                                            onChange={(e) => handleFieldChange(idx, field.key, e.target.value)}
                                            placeholder={`Ingrese ${field.label.toLowerCase()}`}
                                        />
                                    </div>
                                ))}
                            </div>

                            <div className="mt-10 flex flex-col gap-4">
                                <button
                                    onClick={() => handleSave(config)}
                                    className="w-full py-5 bg-slate-900 text-white rounded-[2rem] font-black text-lg hover:bg-indigo-600 transition-all shadow-xl shadow-slate-200 flex items-center justify-center gap-3"
                                >
                                    <Save size={24} /> Guardar Cambios
                                </button>
                                {config.is_active && (
                                    <div className="flex items-center justify-center gap-2 text-[10px] font-black text-indigo-500 uppercase tracking-widest">
                                        <CircleCheckBig size={14} /> Proveedor por defecto actual
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <footer className="mt-16 p-8 bg-indigo-50 rounded-[3rem] border-2 border-indigo-100 flex flex-col md:flex-row items-center gap-8 text-center md:text-left">
                <div className="bg-indigo-600 p-4 rounded-3xl text-white shadow-lg shadow-indigo-200">
                    <AlertCircle size={32} />
                </div>
                <div>
                    <h3 className="text-xl font-black text-indigo-900 mb-2">Importante sobre las API Keys</h3>
                    <p className="text-indigo-700 font-medium leading-relaxed">
                        Tus claves se cifran antes de guardarse en la base de datos. Recuerda que el uso de Anthropic y OpenAI genera cargos según el consumo de tokens. Para uso local con Ollama, asegúrate de que el VPS tenga acceso al puerto configurado.
                    </p>
                </div>
            </footer>
        </div>
    );
}

export default AIConfigPage;
