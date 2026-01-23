import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Search, Filter, Eye, AlertCircle, CheckCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import accountingService from '../../services/accountingService';
import { useAuthStore } from '../../context/authStore';

const JournalEntriesPage = () => {
    const { user } = useAuthStore();
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);

    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');

    useEffect(() => {
        loadEntries();
    }, [statusFilter]);

    const loadEntries = async () => {
        setLoading(true);
        try {
            const params = {};
            if (searchTerm) params.search = searchTerm;
            if (statusFilter !== 'ALL') params.state = statusFilter;

            const data = await accountingService.getEntries(params);
            setEntries(data);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando Libro Diario");
        } finally {
            setLoading(false);
        }
    };

    const handlePostEntry = async (id) => {
        if (!window.confirm("¿Está seguro de asentar este asiento? Esta acción no se puede deshacer.")) return;

        try {
            await accountingService.postEntry(id);
            toast.success("Asiento asentado correctamente");
            loadEntries();
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.error || "Error al asentar asiento");
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <BookOpen className="text-indigo-600" /> Libro Diario
                </h1>
                <div className="flex gap-2">
                    <button className="btn-primary flex items-center gap-2">
                        <Plus size={18} /> Nuevo Asiento
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-2.5 text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="Buscar por descripción, referencia o monto..."
                        className="pl-10 input-modern w-full"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && loadEntries()}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Filter className="text-slate-400" size={18} />
                    <select
                        className="input-modern"
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                    >
                        <option value="ALL">Todos los Estados</option>
                        <option value="DRAFT">Borrador</option>
                        <option value="POSTED">Asentado</option>
                        <option value="CANCELLED">Anulado</option>
                    </select>
                </div>
                <button onClick={loadEntries} className="btn-secondary">Buscar</button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-100">
                            <tr>
                                <th className="px-6 py-4">Fecha / Nro</th>
                                <th className="px-6 py-4">Descripción</th>
                                <th className="px-6 py-4">Referencia</th>
                                <th className="px-6 py-4 text-right">Débito</th>
                                <th className="px-6 py-4 text-right">Crédito</th>
                                <th className="px-6 py-4 text-center">Estado</th>
                                <th className="px-6 py-4 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                            {loading ? (
                                <tr><td colSpan="7" className="p-8 text-center text-slate-400">Cargando asientos...</td></tr>
                            ) : entries.length === 0 ? (
                                <tr><td colSpan="7" className="p-8 text-center text-slate-400">No hay asientos registrados.</td></tr>
                            ) : (
                                entries.map(entry => (
                                    <tr key={entry.id} className="hover:bg-slate-50 transition-colors group">
                                        <td className="px-6 py-4 font-mono text-xs text-slate-600">
                                            <div>{entry.date}</div>
                                            <div className="font-bold text-slate-800">#{entry.id.toString().padStart(6, '0')}</div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="font-medium text-slate-800 line-clamp-1">{entry.description}</div>
                                            <div className="text-xs text-slate-500">Por: {entry.created_by_name}</div>
                                        </td>
                                        <td className="px-6 py-4 text-slate-500 text-xs">
                                            {entry.reference || '-'}
                                        </td>
                                        <td className="px-6 py-4 text-right font-mono text-slate-700">
                                            ${parseFloat(entry.total_debit).toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4 text-right font-mono text-slate-700">
                                            ${parseFloat(entry.total_credit).toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {entry.state === 'POSTED' ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-50 text-green-700 text-xs font-bold border border-green-100">
                                                    <CheckCircle size={10} /> Asentado
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-50 text-yellow-700 text-xs font-bold border border-yellow-100">
                                                    Borrador
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button className="p-1 hover:text-indigo-600" title="Ver Detalle"><Eye size={18} /></button>
                                                {entry.state === 'DRAFT' && entry.is_balanced && (
                                                    <button
                                                        onClick={() => handlePostEntry(entry.id)}
                                                        className="p-1 hover:text-green-600" title="Asentar"
                                                    >
                                                        <CheckCircle size={18} />
                                                    </button>
                                                )}
                                                {!entry.is_balanced && (
                                                    <span className="text-red-500" title="Descuadrado"><AlertCircle size={18} /></span>
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
        </div>
    );
};

export default JournalEntriesPage;
