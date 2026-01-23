import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../context/authStore';
import userService from '../services/userService';
import { useSocket } from '../context/SocketContext';
import communicationService from '../services/communicationService';
import { Toaster, toast } from 'react-hot-toast';
import {
    LogOut,
    LayoutDashboard,
    GraduationCap,
    BookOpen,
    Users,
    FileText,
    Settings,
    Bell,
    Search,
    MessageSquare,
    Building,
    Award,
    UserCheck,
    Calendar,
    DollarSign,
    ShoppingCart,
    FolderTree,
    BarChart,
    LifeBuoy,
    ShieldCheck,
    Database,
    Wrench,
    FileCode,
    RefreshCw
} from 'lucide-react';

const DashboardLayout = () => {
    const { logout, user, activeInstitution, setActiveInstitution } = useAuthStore();
    const navigate = useNavigate();
    const location = useLocation();
    const { lastMessage } = useSocket();
    const [unreadCount, setUnreadCount] = useState(0);
    const [institutions, setInstitutions] = useState([]);

    // Fetch institutions if Admin for Selector
    useEffect(() => {
        if (user?.role === 'ADMIN') {
            const fetchInstitutions = async () => {
                try {
                    const data = await userService.getInstitutions();
                    setInstitutions(data);
                } catch (error) {
                    console.error("Failed to fetch institutions");
                }
            };
            fetchInstitutions();
        }
    }, [user]);

    const handleInstitutionChange = (e) => {
        const value = e.target.value;
        const newInst = value === "" ? null : value;
        setActiveInstitution(newInst);
        window.location.reload(); // Force reload to Apply Header Context
    };

    useEffect(() => {
        // Fetch initial unread count
        const fetchNotifications = async () => {
            try {
                const notifs = await communicationService.getNotifications();
                setUnreadCount(notifs.filter(n => !n.is_read).length);
            } catch (error) {
                console.error("Error fetching notifications", error);
            }
        };
        fetchNotifications();
    }, []);

    useEffect(() => {
        if (lastMessage) {
            if (lastMessage.type === 'notification_message') {
                setUnreadCount(prev => prev + 1);
                toast.success(lastMessage.payload.title || 'Nueva notificación');
            }
        }
    }, [lastMessage]);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isActive = (path) => location.pathname === path;

    // Memoize nav items to avoid recreation on render
    const navItems = React.useMemo(() => [
        // Principal
        { section: 'Principal', path: '/dashboard', label: 'Inicio', icon: LayoutDashboard, roles: ['ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT'] },
        { section: 'Principal', path: '/dashboard/institution', label: 'Instituciones', icon: Building, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Principal', path: '/dashboard/users', label: 'Gestión Usuarios', icon: Settings, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Principal', path: '/dashboard/teachers', label: 'Profesores', icon: UserCheck, roles: ['ADMIN', 'RECTOR'] },

        // Académico
        { section: 'Académico', path: '/dashboard/academic-years', label: 'Año Lectivo', icon: Calendar, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Académico', path: '/dashboard/courses', label: 'Cursos', icon: GraduationCap, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Académico', path: '/dashboard/subjects', label: 'Materias', icon: BookOpen, roles: ['ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/students', label: 'Estudiantes', icon: Users, roles: ['ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/attendance', label: 'Asistencia', icon: Calendar, roles: ['ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/grades', label: 'Calificaciones', icon: FileText, roles: ['ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/student-grades', label: 'Mis Notas', icon: Award, roles: ['STUDENT', 'PARENT'] },
        { section: 'Académico', path: '/dashboard/communication', label: 'Comunicación', icon: MessageSquare, roles: ['ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT'] },
        { section: 'Académico', path: '/dashboard/parent', label: 'Mi Familia', icon: Users, roles: ['PARENT'] },

        // Contabilidad
        { section: 'Contabilidad', path: '/dashboard/treasury/concepts', label: 'Tesorería', icon: DollarSign, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Contabilidad', path: '/dashboard/treasury/payments', label: 'Caja', icon: ShoppingCart, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Contabilidad', path: '/dashboard/treasury/invoices', label: 'Facturación Electrónica', icon: FileText, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Contabilidad', path: '/dashboard/accounting/accounts', label: 'Plan de Cuentas', icon: FolderTree, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Contabilidad', path: '/dashboard/accounting/entries', label: 'Libro Diario', icon: BookOpen, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Contabilidad', path: '/dashboard/accounting/reports', label: 'Reportes Financieros', icon: BarChart, roles: ['ADMIN', 'RECTOR'] },

        // Compras
        { section: 'Compras', path: '/dashboard/purchases/suppliers', label: 'Proveedores', icon: Users, roles: ['ADMIN', 'RECTOR'] },
        { section: 'Compras', path: '/dashboard/purchases/invoices', label: 'Facturas Compra', icon: ShoppingCart, roles: ['ADMIN', 'RECTOR'] },


        // Mesa de Ayuda
        { section: 'Ayuda', path: '/dashboard/helpdesk/tickets', label: 'Mis Tickets', icon: LifeBuoy, roles: ['ADMIN', 'RECTOR', 'TEACHER', 'PARENT', 'SECRETARY'] },
        { section: 'Ayuda', path: '/dashboard/helpdesk/agent', label: 'Consola Agente', icon: Users, roles: ['ADMIN', 'RECTOR', 'SECRETARY'] },

        // Privacidad
        { section: 'Privacidad', path: '/dashboard/privacy/consents', label: 'Mis Datos', icon: ShieldCheck, roles: ['ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT'] },

        // Mantenimiento
        { section: 'Mantenimiento', path: '/dashboard/maintenance/backup', label: 'Backup y Restauración', icon: Database, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/maintenance/users', label: 'Mant. Usuarios', icon: Wrench, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/maintenance/log', label: 'Revisión de Logs', icon: FileCode, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/maintenance/reset', label: 'Resetear Sistema', icon: RefreshCw, roles: ['ADMIN'] },
    ], []);

    const groupedNavItems = React.useMemo(() => {
        const filtered = navItems.filter(item => {
            if (!user) return false;
            return item.roles.includes(user.role);
        });

        return filtered.reduce((acc, item) => {
            const section = item.section || 'General';
            if (!acc[section]) acc[section] = [];
            acc[section].push(item);
            return acc;
        }, {});
    }, [user, navItems]);

    return (
        <div className="flex h-screen bg-slate-50">
            {/* Sidebar Moderno */}
            <aside className="w-72 bg-slate-900 text-white flex flex-col shadow-2xl relative z-20">
                <div className="p-6 flex items-center gap-3 border-b border-slate-800">
                    <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
                        <GraduationCap size={24} className="text-white" />
                    </div>
                    <div>
                        <h1 className="font-bold text-xl tracking-wide">EduERP</h1>
                        <p className="text-xs text-slate-400">Panel de Gestión</p>
                    </div>
                </div>

                <nav className="flex-1 px-4 py-6 space-y-6 overflow-y-auto">
                    {Object.entries(groupedNavItems).map(([section, items]) => (
                        <div key={section}>
                            <p className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{section}</p>
                            <div className="space-y-1">
                                {items.map((item) => {
                                    const Icon = item.icon;
                                    const active = isActive(item.path);
                                    return (
                                        <Link
                                            key={item.path}
                                            to={item.path}
                                            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group ${active
                                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/50'
                                                : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                                }`}
                                        >
                                            <Icon size={20} className={active ? 'text-white' : 'text-slate-500 group-hover:text-white transition-colors'} />
                                            <span className="font-medium">{item.label}</span>
                                            {active && <div className="ml-auto w-1.5 h-1.5 bg-white rounded-full" />}
                                        </Link>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </nav>

                <div className="p-4 border-t border-slate-800">
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 w-full px-4 py-3 text-slate-400 hover:bg-red-500/10 hover:text-red-400 rounded-xl transition-all duration-200 group"
                    >
                        <LogOut size={20} className="group-hover:text-red-400" />
                        <span className="font-medium">Cerrar Sesión</span>
                    </button>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                <Toaster position="top-right" />
                {/* Modern Header */}
                <header className="h-20 bg-white border-b border-slate-100 flex items-center justify-between px-8 shadow-sm relative z-10">
                    {/* Search Bar */}
                    <div className="flex items-center bg-slate-50 px-4 py-2 rounded-lg border border-slate-100 w-96 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
                        <Search size={18} className="text-slate-400 mr-3" />
                        <input
                            type="text"
                            placeholder="Buscar cursos, estudiantes..."
                            className="bg-transparent border-none focus:ring-0 text-sm w-full text-slate-600 placeholder:text-slate-400"
                        />
                    </div>

                    <div className="flex items-center gap-6">

                        {/* Institution Selector for Admin */}
                        {user?.role === 'ADMIN' && institutions.length > 0 && (
                            <div className="relative">
                                <Building size={16} className="absolute left-3 top-3 text-slate-400 pointer-events-none" />
                                <select
                                    className="pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600 focus:ring-2 focus:ring-indigo-100 outline-none appearance-none cursor-pointer hover:bg-slate-100 transition-colors"
                                    value={activeInstitution || ""}
                                    onChange={handleInstitutionChange}
                                >
                                    <option value="">Todas las Instituciones</option>
                                    {institutions.map(inst => (
                                        <option key={inst.id} value={inst.id}>{inst.name}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        <Link to={user?.role === 'STUDENT' ? "/dashboard/communication?tab=notices" : "/dashboard/communication"} className="relative p-2 text-slate-400 hover:bg-slate-50 rounded-full transition-colors">
                            <Bell size={20} />
                            {unreadCount > 0 && (
                                <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
                            )}
                        </Link>

                        <div className="flex items-center gap-3 pl-6 border-l border-slate-100">
                            <div className="text-right hidden md:block">
                                <p className="text-sm font-semibold text-slate-800">{user?.username || 'Usuario'}</p>
                                <p className="text-xs text-slate-500 capitalize">
                                    {(() => {
                                        const roles = {
                                            'ADMIN': 'Administrador',
                                            'RECTOR': 'Rector',
                                            'TEACHER': 'Profesor',
                                            'STUDENT': 'Estudiante',
                                            'PARENT': 'Padre',
                                            'SECRETARY': 'Secretario/a'
                                        };
                                        return roles[user?.role] || user?.role || 'Admin';
                                    })()}
                                </p>
                            </div>
                            <div className="w-10 h-10 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold shadow-md ring-2 ring-white">
                                {user?.username?.charAt(0).toUpperCase()}
                            </div>
                        </div>
                    </div>
                </header>

                {/* Content Scrollable */}
                <main className="flex-1 overflow-y-auto bg-slate-50/50 p-8">
                    {/* Key forces remount on institution change to refresh data */}
                    <Outlet key={activeInstitution} />
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
