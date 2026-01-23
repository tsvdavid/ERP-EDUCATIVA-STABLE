import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Search, DollarSign, X } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import treasuryService from '../../services/treasuryService';
import userService from '../../services/userService';
import { useAuthStore } from '../../context/authStore';

const ConceptsPage = () => {
    const { activeInstitution, user } = useAuthStore();
    const [concepts, setConcepts] = useState([]);
    const [institutions, setInstitutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState(null);

    const initialFormState = {
        name: '',
        price: '',
        iva_rate: '0.00',
        due_day: '',
        institution: ''
    };

    const [formData, setFormData] = useState(initialFormState);

    useEffect(() => {
        loadConcepts();
        if (user?.role === 'ADMIN') {
            loadInstitutions();
        }
    }, [user]);

    const loadInstitutions = async () => {
        try {
            const data = await userService.getInstitutions();
            setInstitutions(data);
        } catch (error) {
            console.error(error);
        }
    };

    const loadConcepts = async () => {
        setLoading(true);
        try {
            const data = await treasuryService.getConcepts();
            setConcepts(data);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar rubros");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!activeInstitution && !formData.institution) {
            toast.error("No hay una institución activa seleccionada. Por favor seleccione una.");
            return;
        }

        try {
            const payload = {
                ...formData,
                price: parseFloat(formData.price),
                iva_rate: formData.iva_rate, // Send as string "0.00" to match Django DecimalField choices validation
                due_day: formData.due_day ? parseInt(formData.due_day) : null,
                institution: parseInt(formData.institution || activeInstitution)
            };

            if (editingId) {
                await treasuryService.updateConcept(editingId, payload);
                toast.success("Rubro actualizado");
            } else {
                await treasuryService.createConcept(payload);
                toast.success("Rubro creado");
            }
            setIsModalOpen(false);
            setFormData(initialFormState);
            setEditingId(null);
            loadConcepts();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data
                ? Object.entries(error.response.data).map(([k, v]) => `${k}: ${v}`).join(', ')
                : "Error al guardar";
            toast.error(msg);
        }
    };

    const handleEdit = (item) => {
        setEditingId(item.id);
        setFormData({
            name: item.name,
            price: item.price,
            iva_rate: item.iva_rate,
            due_day: item.due_day || '',
            institution: item.institution
        });
        setIsModalOpen(true);
    };

    const handleDelete = async (id) => {
        if (window.confirm("¿Eliminar este rubro?")) {
            try {
                await treasuryService.deleteConcept(id);
                toast.success("Rubro eliminado");
                loadConcepts();
            } catch (error) {
                toast.error("Error al eliminar");
            }
        }
    };

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />

            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Rubros y Conceptos</h1>
                    <p className="text-slate-500">Configura pensiones, matrículas y otros cobros.</p>
                </div>
                <button
                    onClick={() => { setEditingId(null); setFormData(initialFormState); setIsModalOpen(true); }}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={18} /> Nuevo Rubro
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {concepts.map(item => (
                    <div key={item.id} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-3 bg-green-50 text-green-600 rounded-lg">
                                <DollarSign size={24} />
                            </div>
                            <div className="flex gap-2">
                                <button onClick={() => handleEdit(item)} className="text-slate-400 hover:text-indigo-600">
                                    <Edit size={18} />
                                </button>
                                <button onClick={() => handleDelete(item.id)} className="text-slate-400 hover:text-red-600">
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>
                        <h3 className="font-bold text-lg text-slate-800 mb-1">{item.name}</h3>
                        <div className="flex items-baseline gap-1">
                            <span className="text-2xl font-bold text-green-600">${item.price}</span>
                            <span className="text-xs text-slate-500">+ {parseFloat(item.iva_rate) * 100}% IVA</span>
                        </div>
                        {item.due_day && (
                            <p className="text-xs text-slate-400 mt-2">Vence el día {item.due_day} de cada mes</p>
                        )}
                    </div>
                ))}
            </div>

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                            <h2 className="text-xl font-bold text-slate-800">{editingId ? 'Editar' : 'Nuevo'} Rubro</h2>
                            <button onClick={() => setIsModalOpen(false)}><X size={24} className="text-slate-400" /></button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            {/* Institution Selector for Admin */}
                            {user?.role === 'ADMIN' && (
                                <div>
                                    <label className="label-modern">Institución</label>
                                    <select
                                        className="input-modern w-full"
                                        value={formData.institution}
                                        onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
                                    >
                                        <option value="">-- Seleccione Institución --</option>
                                        {institutions.map(inst => (
                                            <option key={inst.id} value={inst.id}>{inst.name}</option>
                                        ))}
                                    </select>
                                </div>
                            )}
                            <div>
                                <label className="label-modern">Nombre del Concepto</label>
                                <input type="text" required className="input-modern w-full" placeholder="Ej. Pensión Abril"
                                    value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label-modern">Precio ($)</label>
                                    <input type="number" step="0.01" required className="input-modern w-full"
                                        value={formData.price} onChange={e => setFormData({ ...formData, price: e.target.value })} />
                                </div>
                                <div>
                                    <label className="label-modern">Tarifa IVA</label>
                                    <select className="input-modern w-full" value={formData.iva_rate} onChange={e => setFormData({ ...formData, iva_rate: e.target.value })}>
                                        <option value="0.00">0%</option>
                                        <option value="0.15">15%</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="label-modern">Día de Vencimiento (Opcional)</label>
                                <input type="number" className="input-modern w-full" placeholder="Ej. 5"
                                    value={formData.due_day} onChange={e => setFormData({ ...formData, due_day: e.target.value })} />
                            </div>
                            <button type="submit" className="btn-primary w-full mt-4">Guardar Rubro</button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ConceptsPage;
