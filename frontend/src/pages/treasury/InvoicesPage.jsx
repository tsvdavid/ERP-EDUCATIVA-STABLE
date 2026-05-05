import React, { useState, useEffect } from 'react';
import { FileText, Download, Send, Check, AlertCircle, RefreshCw, Settings, Save, FileCode, History, Mail, X, Zap } from 'lucide-react';
import { toast } from 'react-hot-toast';
import treasuryService from '../../services/treasuryService';
import userService from '../../services/userService';
import { useAuthStore } from '../../context/authStore';

const InvoicesPage = () => {
    const { user } = useAuthStore();
    const [activeTab, setActiveTab] = useState('invoices'); // 'invoices' or 'config'

    // Invoices State
    const [invoices, setInvoices] = useState([]);
    const [loadingInvoices, setLoadingInvoices] = useState(true);

    // Modals State
    const [selectedInvoice, setSelectedInvoice] = useState(null);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [historyLogs, setHistoryLogs] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    const [showAltEmailModal, setShowAltEmailModal] = useState(false);
    const [altEmail, setAltEmail] = useState('');
    const [sendingAltEmail, setSendingAltEmail] = useState(false);

    // Config State
    const [loadingConfig, setLoadingConfig] = useState(false);
    const [instId, setInstId] = useState(null);
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [configData, setConfigData] = useState({
        ruc: '',
        establishment_code: '001',
        emission_point: '001',
        special_taxpayer_number: '',
        obligado_contabilidad: false,
        sri_environment: 1,
        electronic_signature: null,
        signature_password: ''
    });

    useEffect(() => {
        if (activeTab === 'invoices') {
            loadInvoices();
        } else {
            loadInstitutionConfig();
        }
    }, [activeTab]);

    const loadInvoices = async () => {
        setLoadingInvoices(true);
        try {
            const data = await treasuryService.getInvoices({});
            setInvoices(data);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando facturas");
        } finally {
            setLoadingInvoices(false);
        }
    };

    const loadInstitutionConfig = async () => {
        setLoadingConfig(true);
        try {
            const data = await userService.getInstitutions();
            if (data && data.length > 0) {
                // HARDENING: No asumir data[0]. Buscar la que coincide con el tenant activo del usuario.
                const activeId = localStorage.getItem('active_institution');
                let inst = data.find(i => i.id.toString() === activeId);
                
                // Fallback si no hay activeId o no se encuentra (pero data tiene algo)
                if (!inst) inst = data[0];

                setInstId(inst.id);
                setConfigData({
                    ruc: inst.ruc || '',
                    establishment_code: inst.establishment_code || '001',
                    emission_point: inst.emission_point || '001',
                    special_taxpayer_number: inst.special_taxpayer_number || '',
                    obligado_contabilidad: inst.obligado_contabilidad || false,
                    sri_environment: inst.sri_environment || 1,
                    electronic_signature: inst.electronic_signature, // URL string
                    signature_password: inst.signature_password || '',
                    sri_url_reception_test: inst.sri_url_reception_test || '',
                    sri_url_authorization_test: inst.sri_url_authorization_test || '',
                    sri_url_reception_prod: inst.sri_url_reception_prod || '',
                    sri_url_authorization_prod: inst.sri_url_authorization_prod || ''
                });
            }
        } catch (error) {
            console.error(error);
            toast.error("Error cargando configuración");
        } finally {
            setLoadingConfig(false);
        }
    };

    const handleSaveConfig = async (e) => {
        e.preventDefault();
        if (!instId) {
            toast.error("Error: No se ha cargado la institución");
            return;
        }

        const toastId = toast.loading("Guardando configuración...");
        try {
            const data = new FormData();

            // Solo enviamos lo necesario para actualizar la configuración SRI
            // El backend ahora maneja PATCH correctamente gracias al fix en el serializer
            data.append('ruc', configData.ruc);
            data.append('establishment_code', configData.establishment_code);
            data.append('emission_point', configData.emission_point);
            data.append('special_taxpayer_number', configData.special_taxpayer_number || '');
            data.append('obligado_contabilidad', configData.obligado_contabilidad ? 'true' : 'false');
            data.append('sri_environment', configData.sri_environment);
            data.append('signature_password', configData.signature_password || '');

            data.append('sri_url_reception_test', configData.sri_url_reception_test || '');
            data.append('sri_url_authorization_test', configData.sri_url_authorization_test || '');
            data.append('sri_url_reception_prod', configData.sri_url_reception_prod || '');
            data.append('sri_url_authorization_prod', configData.sri_url_authorization_prod || '');

            if (configData.electronic_signature instanceof File) {
                data.append('electronic_signature', configData.electronic_signature);
            }

            await userService.updateInstitution(instId, data);
            toast.success("Configuración SRI actualizada", { id: toastId });
            loadInstitutionConfig(); // recargar para confirmar
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.error || "Error al guardar configuración";
            toast.error(msg, { id: toastId });
        }
    };

    const handleDownloadPDF = async (invoice) => {
        try {
            const blob = await treasuryService.downloadInvoice(invoice.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Factura_${invoice.number}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            toast.error("Error al descargar PDF");
        }
    };

    const handleDownloadXML = async (invoice) => {
        try {
            const blob = await treasuryService.downloadInvoiceXml(invoice.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Factura_${invoice.number}.xml`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (e) {
            console.error(e);
            toast.error("Error al descargar XML (Quizás no está generada aún)");
        }
    };

    const handleSendToSri = async (invoice) => {
        const toastId = toast.loading(`Iniciando envío de Factura #${invoice.number}...`);
        try {
            const result = await treasuryService.sendToSri(invoice.id);
            toast.success(result.message || "Proceso iniciado en segundo plano", { id: toastId });
            loadInvoices();
            
            // Opcional: Polling manual corto para feedback inmediato si el SRI responde rápido
            let attempts = 0;
            const interval = setInterval(async () => {
                attempts++;
                try {
                    const data = await treasuryService.getInvoices({});
                    const updated = data.find(i => i.id === invoice.id);
                    if (updated && (updated.sri_status === 'AUTHORIZED' || updated.sri_status === 'REJECTED' || attempts > 10)) {
                        setInvoices(data);
                        clearInterval(interval);
                        if (updated.sri_status === 'AUTHORIZED') toast.success(`¡Factura #${invoice.number} Autorizada!`);
                    }
                } catch (e) { clearInterval(interval); }
            }, 3000);
            
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.error || error.response?.data?.message || "Error al iniciar envío";
            toast.error(msg, { id: toastId });
        }
    };

    const handleSendEmailSync = async (invoice) => {
        const toastId = toast.loading(`Enviando Sincrónicamente Factura #${invoice.number}...`);
        try {
            const res = await treasuryService.sendEmail(invoice.id, { sync: true });
            toast.success(res.message, { id: toastId });
            loadInvoices();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.error || "Error en envío síncrono";
            toast.error(msg, { id: toastId });
        }
    };

    const handleSendEmail = async (invoice) => {
        const typeLabel = invoice.was_sent ? "Reenviando" : "Enviando";
        const toastId = toast.loading(`${typeLabel} Correo Factura #${invoice.number}...`);
        try {
            const res = await treasuryService.sendEmail(invoice.id);
            toast.success(res.message || "Correo encolado con éxito", { id: toastId });
            loadInvoices();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.error || "Error al enviar correo";
            toast.error(msg, { id: toastId });
        }
    };

    const handleOpenHistory = async (invoice) => {
        setSelectedInvoice(invoice);
        setShowHistoryModal(true);
        setLoadingHistory(true);
        try {
            const logs = await treasuryService.getEmailHistory(invoice.id);
            setHistoryLogs(logs);
        } catch (error) {
            toast.error("Error al cargar historial");
        } finally {
            setLoadingHistory(false);
        }
    };

    const handleOpenAltEmail = (invoice) => {
        setSelectedInvoice(invoice);
        setAltEmail(invoice.client_email || '');
        setShowAltEmailModal(true);
    };

    const handleSendAltEmail = async (e) => {
        e.preventDefault();
        if (!altEmail) return;
        
        setSendingAltEmail(true);
        const toastId = toast.loading(`Enviando a ${altEmail}...`);
        try {
            await treasuryService.sendToAltEmail(selectedInvoice.id, altEmail);
            toast.success("Correo enviado a destinatario alterno", { id: toastId });
            setShowAltEmailModal(false);
            loadInvoices();
        } catch (error) {
            const msg = error.response?.data?.error || "Error al enviar";
            toast.error(msg, { id: toastId });
        } finally {
            setSendingAltEmail(false);
        }
    };

    const isAuthorized = ['ADMIN', 'LOCAL_ADMIN', 'ACCOUNTANT', 'SECRETARY'].includes(user?.role);
    const canEditConfig = user?.role === 'ADMIN' || user?.role === 'LOCAL_ADMIN';

    const EmailStatusBadge = ({ status, count }) => {
        const labels = {
            'SENT': { class: 'bg-green-100 text-green-700 border-green-200', icon: <Check size={10} />, text: 'Enviado' },
            'FAILED': { class: 'bg-red-100 text-red-700 border-red-200', icon: <AlertCircle size={10} />, text: 'Error' },
            'RETRYING': { class: 'bg-yellow-100 text-yellow-700 border-yellow-200', icon: <RefreshCw size={10} className="animate-spin" />, text: 'Reintentando' },
            'PENDING': { class: 'bg-blue-100 text-blue-700 border-blue-200', icon: <Send size={10} />, text: 'Pendiente' },
        };
        const config = labels[status] || labels['PENDING'];
        return (
            <div className="flex flex-col items-start gap-1">
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${config.class}`}>
                    {config.icon} {config.text}
                </span>
                {count > 0 && status !== 'SENT' && (
                    <span className="text-[9px] text-slate-400 italic">Intento {count}/4</span>
                )}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <FileText className="text-indigo-600" /> Facturación Electrónica
                </h1>

                <div className="flex bg-white rounded-lg p-1 border border-slate-200 shadow-sm">
                    <button
                        onClick={() => setActiveTab('invoices')}
                        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${activeTab === 'invoices' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
                    >
                        <FileText size={16} /> Emitidas
                    </button>
                    {isAuthorized && (
                        <button
                            onClick={() => setActiveTab('config')}
                            className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${activeTab === 'config' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
                        >
                            <Settings size={16} /> Configuración Tributaria
                        </button>
                    )}
                </div>
            </div>

            {activeTab === 'invoices' && (
                <>
                    <div className="flex justify-end">
                        <button
                            onClick={loadInvoices}
                            className="p-2 text-slate-500 hover:bg-white hover:text-indigo-600 rounded-lg transition-colors"
                            title="Recargar"
                        >
                            <RefreshCw size={20} className={loadingInvoices ? "animate-spin" : ""} />
                        </button>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left">
                                <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100">
                                    <tr>
                                        <th className="px-6 py-4">Número</th>
                                        <th className="px-6 py-4">Fecha</th>
                                        <th className="px-6 py-4">Cliente / RUC</th>
                                        <th className="px-6 py-4">Total</th>
                                        <th className="px-6 py-4">Estado SRI</th>
                                        <th className="px-6 py-4">Email</th>
                                        <th className="px-6 py-4 text-right">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-50">
                                    {loadingInvoices && invoices.length === 0 ? (
                                        <tr>
                                            <td colSpan="7" className="px-6 py-8 text-center text-slate-400">
                                                Cargando facturas...
                                            </td>
                                        </tr>
                                    ) : invoices.length === 0 ? (
                                        <tr>
                                            <td colSpan="7" className="px-6 py-8 text-center text-slate-400">
                                                No hay facturas registradas.
                                            </td>
                                        </tr>
                                    ) : (
                                        invoices.map(inv => (
                                            <tr key={inv.id} className="hover:bg-indigo-50/30 transition-colors">
                                                <td className="px-6 py-4 font-bold text-slate-700">
                                                    {inv.number}
                                                </td>
                                                <td className="px-6 py-4 text-slate-600">
                                                    {new Date(inv.issue_date).toLocaleDateString()}
                                                    <div className="text-xs text-slate-400">{new Date(inv.issue_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="font-medium text-slate-800">{inv.client_name}</div>
                                                    <div className="text-xs text-slate-500">{inv.client_ruc}</div>
                                                </td>
                                                <td className="px-6 py-4 font-bold text-slate-700">
                                                    ${inv.total}
                                                </td>
                                                <td className="px-6 py-4">
                                                    {(() => {
                                                        const statusConfig = {
                                                            'AUTHORIZED': { class: 'bg-green-100 text-green-700 border-green-200', icon: <Check size={12} />, text: 'AUTORIZADO' },
                                                            'RECEIVED': { class: 'bg-blue-100 text-blue-700 border-blue-200', icon: <RefreshCw size={12} className="animate-spin" />, text: 'RECIBIDO / PROCESANDO' },
                                                            'PENDING_SRI': { class: 'bg-orange-100 text-orange-700 border-orange-200', icon: <History size={12} />, text: 'COLA DE REINTENTO' },
                                                            'REJECTED': { class: 'bg-red-100 text-red-700 border-red-200', icon: <AlertCircle size={12} />, text: 'RECHAZADO' },
                                                            'SIGNED': { class: 'bg-indigo-50 text-indigo-600 border-indigo-100', icon: <FileCode size={12} />, text: 'FIRMADO' },
                                                            'DRAFT': { class: 'bg-slate-100 text-slate-500 border-slate-200', icon: <FileText size={12} />, text: 'BORRADOR' },
                                                        };
                                                        const config = statusConfig[inv.sri_status] || statusConfig['DRAFT'];
                                                        return (
                                                            <div className="flex flex-col gap-1">
                                                                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold border ${config.class}`}>
                                                                    {config.icon} {config.text}
                                                                </span>
                                                                {inv.sri_attempts > 0 && inv.sri_status !== 'AUTHORIZED' && (
                                                                    <span className="text-[9px] text-slate-400 italic text-center">Intento SRI: {inv.sri_attempts}</span>
                                                                )}
                                                            </div>
                                                        );
                                                    })()}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-1">
                                                        <EmailStatusBadge status={inv.email_status} count={inv.email_attempts_count} />
                                                        
                                                        {isAuthorized && (
                                                            <button 
                                                                onClick={() => handleOpenHistory(inv)}
                                                                className="text-[10px] text-indigo-500 hover:underline flex items-center gap-1 mt-1"
                                                            >
                                                                <History size={10} /> Ver historial
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 text-right">
                                                    <div className="flex items-center justify-end gap-2">
                                                        <button
                                                            onClick={() => handleDownloadPDF(inv)}
                                                            className="p-2 hover:bg-slate-200 rounded-lg text-slate-600 transition-colors"
                                                            title="Descargar PDF"
                                                        >
                                                            <Download size={18} />
                                                        </button>
                                                        {inv.sri_status === 'AUTHORIZED' && (
                                                            <>
                                                                <button
                                                                    onClick={() => handleDownloadXML(inv)}
                                                                    className="p-2 hover:bg-slate-200 rounded-lg text-green-600 transition-colors"
                                                                    title="Descargar XML"
                                                                >
                                                                    <FileCode size={18} />
                                                                </button>
                                                                
                                                                {isAuthorized && (
                                                                    <>
                                                                        <button
                                                                            onClick={() => handleSendEmail(inv)}
                                                                            className={`p-2 rounded-lg transition-colors ${inv.email_status === 'SENT' ? 'hover:bg-yellow-50 text-yellow-600' : 'hover:bg-indigo-50 text-indigo-600'}`}
                                                                            title={inv.email_status === 'SENT' ? "Reenviar Correo" : "Enviar Correo"}
                                                                        >
                                                                            {inv.email_status === 'SENT' ? <RefreshCw size={18} /> : <Send size={18} />}
                                                                        </button>
                                                                        {user?.role === 'ADMIN' && (
                                                                            <button
                                                                                onClick={() => handleSendEmailSync(inv)}
                                                                                className="p-2 hover:bg-orange-50 rounded-lg text-orange-600 transition-colors"
                                                                                title="Forzar Envío Sincrónico (Fallback)"
                                                                            >
                                                                                <Zap size={18} />
                                                                            </button>
                                                                        )}
                                                                        <button
                                                                            onClick={() => handleOpenAltEmail(inv)}
                                                                            className="p-2 hover:bg-purple-50 rounded-lg text-purple-600 transition-colors"
                                                                            title="Enviar a otro correo"
                                                                        >
                                                                            <Mail size={18} />
                                                                        </button>
                                                                    </>
                                                                )}
                                                            </>
                                                        )}
                                                        {isAuthorized && inv.sri_status !== 'AUTHORIZED' && (
                                                            <button
                                                                onClick={() => handleSendToSri(inv)}
                                                                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
                                                                    ['PENDING_SRI', 'RECEIVED'].includes(inv.sri_status) 
                                                                    ? 'bg-orange-50 text-orange-600 hover:bg-orange-100' 
                                                                    : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
                                                                }`}
                                                                title="Enviar al SRI"
                                                            >
                                                                {['PENDING_SRI', 'RECEIVED'].includes(inv.sri_status) ? (
                                                                    <><RefreshCw size={14} /> Reintentar Ya</>
                                                                ) : inv.sri_status === 'REJECTED' ? (
                                                                    <><RefreshCw size={14} /> Re-enviar</>
                                                                ) : (
                                                                    <><Send size={14} /> Enviar SRI</>
                                                                )}
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {activeTab === 'config' && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4">
                    <form onSubmit={handleSaveConfig} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <div className="md:col-span-3 pb-4 border-b border-slate-100 mb-2">
                                <h3 className="font-bold text-slate-700 mb-1">Datos Tributarios (SRI)</h3>
                                <p className="text-sm text-slate-500">Estos datos aparecerán en su factura electrónica y son necesarios para la autorización.</p>
                            </div>

                            <div className="space-y-2">
                                <label className="label">R.U.C.</label>
                                <input required readOnly={!canEditConfig} type="text" maxLength={13} className="input-modern w-full" value={configData.ruc || ''} onChange={e => setConfigData({ ...configData, ruc: e.target.value })} placeholder="17900..." />
                            </div>
                            <div className="space-y-2">
                                <label className="label">Ambiente SRI</label>
                                <select disabled={!canEditConfig} className="input-modern w-full" value={configData.sri_environment || 1} onChange={e => setConfigData({ ...configData, sri_environment: parseInt(e.target.value) })}>
                                    <option value={1}>Pruebas</option>
                                    <option value={2}>Producción</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="label">Cod. Establecimiento</label>
                                <input required readOnly={!canEditConfig} type="text" maxLength={3} className="input-modern w-full" value={configData.establishment_code || '001'} onChange={e => setConfigData({ ...configData, establishment_code: e.target.value })} placeholder="001" />
                            </div>
                            <div className="space-y-2">
                                <label className="label">Pto. Emisión</label>
                                <input required readOnly={!canEditConfig} type="text" maxLength={3} className="input-modern w-full" value={configData.emission_point || '001'} onChange={e => setConfigData({ ...configData, emission_point: e.target.value })} placeholder="001" />
                            </div>
                            <div className="space-y-2">
                                <label className="label">Nro. Contribuyente Especial</label>
                                <input readOnly={!canEditConfig} type="text" className="input-modern w-full" value={configData.special_taxpayer_number || ''} onChange={e => setConfigData({ ...configData, special_taxpayer_number: e.target.value })} placeholder="Opcional" />
                            </div>
                            <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                                <div className="space-y-2">
                                    <label className="label">Firma Electrónica (.p12)</label>
                                    {canEditConfig ? (
                                        <input type="file" accept=".p12,.pfx" className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                                            onChange={(e) => {
                                                if (e.target.files[0]) setConfigData({ ...configData, electronic_signature: e.target.files[0] });
                                            }}
                                        />
                                    ) : (
                                        <p className="text-sm text-slate-500 italic">Solo administradores pueden cambiar la firma.</p>
                                    )}
                                    {configData.electronic_signature && typeof configData.electronic_signature === 'string' && (
                                        <p className="text-xs text-green-600 font-bold">✓ Firma cargada previamente</p>
                                    )}
                                </div>
                                <div className="space-y-2">
                                    <label className="label">Contraseña de Firma</label>
                                    <input readOnly={!canEditConfig} type="password" className="input-modern w-full" value={configData.signature_password || ''} onChange={e => setConfigData({ ...configData, signature_password: e.target.value })} placeholder="******" />
                                </div>
                            </div>

                            <div className="md:col-span-3 flex items-center pt-2">
                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        disabled={!canEditConfig}
                                        checked={configData.obligado_contabilidad || false}
                                        onChange={e => setConfigData({ ...configData, obligado_contabilidad: e.target.checked })}
                                        className="w-5 h-5 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500"
                                    />
                                    <span className="text-slate-700 font-medium">Obligado a llevar Contabilidad</span>
                                </label>
                            </div>

                            <div className="md:col-span-3 border-t border-slate-100 pt-4">
                                <button type="button" onClick={() => setShowAdvanced(!showAdvanced)} className="text-indigo-600 text-sm font-bold flex items-center gap-1 hover:underline">
                                    <Settings size={14} /> {showAdvanced ? 'Ocultar Configuración Avanzada de Servidores' : 'Mostrar Configuración Avanzada de Servidores'}
                                </button>

                                {showAdvanced && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 p-4 bg-slate-50 rounded-xl border border-slate-200">
                                        <div className="space-y-2">
                                            <label className="label text-xs">URL Recepción (Pruebas)</label>
                                            <input readOnly={!canEditConfig} type="url" className="input-modern w-full text-xs" value={configData.sri_url_reception_test || ''} onChange={e => setConfigData({ ...configData, sri_url_reception_test: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="label text-xs">URL Autorización (Pruebas)</label>
                                            <input readOnly={!canEditConfig} type="url" className="input-modern w-full text-xs" value={configData.sri_url_authorization_test || ''} onChange={e => setConfigData({ ...configData, sri_url_authorization_test: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="label text-xs">URL Recepción (Producción)</label>
                                            <input readOnly={!canEditConfig} type="url" className="input-modern w-full text-xs" value={configData.sri_url_reception_prod || ''} onChange={e => setConfigData({ ...configData, sri_url_reception_prod: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="label text-xs">URL Autorización (Producción)</label>
                                            <input readOnly={!canEditConfig} type="url" className="input-modern w-full text-xs" value={configData.sri_url_authorization_prod || ''} onChange={e => setConfigData({ ...configData, sri_url_authorization_prod: e.target.value })} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {canEditConfig && (
                            <div className="pt-6 border-t border-slate-100 flex justify-end">
                                <button type="submit" className="btn-primary flex items-center gap-2 px-8 py-3 text-lg shadow-lg shadow-indigo-200">
                                    <Save size={20} />
                                    Guardar Configuración
                                </button>
                            </div>
                        )}
                    </form>
                </div>
            )}

            {/* MODAL HISTORIAL */}
            {showHistoryModal && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                            <div>
                                <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                                    <History className="text-indigo-600" /> Historial de Envío de Correo
                                </h2>
                                <p className="text-sm text-slate-500">Factura No. {selectedInvoice?.number}</p>
                            </div>
                            <button onClick={() => setShowHistoryModal(false)} className="p-2 hover:bg-slate-200 rounded-full transition-colors">
                                <X size={20} />
                            </button>
                        </div>
                        
                        <div className="flex-1 overflow-y-auto p-6">
                            {loadingHistory ? (
                                <div className="flex flex-col items-center justify-center py-12 gap-4 text-slate-400">
                                    <RefreshCw className="animate-spin" size={32} />
                                    <p>Cargando historial...</p>
                                </div>
                            ) : historyLogs.length === 0 ? (
                                <div className="text-center py-12 text-slate-400">
                                    No hay intentos de envío registrados para esta factura.
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {historyLogs.map(log => (
                                        <div key={log.id} className="p-4 rounded-xl border border-slate-100 bg-white hover:border-indigo-100 transition-colors shadow-sm">
                                            <div className="flex justify-between items-start mb-3">
                                                <div>
                                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                                        log.send_type === 'AUTO' ? 'bg-slate-100 text-slate-600' :
                                                        log.send_type === 'MANUAL' ? 'bg-blue-100 text-blue-600' :
                                                        log.send_type === 'REENVIO' ? 'bg-yellow-100 text-yellow-600' :
                                                        'bg-purple-100 text-purple-600'
                                                    }`}>
                                                        {log.send_type}
                                                    </span>
                                                    <h4 className="font-bold text-slate-700 mt-1">{log.recipient}</h4>
                                                </div>
                                                <div className="text-right">
                                                    {log.status === 'sent' ? (
                                                        <span className="text-green-600 text-xs font-bold flex items-center gap-1 justify-end">
                                                            <Check size={12} /> Enviado
                                                        </span>
                                                    ) : log.status === 'failed' ? (
                                                        <span className="text-red-600 text-xs font-bold flex items-center gap-1 justify-end">
                                                            <AlertCircle size={12} /> Fallido
                                                        </span>
                                                    ) : (
                                                        <span className="text-slate-400 text-xs font-bold flex items-center gap-1 justify-end">
                                                            <RefreshCw size={12} className="animate-spin" /> En cola
                                                        </span>
                                                    )}
                                                    <div className="text-[10px] text-slate-400 mt-1">
                                                        {new Date(log.created_at).toLocaleString()}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2 text-xs text-slate-500 pt-2 border-t border-slate-50">
                                                <Mail size={12} /> {log.subject}
                                                <span className="mx-2">•</span>
                                                <Send size={12} /> Enviado por: <span className="font-medium text-slate-700">{log.sent_by_name || 'Sistema'}</span>
                                            </div>
                                            {log.error_message && (
                                                <div className="mt-2 p-2 bg-red-50 text-red-600 text-[10px] rounded border border-red-100 italic">
                                                    Error: {log.error_message}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                        
                        <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
                            <button onClick={() => setShowHistoryModal(false)} className="px-6 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg font-bold transition-colors">
                                Cerrar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* MODAL CORREO ALTERNO */}
            {showAltEmailModal && (
                <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md animate-in zoom-in-95 duration-200">
                        <div className="p-6 border-b border-slate-100">
                            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                                <Mail className="text-purple-600" /> Destinatario Alternativo
                            </h2>
                            <p className="text-sm text-slate-500">Factura No. {selectedInvoice?.number}</p>
                        </div>
                        
                        <form onSubmit={handleSendAltEmail} className="p-6 space-y-4">
                            <div className="space-y-2">
                                <label className="label">Correo Electrónico</label>
                                <input 
                                    required 
                                    type="email" 
                                    className="input-modern w-full" 
                                    value={altEmail} 
                                    onChange={e => setAltEmail(e.target.value)}
                                    placeholder="ejemplo@correo.com"
                                    autoFocus
                                />
                                <p className="text-[10px] text-slate-400 italic">
                                    Se enviarán los archivos PDF y XML a esta dirección.
                                </p>
                            </div>
                            
                            <div className="flex gap-3 pt-2">
                                <button 
                                    type="button" 
                                    onClick={() => setShowAltEmailModal(false)}
                                    className="flex-1 py-3 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold transition-colors"
                                >
                                    Cancelar
                                </button>
                                <button 
                                    type="submit" 
                                    disabled={sendingAltEmail}
                                    className="flex-2 py-3 px-6 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold transition-colors shadow-lg shadow-purple-200 flex items-center justify-center gap-2"
                                >
                                    {sendingAltEmail ? <RefreshCw size={18} className="animate-spin" /> : <Send size={18} />}
                                    Enviar Ahora
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default InvoicesPage;
