import React, { useState, useEffect } from 'react';
import { 
    MonitorPlay, Search, BookOpen, Star, 
    ChevronRight, Play, Clock, Users,
    Trophy, Layout, Filter, Sparkles, Settings, ShieldCheck,
    Calendar as CalendarIcon
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../context/authStore';
import learningService from '../../services/learningService';

const CampusVirtualPage = () => {
    const navigate = useNavigate();
    const { user } = useAuthStore();
    const isAdminOrTeacher = ['ADMIN', 'RECTOR', 'TEACHER'].includes(user?.role);
    const [courses, setCourses] = useState([]);
    const [myEnrollments, setMyEnrollments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('marketplace'); // 'marketplace', 'my-courses'
    const [searchTerm, setSearchTerm] = useState('');
    const [filterCategory, setFilterCategory] = useState(''); // Filtro por Grado/Nivel

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [coursesData, enrollmentsData] = await Promise.all([
                learningService.getCourses(),
                learningService.getMyEnrollments()
            ]);
            setCourses(coursesData);
            setMyEnrollments(enrollmentsData);
        } catch (error) {
            console.error("Error fetching LMS data:", error);
        } finally {
            setLoading(false);
        }
    };

    // Lógica de Filtrado Local (React-Side)
    const filteredCourses = courses.filter(course => {
        const matchesSearch = course.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                             (course.subtitle && course.subtitle.toLowerCase().includes(searchTerm.toLowerCase()));
        
        const matchesCategory = filterCategory ? course.academic_course_name === filterCategory : true;
        
        return matchesSearch && matchesCategory;
    });

    // Extraer categorías únicas para el selector de filtros
    const availableCategories = [...new Set(courses.map(c => c.academic_course_name).filter(Boolean))].sort();

    const handleEnroll = async (courseId) => {
        try {
            await learningService.enrollInCourse(courseId);
            fetchData();
            setActiveTab('my-courses');
        } catch (error) {
            console.error("Enrollment failed:", error);
        }
    };

    const renderHeader = () => (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-8 lg:p-16 rounded-[2rem] lg:rounded-[4rem] shadow-2xl relative overflow-hidden mb-12 border border-white/5">
            <div className="relative z-10 max-w-3xl">
                <div className="flex items-center gap-4 mb-4 lg:mb-6">
                    <button 
                        onClick={() => navigate('/dashboard')}
                        className="px-4 py-2 bg-white/10 backdrop-blur-md rounded-full text-white text-[10px] lg:text-xs font-black uppercase tracking-widest border border-white/10 hover:bg-white/20 transition-all flex items-center gap-2"
                    >
                        <Layout size={14} />
                        <span>Volver al Dashboard</span>
                    </button>
                    <div className="h-4 w-px bg-white/10"></div>
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-500/10 backdrop-blur-md rounded-full text-indigo-400 text-[10px] lg:text-xs font-black uppercase tracking-widest border border-indigo-500/20">
                        <Sparkles size={14} />
                        <span>Plataforma de Aprendizaje Pro</span>
                    </div>
                </div>
                <h1 className="text-3xl md:text-5xl lg:text-7xl font-black text-white tracking-tighter mb-4 lg:mb-6 leading-none">
                    Campus Virtual <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Eduka360</span>
                </h1>
                <p className="text-indigo-100/60 text-base lg:text-xl mb-8 lg:mb-10 font-medium max-w-xl">
                    Impulsa tu carrera con cursos diseñados por expertos y potenciados por Inteligencia Artificial.
                </p>
                
                <div className="flex flex-col sm:flex-row flex-wrap gap-4">
                    <button 
                        onClick={() => setActiveTab('marketplace')}
                        className={`px-8 py-4 rounded-2xl font-black transition-all flex items-center gap-3 ${activeTab === 'marketplace' ? 'bg-white text-slate-950 shadow-xl scale-105' : 'bg-white/5 text-white hover:bg-white/10'}`}
                    >
                        <Layout size={20} />
                        Explorar Cursos
                    </button>
                    <button 
                        onClick={() => setActiveTab('my-courses')}
                        className={`px-8 py-4 rounded-2xl font-black transition-all flex items-center gap-3 ${activeTab === 'my-courses' ? 'bg-indigo-600 text-white shadow-xl scale-105 shadow-indigo-500/20' : 'bg-white/5 text-white hover:bg-white/10'}`}
                    >
                        <Trophy size={20} />
                        Mis Aprendizajes
                    </button>
                    
                    {isAdminOrTeacher && (
                        <button 
                            onClick={() => navigate('/dashboard/campus-virtual/instructor')}
                            className="px-8 py-4 bg-emerald-500/10 backdrop-blur-md text-emerald-400 rounded-2xl font-black border border-emerald-500/30 hover:bg-emerald-500/20 transition-all flex items-center gap-3"
                        >
                            <Settings size={20} />
                            Panel Instructor
                        </button>
                    )}

                    <button 
                        onClick={() => navigate('/dashboard/campus-virtual/calendario')}
                        className="px-8 py-4 bg-white/5 backdrop-blur-md text-white rounded-2xl font-black border border-white/10 hover:bg-white/10 transition-all flex items-center gap-3"
                    >
                        <CalendarIcon size={20} />
                        Cronograma
                    </button>
                </div>
            </div>
            
            <div className="absolute top-1/2 right-12 -translate-y-1/2 hidden xl:block">
                <div className="relative w-96 h-96">
                    <div className="absolute inset-0 bg-indigo-500/20 blur-[100px] rounded-full animate-pulse"></div>
                    <MonitorPlay size={400} className="text-white/5 rotate-12 absolute -right-20 -bottom-20" />
                </div>
            </div>
        </div>
    );

    const renderMarketplace = () => (
        <div className="space-y-12">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex-grow">
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-2">Cursos Disponibles</h2>
                    <p className="text-slate-400 font-medium">Filtra por materia o grado para encontrar tu aula.</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto">
                    {/* Selector de Grados */}
                    <div className="relative">
                        <Filter className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                        <select 
                            value={filterCategory}
                            onChange={(e) => setFilterCategory(e.target.value)}
                            className="pl-12 pr-4 py-4 bg-white border-2 border-slate-100 rounded-2xl text-slate-700 font-semibold focus:border-indigo-500 outline-none appearance-none cursor-pointer min-w-[200px]"
                        >
                            <option value="">Filtrar: Todos los Grados</option>
                            {availableCategories.map(cat => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>

                    {/* Buscador General */}
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors" size={20} />
                        <input 
                            type="text" 
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            placeholder="Buscar curso o tema..." 
                            className="w-full md:w-80 bg-white border-2 border-slate-100 rounded-2xl py-4 pl-12 pr-4 text-slate-700 placeholder:text-slate-400 focus:outline-none focus:border-indigo-500 transition-all font-semibold shadow-sm"
                        />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-10">
                {filteredCourses.map(course => (
                    <div key={course.id} className="group bg-white rounded-[2rem] lg:rounded-[3rem] overflow-hidden border border-slate-100 shadow-sm hover:shadow-2xl hover:-translate-y-2 transition-all">
                        <div className="h-56 relative overflow-hidden">
                            <img 
                                src={course.cover_image || 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2070&auto=format&fit=crop'} 
                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" 
                                alt={course.title} 
                            />
                            <div className="absolute top-6 right-6 px-4 py-2 bg-white/90 backdrop-blur-md rounded-xl font-black text-slate-950 shadow-lg">
                                {course.price > 0 ? `$${course.price}` : 'GRATIS'}
                            </div>
                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 to-transparent"></div>
                            {course.is_public && (
                                <div className="absolute bottom-6 left-6 px-3 py-1 bg-cyan-400 text-slate-950 text-[10px] font-black uppercase tracking-tighter rounded-full">
                                    Venta Pública
                                </div>
                            )}
                        </div>
                        <div className="p-6 lg:p-10">
                            <h3 className="text-xl lg:text-2xl font-black text-slate-900 mb-2 leading-tight group-hover:text-indigo-600 transition-colors uppercase tracking-tight">{course.title}</h3>
                            <p className="text-slate-400 text-sm font-medium line-clamp-2 mb-8">{course.subtitle || course.description}</p>
                            
                            <div className="flex items-center justify-between mb-8 border-y border-slate-50 py-4">
                                <div className="flex items-center gap-2">
                                    <Users size={16} className="text-slate-300" />
                                    <span className="text-xs font-bold text-slate-500">{course.enrollment_count || 0} alumnos</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <BookOpen size={16} className="text-slate-300" />
                                    <span className="text-xs font-bold text-slate-500">{course.modules?.length || 0} módulos</span>
                                </div>
                            </div>

                            <button 
                                onClick={() => handleEnroll(course.id)}
                                className="w-full py-4 bg-slate-900 text-white rounded-[1.5rem] font-black hover:bg-indigo-600 transition-all shadow-lg flex items-center justify-center gap-2"
                            >
                                Inscribirse Ahora
                                <ChevronRight size={18} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const renderMyCourses = () => (
        <div className="space-y-12">
            <div>
                <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-2">Mi Progreso</h2>
                <p className="text-slate-400 font-medium">Continúa donde lo dejaste y alcanza tus metas.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10">
                {myEnrollments.map(enrollment => (
                    <div key={enrollment.id} className="bg-white p-6 lg:p-8 rounded-[2rem] lg:rounded-[3.5rem] border border-slate-100 shadow-sm flex flex-col md:flex-row gap-8 items-center group hover:shadow-xl transition-all">
                        <div className="w-full md:w-40 h-48 md:h-40 rounded-[2rem] overflow-hidden flex-shrink-0 relative">
                            <img 
                                src={enrollment.course_cover || 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2070&auto=format&fit=crop'} 
                                className="w-full h-full object-cover" 
                                alt=""
                            />
                            <div className="absolute inset-0 bg-indigo-600/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                <Play size={40} className="text-white fill-white" />
                            </div>
                        </div>
                        <div className="flex-grow space-y-4 text-center md:text-left">
                            <h3 className="text-2xl font-black text-slate-900 leading-tight">{enrollment.course_title}</h3>
                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-xs font-bold uppercase tracking-widest">
                                    <span className="text-indigo-600">{enrollment.progress_percentage}% completado</span>
                                    <span className="text-slate-400">{enrollment.status}</span>
                                </div>
                                <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-1000" 
                                        style={{ width: `${enrollment.progress_percentage}%` }}
                                    ></div>
                                </div>
                            </div>
                            <button 
                                onClick={() => navigate(`/dashboard/campus-virtual/player/${enrollment.course}`)}
                                className="px-8 py-3 bg-indigo-50 text-indigo-600 rounded-2xl font-black hover:bg-indigo-600 hover:text-white transition-all inline-flex items-center gap-2"
                            >
                                Continuar Lección
                                <ChevronRight size={18} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
            
            {myEnrollments.length === 0 && (
                <div className="text-center py-20 bg-slate-50 rounded-[4rem] border-2 border-dashed border-slate-200">
                    <BookOpen size={64} className="text-slate-200 mx-auto mb-6" />
                    <h3 className="text-2xl font-bold text-slate-400 mb-2">Aún no te has inscrito en ningún curso</h3>
                    <button 
                        onClick={() => setActiveTab('marketplace')}
                        className="text-indigo-600 font-black hover:underline"
                    >
                        Explora el catálogo ahora
                    </button>
                </div>
            )}
        </div>
    );

    if (loading) return (
        <div className="flex items-center justify-center h-[50vh]">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600"></div>
        </div>
    );

    return (
        <div className="space-y-4 animate-fade-in pb-20">
            {renderHeader()}
            {activeTab === 'marketplace' ? renderMarketplace() : renderMyCourses()}
        </div>
    );
};

export default CampusVirtualPage;
