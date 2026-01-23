import React, { useState, useEffect } from 'react';
import academicService from '../services/academicService';
import { useAuthStore } from '../context/authStore';
import { toast } from 'react-hot-toast';
import {
    Calendar,
    Plus,
    CheckCircle,
    XCircle,
    Lock,
    Unlock,
    Edit2,
    Trash2,
    ChevronDown,
    ChevronUp
} from 'lucide-react';

const AcademicYearPage = () => {
    const { activeInstitution } = useAuthStore();
    const [years, setYears] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [expandedYear, setExpandedYear] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        name: '',
        year: new Date().getFullYear(),
        start_date: '',
        end_date: '',
        is_active: false
    });
    const [editingId, setEditingId] = useState(null);

    useEffect(() => {
        fetchYears();
    }, [activeInstitution]);

    const fetchYears = async () => {
        setLoading(true);
        try {
            const data = await academicService.getAcademicYears();
            // Filter by active institution if needed, though backend handles it largely
            setYears(data);
        } catch (error) {
            toast.error("Error al cargar años lectivos");
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                ...formData,
                year: parseInt(formData.year),
            };

            if (editingId) {
                await academicService.updateAcademicYear(editingId, payload);
                toast.success("Año lectivo actualizado");
            } else {
                if (!activeInstitution) {
                    toast.error("Debe seleccionar una institución activa");
                    return;
                }
                payload.institution = activeInstitution;
                await academicService.createAcademicYear(payload);
                toast.success("Año lectivo creado");
            }
            setIsModalOpen(false);
            resetForm();
            fetchYears();
        } catch (error) {
            console.error(error);
            const msg = error.response?.data?.detail || "Error al guardar año lectivo";
            toast.error(msg);
        }
    };

    const handleEdit = (year) => {
        setFormData({
            name: year.name,
            year: year.year,
            start_date: year.start_date,
            end_date: year.end_date,
            is_active: year.is_active
        });
        setEditingId(year.id);
        setIsModalOpen(true);
    };

    const resetForm = () => {
        setFormData({
            name: '',
            year: new Date().getFullYear(),
            start_date: '',
            end_date: '',
            is_active: false
        });
        setEditingId(null);
    };

    const toggleYearStatus = async (year) => {
        try {
            await academicService.updateAcademicYear(year.id, { is_closed: !year.is_closed });
            toast.success(`Año lectivo ${year.is_closed ? 'abierto' : 'cerrado'}`);
            fetchYears();
        } catch (error) {
            toast.error("Error al cambiar estado");
        }
    };

    const togglePeriodStatus = async (period) => {
        try {
            await academicService.updateAcademicPeriod(period.id, { is_closed: !period.is_closed });
            toast.success(`Periodo ${period.is_closed ? 'abierto' : 'cerrado'}`);
            fetchYears();
        } catch (error) {
            toast.error("Error al cambiar estado del periodo");
        }
    };

    const updatePeriodDates = async (period, field, value) => {
        try {
            await academicService.updateAcademicPeriod(period.id, { [field]: value });
            toast.success("Fechas actualizadas");
            fetchYears();
        } catch (error) {
            toast.error("Error al actualizar fechas");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Gestión de Años Lectivos</h1>
                    <p className="text-slate-500">Configure los periodos académicos y trimestres</p>
                </div>
                <button
                    onClick={() => { resetForm(); setIsModalOpen(true); }}
                    className="btn-primary flex items-center gap-2"
                >
                    <Plus size={20} />
                    Nuevo Año Lectivo
                </button>
            </div>

            {loading ? (
                <div className="text-center py-10">Cargando...</div>
            ) : (
                <div className="grid gap-6">
                    {years.map((year) => (
                        <div key={year.id} className={`card-premium overflow-hidden ${year.is_active ? 'ring-2 ring-indigo-500' : ''}`}>
                            <div className="p-6">
                                <div className="flex justify-between items-start">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${year.is_active ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
                                            <Calendar size={24} />
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-3">
                                                <h3 className="text-lg font-bold text-slate-800">{year.name}</h3>
                                                {year.is_active && <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-100 text-indigo-700 rounded-full">Actual</span>}
                                                {year.is_closed && <span className="px-2 py-0.5 text-xs font-semibold bg-red-100 text-red-700 rounded-full flex items-center gap-1"><Lock size={10} /> Cerrado</span>}
                                            </div>
                                            <p className="text-sm text-slate-500">
                                                {new Date(year.start_date).toLocaleDateString()} - {new Date(year.end_date).toLocaleDateString()}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => toggleYearStatus(year)}
                                            className={`p-2 rounded-lg transition-colors ${year.is_closed ? 'text-red-600 hover:bg-red-50' : 'text-green-600 hover:bg-green-50'}`}
                                            title={year.is_closed ? "Abrir Año" : "Cerrar Año"}
                                        >
                                            {year.is_closed ? <Unlock size={20} /> : <Lock size={20} />}
                                        </button>
                                        <button onClick={() => handleEdit(year)} className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
                                            <Edit2 size={20} />
                                        </button>
                                        <button
                                            onClick={() => setExpandedYear(expandedYear === year.id ? null : year.id)}
                                            className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                                        >
                                            {expandedYear === year.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                        </button>
                                    </div>
                                </div>

                                {/* Periods Section */}
                                {expandedYear === year.id && (
                                    <div className="mt-6 pt-6 border-t border-slate-100 animate-fadeIn">
                                        <h4 className="text-sm font-semibold text-slate-700 mb-4 uppercase tracking-wider">Trimestres</h4>
                                        <div className="grid md:grid-cols-3 gap-4">
                                            {year.periods.sort((a, b) => a.number - b.number).map((period) => (
                                                <div key={period.id} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                                                    <div className="flex justify-between items-center mb-3">
                                                        <span className="font-semibold text-slate-700">Trimestre {period.number}</span>
                                                        <button
                                                            onClick={() => togglePeriodStatus(period)}
                                                            className={`text-xs font-medium px-2 py-1 rounded-md flex items-center gap-1 transition-colors ${period.is_closed
                                                                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                                                : 'bg-green-100 text-green-700 hover:bg-green-200'
                                                                }`}
                                                        >
                                                            {period.is_closed ? <Lock size={12} /> : <Unlock size={12} />}
                                                            {period.is_closed ? 'Cerrado' : 'Abierto'}
                                                        </button>
                                                    </div>
                                                    <div className="space-y-3">
                                                        <div>
                                                            <label className="text-xs text-slate-500 block mb-1">Inicio</label>
                                                            <input
                                                                type="date"
                                                                className="w-full text-xs p-1.5 rounded border border-slate-200 focus:ring-1 focus:ring-indigo-500"
                                                                value={period.start_date}
                                                                onChange={(e) => updatePeriodDates(period, 'start_date', e.target.value)}
                                                                disabled={year.is_closed} // Block logic handled well
                                                            />
                                                        </div>
                                                        <div>
                                                            <label className="text-xs text-slate-500 block mb-1">Fin</label>
                                                            <input
                                                                type="date"
                                                                className="w-full text-xs p-1.5 rounded border border-slate-200 focus:ring-1 focus:ring-indigo-500"
                                                                value={period.end_date}
                                                                onChange={(e) => updatePeriodDates(period, 'end_date', e.target.value)}
                                                                disabled={year.is_closed}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Modal */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 animate-scaleIn">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-bold text-slate-800">
                                {editingId ? 'Editar Año Lectivo' : 'Nuevo Año Lectivo'}
                            </h2>
                            <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                                <XCircle size={24} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="input-label">Nombre (Ej: 2024-2025)</label>
                                <input
                                    required
                                    type="text"
                                    className="input-modern"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="2024-2025"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="input-label">Año (Numérico)</label>
                                    <input
                                        required
                                        type="number"
                                        className="input-modern"
                                        value={formData.year}
                                        onChange={(e) => setFormData({ ...formData, year: e.target.value })}
                                    />
                                </div>
                                <div className="flex items-end mb-2">
                                    <label className="flex items-center gap-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                                            checked={formData.is_active}
                                            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                        />
                                        <span className="text-sm font-medium text-slate-700">Año Actual (Activo)</span>
                                    </label>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="input-label">Fecha Inicio</label>
                                    <input
                                        required
                                        type="date"
                                        className="input-modern"
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                    />
                                </div>
                                <div>
                                    <label className="input-label">Fecha Fin</label>
                                    <input
                                        required
                                        type="date"
                                        className="input-modern"
                                        value={formData.end_date}
                                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                    />
                                </div>
                            </div>

                            <div className="pt-4 flex gap-3 justify-end">
                                <button
                                    type="button"
                                    onClick={() => setIsModalOpen(false)}
                                    className="btn-secondary"
                                >
                                    Cancelar
                                </button>
                                <button
                                    type="submit"
                                    className="btn-primary"
                                >
                                    {editingId ? 'Guardar Cambios' : 'Crear Año'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AcademicYearPage;
