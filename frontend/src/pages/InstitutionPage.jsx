import React, { useState, useEffect } from 'react';
import userService from '../services/userService';
import { Building, Save } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../context/authStore';

const InstitutionPage = () => {
    const { user } = useAuthStore();
    const [loading, setLoading] = useState(true);
    const [formData, setFormData] = useState({
        id: null,
        name: '',
        address: '',
        phone: '',
        email: '',
        website: '',
        logo: null,
        ruc: '',
        establishment_code: '001',
        emission_point: '001',
        special_taxpayer_number: '',
        obligado_contabilidad: false
    });
    const [exists, setExists] = useState(false);

    useEffect(() => {
        loadInstitution();
    }, []);

    const loadInstitution = async () => {
        setLoading(true);
        try {
            const data = await userService.getInstitutions();
            if (data && data.length > 0) {
                // Load the first institution found
                const inst = data[0];
                setFormData(inst);
                setExists(true);
            } else {
                // Ready to create
                setExists(false);
            }
        } catch (error) {
            console.error("Error loading institution", error);
            toast.error("Error al cargar información institucional");
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFormData({ ...formData, logo: e.target.files[0] });
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const data = new FormData();
            data.append('name', formData.name);
            data.append('address', formData.address || '');
            data.append('phone', formData.phone || '');
            data.append('email', formData.email || '');
            data.append('website', formData.website || '');

            if (formData.logo instanceof File) {
                data.append('logo', formData.logo);
            }

            if (exists) {
                await userService.updateInstitution(formData.id, data);
                toast.success('Institución actualizada');
            } else {
                await userService.createInstitution(data);
                toast.success('Institución configurada');
                setExists(true);
            }
            loadInstitution();
        } catch (error) {
            console.error(error);
            toast.error('Error al guardar institución');
        }
    };

    const canEdit = user?.role === 'ADMIN';

    if (loading) return <div className="p-8 text-center text-slate-500">Cargando información...</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center border-b border-slate-200 pb-4">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center text-indigo-600">
                        <Building size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-800">
                            Institución Educativa
                        </h1>
                        <p className="text-slate-500 text-sm">Configuración de datos maestras</p>
                    </div>
                </div>
            </div>

            <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-100 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-indigo-500 to-purple-500"></div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Logo Section */}
                    <div className="flex flex-col items-center justify-center p-6 bg-slate-50 rounded-xl border-2 border-dashed border-slate-200 hover:border-indigo-300 transition-colors">
                        {formData.logo && typeof formData.logo === 'string' ? (
                            <img src={formData.logo} alt="Logo" className="h-32 object-contain mb-4" />
                        ) : (
                            <div className="h-32 w-32 bg-slate-200 rounded-full flex items-center justify-center mb-4 text-slate-400">
                                <Building size={48} />
                            </div>
                        )}
                        {canEdit && (
                            <div className="w-full max-w-xs text-center">
                                <label className="block text-sm font-medium text-slate-700 mb-2">Logo Institucional</label>
                                <input type="file" accept="image/*" className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100" onChange={handleFileChange} />
                            </div>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <label className="label">Nombre de la Institución</label>
                            <input required readOnly={!canEdit} type="text" className="input-modern w-full font-bold text-lg" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} />
                        </div>
                        <div className="space-y-2">
                            <label className="label">Correo Electrónico</label>
                            <input readOnly={!canEdit} type="email" className="input-modern w-full" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} />
                        </div>
                        <div className="space-y-2">
                            <label className="label">Teléfono</label>
                            <input readOnly={!canEdit} type="text" className="input-modern w-full" value={formData.phone} onChange={e => setFormData({ ...formData, phone: e.target.value })} />
                        </div>
                        <div className="space-y-2">
                            <label className="label">Sitio Web</label>
                            <input readOnly={!canEdit} type="url" className="input-modern w-full" value={formData.website} onChange={e => setFormData({ ...formData, website: e.target.value })} />
                        </div>
                        <div className="md:col-span-2 space-y-2">
                            <label className="label">Dirección</label>
                            <textarea readOnly={!canEdit} rows="3" className="input-modern w-full" value={formData.address} onChange={e => setFormData({ ...formData, address: e.target.value })} />
                        </div>

                        {/* SRI Configuration moved to Invoices Page */}
                    </div>

                    {canEdit && (
                        <div className="pt-6 border-t border-slate-100 flex justify-end">
                            <button type="submit" className="btn-primary flex items-center gap-2 px-8 py-3 text-lg shadow-lg shadow-indigo-200">
                                <Save size={20} />
                                Guardar Cambios
                            </button>
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
};

export default InstitutionPage;
