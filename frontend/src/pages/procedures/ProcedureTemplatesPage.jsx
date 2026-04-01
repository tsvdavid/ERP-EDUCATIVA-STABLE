import React, { useState, useEffect } from 'react';
import { FileText, Plus, Edit2, Trash2, AlertCircle } from 'lucide-react';
import { procedureService } from '../../services/procedureService';

const ProcedureTemplatesPage = () => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        content_template: '',
        requires_approval: true,
        approver_role: 'ADMIN',
        is_active: true
    });
    const [editingId, setEditingId] = useState(null);

    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        try {
            setLoading(true);
            const data = await procedureService.getTemplates();
            setTemplates(data);
        } catch (err) {
            setError('Error al cargar plantillas');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if (editingId) {
                await procedureService.updateTemplate(editingId, formData);
            } else {
                await procedureService.createTemplate(formData);
            }
            setShowModal(false);
            loadTemplates();
        } catch (err) {
            setError('Error al guardar la plantilla');
            console.error(err);
        }
    };

    const handleEdit = (template) => {
        setFormData(template);
        setEditingId(template.id);
        setShowModal(true);
    };

    const handleDelete = async (id) => {
        if (window.confirm('¿Está seguro de eliminar esta plantilla?')) {
            try {
                await procedureService.deleteTemplate(id);
                loadTemplates();
            } catch (err) {
                setError('Error al eliminar la plantilla');
            }
        }
    };

    const openCreateModal = () => {
        setFormData({
            name: '',
            description: '',
            content_template: '',
            requires_approval: true,
            approver_role: 'ADMIN',
            is_active: true
        });
        setEditingId(null);
        setShowModal(true);
    };

    if (loading) return <div className="p-8 text-center text-slate-500">Cargando plantillas...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Plantillas de Trámites y Documentos</h1>
                    <p className="text-slate-600 mt-1">Configura los formatos para certificados y solicitudes.</p>
                </div>
                <button
                    onClick={openCreateModal}
                    className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center gap-2"
                >
                    <Plus className="w-4 h-4" />
                    Nueva Plantilla
                </button>
            </div>

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {templates.map(template => (
                    <div key={template.id} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
                        <div>
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
                                    <FileText className="w-6 h-6" />
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => handleEdit(template)} className="text-slate-400 hover:text-indigo-600">
                                        <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button onClick={() => handleDelete(template.id)} className="text-slate-400 hover:text-red-600">
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                            <h3 className="text-lg font-semibold text-slate-800">{template.name}</h3>
                            <p className="text-sm text-slate-500 mt-2 line-clamp-2">{template.description || "Sin descripción"}</p>

                            <div className="mt-4 flex flex-wrap gap-2">
                                {template.requires_approval ? (
                                    <span className="text-xs font-medium px-2.5 py-1 bg-yellow-100 text-yellow-800 rounded-full">
                                        Requiere Aprobación ({template.approver_role})
                                    </span>
                                ) : (
                                    <span className="text-xs font-medium px-2.5 py-1 bg-green-100 text-green-800 rounded-full">Automático</span>
                                )}
                                {!template.is_active && (
                                    <span className="text-xs font-medium px-2.5 py-1 bg-slate-100 text-slate-600 rounded-full">Inactivo</span>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Modal de Creación/Edición */}
            {showModal && (
                <div className="fixed inset-0 bg-slate-900/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl flex flex-col max-h-[90vh]">
                        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
                            <h2 className="text-xl font-bold text-slate-800">
                                {editingId ? 'Editar Plantilla' : 'Nueva Plantilla'}
                            </h2>
                            <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600">
                                &times;
                            </button>
                        </div>

                        <div className="p-6 overflow-y-auto">
                            <form id="templateForm" onSubmit={handleSubmit} className="space-y-6">
                                <div className="grid grid-cols-2 gap-6">
                                    <div className="col-span-2">
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Nombre del Documento</label>
                                        <input
                                            type="text"
                                            required
                                            value={formData.name}
                                            onChange={e => setFormData({ ...formData, name: e.target.value })}
                                            className="w-full border-slate-200 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                                            placeholder="Ej. Certificado de Matrícula"
                                        />
                                    </div>
                                    <div className="col-span-2">
                                        <label className="block text-sm font-medium text-slate-700 mb-1">Descripción / Instrucciones</label>
                                        <textarea
                                            rows="2"
                                            value={formData.description}
                                            onChange={e => setFormData({ ...formData, description: e.target.value })}
                                            className="w-full border-slate-200 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                                            placeholder="Instrucciones breves para el estudiante"
                                        />
                                    </div>

                                    <div className="col-span-2">
                                        <div className="flex justify-between mb-1">
                                            <label className="block text-sm font-medium text-slate-700">Contenido del Documento</label>
                                            <span className="text-xs text-indigo-600">
                                                Variables disponibles: {'{{student_name}}, {{student_cedula}}, {{course_name}}, {{date}}, {{institution_name}}'}
                                            </span>
                                        </div>
                                        <textarea
                                            rows="12"
                                            required
                                            value={formData.content_template}
                                            onChange={e => setFormData({ ...formData, content_template: e.target.value })}
                                            className="w-full border-slate-200 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 font-mono text-sm"
                                            placeholder="Por medio del presente, certifico que el estudiante {{student_name}} está matriculado..."
                                        />
                                    </div>

                                    <div>
                                        <label className="flex items-center space-x-2 mt-6">
                                            <input
                                                type="checkbox"
                                                checked={formData.requires_approval}
                                                onChange={e => setFormData({ ...formData, requires_approval: e.target.checked })}
                                                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="text-sm font-medium text-slate-700">Requiere Aprobación Manual</span>
                                        </label>
                                    </div>

                                    {formData.requires_approval && (
                                        <div>
                                            <label className="block text-sm font-medium text-slate-700 mb-1">Rol que aprueba</label>
                                            <select
                                                value={formData.approver_role}
                                                onChange={e => setFormData({ ...formData, approver_role: e.target.value })}
                                                className="w-full border-slate-200 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
                                            >
                                                <option value="ADMIN">Administrativos</option>
                                                <option value="RECTOR">Rectoría</option>
                                                <option value="TEACHER">Profesores</option>
                                            </select>
                                        </div>
                                    )}

                                    <div className="col-span-2">
                                        <label className="flex items-center space-x-2">
                                            <input
                                                type="checkbox"
                                                checked={formData.is_active}
                                                onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                                                className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                                            />
                                            <span className="text-sm font-medium text-slate-700">Plantilla Activa</span>
                                        </label>
                                    </div>
                                </div>
                            </form>
                        </div>

                        <div className="p-6 border-t border-slate-100 bg-slate-50 rounded-b-xl flex justify-end gap-3">
                            <button
                                type="button"
                                onClick={() => setShowModal(false)}
                                className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg hover:bg-slate-100"
                            >
                                Cancelar
                            </button>
                            <button
                                type="submit"
                                form="templateForm"
                                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                            >
                                {editingId ? 'Guardar Cambios' : 'Crear Plantilla'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProcedureTemplatesPage;
