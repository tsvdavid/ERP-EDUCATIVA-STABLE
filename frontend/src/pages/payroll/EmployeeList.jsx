import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Filter, 
  MoreVertical, 
  UserPlus, 
  Users,
  Mail, 
  Phone,
  Calendar,
  ShieldCheck,
  Briefcase,
  X
} from 'lucide-react';
import api from '../../services/api';
import { toast } from 'react-hot-toast';

const EMPTY_FORM = {
  user: '',
  identification: '',
  birth_date: '',
  gender: '',
  phone: '',
  address: '',
  emergency_contact: '',
  emergency_phone: '',
};

const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await api.get('/payroll/employees/');
      setEmployees(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      toast.error('Error al cargar empleados');
    } finally {
      setLoading(false);
    }
  };

  const openModal = async () => {
    setFormData(EMPTY_FORM);
    setIsModalOpen(true);
    try {
      const res = await api.get('/users/?limit=5000');
      const allUsers = Array.isArray(res.data)
        ? res.data
        : Array.isArray(res.data?.results)
        ? res.data.results
        : [];
      // Exclude users that already have an employee profile
      const employeeUserIds = new Set(employees.map(e => e.user));
      setAvailableUsers(allUsers.filter(u => !employeeUserIds.has(u.id)));
    } catch {
      toast.error('No se pudo cargar la lista de usuarios.');
    }
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setFormData(EMPTY_FORM);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.user || !formData.identification || !formData.birth_date || !formData.gender) {
      toast.error('Completa los campos obligatorios: usuario, identificación, fecha de nacimiento y género.');
      return;
    }
    setSaving(true);
    try {
      await api.post('/payroll/employees/', {
        user: Number(formData.user),
        identification: formData.identification,
        birth_date: formData.birth_date,
        gender: formData.gender,
        phone: formData.phone,
        address: formData.address,
        emergency_contact: formData.emergency_contact,
        emergency_phone: formData.emergency_phone,
      });
      toast.success('Empleado registrado correctamente.');
      closeModal();
      await fetchEmployees();
    } catch (error) {
      const detail = error.response?.data;
      const msg = typeof detail === 'string'
        ? detail
        : detail?.detail || detail?.user?.[0] || detail?.identification?.[0] || 'Error al crear empleado.';
      toast.error(msg);
    } finally {
      setSaving(false);
    }
  };

  const filteredEmployees = employees.filter(emp => {
    if (!emp.full_name) return false;
    return (
      emp.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (emp.identification || '').includes(searchTerm)
    );
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">Personal & Talento</h1>
          <p className="text-slate-500 font-medium">Directorio centralizado de docentes y administrativos.</p>
        </div>
        <button
          onClick={openModal}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-2xl font-bold transition-all shadow-lg shadow-slate-200"
        >
          <UserPlus size={18} />
          Nuevo Empleado
        </button>
      </header>

      {/* Modal Nuevo Empleado */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[2rem] shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-8 border-b border-slate-100">
              <div>
                <h2 className="text-2xl font-black text-slate-800">Nuevo Empleado</h2>
                <p className="text-slate-500 text-sm">Selecciona un usuario de la institución y completa sus datos.</p>
              </div>
              <button onClick={closeModal} className="p-2 rounded-xl hover:bg-slate-100 text-slate-400 transition-colors">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-8 space-y-5">
              {/* Usuario */}
              <div>
                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">
                  Usuario del sistema <span className="text-rose-500">*</span>
                </label>
                <select
                  name="user"
                  value={formData.user}
                  onChange={handleChange}
                  required
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                >
                  <option value="">-- Seleccionar usuario --</option>
                  {availableUsers.map(u => (
                    <option key={u.id} value={u.id}>
                      {u.first_name} {u.last_name} (@{u.username})
                    </option>
                  ))}
                </select>
                {availableUsers.length === 0 && (
                  <p className="text-xs text-amber-600 mt-1">No hay usuarios disponibles o todos ya son empleados.</p>
                )}
              </div>

              {/* Identificación */}
              <div>
                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">
                  Cédula / Identificación <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  name="identification"
                  value={formData.identification}
                  onChange={handleChange}
                  required
                  placeholder="0000000000"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Fecha de nacimiento */}
                <div>
                  <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">
                    Fecha de nacimiento <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="date"
                    name="birth_date"
                    value={formData.birth_date}
                    onChange={handleChange}
                    required
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  />
                </div>

                {/* Género */}
                <div>
                  <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">
                    Género <span className="text-rose-500">*</span>
                  </label>
                  <select
                    name="gender"
                    value={formData.gender}
                    onChange={handleChange}
                    required
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  >
                    <option value="">-- Seleccionar --</option>
                    <option value="M">Masculino</option>
                    <option value="F">Femenino</option>
                    <option value="O">Otro</option>
                  </select>
                </div>
              </div>

              {/* Teléfono */}
              <div>
                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Teléfono</label>
                <input
                  type="text"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  placeholder="0991234567"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
              </div>

              {/* Dirección */}
              <div>
                <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Dirección</label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  placeholder="Calle, número, ciudad"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Contacto emergencia</label>
                  <input
                    type="text"
                    name="emergency_contact"
                    value={formData.emergency_contact}
                    onChange={handleChange}
                    placeholder="Nombre completo"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">Tel. emergencia</label>
                  <input
                    type="text"
                    name="emergency_phone"
                    value={formData.emergency_phone}
                    onChange={handleChange}
                    placeholder="0991234567"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 font-medium text-slate-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>

              <div className="flex gap-4 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="flex-1 py-3 bg-slate-100 text-slate-600 rounded-2xl font-bold hover:bg-slate-200 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 py-3 bg-slate-900 text-white rounded-2xl font-bold hover:bg-slate-800 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Guardando...' : 'Registrar Empleado'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}


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
