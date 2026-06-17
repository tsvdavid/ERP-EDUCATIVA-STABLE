import React from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../context/authStore';
import { 
    GraduationCap, MonitorPlay, FileText, 
    HeartHandshake, Landmark, ShoppingCart, Users, LifeBuoy
} from 'lucide-react';
import logoEduka360 from '../assets/logo-eduka360.jpg';

const MODULES = [
    {
        id: 'academico',
        title: 'Académico',
        description: 'Gestión de clases, horarios y calificaciones.',
        icon: GraduationCap,
        path: '/dashboard/courses',
        color: 'from-primary-500 to-primary-700',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER']
    },
    {
        id: 'academico-student',
        title: 'Mi Academia',
        description: 'Consulta tus notas, horarios y progreso.',
        icon: GraduationCap,
        path: '/dashboard/student-grades',
        color: 'from-primary-500 to-primary-700',
        roles: ['STUDENT', 'PARENT']
    },
    {
        id: 'portal',
        title: 'Portal Digital',
        description: 'Accede a clases virtuales y recursos.',
        icon: MonitorPlay,
        path: '/dashboard/campus-virtual',
        color: 'from-indigo-500 to-indigo-700',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'STUDENT', 'PARENT']
    },
    {
        id: 'admin',
        title: 'Trámites',
        description: 'Bandeja de gestión y solicitudes online.',
        icon: FileText,
        path: '/dashboard/procedures/inbox',
        color: 'from-blue-500 to-blue-700',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER']
    },
    {
        id: 'admin-student',
        title: 'Mis Trámites',
        description: 'Solicita y descarga certificados.',
        icon: FileText,
        path: '/dashboard/procedures/student',
        color: 'from-blue-500 to-blue-700',
        roles: ['STUDENT', 'PARENT']
    },
    {
        id: 'health',
        title: 'Salud y Bienestar',
        description: 'Dispensario médico y control DECE.',
        icon: HeartHandshake,
        path: '/dashboard/health/medical-dispensary',
        color: 'from-emerald-500 to-teal-700',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER']
    },
    {
        id: 'health-student',
        title: 'Mi Salud',
        description: 'Accede a tu ficha médica y seguimientos.',
        icon: HeartHandshake,
        path: '/dashboard/health/my-health',
        color: 'from-emerald-500 to-teal-700',
        roles: ['STUDENT', 'PARENT']
    },
    {
        id: 'accounting',
        title: 'Módulo Contable',
        description: 'Libros, balances y gestión financiera.',
        icon: Landmark,
        path: '/dashboard/accounting/dashboard',
        color: 'from-slate-700 to-slate-900',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']
    },
    {
        id: 'treasury',
        title: 'Ventas y Tesorería',
        description: 'Facturación, cobros y comprobantes.',
        icon: ShoppingCart,
        path: '/dashboard/treasury/concepts',
        color: 'from-violet-500 to-violet-700',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']
    },
    {
        id: 'purchases',
        title: 'Compras',
        description: 'Proveedores, gastos y liquidaciones.',
        icon: Users,
        path: '/dashboard/purchases/suppliers',
        color: 'from-cyan-600 to-cyan-800',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']
    },
    {
        id: 'helpdesk',
        title: 'Mesa de Ayuda',
        description: 'Soporte técnico e incidentes.',
        icon: LifeBuoy,
        path: '/dashboard/helpdesk/tickets',
        color: 'from-orange-500 to-orange-700',
        roles: ['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'TEACHER', 'PARENT', 'SECRETARY', 'ACCOUNTANT']
    }
];

const DashboardHome = () => {
    const { user } = useAuthStore();

    const allowedModules =
    user?.role === 'GLOBAL' || user?.is_superuser
        ? MODULES
        : MODULES.filter(
              m => m.roles.includes(user?.role)
          );

    return (
        <div className="p-4 md:p-8 max-w-7xl mx-auto w-full animate-fade-in">
            {/* Logo Central */}
            <div className="flex justify-center mb-8">
                <div className="w-64 bg-white p-5 rounded-3xl shadow-md border border-slate-100 flex items-center justify-center">
                     <img src={logoEduka360} alt="Eduka360 Logo" className="w-full h-auto object-contain" />
                </div>
            </div>

            {/* Cabecera Interactiva */}
            <div className="mb-12 flex flex-col items-center justify-center relative bg-white/50 p-6 md:p-8 rounded-3xl border border-slate-100 backdrop-blur-sm min-h-[120px]">
                <div className="text-center z-10">
                    <h1 className="text-3xl md:text-4xl font-bold text-slate-800 tracking-tight">¡Bienvenido a Eduka360!</h1>
                    <p className="text-slate-500 text-lg mt-2 font-medium">Selecciona un panel para comenzar a trabajar.</p>
                </div>
                
                <div className="flex flex-row gap-3 mt-6 md:mt-0 md:absolute md:right-8 md:top-1/2 md:-translate-y-1/2 z-20">
                    <div className="p-3 px-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Estado</p>
                        <p className="text-sm text-emerald-500 font-bold flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> En Línea</p>
                    </div>
                    <div className="p-3 px-5 rounded-xl bg-white border border-slate-200 shadow-sm flex flex-col items-center justify-center text-center hover:shadow-md transition-shadow">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-0.5">Perfil</p>
                        <p className="text-sm text-primary-600 font-bold max-w-[100px] truncate">
                            {(() => {
                                const r = user?.role;
                                const m = { 'ADMIN': 'Administrador', 'LOCAL_ADMIN': 'Administrador', 'RECTOR': 'Rector', 'TEACHER': 'Profesor', 'STUDENT': 'Estudiante', 'PARENT': 'Representante', 'ACCOUNTANT': 'Contador', 'SECRETARY': 'Secretaría' };
                                return m[r] || r || 'Usuario';
                            })()}
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {allowedModules.map((module) => {
                    const Icon = module.icon;
                    return (
                        <Link 
                            key={module.id} 
                            to={module.path}
                            className="group relative bg-white rounded-3xl p-6 shadow-sm hover:shadow-2xl hover:shadow-primary-500/20 border border-slate-100 transition-all duration-300 transform hover:-translate-y-2 overflow-hidden flex flex-col h-full"
                        >
                            {/* Decorative background shape */}
                            <div className={`absolute -right-8 -top-8 w-32 h-32 rounded-full bg-gradient-to-br ${module.color} opacity-10 group-hover:opacity-20 transition-opacity duration-500 pointer-events-none blur-2xl`}></div>
                            
                            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${module.color} text-white flex items-center justify-center shadow-lg mb-5 transform group-hover:scale-110 transition-transform duration-300`}>
                                <Icon size={28} strokeWidth={1.5} />
                            </div>
                            
                            <h3 className="text-xl font-bold text-slate-800 mb-2 group-hover:text-primary-600 transition-colors">{module.title}</h3>
                            <p className="text-slate-500 text-sm leading-relaxed flex-1">{module.description}</p>
                            
                            <div className="mt-6 flex items-center text-sm font-semibold text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-4 group-hover:translate-x-0 duration-300">
                                Abrir Módulo <span className="ml-2">→</span>
                            </div>
                        </Link>
                    )
                })}
            </div>
            
            {/* Los stats inferiores fueron movidos a la cabecera principal */}
        </div>
    );
};

export default DashboardHome;
