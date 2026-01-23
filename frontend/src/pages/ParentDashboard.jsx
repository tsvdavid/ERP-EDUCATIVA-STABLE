import React, { useState, useEffect } from 'react';
import { useAuthStore } from '../context/authStore';
import userService from '../services/userService';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';
import { Users, GraduationCap, Calendar, AlertTriangle, ChevronRight, Activity } from 'lucide-react';

const ParentDashboard = () => {
    const { user } = useAuthStore();
    const navigate = useNavigate();
    const [children, setChildren] = useState([]);
    const [selectedChild, setSelectedChild] = useState(null);
    const [stats, setStats] = useState({ average: 0, attendance: 0, alerts: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Load children from user profile (assuming populated in authStore or fetch fresh)
        // For now, we fetch the fresh user profile to get children
        const fetchChildren = async () => {
            try {
                // We need an endpoint to get "myself" with children populated
                // Or if user object already has children (from login/profile fetch)
                // Let's assume we can fetch user profile
                // Currently userService.getUsers() lists all users. 
                // Best way: use the ID from auth store to fetch specific user details if not fully populated
                if (user?.children && user.children.length > 0) {
                    setChildren(user.children);
                    setSelectedChild(user.children[0]);
                } else {
                    // Fallback if authStore doesn't have deep children data yet
                    // fetching /api/users/{id}/ might return it if serializer is set up
                    try {
                        const response = await api.get(`/users/${user.id}/`);
                        if (response.data.children) {
                            setChildren(response.data.children);
                            setSelectedChild(response.data.children[0]);
                        }
                    } catch (err) {
                        console.error("Error loading children", err);
                    }
                }
            } catch (error) {
                console.error("Error fetching data", error);
            } finally {
                setLoading(false);
            }
        };

        fetchChildren();
    }, [user.id]);

    useEffect(() => {
        if (selectedChild) {
            loadChildStats(selectedChild.id);
        }
    }, [selectedChild]);

    const loadChildStats = async (studentId) => {
        // In a real app, these would be aggregated endpoints.
        // For MVP, we fetch raw lists and calculate.
        try {
            const [gradesRes, attendanceRes] = await Promise.all([
                api.get(`/academic/grades/?student_id=${studentId}`),
                api.get(`/academic/attendance/?student_id=${studentId}`)
            ]);

            const grades = gradesRes.data;
            const attendance = attendanceRes.data;

            // Calculate Average
            const totalScore = grades.reduce((acc, curr) => acc + parseFloat(curr.score), 0);
            const average = grades.length ? (totalScore / grades.length).toFixed(1) : 0;

            // Calculate Attendance %
            const present = attendance.filter(a => a.status === 'PRESENT').length;
            const totalDays = attendance.length;
            const attendancePct = totalDays ? Math.round((present / totalDays) * 100) : 100;

            // Alerts (e.g. absent or low grade)
            // Simplified: any grade < 7 or absent status
            const alrts = grades.filter(g => parseFloat(g.score) < 7).length +
                attendance.filter(a => a.status === 'ABSENT').length;

            setStats({
                average,
                attendance: attendancePct,
                alerts: alrts
            });
        } catch (error) {
            console.error("Error loading stats", error);
        }
    };

    if (loading) return <div className="p-8 text-center">Cargando...</div>;

    if (!children.length) {
        return (
            <div className="p-8 text-center bg-white rounded-xl shadow-sm">
                <Users size={48} className="mx-auto text-slate-300 mb-4" />
                <h2 className="text-xl font-semibold text-slate-700">No hay estudiantes asociados</h2>
                <p className="text-slate-500">No se encontraron hijos asociados a su cuenta. Contacte a soporte.</p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Header / Child Selector */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Panel de Padres</h1>
                    <p className="text-slate-500">Resumen académico y bienestar</p>
                </div>

                {children.length > 1 && (
                    <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm border border-slate-200">
                        <Users size={18} className="text-indigo-600" />
                        <select
                            className="bg-transparent border-none text-slate-700 font-medium focus:ring-0"
                            value={selectedChild?.id || ''}
                            onChange={(e) => {
                                const child = children.find(c => c.id === parseInt(e.target.value));
                                setSelectedChild(child);
                            }}
                        >
                            {children.map(child => (
                                <option key={child.id} value={child.id}>{child.first_name} {child.last_name}</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>

            {/* Selected Child Content */}
            {selectedChild && (
                <>
                    {/* Stats Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
                            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
                                <GraduationCap size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Promedio General</p>
                                <h3 className="text-3xl font-bold text-slate-800">{stats.average}</h3>
                                <p className="text-xs text-slate-400">Escala 1-10</p>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${stats.attendance >= 80 ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                                <Calendar size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Asistencia Mensual</p>
                                <h3 className="text-3xl font-bold text-slate-800">{stats.attendance}%</h3>
                                <p className="text-xs text-slate-400">Días presentes</p>
                            </div>
                        </div>

                        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 flex items-center gap-4">
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${stats.alerts === 0 ? 'bg-indigo-100 text-indigo-600' : 'bg-amber-100 text-amber-600'}`}>
                                <AlertTriangle size={24} />
                            </div>
                            <div>
                                <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Alertas Activas</p>
                                <h3 className="text-3xl font-bold text-slate-800">{stats.alerts}</h3>
                                <p className="text-xs text-slate-400">Atención requerida</p>
                            </div>
                        </div>
                    </div>

                    {/* Quick Access / Activity */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Recent Activity (Placeholder) */}
                        <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="font-bold text-slate-700 flex items-center gap-2">
                                    <Activity size={20} className="text-indigo-500" /> Actividad Reciente
                                </h3>
                                <button className="text-indigo-600 text-sm font-medium hover:underline">Ver todo</button>
                            </div>
                            <div className="space-y-4">
                                <div className="flex items-start gap-3 pb-3 border-b border-slate-50 last:border-0 hover:bg-slate-50 p-2 rounded-lg transition-colors">
                                    <div className="w-2 h-2 mt-2 bg-green-500 rounded-full"></div>
                                    <div>
                                        <p className="text-sm font-medium text-slate-800">Asistencia registrada: Presente</p>
                                        <p className="text-xs text-slate-400">Hoy, 08:00 AM</p>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3 pb-3 border-b border-slate-50 last:border-0 hover:bg-slate-50 p-2 rounded-lg transition-colors">
                                    <div className="w-2 h-2 mt-2 bg-blue-500 rounded-full"></div>
                                    <div>
                                        <p className="text-sm font-medium text-slate-800">Nueva calificación en Matemáticas</p>
                                        <p className="text-xs text-slate-400">Ayer, 10:30 AM</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Navigation Actions */}
                        <div className="bg-indigo-900 rounded-xl shadow-lg p-6 text-white relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-10 -mt-10 blur-2xl"></div>

                            <h3 className="font-bold text-lg mb-2 relative z-10">Acciones Frecuentes</h3>
                            <div className="space-y-2 relative z-10 mt-6">
                                <button
                                    onClick={() => navigate(`/dashboard/parent/student/${selectedChild.id}`)}
                                    className="w-full bg-white/10 hover:bg-white/20 p-3 rounded-lg flex items-center justify-between transition-colors"
                                >
                                    <span className="font-medium">Ver Detalle Académico</span>
                                    <ChevronRight size={18} />
                                </button>
                                <button className="w-full bg-white/10 hover:bg-white/20 p-3 rounded-lg flex items-center justify-between transition-colors">
                                    <span className="font-medium">Enviar Mensaje a Docente</span>
                                    <ChevronRight size={18} />
                                </button>
                            </div>
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default ParentDashboard;
