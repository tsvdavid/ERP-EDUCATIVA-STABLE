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
    ArrowLeftRight,
    BarChart,
    LifeBuoy,
    ShieldCheck,
    Database,
    Wrench,
    FileCode,
    RefreshCw,
    Menu,
    X,
    Book,
    Lock,
    Link as LinkIcon,
    TrendingUp,
    Landmark,
    PieChart,
    Package,
    MonitorPlay,
    Library,
    Sparkles,
    Activity,
    HeartHandshake,
    ChevronDown, 
    ChevronRight
} from 'lucide-react';
import logoEduka360 from '../assets/logo-eduka360.jpg';

const DashboardLayout = () => {
    const { logout, user, activeInstitution, setActiveInstitution } = useAuthStore();
    const navigate = useNavigate();
    const location = useLocation();
    const { lastMessage } = useSocket();
    const [unreadCount, setUnreadCount] = useState(0);
    const [institutions, setInstitutions] = useState([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [expandedSections, setExpandedSections] = useState({ 'Principal': true });

    const toggleSection = (section) => {
        setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
    };

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
        { section: 'Principal', path: '/dashboard', label: 'Inicio', icon: LayoutDashboard, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT', 'ACCOUNTANT'] },
        { section: 'Principal', path: '/dashboard/institution', label: 'Instituciones', icon: Building, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] },
        { section: 'Principal', path: '/dashboard/users', label: 'Gestión Usuarios', icon: Settings, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] },
        { section: 'Principal', path: '/dashboard/teachers', label: 'Profesores', icon: UserCheck, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] },

        // Académico
        { section: 'Académico', path: '/dashboard/academic-years', label: 'Año Lectivo', icon: Calendar, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] },
        { section: 'Académico', path: '/dashboard/courses', label: 'Cursos', icon: GraduationCap, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] },
        { section: 'Académico', path: '/dashboard/subjects', label: 'Materias', icon: BookOpen, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/students', label: 'Estudiantes', icon: Users, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/attendance', label: 'Asistencia', icon: Calendar, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/grades', label: 'Calificaciones', icon: FileText, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/academic/reports', label: 'Estadísticas por Curso', icon: BarChart, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/academic/schedules-manager', label: 'Gestor de Horarios', icon: Calendar, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Académico', path: '/dashboard/academic/global-reports', label: 'Reportes Institucionales', icon: Award, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR'] },
        { section: 'Académico', path: '/dashboard/student-grades', label: 'Mis Notas', icon: Award, roles: ['STUDENT', 'PARENT'] },
        { section: 'Académico', path: '/dashboard/my-schedule', label: 'Mi Horario', icon: Calendar, roles: ['STUDENT', 'PARENT'] },
        { section: 'Académico', path: '/dashboard/communication', label: 'Comunicación', icon: MessageSquare, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT', 'ACCOUNTANT'] },
        { section: 'Académico', path: '/dashboard/parent', label: 'Mi Familia', icon: Users, roles: ['PARENT'] },
        
        // Portal Digital
        { section: 'Portal Digital', path: '/dashboard/campus-virtual', label: 'Campus Virtual', icon: MonitorPlay, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT'] },
        { section: 'Portal Digital', path: '/dashboard/campus-virtual/instructor', label: 'Panel Docente', icon: Settings, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Portal Digital', path: '/dashboard/recursos', label: 'Centro de Recursos', icon: Library, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT'] },

        // Administrativo
        { section: 'Administrativo', path: '/dashboard/procedures/templates', label: 'Plantillas de Trámites', icon: FileText, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'DECE', 'MEDICO'] },
        { section: 'Administrativo', path: '/dashboard/procedures/inbox', label: 'Bandeja de Solicitudes', icon: MessageSquare, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER'] },
        { section: 'Administrativo', path: '/dashboard/procedures/student', label: 'Mis Trámites', icon: FileText, roles: ['STUDENT', 'PARENT'] },
        { section: 'Administrativo', path: '/dashboard/my-account', label: 'Mi Cuenta', icon: DollarSign, roles: ['STUDENT', 'PARENT', 'ADMIN'] },

        // Salud y Bienestar
        { section: 'Salud y Bienestar', path: '/dashboard/health/medical-dispensary', label: 'Dispensario Médico', icon: Activity, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'MEDICO'] },
        { section: 'Salud y Bienestar', path: '/dashboard/health/dece', label: 'Panel DECE', icon: HeartHandshake, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'DECE'] },
        { section: 'Salud y Bienestar', path: '/dashboard/health/behavior-records', label: 'Registro Conductual', icon: FileText, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'DECE'] },
        { section: 'Salud y Bienestar', path: '/dashboard/health/my-health', label: 'Mi Perfil de Salud', icon: Activity, roles: ['STUDENT', 'PARENT'] },

        // ==========================
        // MÓDULO CONTABLE
        // ==========================

        // 1. Contabilidad (Core)
        { section: 'Módulo Contable', path: '/dashboard/accounting/dashboard', label: 'Dashboard Contable', icon: LayoutDashboard, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/accounts', label: 'Catálogo Contable', icon: Book, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/entries', label: 'Libro Diario', icon: BookOpen, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/ledger', label: 'Libro Mayor', icon: BarChart, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/reports', label: 'Estados Financieros', icon: TrendingUp, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/taxes', label: 'IVA y Tributos', icon: Landmark, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/coming-soon/bank-reconciliation', label: 'Conciliación Bancaria', icon: Building, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/assets', label: 'Activos Fijos', icon: Package, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/closing', label: 'Cierre Contable', icon: Lock, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/analysis', label: 'Análisis y Reportes', icon: PieChart, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/integrations', label: 'Integraciones', icon: LinkIcon, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Módulo Contable', path: '/dashboard/accounting/settings', label: 'Configuración / Seguridad', icon: Settings, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },

        // 2. Ventas
        { section: 'Ventas', path: '/dashboard/treasury/concepts', label: 'Gestión de Cajas', icon: DollarSign, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Ventas', path: '/dashboard/treasury/payments', label: 'Facturación', icon: ShoppingCart, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Ventas', path: '/dashboard/treasury/mass-billing', label: 'Facturación Masiva', icon: Users, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Ventas', path: '/dashboard/treasury/transfers', label: 'Verificar Transferencias', icon: UserCheck, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Ventas', path: '/dashboard/treasury/invoices', label: 'Facturación Electrónica', icon: FileText, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Ventas', path: '/dashboard/treasury/credit-notes', label: 'Notas de Crédito', icon: ArrowLeftRight, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Ventas', path: '/dashboard/treasury/debit-notes', label: 'Notas de Débito', icon: FileText, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },

        // 3. Compras
        { section: 'Compras', path: '/dashboard/purchases/suppliers', label: 'Proveedores (Compras)', icon: Users, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Compras', path: '/dashboard/purchases/invoices', label: 'Facturas de Compra', icon: FileText, roles: ['ADMIN', 'ACCOUNTANT'] },
        { section: 'Compras', path: '/dashboard/purchases/liquidations', label: 'Liquidaciones de Compra', icon: FileText, roles: ['ADMIN', 'ACCOUNTANT'] },
        { section: 'Compras', path: '/dashboard/purchases/credit-notes', label: 'Notas de Crédito (C)', icon: ArrowLeftRight, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },
        { section: 'Compras', path: '/dashboard/purchases/debit-notes', label: 'Notas de Débito (C)', icon: FileText, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT'] },

        // Mesa de Ayuda
        { section: 'Ayuda', path: '/dashboard/helpdesk/tickets', label: 'Mis Tickets', icon: LifeBuoy, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'PARENT', 'SECRETARY', 'ACCOUNTANT'] },
        { section: 'Ayuda', path: '/dashboard/helpdesk/agent', label: 'Consola Agente', icon: Users, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'SECRETARY'] },

        // Privacidad
        { section: 'Privacidad', path: '/dashboard/privacy/consents', label: 'Mis Datos', icon: ShieldCheck, roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT', 'ACCOUNTANT'] },

        // Mantenimiento
        { section: 'Mantenimiento', path: '/dashboard/maintenance/backup', label: 'Backup y Restauración', icon: Database, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/maintenance/users', label: 'Mant. Usuarios', icon: Wrench, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/maintenance/log', label: 'Revisión de Logs', icon: FileCode, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/maintenance/reset', label: 'Resetear Sistema', icon: RefreshCw, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/admin/payment-gateways', label: 'Config. Pagos', icon: Settings, roles: ['ADMIN'] },
        { section: 'Mantenimiento', path: '/dashboard/admin/ai-config', label: 'Config. Eduka AI', icon: Sparkles, roles: ['ADMIN'] },
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
        <div className="flex h-screen bg-slate-50 relative">
            {/* Mobile Sidebar Overlay */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-30 md:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar Responsive */}
            <aside className={`
                fixed inset-y-0 left-0 z-40
                w-72 bg-slate-900 text-white flex flex-col shadow-2xl transition-transform duration-300 ease-in-out
                md:relative md:translate-x-0
                ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            `}>
                <div className="p-6 flex flex-col items-center border-b border-slate-800">
                    <div className="w-48 h-16 flex items-center justify-center overflow-hidden">
                        <img src={logoEduka360} alt="Eduka360 Logo" className="w-full h-full object-contain" />
                    </div>
                    <div className="mt-2 text-center">
                        <p className="text-xs font-medium text-primary-400 tracking-widest uppercase">Panel de Gestión</p>
                    </div>
                    <button
                        className="ml-auto md:hidden text-slate-400 hover:text-white"
                        onClick={() => setIsSidebarOpen(false)}
                    >
                        <X size={24} />
                    </button>
                </div>

                <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
                    {Object.entries(groupedNavItems).map(([section, items]) => {
                        const isExpanded = expandedSections[section] || false;
                        return (
                        <div key={section} className="bg-slate-900/40 rounded-xl overflow-hidden border border-slate-800/50">
                            <button
                                onClick={() => toggleSection(section)}
                                className="w-full flex items-center justify-between px-4 py-3 text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-800/50 uppercase tracking-wider transition-colors focus:outline-none"
                            >
                                <span>{section}</span>
                                {isExpanded ? <ChevronDown size={16} className="text-slate-500" /> : <ChevronRight size={16} className="text-slate-600" />}
                            </button>
                            
                            {isExpanded && (
                            <div className="space-y-1 px-3 pb-3 pt-1">
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
                                            onClick={() => setIsSidebarOpen(false)} // Close on navigate (mobile)
                                        >
                                            <Icon size={20} className={active ? 'text-white' : 'text-slate-500 group-hover:text-white transition-colors'} />
                                            <span className="font-medium">{item.label}</span>
                                            {active && <div className="ml-auto w-1.5 h-1.5 bg-accent-yellow rounded-full shadow-[0_0_8px_rgba(250,204,21,0.6)]" />}
                                        </Link>
                                    );
                                })}
                            </div>
                            )}
                        </div>
                    )})}
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
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden w-full">
                <Toaster position="top-right" />
                {/* Modern Header */}
                <header className="h-16 md:h-20 bg-white border-b border-slate-100 flex items-center justify-between px-4 md:px-8 shadow-sm relative z-10">
                    {/* Mobile Toggle & Search */}
                    <div className="flex items-center gap-4 flex-1">
                        <button
                            className="p-2 -ml-2 text-slate-500 md:hidden hover:bg-slate-50 rounded-lg"
                            onClick={() => setIsSidebarOpen(true)}
                        >
                            <Menu size={24} />
                        </button>

                        <div className="hidden sm:flex items-center bg-slate-50 px-4 py-2 rounded-lg border border-slate-100 w-full max-w-md focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
                            <Search size={18} className="text-slate-400 mr-3" />
                            <input
                                type="text"
                                placeholder="Buscar..."
                                className="bg-transparent border-none focus:ring-0 text-sm w-full text-slate-600 placeholder:text-slate-400"
                            />
                        </div>
                    </div>

                    <div className="flex items-center gap-3 md:gap-6">

                        {/* Institution Selector for Admin - Mobile Optimized */}
                        {(user?.role === 'ADMIN' || user?.role === 'LOCAL_ADMIN') && institutions.length > 0 && (
                            <div className="relative hidden sm:block">
                                <Building size={16} className="absolute left-3 top-3 text-slate-400 pointer-events-none" />
                                <select
                                    className="pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600 focus:ring-2 focus:ring-indigo-100 outline-none appearance-none cursor-pointer hover:bg-slate-100 transition-colors max-w-[150px] md:max-w-xs truncate"
                                    value={activeInstitution || ""}
                                    onChange={handleInstitutionChange}
                                >
                                    <option value="">Todas</option>
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

                        <div className="flex items-center gap-3 pl-3 md:pl-6 border-l border-slate-100">
                            <div className="text-right hidden md:block">
                                <p className="text-sm font-semibold text-slate-800">{user?.username || 'Usuario'}</p>
                                <p className="text-xs text-slate-500 capitalize">
                                    {(() => {
                                        const roles = {
                                            'ADMIN': 'Administrador',
                                            'LOCAL_ADMIN': 'Administrador Local',
                                            'ACCOUNTANT': 'Contabilidad',
                                            'RECTOR': 'Rector',
                                            'TEACHER': 'Profesor',
                                            'STUDENT': 'Estudiante',
                                            'PARENT': 'Padre',
                                            'SECRETARY': 'Secretario/a',
                                            'DECE': 'DECE',
                                            'MEDICO': 'Médico'
                                        };
                                        return roles[user?.role] || user?.role || 'Admin';
                                    })()}
                                </p>
                            </div>
                            <div className="w-8 h-8 md:w-10 md:h-10 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white font-bold shadow-md ring-2 ring-white">
                                {user?.username?.charAt(0).toUpperCase()}
                            </div>
                        </div>
                    </div>
                </header>

                {/* Content Scrollable */}
                <main className="flex-1 overflow-y-auto bg-slate-50/50 p-4 md:p-8">
                    {/* Key forces remount on institution change to refresh data */}
                    <Outlet key={activeInstitution} />
                </main>
            </div>
        </div>
    );
};

export default DashboardLayout;
