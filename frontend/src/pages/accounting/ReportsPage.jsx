import React, { useState, useEffect } from 'react';
import { BarChart, PieChart, Printer, Download, TrendingUp, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';
import accountingService from '../../services/accountingService';

const ReportsPage = () => {
    const [activeTab, setActiveTab] = useState('balance_sheet');
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);

    // ATS State
    const [atsYear, setAtsYear] = useState(new Date().getFullYear());
    const [atsMonth, setAtsMonth] = useState(new Date().getMonth() + 1);

    useEffect(() => {
        if (activeTab === 'ats') return;
        loadReport();
    }, [activeTab]);

    const loadReport = async () => {
        setLoading(true);
        try {
            let result;
            if (activeTab === 'balance_sheet') {
                result = await accountingService.getBalanceSheet();
            } else if (activeTab === 'income_statement') {
                result = await accountingService.getIncomeStatement();
            }
            setData(result);
        } catch (error) {
            console.error(error);
            toast.error("Error cargando reporte");
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadATS = async () => {
        setLoading(true);
        try {
            const blob = await accountingService.downloadATS(atsYear, atsMonth);
            // Create download link
            const url = window.URL.createObjectURL(new Blob([blob]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `ATS_${atsYear}_${atsMonth.toString().padStart(2, '0')}.xml`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
            toast.success("ATS descargado correctamente");
        } catch (error) {
            console.error(error);
            toast.error("Error descargando ATS");
        } finally {
            setLoading(false);
        }
    };

    const renderAccountTree = (nodes, level = 0) => {
        if (!nodes) return null;
        return nodes.map(node => (
            <div key={node.id}>
                <div className={`flex justify-between py-2 border-b border-slate-50 hover:bg-slate-50 ${level === 0 ? 'font-bold text-slate-800' : 'text-slate-600 text-sm'}`}
                    style={{ paddingLeft: `${level * 20}px` }}>
                    <div className="flex gap-2">
                        <span className="font-mono text-xs text-slate-400">{node.code}</span>
                        <span>{node.name}</span>
                    </div>
                    <span>
                        ${node.balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                </div>
                {node.children && renderAccountTree(node.children, level + 1)}
            </div>
        ));
    };

    const renderDataContent = () => {
        if (loading) return <div className="text-center py-20 text-slate-400">Procesando...</div>;

        if (activeTab === 'ats') {
            return (
                <div className="max-w-xl mx-auto py-10">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-bold uppercase tracking-wider text-slate-800">Anexo Transaccional Simplificado (ATS)</h2>
                        <p className="text-slate-500 text-sm mt-2">Generación de XML para el SRI</p>
                    </div>

                    <div className="bg-slate-50 p-8 rounded-xl border border-slate-200">
                        <div className="grid grid-cols-2 gap-6 mb-8">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">Año Fiscal</label>
                                <input
                                    type="number"
                                    className="w-full border-slate-300 rounded shadow-sm p-2 bg-white"
                                    value={atsYear}
                                    onChange={(e) => setAtsYear(parseInt(e.target.value))}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">Mes</label>
                                <select
                                    className="w-full border-slate-300 rounded shadow-sm p-2 bg-white"
                                    value={atsMonth}
                                    onChange={(e) => setAtsMonth(parseInt(e.target.value))}
                                >
                                    <option value={1}>Enero</option>
                                    <option value={2}>Febrero</option>
                                    <option value={3}>Marzo</option>
                                    <option value={4}>Abril</option>
                                    <option value={5}>Mayo</option>
                                    <option value={6}>Junio</option>
                                    <option value={7}>Julio</option>
                                    <option value={8}>Agosto</option>
                                    <option value={9}>Septiembre</option>
                                    <option value={10}>Octubre</option>
                                    <option value={11}>Noviembre</option>
                                    <option value={12}>Diciembre</option>
                                </select>
                            </div>
                        </div>

                        <button
                            onClick={handleDownloadATS}
                            disabled={loading}
                            className="w-full bg-indigo-600 text-white font-bold py-3 px-4 rounded hover:bg-indigo-700 transition flex justify-center items-center gap-2"
                        >
                            <Download size={20} />
                            {loading ? 'Generando XML...' : 'Descargar XML ATS'}
                        </button>

                        <p className="text-xs text-slate-400 mt-4 text-center">
                            Nota: Este archivo debe ser validado en el software DIMM del SRI antes de su envío.
                        </p>
                    </div>
                </div>
            );
        }

        if (!data) return <div className="text-center py-20 text-slate-400">No hay datos disponibles.</div>;

        if (activeTab === 'balance_sheet') {
            return (
                <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in">
                    <div className="text-center border-b-2 border-slate-800 pb-4 mb-8">
                        <h2 className="text-2xl font-bold uppercase tracking-wider">Balance General</h2>
                        <p className="text-slate-500 text-sm">Al {new Date().toLocaleDateString()}</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                        <div>
                            <h3 className="text-lg font-bold text-indigo-700 border-b border-indigo-200 pb-2 mb-4">ACTIVOS</h3>
                            {renderAccountTree(data.assets)}
                            <div className="mt-4 pt-4 border-t-2 border-slate-800 flex justify-between font-bold text-lg">
                                <span>TOTAL ACTIVOS</span>
                                <span>${data.total_assets.toLocaleString()}</span>
                            </div>
                        </div>

                        <div className="space-y-8">
                            <div>
                                <h3 className="text-lg font-bold text-indigo-700 border-b border-indigo-200 pb-2 mb-4">PASIVOS</h3>
                                {renderAccountTree(data.liabilities)}
                                <div className="mt-2 pt-2 border-t border-slate-200 flex justify-between font-bold">
                                    <span>Total Pasivos</span>
                                    <span>${data.total_liabilities.toLocaleString()}</span>
                                </div>
                            </div>

                            <div>
                                <h3 className="text-lg font-bold text-indigo-700 border-b border-indigo-200 pb-2 mb-4">PATRIMONIO</h3>
                                {renderAccountTree(data.equity)}

                                <div className="flex justify-between py-2 text-green-700 font-medium">
                                    <span>Utilidad del Ejercicio</span>
                                    <span>${data.net_income.toLocaleString()}</span>
                                </div>

                                <div className="mt-2 pt-2 border-t border-slate-200 flex justify-between font-bold">
                                    <span>Total Patrimonio</span>
                                    <span>${(data.total_equity + data.net_income).toLocaleString()}</span>
                                </div>
                            </div>

                            <div className="mt-4 pt-4 border-t-2 border-slate-800 flex justify-between font-bold text-lg">
                                <span>TOTAL PASIVO + PATRIMONIO</span>
                                <span>${data.total_equity_and_liabilities.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        if (activeTab === 'income_statement') {
            return (
                <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in">
                    <div className="text-center border-b-2 border-slate-800 pb-4 mb-8">
                        <h2 className="text-2xl font-bold uppercase tracking-wider">Estado de Resultados (P&G)</h2>
                        <p className="text-slate-500 text-sm">Al {new Date().toLocaleDateString()}</p>
                    </div>

                    <div>
                        <h3 className="text-lg font-bold text-green-700 border-b border-green-200 pb-2 mb-4">INGRESOS</h3>
                        {renderAccountTree(data.income)}
                        <div className="mt-4 pt-2 flex justify-between font-bold text-lg text-green-800">
                            <span>TOTAL INGRESOS</span>
                            <span>${data.total_income.toLocaleString()}</span>
                        </div>
                    </div>

                    <div>
                        <h3 className="text-lg font-bold text-red-700 border-b border-red-200 pb-2 mb-4">GASTOS</h3>
                        {renderAccountTree(data.expenses)}
                        <div className="mt-4 pt-2 flex justify-between font-bold text-lg text-red-800">
                            <span>TOTAL GASTOS</span>
                            <span>${data.total_expenses.toLocaleString()}</span>
                        </div>
                    </div>

                    <div className="mt-8 pt-4 border-t-4 border-double border-slate-800 flex justify-between font-bold text-2xl bg-slate-50 p-4 rounded-xl">
                        <span>UTILIDAD NETA</span>
                        <span className={data.net_income >= 0 ? 'text-green-600' : 'text-red-600'}>
                            ${data.net_income.toLocaleString()}
                        </span>
                    </div>
                </div>
            );
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                <TrendingUp className="text-indigo-600" /> Reportes Financieros
            </h1>

            <div className="flex bg-white rounded-lg p-1 border border-slate-200 shadow-sm w-fit">
                <button
                    onClick={() => setActiveTab('balance_sheet')}
                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${activeTab === 'balance_sheet' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
                >
                    <PieChart size={16} /> Balance General
                </button>
                <button
                    onClick={() => setActiveTab('income_statement')}
                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${activeTab === 'income_statement' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
                >
                    <BarChart size={16} /> Estado de Resultados
                </button>
                <button
                    onClick={() => setActiveTab('ats')}
                    className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-2 ${activeTab === 'ats' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-500 hover:text-slate-700'}`}
                >
                    <FileText size={16} /> Anexos Fiscales (ATS)
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-8 min-h-[500px]">
                {renderDataContent()}
            </div>
        </div>
    );
};

export default ReportsPage;
