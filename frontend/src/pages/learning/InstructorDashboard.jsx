import React, { useState, useEffect } from 'react';
import { 
    Plus, Edit, Trash2, BookOpen, 
    Users, DollarSign, Settings, Save,
    X, ChevronRight, Layout, BarChart3,
    Video, FileText, Link, ChevronDown, 
    ChevronUp, MoreVertical, CheckCircle2,
    Calendar, Trophy, HelpCircle
} from 'lucide-react';
import learningService from '../../services/learningService';

const InstructorDashboard = () => {
    const [courses, setCourses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [editingCourse, setEditingCourse] = useState(null);
    const [newCourse, setNewCourse] = useState({
        title: '',
        subtitle: '',
        description: '',
        price: 0,
        is_public: false,
        is_active: true
    });
    const [managingCourse, setManagingCourse] = useState(null);
    const [activeModule, setActiveModule] = useState(null);
    const [activeTab, setActiveTab] = useState('content');
    const [quizData, setQuizData] = useState({ title: '', questions: [], passing_score: 70 });

    useEffect(() => {
        fetchCourses();
    }, []);

    const fetchCourses = async () => {
        try {
            setLoading(true);
            const data = await learningService.getCourses();
            setCourses(data);
        } catch (error) {
            console.error("Error fetching instructor courses:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveCourse = async () => {
        try {
            if (editingCourse) {
                await learningService.updateCourse(editingCourse.id, newCourse);
            } else {
                await learningService.createCourse(newCourse);
            }
            setIsCreating(false);
            setEditingCourse(null);
            setNewCourse({ title: '', subtitle: '', description: '', price: 0, is_public: false, is_active: true });
            fetchCourses();
        } catch (error) {
            console.error("Error saving course:", error);
        }
    };

    const handleDeleteCourse = async (id) => {
        if (window.confirm('¿Estás seguro de que deseas eliminar este curso? Esta acción no se puede deshacer.')) {
            try {
                await learningService.deleteCourse(id);
                fetchCourses();
            } catch (error) {
                console.error("Error deleting course:", error);
            }
        }
    };
    
    const [editingLesson, setEditingLesson] = useState(null);
    const [isAddingLesson, setIsAddingLesson] = useState(false);

    const handleAddModule = async () => {
        const title = prompt('Título del nuevo módulo:');
        if (!title) return;
        try {
            await learningService.createModule({
                course: managingCourse.id,
                title,
                order: (managingCourse.modules?.length || 0) + 1
            });
            const updated = await learningService.getCourse(managingCourse.id);
            setManagingCourse(updated);
            fetchCourses();
        } catch (error) {
            console.error("Error adding module:", error);
        }
    };

    const handleSaveLesson = async (lessonData) => {
        try {
            if (editingLesson) {
                await learningService.updateLesson(editingLesson.id, lessonData);
            } else {
                await learningService.createLesson({
                    ...lessonData,
                    module: activeModule.id,
                    order: (activeModule.lessons?.length || 0) + 1
                });
            }
            const updated = await learningService.getCourse(managingCourse.id);
            setManagingCourse(updated);
            const updatedModule = updated.modules.find(m => m.id === activeModule.id);
            setActiveModule(updatedModule);
            setEditingLesson(null);
            setIsAddingLesson(false);
        } catch (error) {
            console.error("Error saving lesson:", error);
        }
    };

    const handleUploadResource = async (lessonId, file) => {
        const formData = new FormData();
        formData.append('lesson', lessonId);
        formData.append('file', file);
        formData.append('title', file.name);
        try {
            await learningService.addResource(formData);
            const updated = await learningService.getCourse(managingCourse.id);
            setManagingCourse(updated);
            if (activeModule) {
                setActiveModule(updated.modules.find(m => m.id === activeModule.id));
            }
        } catch (error) {
            console.error("Error uploading resource:", error);
        }
    };

    const handleSaveQuiz = async () => {
        try {
            const data = {
                ...quizData,
                module: activeModule.id
            };
            if (activeModule.quiz) {
                await learningService.updateQuiz(activeModule.quiz.id, data);
            } else {
                await learningService.createQuiz(data);
            }
            const updated = await learningService.getCourse(managingCourse.id);
            setManagingCourse(updated);
            setActiveModule(updated.modules.find(m => m.id === activeModule.id));
            alert('Quiz guardado exitosamente');
        } catch (error) {
            console.error("Error saving quiz:", error);
        }
    };

    if (loading) return <div className="p-20 text-center">Cargando panel de instructor...</div>;

    return (
        <div className="p-4 lg:p-12 space-y-8 lg:space-y-12 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-3xl lg:text-4xl font-black text-slate-900 tracking-tight mb-2">Panel del Instructor</h1>
                    <p className="text-slate-400 text-sm lg:text-base font-medium">Gestiona tus cursos y módulos.</p>
                </div>
                <button 
                    onClick={() => setIsCreating(true)}
                    className="px-8 py-4 bg-indigo-600 text-white rounded-[1.5rem] font-black shadow-xl hover:bg-slate-900 transition-all flex items-center gap-3 scale-105"
                >
                    <Plus size={20} />
                    Crear Nuevo Curso
                </button>
            </div>

            {/* Stats Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 lg:gap-8">
                <div className="bg-white p-6 lg:p-8 rounded-[2rem] lg:rounded-[3rem] border border-slate-100 shadow-sm">
                    <div className="w-10 h-10 lg:w-12 lg:h-12 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 mb-6">
                        <BookOpen size={20} />
                    </div>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Cursos</p>
                    <h3 className="text-2xl lg:text-3xl font-black text-slate-900">{courses.length}</h3>
                </div>
                <div className="bg-white p-6 lg:p-8 rounded-[2rem] lg:rounded-[3rem] border border-slate-100 shadow-sm">
                    <div className="w-10 h-10 lg:w-12 lg:h-12 bg-emerald-50 rounded-2xl flex items-center justify-center text-emerald-600 mb-6">
                        <Users size={20} />
                    </div>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Alumnos</p>
                    <h3 className="text-2xl lg:text-3xl font-black text-slate-900">
                        {courses.reduce((acc, c) => acc + (c.enrollment_count || 0), 0)}
                    </h3>
                </div>
                <div className="bg-white p-6 lg:p-8 rounded-[2rem] lg:rounded-[3rem] border border-slate-100 shadow-sm">
                    <div className="w-10 h-10 lg:w-12 lg:h-12 bg-amber-50 rounded-2xl flex items-center justify-center text-amber-600 mb-6">
                        <DollarSign size={20} />
                    </div>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-1">Ingresos</p>
                    <h3 className="text-2xl lg:text-3xl font-black text-slate-900">$0.00</h3>
                </div>
            </div>

            {/* Courses List */}
            <div className="bg-white rounded-[4rem] border border-slate-100 shadow-sm overflow-hidden">
                <div className="p-10 border-b border-slate-50 flex items-center justify-between">
                    <h2 className="text-2xl font-black text-slate-900 tracking-tight">Mis Cursos</h2>
                    <div className="flex bg-slate-50 p-1.5 rounded-2xl">
                        <button className="px-6 py-2 bg-white rounded-xl shadow-sm text-sm font-black text-indigo-600">Activos</button>
                        <button className="px-6 py-2 text-sm font-bold text-slate-400">Borradores</button>
                    </div>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-slate-50/50">
                            <tr>
                                <th className="px-10 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Curso</th>
                                <th className="px-10 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Precio / Visibilidad</th>
                                <th className="px-10 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Inscritos</th>
                                <th className="px-10 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                            {courses.map(course => (
                                <tr key={course.id} className="hover:bg-slate-50/50 transition-colors">
                                    <td className="px-6 lg:px-10 py-6 lg:py-8">
                                        <div className="flex items-center gap-3 lg:gap-4">
                                            <div className="w-12 h-12 lg:w-16 lg:h-16 rounded-xl lg:rounded-2xl overflow-hidden bg-slate-100 flex-shrink-0">
                                                <img src={course.cover_image || 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=2070&auto=format&fit=crop'} className="w-full h-full object-cover" alt="" />
                                            </div>
                                            <div>
                                                <p className="font-black text-slate-900 text-sm lg:text-lg leading-tight line-clamp-1">{course.title}</p>
                                                <p className="text-slate-400 text-[10px] lg:text-sm font-medium">{course.modules?.length || 0} módulos</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-10 py-8">
                                        <div className="space-y-1">
                                            <span className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-lg text-[10px] font-black uppercase tracking-tight">
                                                {course.price > 0 ? `$${course.price}` : 'GRATIS'}
                                            </span>
                                            <div className="flex items-center gap-1.5 pt-1">
                                                <div className={`w-2 h-2 rounded-full ${course.is_public ? 'bg-emerald-500' : 'bg-slate-300'}`}></div>
                                                <span className="text-[10px] font-black text-slate-400 uppercase tracking-tighter">
                                                    {course.is_public ? 'Público (Commercial)' : 'Solo Institución'}
                                                </span>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-10 py-8">
                                        <div className="flex items-center gap-2">
                                            <Users size={16} className="text-slate-300" />
                                            <span className="font-black text-slate-700">{course.enrollment_count || 0}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 lg:px-10 py-6 lg:py-8">
                                        <div className="flex items-center gap-2 lg:gap-3">
                                            <button 
                                                onClick={() => {
                                                    setEditingCourse(course);
                                                    setNewCourse({ ...course });
                                                    setIsCreating(true);
                                                }}
                                                className="p-2 lg:p-3 bg-white border border-slate-100 rounded-xl lg:rounded-2xl text-slate-400 hover:text-indigo-600 shadow-sm"
                                            >
                                                <Edit size={16} />
                                            </button>
                                            <button 
                                                onClick={() => handleDeleteCourse(course.id)}
                                                className="p-2 lg:p-3 bg-white border border-slate-100 rounded-xl lg:rounded-2xl text-slate-400 hover:text-red-600 shadow-sm"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                            <button 
                                                onClick={() => setManagingCourse(course)}
                                                className="px-4 lg:px-6 py-2 lg:py-3 bg-slate-900 text-white rounded-xl lg:rounded-2xl font-black text-[10px] lg:text-xs hover:bg-indigo-600 transition-all"
                                            >
                                                Módulos
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Course Content Manager Modal */}
            {managingCourse && (
                <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xl flex items-center justify-center z-[250] p-4 lg:p-12">
                    <div className="bg-white w-full h-full max-w-7xl rounded-[2.5rem] lg:rounded-[4rem] shadow-2xl overflow-hidden flex flex-col lg:flex-row animate-zoom-in">
                        {/* Sidebar: Modules */}
                        <div className="w-full lg:w-80 bg-slate-50 border-r border-slate-100 flex flex-col">
                            <div className="p-6 lg:p-8 border-b border-slate-100 flex items-center justify-between bg-white">
                                <h3 className="font-black text-slate-900 tracking-tight">Estructura</h3>
                                <button onClick={handleAddModule} className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-slate-900 transition-all">
                                    <Plus size={16} />
                                </button>
                            </div>
                            <div className="flex-grow overflow-y-auto p-4 lg:p-6 space-y-3">
                                {managingCourse.modules?.map((module, idx) => (
                                    <button 
                                        key={module.id}
                                        onClick={() => setActiveModule(module)}
                                        className={`w-full text-left p-4 rounded-2xl transition-all flex items-center justify-between group ${activeModule?.id === module.id ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200' : 'bg-white text-slate-600 hover:bg-indigo-50'}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <span className="text-[10px] font-black opacity-50">{idx + 1}</span>
                                            <span className="font-bold text-sm lg:text-base line-clamp-1">{module.title}</span>
                                        </div>
                                        <ChevronRight size={16} className={activeModule?.id === module.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-50'} />
                                    </button>
                                ))}
                            </div>
                            <div className="p-6 lg:p-8 border-t border-slate-100 bg-white">
                                <button 
                                    onClick={() => { setManagingCourse(null); setActiveModule(null); }}
                                    className="w-full py-4 bg-slate-100 text-slate-500 rounded-2xl font-black hover:bg-slate-200 transition-all flex items-center justify-center gap-2"
                                >
                                    <X size={18} /> Cerrar Editor
                                </button>
                            </div>
                        </div>

                        {/* Content Area: Lessons & Quizzes */}
                        <div className="flex-grow flex flex-col overflow-hidden bg-white">
                            {activeModule ? (
                                <>
                                    <div className="p-6 lg:p-10 border-b border-slate-50 flex items-center justify-between bg-white/50 backdrop-blur-sm sticky top-0 z-10">
                                        <div>
                                            <div className="flex items-center gap-3 mb-1">
                                                <div className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-[10px] font-black rounded-md uppercase tracking-wider">Módulo {managingCourse.modules?.findIndex(m => m.id === activeModule.id) + 1}</div>
                                                <h2 className="text-xl lg:text-2xl font-black text-slate-900 tracking-tight">{activeModule.title}</h2>
                                            </div>
                                            <p className="text-slate-400 text-xs font-medium">Gestiona lecciones, recursos y evaluaciones.</p>
                                        </div>
                                        <div className="flex bg-slate-100 p-1 rounded-xl shadow-inner border border-slate-200/50">
                                            <button 
                                                onClick={() => setActiveTab('content')}
                                                className={`px-6 py-2 rounded-lg text-xs font-black transition-all ${activeTab === 'content' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                                            >
                                                Contenido
                                            </button>
                                            <button 
                                                onClick={() => {
                                                    setActiveTab('quiz');
                                                    if (activeModule.quiz) {
                                                        setQuizData(activeModule.quiz);
                                                    } else {
                                                        setQuizData({ title: `Quiz: ${activeModule.title}`, questions: [], passing_score: 70 });
                                                    }
                                                }}
                                                className={`px-6 py-2 rounded-lg text-xs font-black transition-all ${activeTab === 'quiz' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                                            >
                                                Quiz
                                            </button>
                                        </div>
                                    </div>

                                    <div className="flex-grow overflow-y-auto p-6 lg:p-10 space-y-8 custom-scrollbar bg-slate-50/30">
                                        {activeTab === 'content' ? (
                                            /* Lessons Section */
                                            <div className="space-y-6">
                                                <div className="flex items-center justify-between">
                                                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Lecciones del Módulo</h4>
                                                    <button 
                                                        onClick={() => setIsAddingLesson(true)}
                                                        className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-indigo-600 font-black text-[10px] flex items-center gap-2 hover:bg-indigo-50 transition-all shadow-sm"
                                                    >
                                                        <Plus size={14} /> Nueva Lección
                                                    </button>
                                                </div>

                                                <div className="grid grid-cols-1 gap-4">
                                                    {activeModule.lessons?.map((lesson, idx) => (
                                                        <div key={lesson.id} className="bg-white rounded-3xl p-6 border border-slate-100 group transition-all hover:shadow-2xl hover:shadow-indigo-100/30 hover:border-indigo-100">
                                                            <div className="flex items-center justify-between mb-4">
                                                                <div className="flex items-center gap-4">
                                                                    <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 font-black text-sm">
                                                                        {idx + 1}
                                                                    </div>
                                                                    <div>
                                                                        <p className="font-black text-slate-900 text-lg leading-tight">{lesson.title}</p>
                                                                        <div className="flex items-center gap-3 mt-1.5">
                                                                            {lesson.video_url ? (
                                                                                <span className="flex items-center gap-1.5 text-[10px] font-black text-indigo-500 uppercase bg-indigo-50/50 px-2 py-0.5 rounded-md"><Video size={12}/> Video</span>
                                                                            ) : (
                                                                                <span className="flex items-center gap-1.5 text-[10px] font-black text-slate-300 uppercase"><Video size={12}/> Sin Video</span>
                                                                            )}
                                                                            {lesson.resources?.length > 0 ? (
                                                                                <span className="flex items-center gap-1.5 text-[10px] font-black text-emerald-500 uppercase bg-emerald-50/50 px-2 py-0.5 rounded-md"><FileText size={12}/> {lesson.resources.length} Archivos</span>
                                                                            ) : (
                                                                                <span className="flex items-center gap-1.5 text-[10px] font-black text-slate-300 uppercase"><FileText size={12}/> Sin PDF</span>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all">
                                                                    <button onClick={() => setEditingLesson(lesson)} className="p-3 bg-slate-50 text-slate-400 hover:text-indigo-600 rounded-xl transition-all"><Edit size={18}/></button>
                                                                    <button className="p-3 bg-slate-50 text-slate-400 hover:text-red-500 rounded-xl transition-all"><Trash2 size={18}/></button>
                                                                </div>
                                                            </div>
                                                            
                                                            {/* Resource Quick Upload */}
                                                            <div className="flex items-center gap-3 pt-5 border-t border-slate-50">
                                                                <label className="flex-grow cursor-pointer group/upload">
                                                                    <input 
                                                                        type="file" 
                                                                        className="hidden" 
                                                                        onChange={(e) => handleUploadResource(lesson.id, e.target.files[0])}
                                                                    />
                                                                    <div className="py-3 bg-slate-50/50 border border-dashed border-slate-200 rounded-2xl flex items-center justify-center gap-2 text-[10px] font-black text-slate-400 group-hover/upload:bg-indigo-50 group-hover/upload:border-indigo-200 group-hover/upload:text-indigo-600 transition-all">
                                                                        <Plus size={14} /> Subir Material de Apoyo (PDF / ZIP)
                                                                    </div>
                                                                </label>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        ) : (
                                            /* Quiz Section */
                                            <div className="space-y-8 animate-fade-in pb-20">
                                                <div className="bg-white rounded-[3rem] p-10 border border-slate-100 shadow-xl shadow-slate-200/20 space-y-8">
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                                        <div className="space-y-3">
                                                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Título de la Evaluación</label>
                                                            <div className="relative">
                                                                <Trophy size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-300" />
                                                                <input 
                                                                    type="text" 
                                                                    value={quizData.title}
                                                                    onChange={(e) => setQuizData({...quizData, title: e.target.value})}
                                                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl py-4 pl-14 pr-6 font-black text-slate-700 outline-none transition-all"
                                                                    placeholder="Ej: Evaluación Final del Módulo"
                                                                />
                                                            </div>
                                                        </div>
                                                        <div className="space-y-3">
                                                            <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Calificación Mínima para Aprobar (%)</label>
                                                            <div className="relative">
                                                                <CheckCircle2 size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-300" />
                                                                <input 
                                                                    type="number" 
                                                                    value={quizData.passing_score}
                                                                    onChange={(e) => setQuizData({...quizData, passing_score: parseInt(e.target.value) || 0})}
                                                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl py-4 pl-14 pr-6 font-black text-slate-700 outline-none transition-all"
                                                                    min="0" max="100"
                                                                />
                                                            </div>
                                                        </div>
                                                    </div>
                                                    
                                                    <div className="space-y-6 pt-4 border-t border-slate-50">
                                                        <div className="flex items-center justify-between">
                                                            <div>
                                                                <h4 className="text-xl font-black text-slate-900 tracking-tight">Preguntas</h4>
                                                                <p className="text-slate-400 text-xs font-medium">Define las preguntas y sus opciones de respuesta.</p>
                                                            </div>
                                                            <button 
                                                                onClick={() => setQuizData({...quizData, questions: [...(quizData.questions || []), { text: '', question_type: 'MCQ', points: 1, choices: [{text: '', is_correct: true}, {text: '', is_correct: false}] }]})}
                                                                className="bg-slate-950 text-white px-8 py-4 rounded-2xl text-[10px] font-black hover:bg-indigo-600 transition-all shadow-xl flex items-center gap-2"
                                                            >
                                                                <Plus size={16}/> Añadir Pregunta
                                                            </button>
                                                        </div>

                                                        <div className="space-y-6">
                                                            {quizData.questions?.map((question, qIdx) => (
                                                                <div key={qIdx} className="bg-slate-50 rounded-[2rem] p-8 border border-slate-100 group/q transition-all hover:bg-white hover:shadow-xl hover:border-indigo-100">
                                                                    <div className="flex items-start justify-between gap-6 mb-6">
                                                                        <div className="flex-grow flex items-center gap-4">
                                                                            <span className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-slate-400 font-black text-xs shadow-sm">{qIdx + 1}</span>
                                                                            <input 
                                                                                type="text"
                                                                                placeholder="Escribe el enunciado de la pregunta aquí..."
                                                                                value={question.text}
                                                                                onChange={(e) => {
                                                                                    const qs = [...quizData.questions];
                                                                                    qs[qIdx].text = e.target.value;
                                                                                    setQuizData({...quizData, questions: qs});
                                                                                }}
                                                                                className="flex-grow bg-transparent font-black text-lg text-slate-800 border-b-2 border-slate-100 focus:border-indigo-500 outline-none py-2 transition-all"
                                                                            />
                                                                        </div>
                                                                        <button 
                                                                            onClick={() => {
                                                                                const qs = quizData.questions.filter((_, i) => i !== qIdx);
                                                                                setQuizData({...quizData, questions: qs});
                                                                            }}
                                                                            className="text-slate-300 hover:text-red-500 p-2 transition-colors"
                                                                        ><Trash2 size={20}/></button>
                                                                    </div>
                                                                    
                                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                        {question.choices?.map((choice, cIdx) => (
                                                                            <div key={cIdx} className={`flex items-center gap-4 p-4 rounded-2xl border-2 transition-all ${choice.is_correct ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-slate-100 hover:border-slate-200'}`}>
                                                                                <button 
                                                                                    onClick={() => {
                                                                                        const qs = [...quizData.questions];
                                                                                        qs[qIdx].choices = qs[qIdx].choices.map((c, i) => ({...c, is_correct: i === cIdx}));
                                                                                        setQuizData({...quizData, questions: qs});
                                                                                    }}
                                                                                    className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${choice.is_correct ? 'bg-emerald-500 text-white' : 'bg-white border-2 border-slate-200 text-transparent'}`}
                                                                                >
                                                                                    <CheckCircle2 size={14} />
                                                                                </button>
                                                                                <input 
                                                                                    type="text"
                                                                                    value={choice.text}
                                                                                    placeholder={`Opción ${cIdx + 1}...`}
                                                                                    onChange={(e) => {
                                                                                        const qs = [...quizData.questions];
                                                                                        qs[qIdx].choices[cIdx].text = e.target.value;
                                                                                        setQuizData({...quizData, questions: qs});
                                                                                    }}
                                                                                    className="flex-grow bg-transparent text-sm font-bold text-slate-700 outline-none"
                                                                                />
                                                                                {question.choices.length > 2 && (
                                                                                    <button 
                                                                                        onClick={() => {
                                                                                            const qs = [...quizData.questions];
                                                                                            qs[qIdx].choices = qs[qIdx].choices.filter((_, i) => i !== cIdx);
                                                                                            setQuizData({...quizData, questions: qs});
                                                                                        }}
                                                                                        className="text-slate-300 hover:text-red-500"
                                                                                    ><X size={14}/></button>
                                                                                )}
                                                                            </div>
                                                                        ))}
                                                                        <button 
                                                                            onClick={() => {
                                                                                const qs = [...quizData.questions];
                                                                                qs[qIdx].choices.push({text: '', is_correct: false});
                                                                                setQuizData({...quizData, questions: qs});
                                                                            }}
                                                                            className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-slate-200 rounded-2xl text-[10px] font-black text-slate-400 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-600 transition-all"
                                                                        >
                                                                            <Plus size={14} /> AÑADIR OPCIÓN DE RESPUESTA
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>

                                                <button 
                                                    onClick={handleSaveQuiz}
                                                    className="w-full py-6 bg-slate-900 text-white rounded-[2rem] font-black text-xl shadow-2xl hover:bg-indigo-600 transition-all flex items-center justify-center gap-3 transform hover:scale-[1.02]"
                                                >
                                                    <Save size={24} /> Guardar Cambios en la Evaluación
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <div className="flex-grow flex flex-col items-center justify-center text-center p-20 opacity-30">
                                    <Layout size={80} strokeWidth={1} className="mb-6" />
                                    <h3 className="text-xl font-black text-slate-900">Selecciona un módulo</h3>
                                    <p className="text-slate-400 max-w-xs mx-auto mt-2">Personaliza el contenido, agrega videos y prepara el material de estudio.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Course Editor Modal */}
            {isCreating && (
                <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xl flex items-center justify-center z-[300] p-4 lg:p-12 overflow-y-auto">
                    <div className="bg-white w-full max-w-2xl rounded-[3rem] shadow-2xl overflow-hidden animate-zoom-in my-auto">
                        <div className="p-8 lg:p-10 border-b border-slate-50 bg-slate-50 flex items-center justify-between">
                            <div>
                                <h3 className="text-2xl font-black text-slate-900 tracking-tight">{editingCourse ? 'Editar Curso' : 'Crear Nuevo Curso'}</h3>
                                <p className="text-slate-400 text-xs font-medium">Define los detalles principales de tu programa.</p>
                            </div>
                            <button onClick={() => { setIsCreating(false); setEditingCourse(null); }} className="p-3 hover:bg-white rounded-2xl transition-all text-slate-400"><X size={24}/></button>
                        </div>
                        <div className="p-8 lg:p-10 space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Título del Curso</label>
                                <input 
                                    type="text" 
                                    value={newCourse.title}
                                    onChange={(e) => setNewCourse({...newCourse, title: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="Ej: Master en React Avanzado"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Subtítulo / Eslogan</label>
                                <input 
                                    type="text" 
                                    value={newCourse.subtitle}
                                    onChange={(e) => setNewCourse({...newCourse, subtitle: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="Ej: De cero a experto en 30 días"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Precio ($)</label>
                                    <input 
                                        type="number" 
                                        value={newCourse.price}
                                        onChange={(e) => setNewCourse({...newCourse, price: parseFloat(e.target.value) || 0})}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Visibilidad</label>
                                    <select 
                                        value={newCourse.is_public}
                                        onChange={(e) => setNewCourse({...newCourse, is_public: e.target.value === 'true'})}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all appearance-none"
                                    >
                                        <option value="false">Solo Institución (Privado)</option>
                                        <option value="true">Público (Marketplace)</option>
                                    </select>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción Detallada</label>
                                <textarea 
                                    rows="4"
                                    value={newCourse.description}
                                    onChange={(e) => setNewCourse({...newCourse, description: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="¿De qué trata el curso? ¿Qué aprenderán los alumnos?..."
                                ></textarea>
                            </div>
                        </div>
                        <div className="p-8 lg:p-10 border-t border-slate-50 bg-slate-50 flex gap-4">
                            <button 
                                onClick={handleSaveCourse}
                                className="flex-grow py-5 bg-slate-900 text-white rounded-3xl font-black text-lg hover:bg-indigo-600 transition-all shadow-xl shadow-slate-200 flex items-center justify-center gap-3"
                            >
                                <Save size={24} /> {editingCourse ? 'Guardar Cambios' : 'Lanzar Curso'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Lesson Editor Modal (Nested) */}
            {(isAddingLesson || editingLesson) && (
                <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-md flex items-center justify-center z-[300] p-6 text-slate-800">
                    <div className="bg-white w-full max-w-xl rounded-[3rem] shadow-2xl overflow-hidden animate-zoom-in">
                        <div className="p-8 border-b border-slate-50 bg-slate-50 flex items-center justify-between">
                            <h3 className="text-xl font-black tracking-tight">{editingLesson ? 'Editar Lección' : 'Nueva Lección'}</h3>
                            <button onClick={() => { setIsAddingLesson(false); setEditingLesson(null); }} className="p-2 hover:bg-white rounded-full transition-all"><X size={20}/></button>
                        </div>
                        <div className="p-8 space-y-4">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Título de la Lección</label>
                                <input 
                                    id="lesson-title"
                                    type="text" 
                                    defaultValue={editingLesson?.title}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl p-3 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="Ej: Introducción a los Algoritmos"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">URL del Video (YouTube/Vimeo)</label>
                                <div className="relative">
                                    <Video size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input 
                                        id="lesson-video"
                                        type="url" 
                                        defaultValue={editingLesson?.video_url}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl py-3 pl-11 pr-4 font-bold text-slate-700 outline-none transition-all"
                                        placeholder="https://..."
                                    />
                                </div>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Contenido / Notas</label>
                                <textarea 
                                    id="lesson-content"
                                    rows="4"
                                    defaultValue={editingLesson?.content}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl p-3 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="Describe brevemente los objetivos de esta lección..."
                                ></textarea>
                            </div>
                        </div>
                        <div className="p-8 border-t border-slate-50 bg-slate-50 flex gap-3">
                            <button 
                                onClick={() => {
                                    const title = document.getElementById('lesson-title').value;
                                    const video_url = document.getElementById('lesson-video').value;
                                    const content = document.getElementById('lesson-content').value;
                                    handleSaveLesson({ title, video_url, content });
                                }}
                                className="flex-grow py-3 bg-slate-900 text-white rounded-2xl font-black hover:bg-indigo-600 transition-all shadow-lg"
                            >
                                <Save size={18} className="inline-block mr-2" /> Guardar Lección
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default InstructorDashboard;
