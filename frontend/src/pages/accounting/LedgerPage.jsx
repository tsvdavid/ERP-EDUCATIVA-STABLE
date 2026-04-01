import React, { useState, useEffect } from 'react';
import { Book, FileText, Download, Calendar, ArrowRight, Search } from 'lucide-react';
import { toast } from 'react-hot-toast';
import accountingService from '../../services/accountingService';
// Podríamos usar jsPDF o algo similar para exportar, por ahora solo lo mostraremos en tabla

const LedgerPage = () => {
    const [accounts, setAccounts] = useState([]);
    const [loading, setLoading] = useState(false);

    // Form State
    const [selectedAccount, setSelectedAccount] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    // Results
    const [ledgerData, setLedgerData] = useState(null);

    useEffect(() => {
        // Load operational accounts for selection
        const loadAccounts = async () => {
            try {
                const accs = await accountingService.getAccounts({});
                setAccounts(accs);
                if (accs.length > 0) {
                    setSelectedAccount(accs[0].id);
                }
            } catch (error) {
                toast.error("Error cargando cuentas contables");
            }
        };
        loadAccounts();
    }, []);

    const handleSearch = async (e) => {
        if (e) e.preventDefault();

        if (!selectedAccount) {
            toast.error("Debe seleccionar una cuenta contable");
            return;
        }

        setLoading(true);
        try {
            const params = { account_id: selectedAccount };
            if (startDate) params.start_date = startDate;
            if (endDate) params.end_date = endDate;

            const data = await accountingService.getLedger(params);
            setLedgerData(data);
        } catch (error) {
            console.error(error);
            toast.error("Error al generar el reporte del Libro Mayor");
        } finally {
            setLoading(false);
        }
    };

    const handleExportCsv = () => {
        if (!ledgerData || !ledgerData.transactions.length) return;

        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Fecha,Comprobante,Referencia,Glosa,Debe,Haber,Saldo\n";

        // Fila de saldo inicial
        csvContent += `,-,-,Saldo Inicial,-,-,${ledgerData.initial_balance}\n`;

        ledgerData.transactions.forEach(row => {
            const line = [
                row.date,
                `#${row.journal_id}`,
                `"${row.reference || ''}"`,
                `"${row.description || ''}"`,
                row.debit,
                row.credit,
                row.balance
            ].join(",");
            csvContent += line + "\n";
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `Libro_Mayor_${ledgerData.account_code}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                <Book className="text-indigo-600" /> Libro Mayor (Mayores)
            </h1>

            {/* Filter Card */}
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                    <div className="md:col-span-2">
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Cuenta Contable</label>
                        <select
                            className="input-modern w-full"
                            value={selectedAccount}
                            onChange={(e) => setSelectedAccount(e.target.value)}
                            required
                        >
                            <option value="">Seleccione una cuenta...</option>
                            {accounts.map(acc => (
                                <option key={acc.id} value={acc.id}>
                                    {acc.code} - {acc.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Desde Fecha</label>
                        <input
                            type="date"
                            className="input-modern w-full"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">Hasta Fecha</label>
                        <div className="flex gap-2">
                            <input
                                type="date"
                                className="input-modern w-full"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                            />
                            <button
                                type="submit"
                                className="btn-primary"
                                disabled={loading}
                            >
                                {loading ? <div className="animate-spin h-5 w-5 border-2 border-white rounded-full border-t-transparent"></div> : <Search size={20} />}
                            </button>
                        </div>
                    </div>
                </form>
            </div>

            {/* General Ledger Result */}
            {ledgerData && (
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="p-5 border-b border-slate-200 bg-slate-50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 sm:gap-0">
                        <div>
                            <h2 className="text-lg font-bold text-slate-800">
                                {ledgerData.account_code} - {ledgerData.account_name}
                            </h2>
                            <p className="text-sm text-slate-500">Reporte de movimientos transaccionales.</p>
                        </div>
                        <button
                            onClick={handleExportCsv}
                            className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 font-medium transition-colors flex items-center gap-2 text-sm"
                        >
                            <Download size={16} /> Exportar CSV
                        </button>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="text-xs text-slate-500 uppercase bg-slate-100 border-b border-slate-200">
                                <tr>
                                    <th className="px-4 py-3">Fecha</th>
                                    <th className="px-4 py-3">Cbte.</th>
                                    <th className="px-4 py-3">Referencia</th>
                                    <th className="px-4 py-3">Glosa</th>
                                    <th className="px-4 py-3 text-right">Debe</th>
                                    <th className="px-4 py-3 text-right">Haber</th>
                                    <th className="px-4 py-3 text-right">Saldo</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                                <tr className="bg-slate-50 font-medium">
                                    <td colSpan="6" className="px-4 py-3 text-right text-slate-600 border-r border-slate-200">SALDO INICIAL :</td>
                                    <td className="px-4 py-3 text-right text-indigo-700 font-bold font-mono">
                                        ${parseFloat(ledgerData.initial_balance).toFixed(2)}
                                    </td>
                                </tr>

                                {ledgerData.transactions.length === 0 ? (
                                    <tr>
                                        <td colSpan="7" className="px-6 py-8 text-center text-slate-500 italic border-l border-r border-slate-100">
                                            No hay movimientos asentados para esta cuenta en el periodo seleccionado.
                                        </td>
                                    </tr>
                                ) : (
                                    ledgerData.transactions.map((tx) => (
                                        <tr key={tx.id} className="hover:bg-indigo-50/30 transition-colors border-l border-r border-slate-100">
                                            <td className="px-4 py-3 font-mono text-xs">{tx.date}</td>
                                            <td className="px-4 py-3 text-indigo-600 font-medium whitespace-nowrap">#{tx.journal_id.toString().padStart(6, '0')}</td>
                                            <td className="px-4 py-3 text-slate-500">{tx.reference || '-'}</td>
                                            <td className="px-4 py-3 max-w-xs truncate" title={tx.description}>{tx.description}</td>
                                            <td className="px-4 py-3 text-right font-mono text-slate-700">${parseFloat(tx.debit).toFixed(2)}</td>
                                            <td className="px-4 py-3 text-right font-mono text-slate-700">${parseFloat(tx.credit).toFixed(2)}</td>
                                            <td className="px-4 py-3 text-right font-mono font-bold text-indigo-800 bg-indigo-50/10">
                                                ${parseFloat(tx.balance).toFixed(2)}
                                            </td>
                                        </tr>
                                    ))
                                )}

                                <tr className="bg-slate-50 font-bold border-t-2 border-slate-200">
                                    <td colSpan="6" className="px-4 py-4 text-right text-slate-800 border-r border-slate-200">SALDO FINAL :</td>
                                    <td className="px-4 py-4 text-right text-indigo-800 font-mono text-base border-l border-slate-200">
                                        ${parseFloat(ledgerData.final_balance).toFixed(2)}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LedgerPage;
