import React, { useState, useEffect } from 'react';
import { FileText, Download, Send, Check, AlertCircle, RefreshCw, Settings, Save, FileCode } from 'lucide-react';
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
                const inst = data[0];
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
        try {
            const data = new FormData();

            const originalData = await userService.getInstitutions();
            const inst = originalData[0];

            data.append('name', inst.name); // Required fields
            data.append('ruc', configData.ruc);
            data.append('establishment_code', configData.establishment_code);
            data.append('emission_point', configData.emission_point);
            data.append('special_taxpayer_number', configData.special_taxpayer_number);
            data.append('obligado_contabilidad', configData.obligado_contabilidad ? 'true' : 'false');
            data.append('sri_environment', configData.sri_environment);
            data.append('signature_password', configData.signature_password);

            data.append('sri_url_reception_test', configData.sri_url_reception_test || '');
            data.append('sri_url_authorization_test', configData.sri_url_authorization_test || '');
            data.append('sri_url_reception_prod', configData.sri_url_reception_prod || '');
            data.append('sri_url_authorization_prod', configData.sri_url_authorization_prod || '');

            if (configData.electronic_signature instanceof File) {
                data.append('electronic_signature', configData.electronic_signature);
            }

            await userService.updateInstitution(instId, data);
            toast.success("Configuración SRI actualizada");
            loadInstitutionConfig(); // reload to confirm
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar configuración");
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
        const toastId = toast.loading(`Enviando Factura #${invoice.number}...`);
        try {
            const result = await treasuryService.sendToSri(invoice.id);
            if (result.status === 'AUTHORIZED') {
                toast.success("¡Factura Autorizada!", { id: toastId });
            } else {
                toast.error(`Estado: ${result.status}. ${result.message}`, { id: toastId, duration: 5000 });
            }
            loadInvoices();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.error || error.response?.data?.message || "Error al enviar al SRI";
            toast.error(msg, { id: toastId });
        }
    };

    const canEdit = user?.role === 'ADMIN';

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
                    <button
                        onClick={() => setActiveTab('config')}
                        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${activeTab === 'config' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
                    >
                        <Settings size={16} /> Configuración Tributaria
                    </button>
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
                                        <th className="px-6 py-4 text-right">Acciones</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-50">
                                    {loadingInvoices && invoices.length === 0 ? (
                                        <tr>
                                            <td colSpan="6" className="px-6 py-8 text-center text-slate-400">
                                                Cargando facturas...
                                            </td>
                                        </tr>
                                    ) : invoices.length === 0 ? (
                                        <tr>
                                            <td colSpan="6" className="px-6 py-8 text-center text-slate-400">
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
                                                    {inv.sri_status === 'AUTHORIZED' ? (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-green-100 text-green-700 text-xs font-bold border border-green-200">
                                                            <Check size={12} /> AUTORIZADO
                                                        </span>
                                                    ) : inv.sri_status === 'SENT' ? (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-yellow-100 text-yellow-700 text-xs font-bold border border-yellow-200">
                                                            Enviado
                                                        </span>
                                                    ) : inv.sri_status === 'REJECTED' ? (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-red-100 text-red-700 text-xs font-bold border border-red-200">
                                                            <AlertCircle size={12} /> Rechazado
                                                        </span>
                                                    ) : (
                                                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-500 text-xs font-bold border border-slate-200">
                                                            Pendiente
                                                        </span>
                                                    )}
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
                                                            <button
                                                                onClick={() => handleDownloadXML(inv)}
                                                                className="p-2 hover:bg-slate-200 rounded-lg text-green-600 transition-colors"
                                                                title="Descargar XML"
                                                            >
                                                                <FileCode size={18} />
                                                            </button>
                                                        )}
                                                        {inv.sri_status !== 'AUTHORIZED' && (
                                                            <button
                                                                onClick={() => handleSendToSri(inv)}
                                                                className="flex items-center gap-1 px-3 py-1.5 bg-indigo-50 text-indigo-600 hover:bg-indigo-100 rounded-lg text-xs font-bold transition-colors"
                                                                title="Enviar al SRI"
                                                            >
                                                                <Send size={14} /> Enviar
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
                                <input required readOnly={!canEdit} type="text" maxLength={13} className="input-modern w-full" value={configData.ruc || ''} onChange={e => setConfigData({ ...configData, ruc: e.target.value })} placeholder="17900..." />
                            </div>
                            <div className="space-y-2">
                                <label className="label">Ambiente SRI</label>
                                <select disabled={!canEdit} className="input-modern w-full" value={configData.sri_environment || 1} onChange={e => setConfigData({ ...configData, sri_environment: parseInt(e.target.value) })}>
                                    <option value={1}>Pruebas</option>
                                    <option value={2}>Producción</option>
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="label">Cod. Establecimiento</label>
                                <input required readOnly={!canEdit} type="text" maxLength={3} className="input-modern w-full" value={configData.establishment_code || '001'} onChange={e => setConfigData({ ...configData, establishment_code: e.target.value })} placeholder="001" />
                            </div>
                            <div className="space-y-2">
                                <label className="label">Pto. Emisión</label>
                                <input required readOnly={!canEdit} type="text" maxLength={3} className="input-modern w-full" value={configData.emission_point || '001'} onChange={e => setConfigData({ ...configData, emission_point: e.target.value })} placeholder="001" />
                            </div>
                            <div className="space-y-2">
                                <label className="label">Nro. Contribuyente Especial</label>
                                <input readOnly={!canEdit} type="text" className="input-modern w-full" value={configData.special_taxpayer_number || ''} onChange={e => setConfigData({ ...configData, special_taxpayer_number: e.target.value })} placeholder="Opcional" />
                            </div>
                            <div className="md:col-span-3 grid grid-cols-1 md:grid-cols-2 gap-6 p-4 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                                <div className="space-y-2">
                                    <label className="label">Firma Electrónica (.p12)</label>
                                    {canEdit ? (
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
                                    <input readOnly={!canEdit} type="password" className="input-modern w-full" value={configData.signature_password || ''} onChange={e => setConfigData({ ...configData, signature_password: e.target.value })} placeholder="******" />
                                </div>
                            </div>

                            <div className="md:col-span-3 flex items-center pt-2">
                                <label className="flex items-center gap-3 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        disabled={!canEdit}
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
                                            <input readOnly={!canEdit} type="url" className="input-modern w-full text-xs" value={configData.sri_url_reception_test || ''} onChange={e => setConfigData({ ...configData, sri_url_reception_test: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="label text-xs">URL Autorización (Pruebas)</label>
                                            <input readOnly={!canEdit} type="url" className="input-modern w-full text-xs" value={configData.sri_url_authorization_test || ''} onChange={e => setConfigData({ ...configData, sri_url_authorization_test: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="label text-xs">URL Recepción (Producción)</label>
                                            <input readOnly={!canEdit} type="url" className="input-modern w-full text-xs" value={configData.sri_url_reception_prod || ''} onChange={e => setConfigData({ ...configData, sri_url_reception_prod: e.target.value })} />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="label text-xs">URL Autorización (Producción)</label>
                                            <input readOnly={!canEdit} type="url" className="input-modern w-full text-xs" value={configData.sri_url_authorization_prod || ''} onChange={e => setConfigData({ ...configData, sri_url_authorization_prod: e.target.value })} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {canEdit && (
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
        </div>
    );
};

export default InvoicesPage;
