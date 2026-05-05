import React, { useState, useEffect } from 'react';
import { 
    Mail, 
    Settings, 
    FileText, 
    History, 
    Plus, 
    Save, 
    Play, 
    CheckCircle2, 
    XCircle, 
    AlertCircle,
    Loader2,
    Eye,
    RefreshCw,
    ShieldCheck,
    Send,
    Edit3,
    Trash2,
    Lock,
    ExternalLink
} from 'lucide-react';
import notificationService from '../../services/notificationService';
import { toast } from 'react-hot-toast';

const EmailCenter = () => {
    const [activeTab, setActiveTab] = useState('config');
    const [loading, setLoading] = useState(false);
    const [configs, setConfigs] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [logs, setLogs] = useState([]);
    const [isTesting, setIsTesting] = useState(false);

    const activeInstitution = localStorage.getItem('active_institution');

    useEffect(() => {
        fetchData();
        // Listener para cambios en localStorage (opcional pero recomendado)
        const handleStorage = () => fetchData();
        window.addEventListener('storage', handleStorage);
        return () => window.removeEventListener('storage', handleStorage);
    }, [activeTab, activeInstitution]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (activeTab === 'config') {
                const data = await notificationService.getConfigs();
                console.log("DEBUG: Configs received from backend:", data);
                setConfigs(data);
            } else if (activeTab === 'templates') {
                const data = await notificationService.getTemplates();
                setTemplates(data);
            } else if (activeTab === 'logs') {
                const data = await notificationService.getLogs();
                setLogs(data);
            }
        } catch (error) {
            console.error("Error fetching data:", error);
            toast.error("Error al cargar datos del módulo de correos");
        } finally {
            setLoading(false);
        }
    };

    const handleTestConnection = async (id) => {
        setIsTesting(true);
        try {
            const res = await notificationService.testConnection(id);
            toast.success(res.message || "Conexión exitosa. Email de prueba enviado.");
        } catch (error) {
            console.error("SMTP Test Error:", error);
            if (error.code === 'ECONNABORTED') {
                toast.error("La solicitud superó el tiempo de espera. El servidor SMTP está tardando demasiado en responder.");
            } else {
                toast.error(error.response?.data?.message || error.response?.data?.error || "Error de conexión SMTP. Verifique sus credenciales.");
            }
        } finally {
            setIsTesting(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50/50 p-4 md:p-8 space-y-8 animate-in fade-in duration-700">
            {/* Header Moderno */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-xl shadow-slate-200/50">
                <div className="flex items-center gap-6">
                    <div className="relative">
                        <div className="bg-rose-500 p-4 rounded-3xl text-white shadow-lg shadow-rose-200 animate-pulse">
                            <Mail size={32} />
                        </div>
                        <div className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-white rounded-full" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-slate-900 tracking-tight leading-none mb-2">
                            Centro de Correos
                        </h1>
                        <p className="text-slate-500 text-sm font-semibold uppercase tracking-[0.15em] flex items-center gap-2">
                            <ShieldCheck size={14} className="text-rose-500" />
                            Gestión Transaccional Multi-tenant
                        </p>
                    </div>
                </div>
                
                <div className="flex bg-slate-100/80 p-1.5 rounded-[1.5rem] self-start md:self-center border border-slate-200/50">
                    <TabButton active={activeTab === 'config'} onClick={() => setActiveTab('config')} icon={<Settings size={18} />} label="Configuración" />
                    <TabButton active={activeTab === 'templates'} onClick={() => setActiveTab('templates')} icon={<FileText size={18} />} label="Plantillas" />
                    <TabButton active={activeTab === 'logs'} onClick={() => setActiveTab('logs')} icon={<History size={18} />} label="Logs" />
                </div>
            </div>

            {loading && !configs.length && !templates.length && !logs.length ? (
                <div className="flex flex-col items-center justify-center p-32 text-slate-400 bg-white rounded-[2.5rem] border border-slate-100 shadow-sm">
                    <div className="relative">
                        <Loader2 className="animate-spin text-rose-500 mb-6" size={64} strokeWidth={1} />
                        <Mail className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-full text-slate-300" size={24} />
                    </div>
                    <p className="font-black text-slate-400 uppercase tracking-widest text-xs">Sincronizando con el motor de email...</p>
                </div>
            ) : (
                <div className={`animate-in slide-in-from-bottom-8 duration-700 ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
                    {activeTab === 'config' && <SmtpConfig configs={configs} onTest={handleTestConnection} isTesting={isTesting} onRefresh={fetchData} />}
                    {activeTab === 'templates' && <TemplatesManager templates={templates} onRefresh={fetchData} />}
                    {activeTab === 'logs' && <LogsList logs={logs} onRefresh={fetchData} />}
                </div>
            )}
        </div>
    );
};

const TabButton = ({ active, onClick, icon, label }) => (
    <button 
        onClick={onClick}
        className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all duration-300 ${
            active 
                ? 'bg-white text-rose-600 shadow-md transform scale-[1.02]' 
                : 'text-slate-500 hover:text-slate-800'
        }`}
    >
        {icon} {label}
    </button>
);

const SmtpConfig = ({ configs, onTest, isTesting, onRefresh }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [saving, setSaving] = useState(false);
    const activeConfig = configs.length > 0 ? configs[0] : null;

    const [formData, setFormData] = useState({
        smtp_host: activeConfig?.smtp_host || '',
        smtp_port: activeConfig?.smtp_port || '',
        smtp_user: activeConfig?.smtp_user || '',
        smtp_password: '',
        sender_name: activeConfig?.sender_name || '',
        sender_email: activeConfig?.sender_email || '',
        use_tls: activeConfig?.use_tls ?? true,
        use_ssl: activeConfig?.use_ssl ?? false,
        is_active: activeConfig?.is_active ?? true
    });

    useEffect(() => {
        if (activeConfig) {
            setFormData({
                ...activeConfig,
                smtp_password: '' // No sobreescribir con password cifrada del backend
            });
        } else {
            // Resetear al cambiar a una institución sin configuración
            setFormData({
                smtp_host: '',
                smtp_port: '',
                smtp_user: '',
                smtp_password: '',
                sender_name: '',
                sender_email: '',
                use_tls: true,
                use_ssl: false,
                is_active: true
            });
        }
    }, [activeConfig]);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        const finalValue = type === 'checkbox' ? checked : value;
        
        setFormData(prev => {
            const newState = { ...prev, [name]: finalValue };
            
            // Regla obligatoria: Exclusividad mutua entre SSL y TLS
            if (name === 'use_tls' && checked) newState.use_ssl = false;
            if (name === 'use_ssl' && checked) newState.use_tls = false;
            
            return newState;
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        
        // Preparar payload final con tipos correctos
        const payload = { 
            ...formData,
            smtp_port: parseInt(formData.smtp_port, 10)
        };

        // Si la contraseña está vacía, no la enviamos (seguridad)
        if (!payload.smtp_password) delete payload.smtp_password;

        try {
            if (activeConfig?.id) {
                await notificationService.updateConfig(activeConfig.id, payload);
                toast.success("Configuración actualizada correctamente");
            } else {
                await notificationService.createConfig(payload);
                toast.success("Servidor SMTP configurado con éxito");
            }
            
            await onRefresh();
            setIsEditing(false);
        } catch (error) {
            console.error("DEBUG: SMTP Save Error Response Data:", error.response?.data);
            const errorMsg = error.response?.data?.non_field_errors?.[0] || 
                           error.response?.data?.detail || 
                           "Error al guardar la configuración SMTP";
            toast.error(errorMsg);
        } finally {
            setSaving(false);
        }
    };

    if (isEditing || !activeConfig) {
        return (
            <div className="max-w-5xl mx-auto bg-white rounded-[3rem] border border-slate-100 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-500">
                <div className="bg-slate-900 p-10 text-white relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-rose-500/10 rounded-full blur-3xl -mr-32 -mt-32" />
                    <div className="relative z-10 flex items-center justify-between">
                        <div>
                            <h3 className="text-2xl font-black tracking-tight mb-2">Configuración SMTP</h3>
                            <p className="text-slate-400 text-xs font-bold uppercase tracking-[0.2em]">Ingrese las credenciales de su proveedor (Gmail, Outlook, etc.)</p>
                        </div>
                        {activeConfig && (
                            <button 
                                onClick={() => setIsEditing(false)}
                                className="text-slate-400 hover:text-white transition-colors uppercase text-[10px] font-black tracking-widest"
                            >
                                Cancelar
                            </button>
                        )}
                    </div>
                </div>

                <form 
                    key={activeConfig?.id || 'new'}
                    onSubmit={handleSubmit} 
                    className="p-10 grid grid-cols-1 md:grid-cols-2 gap-8 bg-slate-50/30"
                >
                    <div className="space-y-6">
                        <h4 className="font-black text-xs text-slate-400 uppercase tracking-widest flex items-center gap-2">
                             <Send size={14} className="text-rose-500" /> Servidor de Salida
                        </h4>
                        
                        <div className="space-y-4">
                            <InputField label="Host SMTP" name="smtp_host" value={formData.smtp_host} onChange={handleChange} placeholder="smtp.gmail.com" required />
                            <InputField label="Puerto" name="smtp_port" type="number" value={formData.smtp_port} onChange={handleChange} placeholder="587" required />
                            <InputField 
                                label="Usuario / Correo" 
                                name="smtp_user" 
                                value={formData.smtp_user} 
                                onChange={handleChange} 
                                placeholder="correo@ejemplo.com" 
                                required 
                                autoComplete="new-password"
                            />
                            <div className="space-y-1.5">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">Contraseña</label>
                                <div className="relative">
                                    <input 
                                        name="smtp_password" 
                                        type="password" 
                                        value={formData.smtp_password}
                                        onChange={handleChange}
                                        autoComplete="new-password"
                                        placeholder={activeConfig ? "•••••••••••• (Dejar en blanco para mantener)" : "Ingresar contraseña"}
                                        className="w-full bg-white border border-slate-200 rounded-2xl px-5 py-4 text-sm font-bold shadow-sm focus:border-rose-500 focus:ring-4 focus:ring-rose-500/5 transition-all outline-none"
                                    />
                                    <Lock size={18} className="absolute right-5 top-1/2 -translate-y-1/2 text-slate-300" />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <h4 className="font-black text-xs text-slate-400 uppercase tracking-widest flex items-center gap-2">
                             <Settings size={14} className="text-rose-500" /> Identidad y Seguridad
                        </h4>
                        
                        <div className="space-y-4">
                            <InputField label="Nombre del Remitente" name="sender_name" value={formData.sender_name} onChange={handleChange} placeholder="Institución Educativa XYZ" required />
                            <InputField label="Email del Remitente" name="sender_email" value={formData.sender_email} onChange={handleChange} placeholder="no-reply@edu.ec" required />
                            
                            <div className="p-6 bg-white border border-slate-100 rounded-[2rem] shadow-sm space-y-4 mt-6">
                                <ToggleField label="Usar TLS" name="use_tls" checked={formData.use_tls} onChange={handleChange} />
                                <ToggleField label="Usar SSL" name="use_ssl" checked={formData.use_ssl} onChange={handleChange} />
                                <hr className="border-slate-50" />
                                <ToggleField label="Habilitar Servicio" name="is_active" checked={formData.is_active} onChange={handleChange} highlighted />
                            </div>
                        </div>
                    </div>

                    <div className="md:col-span-2 pt-6 flex justify-end gap-4 border-t border-slate-100">
                        <button 
                            type="submit" 
                            disabled={saving}
                            className="bg-slate-900 text-white px-12 py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-xl shadow-slate-200 hover:bg-slate-800 transition-all flex items-center gap-3 active:scale-95"
                        >
                            {saving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                            {activeConfig ? 'Guardar Cambios' : 'Finalizar Configuración'}
                        </button>
                    </div>
                </form>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-xl overflow-hidden animate-in slide-in-from-bottom-8">
                <div className="bg-slate-900 p-10 text-white flex items-center justify-between relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
                        <div className="absolute -top-10 -left-10 w-40 h-40 bg-rose-500 rounded-full blur-[80px]" />
                        <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-blue-500 rounded-full blur-[80px]" />
                    </div>
                    
                    <div className="relative z-10 flex items-center gap-6">
                        <div className="bg-slate-800/50 p-4 rounded-3xl border border-slate-700/50 text-rose-500">
                            <Settings size={32} strokeWidth={1.5} />
                        </div>
                        <div>
                            <h3 className="text-2xl font-black tracking-tight">{activeConfig.smtp_host}</h3>
                            <div className="flex items-center gap-3 mt-1">
                                <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${activeConfig.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                                    {activeConfig.is_active ? 'Activo' : 'Offline'}
                                </span>
                                <span className="text-slate-400 text-xs font-bold uppercase tracking-widest">Puerto {activeConfig.smtp_port}</span>
                            </div>
                        </div>
                    </div>

                    <div className="relative z-10 flex items-center gap-4">
                        <button 
                            onClick={() => onTest(activeConfig.id)}
                            disabled={isTesting}
                            className={`flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all ${isTesting ? 'bg-slate-800 text-slate-500 border border-slate-700' : 'bg-rose-600 text-white hover:bg-rose-500 shadow-lg shadow-rose-900/40 active:scale-95'}`}
                        >
                            {isTesting ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                            {isTesting ? 'Validando...' : 'Test Envío'}
                        </button>
                        <button 
                            onClick={() => setIsEditing(true)}
                            className="bg-white/10 hover:bg-white/20 p-4 rounded-2xl text-white transition-all border border-white/5"
                        >
                            <Edit3 size={20} />
                        </button>
                    </div>
                </div>

                <div className="p-10 bg-slate-50/50">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <DetailCard label="Usuario SMTP" value={activeConfig.smtp_user} icon={<Lock size={14}/>} />
                        <DetailCard label="Email Remitente" value={activeConfig.sender_email} icon={<Mail size={14}/>} />
                        <DetailCard label="Nombre Remitente" value={activeConfig.sender_name} icon={<Eye size={14}/>} />
                        <div className="p-6 bg-white border border-slate-100 rounded-3xl shadow-sm flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="bg-indigo-50 p-2 rounded-xl text-indigo-600"><ShieldCheck size={16}/></div>
                                <p className="text-xs font-black text-slate-500 uppercase tracking-widest">Protocolos</p>
                            </div>
                            <div className="flex gap-2">
                                {activeConfig.use_tls && <span className="bg-emerald-50 text-emerald-600 text-[10px] font-black px-2 py-0.5 rounded uppercase">TLS</span>}
                                {activeConfig.use_ssl && <span className="bg-blue-50 text-blue-600 text-[10px] font-black px-2 py-0.5 rounded uppercase">SSL</span>}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-600 to-violet-800 p-8 rounded-[2.5rem] text-white shadow-xl shadow-indigo-200/50 flex flex-col md:flex-row items-center gap-8 border-4 border-white">
                <div className="bg-white/10 p-5 rounded-[2rem] border border-white/10">
                    <ShieldCheck size={48} strokeWidth={1} />
                </div>
                <div className="flex-1 text-center md:text-left">
                    <h4 className="text-xl font-black mb-1 tracking-tight">Seguridad Multi-Tenant Activada</h4>
                    <p className="text-indigo-100 text-sm font-medium leading-relaxed opacity-80">
                        Sus credenciales están protegidas con cifrado AES-256 (Fernet) y aisladas a nivel de base de datos para su institución.
                    </p>
                </div>
                <div className="flex items-center gap-2 bg-white/10 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border border-white/5">
                    <CheckCircle2 size={14} className="text-emerald-400" /> NIST Compliant
                </div>
            </div>
        </div>
    );
};

const InputField = ({ label, name, type = "text", value, onChange, placeholder, required = false, autoComplete = "off" }) => (
    <div className="space-y-1.5 flex flex-col">
        <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest px-1">{label} {required && <span className="text-rose-500">*</span>}</label>
        <input 
            type={type} 
            name={name} 
            value={value || ''} 
            onChange={onChange}
            placeholder={placeholder}
            required={required}
            autoComplete={autoComplete}
            className="w-full bg-white border border-slate-200 rounded-2xl px-5 py-4 text-sm font-bold shadow-sm focus:border-rose-500 focus:ring-4 focus:ring-rose-500/5 transition-all outline-none"
        />
    </div>
);

const ToggleField = ({ label, name, checked, onChange, highlighted = false }) => (
    <div className="flex items-center justify-between group">
        <span className={`text-[11px] font-black uppercase tracking-widest ${highlighted ? 'text-slate-800' : 'text-slate-500'}`}>{label}</span>
        <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" name={name} checked={checked} onChange={onChange} className="sr-only peer" />
            <div className={`w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all ${highlighted ? 'peer-checked:bg-rose-500' : 'peer-checked:bg-slate-900'}`}></div>
        </label>
    </div>
);

const DetailCard = ({ label, value, icon }) => (
    <div className="p-6 bg-white border border-slate-100 rounded-[2rem] shadow-sm group hover:border-rose-200 transition-colors">
        <div className="flex items-center gap-3 mb-2">
            <div className="text-slate-300 group-hover:text-rose-500 transition-colors">{icon}</div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none">{label}</p>
        </div>
        <p className="text-sm font-bold text-slate-700 px-1 truncate">{value}</p>
    </div>
);

const LogsList = ({ logs, onRefresh }) => (
    <div className="max-w-6xl mx-auto bg-white rounded-[3rem] border border-slate-100 shadow-xl overflow-hidden animate-in slide-in-from-bottom-8">
        <div className="px-10 py-8 border-b border-slate-50 flex items-center justify-between bg-white">
            <div>
                <h3 className="font-black text-lg text-slate-800 tracking-tight">Registro de Auditoría</h3>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mt-1">Monitoreo de envíos en tiempo real</p>
            </div>
            <button onClick={onRefresh} className="p-4 bg-slate-50 rounded-2xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-all active:rotate-180 duration-500">
                <RefreshCw size={20} />
            </button>
        </div>
        <div className="overflow-x-auto">
            <table className="w-full text-left">
                <thead>
                    <tr className="bg-slate-50/50 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        <th className="px-10 py-5">Estado</th>
                        <th className="px-6 py-5">Destinatario</th>
                        <th className="px-6 py-5">Asunto</th>
                        <th className="px-6 py-5">Módulo</th>
                        <th className="px-10 py-5">Fecha y Hora</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {logs.length === 0 ? (
                        <tr><td colSpan="5" className="px-10 py-20 text-center text-slate-300 font-bold uppercase tracking-widest text-xs italic">No hay actividad registrada aún</td></tr>
                    ) : (
                        logs.map(log => (
                            <tr key={log.id} className="hover:bg-slate-50/30 transition-colors group">
                                <td className="px-10 py-6">
                                    {log.status === 'sent' && <StatusTag color="emerald" icon={<CheckCircle2 size={12}/>} text="Enviado" />}
                                    {log.status === 'failed' && <StatusTag color="rose" icon={<XCircle size={12}/>} text="Falló" />}
                                    {log.status === 'queued' && <StatusTag color="blue" icon={<History size={12}/>} text="En Cola" />}
                                </td>
                                <td className="px-6 py-6 font-bold text-slate-700 text-sm">{log.recipient}</td>
                                <td className="px-6 py-6 text-slate-500 text-sm max-w-sm truncate font-medium">{log.subject}</td>
                                <td className="px-6 py-6">
                                    <span className="text-[10px] font-black bg-slate-100 px-3 py-1.5 rounded-xl text-slate-500 uppercase tracking-wider">{log.module_origin || 'General'}</span>
                                </td>
                                <td className="px-10 py-6 text-slate-400 text-xs font-bold font-mono">
                                    {new Date(log.created_at).toLocaleDateString()} <span className="opacity-50 mx-1">•</span> {new Date(log.created_at).toLocaleTimeString()}
                                </td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    </div>
);

const StatusTag = ({ color, icon, text }) => (
    <span className={`flex items-center gap-2 w-fit px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider bg-${color}-50 text-${color}-600 border border-${color}-100`}>
        {icon} {text}
    </span>
);

const TemplatesManager = ({ templates, onRefresh }) => {
    const [viewTemplate, setViewTemplate] = useState(null);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
            <div className="bg-white border-4 border-dashed border-slate-100 rounded-[3rem] p-10 flex flex-col items-center justify-center text-slate-300 hover:border-rose-300 hover:text-rose-400 transition-all cursor-pointer group h-[340px]">
                <div className="bg-slate-50 p-6 rounded-[2rem] shadow-sm mb-6 group-hover:scale-110 transition-transform group-hover:bg-rose-50 duration-500">
                    <Plus size={40} strokeWidth={1.5} />
                </div>
                <p className="font-black text-xs uppercase tracking-[0.2em]">Nueva Plantilla</p>
                <div className="mt-4 px-4 py-1.5 bg-slate-100 rounded-full text-[8px] font-black uppercase tracking-widest text-slate-400 group-hover:bg-rose-100 group-hover:text-rose-500 transition-colors">Personalizar Comunicación</div>
            </div>

            {templates.map(tmp => (
                <div key={tmp.id} className="bg-white p-8 rounded-[3rem] border border-slate-100 shadow-xl shadow-slate-200/50 hover:shadow-2xl hover:-translate-y-2 transition-all duration-500 group relative flex flex-col h-[340px]">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-1.5 h-6 bg-rose-500 rounded-full" />
                            <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{tmp.code}</span>
                        </div>
                        <div className={`w-3 h-3 rounded-full ${tmp.is_active ? 'bg-emerald-500 box-content border-4 border-emerald-50' : 'bg-slate-200'}`} />
                    </div>
                    
                    <h4 className="text-xl font-black text-slate-800 tracking-tight mb-4 group-hover:text-rose-600 transition-colors line-clamp-2 leading-tight">
                        {tmp.subject}
                    </h4>
                    
                    <div className="bg-slate-50 p-6 rounded-[2rem] text-slate-400 text-[10px] font-bold leading-relaxed line-clamp-3 mb-auto font-mono opacity-60">
                        {tmp.html_body.replace(/<[^>]*>?/gm, '').substring(0, 150)}...
                    </div>
                    
                    <div className="flex items-center gap-2 mt-6">
                        <button 
                            onClick={() => setViewTemplate(tmp)}
                            className="flex-1 bg-slate-900 text-white py-3.5 rounded-2xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-rose-600 transition-all"
                        >
                            <Eye size={14} /> Vista Previa
                        </button>
                        <button className="p-3.5 bg-slate-100 text-slate-500 rounded-2xl hover:bg-slate-200 transition-all">
                            <Edit3 size={18} />
                        </button>
                    </div>
                </div>
            ))}

            {/* Modal de Vista Previa */}
            {viewTemplate && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-4xl overflow-hidden animate-in zoom-in-95 duration-500">
                        <div className="px-10 py-6 border-b border-slate-50 flex items-center justify-between bg-slate-100/50">
                            <div className="flex items-center gap-4">
                                <div className="bg-white p-3 rounded-2xl shadow-sm text-rose-500">
                                    <Send size={20} />
                                </div>
                                <h3 className="font-black text-slate-900 uppercase tracking-widest text-sm">Previsualización de Plantilla</h3>
                            </div>
                            <button onClick={() => setViewTemplate(null)} className="p-2 text-slate-400 hover:text-slate-900 bg-white rounded-xl shadow-sm">
                                <XCircle size={24} />
                            </button>
                        </div>
                        <div className="p-10 max-h-[70vh] overflow-y-auto bg-slate-50">
                            <div className="bg-white p-8 rounded-[2rem] shadow-sm border border-slate-200/50 min-h-[400px]" dangerouslySetInnerHTML={{ __html: viewTemplate.html_body }} />
                        </div>
                        <div className="px-10 py-6 bg-white border-t border-slate-50 flex justify-end">
                            <button onClick={() => setViewTemplate(null)} className="px-10 py-3 bg-slate-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest">Cerrar</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default EmailCenter;
