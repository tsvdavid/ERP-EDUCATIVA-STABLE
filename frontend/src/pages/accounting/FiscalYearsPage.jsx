import React, { useState, useEffect } from 'react';
import { Plus, CheckCircle, Lock, AlertTriangle, Calendar } from 'lucide-react';
import accountingService from '../../services/accountingService';

const FiscalYearsPage = () => {
  const [years, setYears] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedYear, setSelectedYear] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // New Year Modal specific
  const [isNewYearModalOpen, setIsNewYearModalOpen] = useState(false);
  const [newYearString, setNewYearString] = useState('');

  useEffect(() => {
    fetchYears();
  }, []);

  const fetchYears = async () => {
    try {
      setLoading(true);
      const data = await accountingService.getFiscalYears();
      setYears(data);
      setError(null);
    } catch (err) {
      setError('Error al cargar los años fiscales.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseYearClick = (year) => {
    setSelectedYear(year);
    setIsModalOpen(true);
  };

  const confirmCloseYear = async () => {
    try {
      setActionLoading(true);
      const res = await accountingService.closeFiscalYear(selectedYear.id);
      setIsModalOpen(false);
      fetchYears();
      alert(res.message || '✅ Año fiscal cerrado correctamente.');
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.error || '❌ Error al cerrar el año fiscal.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateYearClick = () => {
    setNewYearString(new Date().getFullYear().toString());
    setIsNewYearModalOpen(true);
  };

  const confirmCreateYear = async () => {
    try {
      setActionLoading(true);
      await accountingService.createFiscalYear({
        year: parseInt(newYearString, 10),
        is_closed: false
      });
      setIsNewYearModalOpen(false);
      fetchYears();
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.year?.[0] || '❌ Error al crear el año fiscal.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Años Fiscales y Cierres</h1>
        <button 
          onClick={handleCreateYearClick}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center shadow-sm"
        >
          <Plus size={20} className="mr-2" />
          Aperturar Nuevo Año
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-slate-500">Cargando...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-500">{error}</div>
        ) : (
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Año</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {years.map((y) => (
                <tr key={y.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Calendar size={18} className="text-slate-400 mr-2" />
                      <span className="font-medium text-slate-900">{y.year}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {y.is_closed ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <Lock size={12} className="mr-1" /> Cerrado
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckCircle size={12} className="mr-1" /> Abierto
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    {!y.is_closed && (
                      <button
                        onClick={() => handleCloseYearClick(y)}
                        className="text-amber-600 hover:text-amber-900 border border-amber-200 bg-amber-50 px-3 py-1 rounded-md"
                      >
                        Ejecutar Cierre Contable
                      </button>
                    )}
                    {y.is_closed && (
                      <span className="text-slate-400">Sin Acciones</span>
                    )}
                  </td>
                </tr>
              ))}
              {years.length === 0 && (
                <tr>
                  <td colSpan="3" className="px-6 py-8 text-center text-slate-500">
                    No hay años fiscales registrados. Por favor apertura un nuevo año.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Confirmation Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center text-amber-600 mb-4">
              <AlertTriangle size={32} className="mr-3" />
              <h2 className="text-xl font-bold text-slate-800">Cierre de Año Fiscal {selectedYear?.year}</h2>
            </div>
            
            <div className="mb-6 space-y-3 text-slate-600">
              <p>Vas a proceder con el cierre contable del año <strong>{selectedYear?.year}</strong>.</p>
              <ul className="list-disc pl-5 space-y-1">
                <li>Se calcularán todos los Ingresos y Gastos del año.</li>
                <li>Se creará un Asiento de Cierre Automático balanceado.</li>
                <li>El resultado (Utilidad/Pérdida) irá a Resultados Acumulados.</li>
                <li><strong className="text-red-600">No se podrán registrar más movimientos en este año.</strong></li>
              </ul>
              <p className="text-sm border-l-4 border-amber-400 pl-3 bg-amber-50 p-2 text-amber-800">
                Asegúrate de haber asignado la cuenta de "Patrimonio - Resultados Acumulados" en las Configuraciones Contables.
              </p>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50"
                disabled={actionLoading}
              >
                Cancelar
              </button>
              <button
                onClick={confirmCloseYear}
                disabled={actionLoading}
                className={`px-4 py-2 bg-amber-600 text-white rounded-lg flex items-center ${actionLoading ? 'opacity-50' : 'hover:bg-amber-700'}`}
              >
                {actionLoading ? 'Generando Asientos...' : 'Confirmar Cierre y Bloquear'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Year Modal */}
      {isNewYearModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-6">
            <h2 className="text-xl font-bold text-slate-800 mb-4">Aperturar Año Fiscal</h2>
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-1">Año (Numérico)</label>
              <input
                type="number"
                value={newYearString}
                onChange={(e) => setNewYearString(e.target.value)}
                className="w-full border border-slate-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ej. 2026"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setIsNewYearModalOpen(false)}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                onClick={confirmCreateYear}
                disabled={actionLoading || !newYearString}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                {actionLoading ? 'Guardando...' : 'Crear Año'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FiscalYearsPage;
