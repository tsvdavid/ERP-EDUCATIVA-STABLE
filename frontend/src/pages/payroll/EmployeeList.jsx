import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  MoreVertical, 
  UserPlus, 
  Mail, 
  Phone,
  Calendar,
  ShieldCheck,
  Briefcase
} from 'lucide-react';
import api from '../../services/api';
import { toast } from 'react-hot-toast';

const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await api.get('/payroll/employees/');
      setEmployees(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Error al cargar empleados');
      setLoading(false);
    }
  };

  const filteredEmployees = employees.filter(emp => 
    emp.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.identification.includes(searchTerm)
  );

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">Personal & Talento</h1>
          <p className="text-slate-500 font-medium">Directorio centralizado de docentes y administrativos.</p>
        </div>
        <button className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-2xl font-bold transition-all shadow-lg shadow-slate-200">
          <UserPlus size={18} />
          Nuevo Empleado
        </button>
      </header>

      {/* Toolbar */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input 
            type="text" 
            placeholder="Buscar por nombre, identificación o email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-12 pr-4 py-3 rounded-2xl border border-slate-100 bg-white shadow-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
          />
        </div>
        <button className="px-5 py-3 rounded-2xl bg-white border border-slate-100 shadow-sm flex items-center gap-2 font-bold text-slate-600 hover:bg-slate-50 transition-all">
          <Filter size={18} /> Filtros
        </button>
      </div>

      {/* Grid of Employees */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {filteredEmployees.map((emp) => (
          <div key={emp.id} className="bg-white rounded-3xl p-6 border border-slate-100 shadow-sm hover:shadow-xl hover:shadow-indigo-50 transition-all group relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
              <button className="p-2 hover:bg-slate-100 rounded-xl text-slate-400">
                <MoreVertical size={18} />
              </button>
            </div>
            
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 font-black text-xl border-2 border-indigo-100">
                {emp.full_name.split(' ').map(n => n[0]).join('')}
              </div>
              <div>
                <h3 className="font-bold text-slate-800 text-lg leading-tight">{emp.full_name}</h3>
                <p className="text-slate-400 text-sm font-medium">{emp.identification}</p>
              </div>
            </div>

            <div className="space-y-3">
              <InfoRow icon={<Mail size={14} />} text={emp.email} />
              <InfoRow icon={<Phone size={14} />} text={emp.phone || 'Sin teléfono'} />
              <InfoRow icon={<Briefcase size={14} />} text="Docente de Matemáticas" /> {/* Placeholder for Position */}
            </div>

            <div className="mt-6 pt-6 border-t border-slate-50 flex justify-between items-center">
              <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${emp.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                {emp.is_active ? 'Activo' : 'Inactivo'}
              </span>
              <button className="text-indigo-600 font-bold text-sm hover:underline">
                Ver Perfil
              </button>
            </div>
          </div>
        ))}
      </div>

      {filteredEmployees.length === 0 && !loading && (
        <div className="py-32 text-center space-y-4">
          <div className="bg-slate-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto text-slate-300">
            <Users size={40} />
          </div>
          <h3 className="text-xl font-bold text-slate-800">No se encontraron empleados</h3>
          <p className="text-slate-500">Intenta con otros criterios de búsqueda o registra un nuevo empleado.</p>
        </div>
      )}
    </div>
  );
};

const InfoRow = ({ icon, text }) => (
  <div className="flex items-center gap-3 text-slate-500 font-medium text-sm">
    <div className="text-slate-300">{icon}</div>
    {text}
  </div>
);

export default EmployeeList;
