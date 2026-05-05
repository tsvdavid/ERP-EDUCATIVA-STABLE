import React, { useState, useEffect } from 'react';
import { 
  Users, 
  CreditCard, 
  Calendar, 
  CheckCircle, 
  AlertCircle,
  Download,
  Plus,
  ArrowRight,
  TrendingUp,
  Briefcase
} from 'lucide-react';
import api from '../../services/api';
import { toast } from 'react-hot-toast';

const PayrollDashboard = () => {
  const [periods, setPeriods] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [rolls, setRolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showGenModal, setShowGenModal] = useState(false);
  const [genData, setGenData] = useState({ year: new Date().getFullYear(), month: new Date().getMonth() + 1 });

  useEffect(() => {
    fetchPeriods();
  }, []);

  const fetchPeriods = async () => {
    try {
      const response = await api.get('/payroll/periods/');
      setPeriods(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Error al cargar periodos de nómina');
      setLoading(false);
    }
  };

  const handleSelectPeriod = async (period) => {
    setSelectedPeriod(period);
    try {
      const response = await api.get(`/payroll/periods/${period.id}/rolls/`);
      setRolls(response.data);
    } catch (error) {
      toast.error('Error al cargar roles del periodo');
    }
  };

  const handleDownloadPDF = async (rollId) => {
    try {
      const response = await api.get(`/payroll/rolls/${rollId}/pdf/`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `rol_${rollId}.pdf`);
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      toast.error('Error al descargar PDF');
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    try {
      await api.post('/payroll/periods/generate_nomina/', genData);
      toast.success('Nómina generada exitosamente');
      setShowGenModal(false);
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al generar nómina');
    }
  };

  const handleApprove = async (id) => {
    try {
      await api.post(`/payroll/periods/${id}/approve/`);
      toast.success('Nómina aprobada y contabilidad integrada');
      fetchPeriods();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Error al aprobar nómina');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-black text-slate-900 tracking-tight">Gestión de Nómina</h1>
          <p className="text-slate-500 mt-2 font-medium">Control de pagos, aportes y beneficios institucionales.</p>
        </div>
        <button 
          onClick={() => setShowGenModal(true)}
          className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-2xl font-bold shadow-xl shadow-indigo-200 transition-all hover:scale-105 active:scale-95"
        >
          <Plus size={20} />
          Generar Nueva Nómina
        </button>
      </header>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Empleados Activos" value="42" icon={<Users className="text-indigo-600" />} color="indigo" />
        <StatCard title="Costo Laboral Mes" value="$24,500" icon={<TrendingUp className="text-emerald-600" />} color="emerald" />
        <StatCard title="Contratos Vigentes" value="38" icon={<Briefcase className="text-amber-600" />} color="amber" />
        <StatCard title="Pdte. Aprobación" value={periods.filter(p => p.state === 'DRAFT').length} icon={<AlertCircle className="text-rose-600" />} color="rose" />
      </div>

      {/* Periods Table */}
      <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-6 border-b border-slate-50 flex justify-between items-center bg-slate-50/50">
          <h2 className="font-bold text-slate-800 flex items-center gap-2">
            <Calendar size={18} className="text-indigo-500" />
            Historial de Periodos
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-50/50 text-slate-400 text-xs uppercase tracking-widest font-black">
              <tr>
                <th className="px-6 py-4">Periodo</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4">Roles</th>
                <th className="px-6 py-4">F. Creación</th>
                <th className="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {periods.map((period) => (
                <tr 
                  key={period.id} 
                  onClick={() => handleSelectPeriod(period)}
                  className={`hover:bg-slate-50/50 transition-colors group cursor-pointer ${selectedPeriod?.id === period.id ? 'bg-indigo-50/30' : ''}`}
                >
                  <td className="px-6 py-5">
                    <div className="font-bold text-slate-700">{period.month_name} {period.year}</div>
                  </td>
                  <td className="px-6 py-5">
                    <StatusBadge state={period.state} />
                  </td>
                  <td className="px-6 py-5 text-slate-500 font-medium">
                    {period.rolls_count} empleados
                  </td>
                  <td className="px-6 py-5 text-slate-400 text-sm">
                    {new Date(period.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-5 text-right">
                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      {period.state === 'DRAFT' && (
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleApprove(period.id); }}
                          className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors flex items-center gap-1 text-sm font-bold"
                        >
                          <CheckCircle size={16} /> Aprobar
                        </button>
                      )}
                      <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                        <ArrowRight size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {periods.length === 0 && !loading && (
                <tr>
                  <td colSpan="5" className="px-6 py-20 text-center text-slate-400 font-medium">
                    No hay periodos de nómina generados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rolls Detail View */}
      {selectedPeriod && (
        <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden animate-in slide-in-from-top-4 duration-500">
          <div className="p-6 border-b border-slate-50 bg-slate-50/50 flex justify-between items-center">
            <h2 className="font-bold text-slate-800 flex items-center gap-2">
              <Users size={18} className="text-indigo-500" />
              Roles Individuales: {selectedPeriod.month_name} {selectedPeriod.year}
            </h2>
            <button className="text-sm font-bold text-slate-400 hover:text-slate-600">Descargar Todo (Excel)</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50/50 text-slate-400 text-xs uppercase tracking-widest font-black">
                <tr>
                  <th className="px-6 py-4">Empleado</th>
                  <th className="px-6 py-4">Sueldo Base</th>
                  <th className="px-6 py-4">IESS</th>
                  <th className="px-6 py-4">Neto</th>
                  <th className="px-6 py-4 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {rolls.map(roll => (
                  <tr key={roll.id} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-700">{roll.employee_name}</div>
                    </td>
                    <td className="px-6 py-4 text-slate-600 font-medium">${roll.base_salary}</td>
                    <td className="px-6 py-4 text-rose-500 font-medium">-${roll.iess_personal}</td>
                    <td className="px-6 py-4 text-indigo-600 font-black">${roll.net_to_pay}</td>
                    <td className="px-6 py-4 text-right">
                      <button 
                        onClick={() => handleDownloadPDF(roll.id)}
                        className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors flex items-center gap-1 text-sm font-bold ml-auto"
                      >
                        <Download size={16} /> Ver Rol
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal Generar */}
      {showGenModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-8 animate-in zoom-in-95 duration-300">
            <h3 className="text-2xl font-black text-slate-800 mb-6">Generar Nómina</h3>
            <form onSubmit={handleGenerate} className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Año</label>
                <input 
                  type="number" 
                  value={genData.year} 
                  onChange={(e) => setGenData({...genData, year: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">Mes</label>
                <select 
                  value={genData.month}
                  onChange={(e) => setGenData({...genData, month: e.target.value})}
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                >
                  <option value="1">Enero</option>
                  <option value="2">Febrero</option>
                  <option value="3">Marzo</option>
                  <option value="4">Abril</option>
                  <option value="5">Mayo</option>
                  <option value="6">Junio</option>
                  <option value="7">Julio</option>
                  <option value="8">Agosto</option>
                  <option value="9">Septiembre</option>
                  <option value="10">Octubre</option>
                  <option value="11">Noviembre</option>
                  <option value="12">Diciembre</option>
                </select>
              </div>
              <div className="flex gap-4 mt-8">
                <button 
                  type="button"
                  onClick={() => setShowGenModal(false)}
                  className="flex-1 px-6 py-3 rounded-xl font-bold text-slate-500 hover:bg-slate-100 transition-colors"
                >
                  Cancelar
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-6 py-3 rounded-xl font-bold bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-100 transition-all"
                >
                  Confirmar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const StatCard = ({ title, value, icon, color }) => (
  <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 flex items-center gap-5 transition-all hover:shadow-md hover:-translate-y-1">
    <div className={`p-4 rounded-2xl bg-${color}-50`}>
      {icon}
    </div>
    <div>
      <p className="text-slate-400 text-xs font-black uppercase tracking-widest">{title}</p>
      <h4 className="text-2xl font-black text-slate-800 tracking-tight">{value}</h4>
    </div>
  </div>
);

const StatusBadge = ({ state }) => {
  const configs = {
    DRAFT: { label: 'Borrador', class: 'bg-slate-100 text-slate-600' },
    APPROVED: { label: 'Aprobado', class: 'bg-emerald-100 text-emerald-700' },
    PAID: { label: 'Pagado', class: 'bg-indigo-100 text-indigo-700' }
  };
  const config = configs[state] || configs.DRAFT;
  return (
    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${config.class}`}>
      {config.label}
    </span>
  );
};

export default PayrollDashboard;
