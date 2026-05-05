import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';
import { TrendingUp, Users, ShoppingBag, Briefcase, UserCircle, DollarSign, ArrowUpRight } from 'lucide-react';
import treasuryService from '../../services/treasuryService';
import { toast, Toaster } from 'react-hot-toast';

const CommercialDashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const data = await treasuryService.getCommercialDashboard();
            setStats(data);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar datos comerciales");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    if (!stats) return null;

    const chartData = [
        { name: 'Alumnos', value: stats.by_type.STUDENT, color: '#4F46E5', icon: <Users /> },
        { name: 'Mostrador', value: stats.by_type.WALKIN, color: '#10B981', icon: <ShoppingBag /> },
        { name: 'Empresas', value: stats.by_type.COMPANY, color: '#F59E0B', icon: <Briefcase /> },
        { name: 'Individuos', value: stats.by_type.INDIVIDUAL, color: '#EC4899', icon: <UserCircle /> },
    ];

    const pieData = chartData.filter(d => d.value > 0);

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            <Toaster position="top-right" />
            
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Dashboard Comercial</h1>
                    <p className="text-slate-500 mt-1">Análisis de ingresos y comportamiento de ventas por segmento.</p>
                </div>
                <div className="bg-indigo-50 px-4 py-2 rounded-lg border border-indigo-100 flex items-center gap-2 text-indigo-700 font-medium">
                    <TrendingUp size={20} />
                    <span>Actualizado hoy</span>
                </div>
            </div>

            {/* Main KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <KPICard 
                    title="Ventas Totales" 
                    value={`$${stats.total_sales.toLocaleString()}`} 
                    subtitle={`${stats.total_count} Facturas Emitidas`}
                    icon={<DollarSign className="text-indigo-600" />}
                    trend="+12.5%"
                    color="indigo"
                />
                <KPICard 
                    title="Ticket Promedio" 
                    value={`$${stats.avg_ticket.toFixed(2)}`} 
                    subtitle="Valor medio por venta"
                    icon={<ArrowUpRight className="text-emerald-600" />}
                    trend="+4.2%"
                    color="emerald"
                />
                <KPICard 
                    title="Ventas Alumnos" 
                    value={`$${stats.by_type.STUDENT.toLocaleString()}`} 
                    subtitle={`${stats.counts_by_type.STUDENT} Pagos realizados`}
                    icon={<Users className="text-blue-600" />}
                    trend="+8.1%"
                    color="blue"
                />
                <KPICard 
                    title="Ventas Empresas" 
                    value={`$${stats.by_type.COMPANY.toLocaleString()}`} 
                    subtitle="Contratos corporativos"
                    icon={<Briefcase className="text-amber-600" />}
                    trend="+15.3%"
                    color="amber"
                />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Bar Chart: Sales by Segment */}
                <div className="lg:col-span-2 bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
                    <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                        <TrendingUp size={24} className="text-indigo-500" />
                        Distribución de Ingresos por Segmento
                    </h3>
                    <div className="h-[350px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 13 }} dy={10} />
                                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748B', fontSize: 13 }} tickFormatter={(val) => `$${val}`} />
                                <Tooltip 
                                    cursor={{ fill: '#F8FAFC' }}
                                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                    formatter={(value) => [`$${value.toLocaleString()}`, 'Ventas']}
                                />
                                <Bar dataKey="value" radius={[8, 8, 0, 0]} barSize={60}>
                                    {chartData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.9} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Pie Chart: Market Share */}
                <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 flex flex-col">
                    <h3 className="text-xl font-bold text-slate-800 mb-6 flex items-center gap-2">
                        Market Share
                    </h3>
                    <div className="flex-1 flex flex-col justify-center">
                        <div className="h-[250px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip 
                                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }}
                                        formatter={(value) => [`$${value.toLocaleString()}`, 'Total']}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                        <div className="mt-6 space-y-3">
                            {chartData.map((item, idx) => (
                                <div key={idx} className="flex justify-between items-center text-sm">
                                    <div className="flex items-center gap-2">
                                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                                        <span className="text-slate-600">{item.name}</span>
                                    </div>
                                    <span className="font-bold text-slate-800">
                                        {stats.total_sales > 0 ? ((item.value / stats.total_sales) * 100).toFixed(1) : 0}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Bottom Section: Mostrador Specifics */}
            <div className="bg-slate-900 rounded-2xl p-8 text-white overflow-hidden relative">
                <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                    <div>
                        <h4 className="text-indigo-400 font-bold uppercase tracking-widest text-sm mb-2">Segmento Mostrador</h4>
                        <h2 className="text-3xl font-bold mb-4">Potencial de Clientes Walk-in</h2>
                        <p className="text-slate-400 mb-6 max-w-md">
                            Los clientes de mostrador representan el {stats.total_sales > 0 ? ((stats.by_type.WALKIN / stats.total_sales) * 100).toFixed(1) : 0}% de tus ingresos totales. 
                            Este segmento tiene un ticket promedio de ${(stats.by_type.WALKIN / (stats.counts_by_type.WALKIN || 1)).toFixed(2)}.
                        </p>
                        <div className="flex gap-4">
                            <div className="bg-white/10 px-4 py-2 rounded-lg backdrop-blur-sm">
                                <p className="text-xs text-slate-400">Total Mostrador</p>
                                <p className="text-xl font-bold">${stats.by_type.WALKIN.toLocaleString()}</p>
                            </div>
                            <div className="bg-white/10 px-4 py-2 rounded-lg backdrop-blur-sm">
                                <p className="text-xs text-slate-400">Tickets</p>
                                <p className="text-xl font-bold">{stats.counts_by_type.WALKIN}</p>
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-center md:justify-end">
                        <div className="w-48 h-48 bg-indigo-600/20 rounded-full flex items-center justify-center animate-pulse">
                            <ShoppingBag size={80} className="text-indigo-400" />
                        </div>
                    </div>
                </div>
                {/* Decorative background circles */}
                <div className="absolute top-[-50px] right-[-50px] w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-[-50px] left-[-50px] w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl"></div>
            </div>
        </div>
    );
};

const KPICard = ({ title, value, subtitle, icon, trend, color }) => {
    const colors = {
        indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
        emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
        blue: 'bg-blue-50 text-blue-600 border-blue-100',
        amber: 'bg-amber-50 text-amber-600 border-amber-100',
    };

    return (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
                <div className={`p-3 rounded-xl border ${colors[color]}`}>
                    {React.cloneElement(icon, { size: 24 })}
                </div>
                <div className="flex items-center gap-1 text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full text-xs font-bold">
                    <TrendingUp size={12} />
                    {trend}
                </div>
            </div>
            <p className="text-slate-500 font-medium text-sm mb-1">{title}</p>
            <h4 className="text-2xl font-bold text-slate-800 mb-1">{value}</h4>
            <p className="text-xs text-slate-400">{subtitle}</p>
        </div>
    );
};

export default CommercialDashboard;
