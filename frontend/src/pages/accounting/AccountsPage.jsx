import React, { useState, useEffect } from 'react';
import { FolderTree, Plus, Edit, Trash2, ChevronRight, ChevronDown, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';
import accountingService from '../../services/accountingService';
import { useAuthStore } from '../../context/authStore';

const AccountsPage = () => {
    const { user } = useAuthStore();
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState({});

    // Form State
    const [showModal, setShowModal] = useState(false);
    const [editingAccount, setEditingAccount] = useState(null);
    const [formData, setFormData] = useState({
        code: '',
        name: '',
        account_type: 'ASSET',
        parent: '',
        description: '',
        tax_id: ''
    });

    useEffect(() => {
        loadAccounts();
    }, []);

    const loadAccounts = async () => {
        setLoading(true);
        try {
            // Fetch all accounts flat, we will build tree or show flat list
            // For now, simpler to fetch all and render hierarchy if possible, 
            // or just flat list sorted by code. Hierarchical view is better.
            const data = await accountingService.getAccounts();
            setAccounts(data);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando plan de cuentas");
        } finally {
            setLoading(false);
        }
    };

    const toggleExpand = (id) => {
        setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const handleEdit = (acc) => {
        setEditingAccount(acc);
        setFormData({
            code: acc.code,
            name: acc.name,
            account_type: acc.account_type,
            parent: acc.parent || '',
            description: acc.description || '',
            tax_id: acc.tax_id || ''
        });
        setShowModal(true);
    };

    const handleCreate = (parentId = null) => {
        setEditingAccount(null);
        setFormData({
            code: '',
            name: '',
            account_type: 'ASSET',
            parent: parentId || '',
            description: '',
            tax_id: ''
        });
        setShowModal(true);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                parent: formData.parent === '' ? null : formData.parent
            };

            if (editingAccount) {
                await accountingService.updateAccount(editingAccount.id, payload);
                toast.success("Cuenta actualizada");
            } else {
                await accountingService.createAccount(payload);
                toast.success("Cuenta creada");
            }
            setShowModal(false);
            loadAccounts();
        } catch (error) {
            console.error(error);
            toast.error("Error al guardar cuenta. Verifique el código.");
        }
    };

    // Recursive Tree Renderer
    const renderTree = (parentId = null, level = 0) => {
        // Filter direct children
        const children = accounts.filter(a => a.parent === parentId).sort((a, b) => a.code.localeCompare(b.code));

        if (children.length === 0) return null;

        return children.map(acc => {
            const hasChildren = accounts.some(child => child.parent === acc.id);
            const isExpanded = expanded[acc.id] || false;

            return (
                <div key={acc.id} className="select-none">
                    <div
                        className={`flex items-center gap-2 p-2 hover:bg-slate-50 border-b border-slate-50 transition-colors ${level === 0 ? 'bg-slate-50/50 font-semibold' : ''}`}
                        style={{ paddingLeft: `${level * 20 + 10}px` }}
                    >
                        <button onClick={() => toggleExpand(acc.id)} className={`p-1 rounded hover:bg-slate-200 ${!hasChildren ? 'invisible' : ''}`}>
                            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        </button>

                        <div className="flex-1 flex items-center gap-3">
                            <span className="font-mono text-slate-500 text-xs w-24">{acc.code}</span>
                            <span className={`text-sm ${hasChildren ? 'text-slate-800' : 'text-slate-600'}`}>{acc.name}</span>
                        </div>

                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => handleCreate(acc.id)} className="p-1 text-slate-400 hover:text-green-600" title="Agregar Subcuenta"><Plus size={14} /></button>
                            <button onClick={() => handleEdit(acc)} className="p-1 text-slate-400 hover:text-indigo-600" title="Editar"><Edit size={14} /></button>
                        </div>
                    </div>

                    {isExpanded && renderTree(acc.id, level + 1)}
                </div>
            );
        });
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <FolderTree className="text-indigo-600" /> Plan de Cuentas
                </h1>
                <button onClick={() => handleCreate()} className="btn-primary flex items-center gap-2">
                    <Plus size={18} /> Nueva Cuenta
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden group">
                <div className="p-4 border-b border-slate-100 flex justify-between bg-slate-50 text-xs font-bold text-slate-500 uppercase">
                    <span className="pl-8">Código / Nombre</span>
                    <span>Acciones (Hover)</span>
                </div>
                <div className="max-h-[70vh] overflow-y-auto">
                    {loading ? (
                        <div className="p-8 text-center text-slate-400">Cargando Plan de Cuentas...</div>
                    ) : accounts.length === 0 ? (
                        <div className="p-8 text-center text-slate-400">No hay cuentas registradas.</div>
                    ) : (
                        renderTree(null)
                    )}
                </div>
            </div>

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                        <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                            <h3 className="font-bold text-slate-700">{editingAccount ? 'Editar Cuenta' : 'Nueva Cuenta'}</h3>
                            <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">×</button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div>
                                <label className="label">Código</label>
                                <input required autoFocus type="text" className="input-modern w-full" value={formData.code} onChange={e => setFormData({ ...formData, code: e.target.value })} placeholder="e.g. 1.1.01" />
                            </div>
                            <div>
                                <label className="label">Nombre</label>
                                <input required type="text" className="input-modern w-full" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} placeholder="Nombre de la cuenta" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Tipo</label>
                                    <select className="input-modern w-full" value={formData.account_type} onChange={e => setFormData({ ...formData, account_type: e.target.value })}>
                                        <option value="ASSET">Activo</option>
                                        <option value="LIABILITY">Pasivo</option>
                                        <option value="EQUITY">Patrimonio</option>
                                        <option value="INCOME">Ingreso</option>
                                        <option value="EXPENSE">Gasto</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="label">Casillero SRI</label>
                                    <input type="text" className="input-modern w-full" value={formData.tax_id} onChange={e => setFormData({ ...formData, tax_id: e.target.value })} placeholder="Opcional" />
                                </div>
                            </div>
                            <div>
                                <label className="label">Descripción</label>
                                <textarea className="input-modern w-full" rows="2" value={formData.description} onChange={e => setFormData({ ...formData, description: e.target.value })}></textarea>
                            </div>

                            <div className="pt-4 flex gap-3 justify-end">
                                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancelar</button>
                                <button type="submit" className="btn-primary">Guardar</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AccountsPage;
