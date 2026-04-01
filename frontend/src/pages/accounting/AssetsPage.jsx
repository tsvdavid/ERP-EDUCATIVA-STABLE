import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import accountingService from '../../services/accountingService';

const AssetsPage = () => {
    const navigate = useNavigate();
    const [assets, setAssets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [depreciating, setDepreciating] = useState(false);

    useEffect(() => {
        loadAssets();
    }, []);

    const loadAssets = async () => {
        try {
            const data = await accountingService.getAssets();
            setAssets(data);
        } catch (error) {
            console.error("Error loading assets", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCalculateDepreciation = async (id, name) => {
        if (!window.confirm(`¿Calcular y registrar depreciación para el activo: ${name}?`)) return;
        setDepreciating(true);
        try {
            const res = await accountingService.calculateDepreciation(id);
            alert(`Depreciación calculada exitosamente. Monto: $${res.amount} (por ${res.months} meses)`);
            loadAssets();
        } catch (error) {
            console.error("Error calculating depreciation", error);
            alert(error.response?.data?.error || "Error al calcular la depreciación. Revise si ya pasó un mes o ya está totalmente depreciado.");
        } finally {
            setDepreciating(false);
        }
    };

    const handleDelete = async (id, name) => {
        if (!window.confirm(`¿Eliminar el activo fijo: ${name}? Esta acción no se puede deshacer.`)) return;
        try {
            await accountingService.deleteAsset(id);
            loadAssets();
        } catch (error) {
            console.error("Error deleting asset", error);
            alert("Error al eliminar el activo. Es posible que tenga registros dependientes.");
        }
    };

    if (loading) return <div className="p-6">Cargando activos fijos...</div>;

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800">Activos Fijos</h1>
                    <p className="text-gray-600 text-sm mt-1">Gestión de bienes y cálculo de depreciaciones</p>
                </div>
                <button
                    onClick={() => navigate('/dashboard/accounting/assets/new')}
                    className="bg-green-600 text-white px-4 py-2 rounded shadow hover:bg-green-700"
                >
                    + Nuevo Activo
                </button>
            </div>

            <div className="bg-white rounded-lg shadow overflow-x-auto">
                <table className="min-w-[1000px] sm:min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Código/Nombre</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha Compra</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Valor Adquisición</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Dep. Acumulada</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Valor Actual</th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {assets.length === 0 ? (
                            <tr>
                                <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                                    No hay activos fijos registrados.
                                </td>
                            </tr>
                        ) : assets.map(asset => (
                            <tr key={asset.id} className="hover:bg-gray-50">
                                <td className="px-6 py-4">
                                    <div className="text-sm font-medium text-gray-900">{asset.name}</div>
                                    <div className="text-xs text-gray-500">{asset.code || 'S/N'} | Vida Útil: {asset.useful_life_years} años</div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {asset.purchase_date}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                                    ${parseFloat(asset.purchase_price).toFixed(2)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 text-right">
                                    ${parseFloat(asset.accumulated_depreciation).toFixed(2)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900 text-right">
                                    ${parseFloat(asset.current_value).toFixed(2)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-center">
                                    {parseFloat(asset.current_value) <= 0 ? (
                                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                                            Depreciado
                                        </span>
                                    ) : (
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${asset.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                            {asset.is_active ? 'Activo' : 'Inactivo'}
                                        </span>
                                    )}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                    <button
                                        onClick={() => handleCalculateDepreciation(asset.id, asset.name)}
                                        disabled={depreciating || parseFloat(asset.current_value) <= 0}
                                        className={`mr-3 ${parseFloat(asset.current_value) <= 0 ? 'text-gray-400 cursor-not-allowed' : 'text-blue-600 hover:text-blue-900'}`}
                                        title="Calcular y asentar depreciación del mes"
                                    >
                                        Depreciar
                                    </button>
                                    <button
                                        onClick={() => handleDelete(asset.id, asset.name)}
                                        className="text-red-600 hover:text-red-900"
                                    >
                                        Eliminar
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AssetsPage;
