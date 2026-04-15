import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    ChevronLeft, CheckCircle, Circle, Play, 
    FileText, Download, Menu, X, ArrowRight,
    Sparkles, BookOpen, Clock, Users, Calendar, MonitorPlay, Layout
} from 'lucide-react';
import learningService from '../../services/learningService';
import aiService from '../../services/aiService';

const CoursePlayerPage = () => {
    const { courseId } = useParams();
    const navigate = useNavigate();
    
    const [course, setCourse] = useState(null);
    const [activeLesson, setActiveLesson] = useState(null);
    const [activeAssignment, setActiveAssignment] = useState(null);
    const [loading, setLoading] = useState(true);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        fetchCourseData();
    }, [courseId]);

    const fetchCourseData = async () => {
        try {
            const data = await learningService.getCourse(courseId);
            setCourse(data);
            
            // Refresh active items from new data to get updated statuses (is_completed, my_submission, etc)
            if (activeLesson) {
                const updatedLesson = data.modules?.flatMap(m => m.lessons || []).find(l => l.id === activeLesson.id);
                if (updatedLesson) setActiveLesson(updatedLesson);
            }
            if (activeAssignment) {
                const updatedAssign = data.modules?.flatMap(m => m.assignments || []).find(a => a.id === activeAssignment.id);
                if (updatedAssign) setActiveAssignment(updatedAssign);
            }

            if (!activeLesson && !activeAssignment && data.modules?.[0]?.lessons?.[0]) {
                setActiveLesson(data.modules[0].lessons[0]);
            }
        } catch (error) {
            console.error("Error fetching course:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCompleteLesson = async (lessonId) => {
        try {
            await learningService.completeLesson(lessonId);
            // Update local state or re-fetch to show completed icon
            fetchCourseData();
        } catch (error) {
            console.error("Error completing lesson:", error);
        }
    };

    const [isAiOpen, setIsAiOpen] = useState(false);
    const [aiMessages, setAiMessages] = useState([]);
    const [aiInput, setAiInput] = useState('');
    const [isAiLoading, setIsAiLoading] = useState(false);

    const handleAiAsk = async (e) => {
        if (e) e.preventDefault();
        if (!aiInput.trim() || isAiLoading) return;

        const userMsg = { role: 'user', content: aiInput };
        setAiMessages(prev => [...prev, userMsg]);
        setAiInput('');
        setIsAiLoading(true);

        try {
            const context = `Lección actual: ${activeLesson?.title}. Contenido: ${activeLesson?.content}`;
            const res = await aiService.askAssistant(aiInput, context);
            setAiMessages(prev => [...prev, { role: 'assistant', content: res.response }]);
        } catch (err) {
            setAiMessages(prev => [...prev, { role: 'assistant', content: "Lo siento, hubo un error al procesar tu consulta. Verifica la configuración de la IA." }]);
        } finally {
            setIsAiLoading(false);
        }
    };

    const handleAiSummarize = async () => {
        if (isAiLoading || !activeLesson) return;
        setAiMessages(prev => [...prev, { role: 'user', content: "Resume esta lección" }]);
        setIsAiLoading(true);

        try {
            const res = await aiService.summarizeContent(activeLesson.content);
            setAiMessages(prev => [...prev, { role: 'assistant', content: res.summary }]);
        } catch (err) {
            setAiMessages(prev => [...prev, { role: 'assistant', content: "Error al generar el resumen. Por favor intenta de nuevo." }]);
        } finally {
            setIsAiLoading(false);
        }
    };

    const handleAssignmentSubmit = async (file) => {
        if (!file || !activeAssignment) return;
        
        setIsSubmitting(true);
        const formData = new FormData();
        formData.append('assignment', activeAssignment.id);
        formData.append('file', file);

        try {
            await learningService.submitAssignmentResponse(formData);
            alert('Tarea enviada con éxito');
            fetchCourseData(); // Refresh to show submission status
        } catch (error) {
            console.error("Error submitting assignment:", error);
            alert('Error al enviar la tarea');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) return <div className="flex items-center justify-center h-screen bg-slate-950 text-white">Cargando experiencia de aprendizaje...</div>;
    if (!course) return <div className="p-20 text-center">Curso no encontrado.</div>;

    return (
        <div className="fixed inset-0 bg-slate-50 flex overflow-hidden z-[100]">
            {/* Sidebar Izquierda: Contenido */}
            <div className={`bg-white border-r border-slate-100 flex flex-col transition-all duration-500 shadow-2xl z-40 fixed lg:relative inset-y-0 left-0 ${sidebarOpen ? 'w-full lg:w-96' : 'w-0 -translate-x-full lg:translate-x-0 lg:w-0'}`}>
                <div className="p-6 lg:p-8 border-b border-slate-50 flex items-center justify-between bg-slate-900 text-white">
                    <div className="flex items-center gap-3">
                        <button onClick={() => navigate('/dashboard/campus-virtual')} className="p-2 hover:bg-white/10 rounded-xl transition-colors">
                            <ChevronLeft size={20} />
                        </button>
                        <h2 className="font-black text-sm uppercase tracking-widest text-indigo-400">Currículo</h2>
                    </div>
                    <button onClick={() => setSidebarOpen(false)} className="p-2 text-white/50 hover:text-white"><X size={20}/></button>
                </div>
                
                <div className="flex-grow overflow-y-auto custom-scrollbar p-6 space-y-8">
                    {course.modules?.map((module, mIdx) => (
                        <div key={module.id} className="space-y-4">
                            <div className="flex items-center gap-3">
                                <span className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center text-[10px] font-black border border-indigo-100/50">
                                    0{mIdx + 1}
                                </span>
                                <h3 className="font-black text-slate-800 text-sm uppercase tracking-tight">{module.title}</h3>
                            </div>
                            <div className="space-y-2 ml-4 border-l-2 border-slate-50">
                                {module.lessons?.map(lesson => (
                                    <button 
                                        key={lesson.id}
                                        onClick={() => { setActiveLesson(lesson); setActiveAssignment(null); }}
                                        className={`w-full flex items-center justify-between p-4 rounded-2xl transition-all group ${activeLesson?.id === lesson.id ? 'bg-white text-indigo-700 shadow-xl border border-indigo-100 ring-1 ring-indigo-500/10' : 'hover:bg-slate-50 text-slate-500'}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            {lesson.is_completed ? (
                                                <CheckCircle size={18} className="text-emerald-500 fill-emerald-50" />
                                            ) : (
                                                <Circle size={18} className="text-slate-200 group-hover:text-indigo-400" />
                                            )}
                                            <span className="text-sm font-bold text-left">{lesson.title}</span>
                                        </div>
                                        <Play size={14} className={`${activeLesson?.id === lesson.id ? 'opacity-100 animate-pulse text-indigo-600' : 'opacity-0'}`} />
                                    </button>
                                ))}
                                {module.assignments?.map(assignment => (
                                    <button 
                                        key={assignment.id}
                                        onClick={() => { setActiveAssignment(assignment); setActiveLesson(null); }}
                                        className={`w-full flex items-center justify-between p-4 rounded-2xl transition-all group ${activeAssignment?.id === assignment.id ? 'bg-white text-amber-700 shadow-xl border border-amber-100 ring-1 ring-amber-500/10' : 'hover:bg-amber-50/50 text-slate-500'}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            {assignment.my_submission ? (
                                                <CheckCircle size={18} className="text-emerald-500 fill-emerald-50" />
                                            ) : (
                                                <FileText size={18} className={activeAssignment?.id === assignment.id ? 'text-amber-500' : 'text-slate-300'} />
                                            )}
                                            <span className="text-sm font-bold text-left">{assignment.title}</span>
                                        </div>
                                        <ArrowRight size={14} className={`${activeAssignment?.id === assignment.id ? 'opacity-100 animate-pulse text-amber-600' : 'opacity-0'}`} />
                                    </button>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
                
                <div className="p-6 lg:p-8 border-t border-slate-100 bg-slate-50">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Tu Progreso</span>
                        <span className="text-indigo-600 font-bold">{course.enrollments?.[0]?.progress_percentage || 0}%</span>
                    </div>
                    <div className="w-full h-3 bg-slate-200 rounded-full overflow-hidden p-0.5">
                        <div 
                            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full shadow-lg shadow-indigo-200 transition-all duration-1000" 
                            style={{ width: `${course.enrollments?.[0]?.progress_percentage || 0}%` }}
                        ></div>
                    </div>
                </div>
            </div>

            {/* Main Player Area */}
            <div className="flex-grow flex flex-col relative overflow-y-auto bg-slate-50/50">
                {/* Fixed Header */}
                <div className="p-4 lg:p-6 border-b border-slate-100 bg-white/90 backdrop-blur-md flex flex-col md:flex-row items-start md:items-center justify-between sticky top-0 z-30 shadow-sm px-4 lg:px-10 gap-4">
                    <div className="flex items-center gap-4 lg:gap-6">
                        {!sidebarOpen && (
                            <button onClick={() => setSidebarOpen(true)} className="p-3 bg-slate-900 rounded-2xl text-white hover:bg-indigo-600 transition-all shadow-lg">
                                <Menu size={20} />
                            </button>
                        )}
                        <div>
                            <h1 className="text-lg lg:text-2xl font-black text-slate-900 tracking-tight leading-none mb-1">
                                {activeLesson?.title || activeAssignment?.title || 'Selecciona un contenido'}
                            </h1>
                            <div className="flex items-center gap-2">
                                <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest">{course.title}</p>
                                <span className="text-slate-200">•</span>
                                <div className="flex items-center gap-1 text-[10px] font-black text-indigo-500">
                                    {activeLesson ? <Clock size={10} /> : <Calendar size={10} />}
                                    {activeLesson ? `${activeLesson.duration_minutes || 0} MIN` : activeAssignment ? `Vence: ${new Date(activeAssignment.due_date).toLocaleDateString()}` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-4 w-full md:w-auto">
                        {activeLesson && (
                            <button 
                                onClick={() => setIsAiOpen(!isAiOpen)}
                                className={`flex-grow md:flex-none flex items-center justify-center gap-3 px-4 lg:px-6 py-2 lg:py-3 rounded-2xl font-black transition-all border-2 ${isAiOpen ? 'bg-indigo-600 text-white border-indigo-600 shadow-xl shadow-indigo-500/20' : 'bg-white text-indigo-600 border-indigo-50 hover:border-indigo-200'}`}
                            >
                                <Sparkles size={18} className={isAiOpen ? 'animate-spin-slow' : ''} />
                                <span className="hidden md:inline">Eduka AI</span>
                            </button>
                        )}
                        
                        <button 
                            onClick={() => activeLesson ? handleCompleteLesson(activeLesson.id) : null}
                            disabled={!activeLesson}
                            className={`flex-grow md:flex-none px-4 lg:px-8 py-2 lg:py-3 rounded-2xl font-black shadow-xl transition-all flex items-center justify-center gap-2 group ${activeLesson ? 'bg-slate-900 text-white hover:bg-emerald-600' : 'bg-slate-100 text-slate-300 cursor-not-allowed'}`}
                        >
                            <CheckCircle size={18} className="group-hover:scale-110 transition-transform" />
                            <span className="text-sm md:text-base">{activeLesson ? 'Finalizar' : 'Tarea'}</span>
                        </button>

                        <div className="h-10 w-px bg-slate-100 hidden md:block mx-1"></div>

                        <button 
                            onClick={() => navigate('/dashboard')}
                            className="flex-none p-3 lg:p-4 bg-white border border-slate-100 rounded-2xl text-slate-400 hover:text-slate-900 hover:shadow-lg transition-all"
                            title="Volver al Dashboard"
                        >
                            <Layout size={20} />
                        </button>
                    </div>
                </div>

                {/* Content Area */}
                <div className="p-4 lg:p-16 space-y-12 flex-grow">
                    {/* Hero Area (Meeting / Video / Assignment Hero / Reading Hero) */}
                    {activeLesson?.meeting_url ? (
                        <div className="aspect-video w-full bg-slate-900 rounded-[2rem] lg:rounded-[3rem] shadow-2xl flex flex-col items-center justify-center p-8 lg:p-20 text-center relative overflow-hidden group">
                            <div className="absolute inset-0 bg-gradient-to-br from-indigo-900 via-slate-900 to-indigo-950 opacity-90 transition-opacity"></div>
                            
                            {/* Animated Background Pulse */}
                            <div className="absolute inset-0 flex items-center justify-center opacity-20 group-hover:opacity-30 transition-opacity">
                                <div className="w-[120%] h-[120%] bg-indigo-500/20 blur-[120px] rounded-full animate-pulse-slow"></div>
                            </div>

                            <div className="relative z-10 space-y-6 lg:space-y-10 max-w-2xl">
                                <div className="inline-flex items-center gap-3 px-6 py-3 bg-red-500/10 border border-red-500/20 rounded-full text-red-500 text-xs font-black uppercase tracking-widest animate-pulse">
                                    <div className="w-2 h-2 bg-red-500 rounded-full shadow-[0_0_10px_rgba(239,68,68,0.8)]"></div>
                                    Sesión en Vivo
                                </div>
                                
                                <div>
                                    <h3 className="text-3xl lg:text-5xl font-black text-white mb-4 tracking-tighter">¡La clase está lista!</h3>
                                    <p className="text-indigo-100/60 text-sm lg:text-lg font-medium">
                                        {activeLesson.meeting_date ? (
                                            <>Programada para el <span className="text-white font-bold">{new Date(activeLesson.meeting_date).toLocaleDateString()}</span> a las <span className="text-white font-bold">{new Date(activeLesson.meeting_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span></>
                                        ) : 'Únete a la sesión ahora desde el enlace oficial proporcionado por tu profesor.'}
                                    </p>
                                </div>

                                <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
                                    <a 
                                        href={activeLesson.meeting_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        onClick={() => handleCompleteLesson(activeLesson.id)}
                                        className="px-12 py-5 bg-white text-slate-950 rounded-3xl font-black text-lg hover:bg-indigo-500 hover:text-white transition-all shadow-[0_20px_40px_rgba(0,0,0,0.4)] hover:shadow-indigo-500/30 flex items-center gap-3 transform hover:scale-105 active:scale-95"
                                    >
                                        <MonitorPlay size={24} />
                                        Entrar a la Clase
                                    </a>
                                </div>
                            </div>
                            
                            <Sparkles size={400} className="absolute -right-20 -top-20 text-white/5 rotate-12" />
                        </div>
                    ) : activeLesson?.video_url ? (
                        <div className="aspect-video w-full bg-slate-900 rounded-[2rem] lg:rounded-[3rem] shadow-2xl overflow-hidden relative group">
                            <iframe 
                                src={activeLesson.video_url} 
                                title={activeLesson.title}
                                className="w-full h-full"
                                frameBorder="0"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowFullScreen
                            ></iframe>
                        </div>
                    ) : activeAssignment ? (
                        <div className="aspect-video w-full bg-gradient-to-br from-amber-400 via-orange-500 to-amber-600 rounded-[2rem] lg:rounded-[3rem] shadow-2xl flex items-center justify-center p-8 lg:p-20 text-center relative overflow-hidden">
                            <div className="relative z-10">
                                <FileText size={48} className="text-white/20 mx-auto mb-4 lg:mb-8" />
                                <h3 className="text-2xl lg:text-4xl font-black text-white mb-4">{activeAssignment.title}</h3>
                                <p className="text-amber-100/70 text-sm lg:text-lg font-medium">Asignación pendiente de entrega.</p>
                            </div>
                        </div>
                    ) : (
                        <div className="aspect-video w-full bg-gradient-to-br from-indigo-500 via-purple-600 to-indigo-800 rounded-[2rem] lg:rounded-[3rem] shadow-2xl flex items-center justify-center p-8 lg:p-20 text-center relative overflow-hidden">
                            <div className="relative z-10">
                                <BookOpen size={48} className="text-white/20 mx-auto mb-4 lg:mb-8" />
                                <h3 className="text-2xl lg:text-4xl font-black text-white mb-4">Material de Lectura</h3>
                                <p className="text-indigo-100/70 text-sm lg:text-lg font-medium">Esta lección se basa en contenido interactivo y material descargable.</p>
                            </div>
                            <Sparkles size={400} className="absolute -right-20 -bottom-20 text-white/5" />
                        </div>
                    )}

                    {/* Detailed Content info */}
                    <div className="max-w-4xl mx-auto space-y-8 lg:space-y-12">
                        {activeAssignment ? (
                            <section className="bg-white p-6 lg:p-12 rounded-[2rem] lg:rounded-[3.5rem] border border-slate-100 shadow-sm leading-relaxed space-y-8">
                                <div>
                                    <h3 className="text-xl lg:text-2xl font-black text-slate-900 mb-4 flex items-center gap-3">
                                        <FileText className="text-amber-600" /> Instrucciones de la Tarea
                                    </h3>
                                    <p className="text-slate-600 text-sm lg:text-lg font-medium">{activeAssignment.description}</p>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    {activeAssignment.attachment && (
                                        <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100">
                                            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Material del Docente</p>
                                            <a 
                                                href={activeAssignment.attachment} 
                                                target="_blank" 
                                                rel="noopener noreferrer"
                                                className="inline-flex items-center gap-3 px-6 py-3 bg-white border border-slate-200 rounded-xl text-indigo-600 font-black hover:bg-indigo-50 transition-all text-xs"
                                            >
                                                <Download size={16} /> Descargar Guía
                                            </a>
                                        </div>
                                    )}

                                    {activeAssignment.my_submission && (
                                        <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-100">
                                            <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-3">Tu Entrega Anterior</p>
                                            <div className="flex items-center justify-between">
                                                <span className="text-[10px] font-bold text-slate-500 tracking-tight">Enviado: {new Date(activeAssignment.my_submission.submitted_at).toLocaleDateString()}</span>
                                                {activeAssignment.my_submission.score !== null && (
                                                    <span className="px-3 py-1 bg-emerald-600 text-white rounded-lg text-xs font-black">Nota: {activeAssignment.my_submission.score}/{activeAssignment.max_score}</span>
                                                )}
                                            </div>
                                            {activeAssignment.my_submission.teacher_feedback && (
                                                <div className="mt-3 p-3 bg-white/50 rounded-lg text-[10px] font-medium text-slate-600 border border-emerald-200">
                                                    <p className="font-bold text-emerald-800 mb-1">Feedback del Profe:</p>
                                                    {activeAssignment.my_submission.teacher_feedback}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <div className="pt-8 border-t border-slate-100">
                                    <h4 className="text-lg font-black text-slate-900 mb-4">{activeAssignment.my_submission ? 'Actualizar Entrega' : 'Tu Entrega'}</h4>
                                    <div className={`p-8 rounded-[2rem] border-2 border-dashed text-center transition-all ${activeAssignment.my_submission ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-50 border-indigo-200'}`}>
                                        <input 
                                            type="file" 
                                            id="assignment-file"
                                            className="hidden" 
                                            onChange={(e) => handleAssignmentSubmit(e.target.files[0])}
                                        />
                                        <label 
                                            htmlFor="assignment-file"
                                            className={`inline-flex items-center gap-3 px-10 py-4 rounded-2xl font-black cursor-pointer transition-all ${isSubmitting ? 'bg-slate-200 text-slate-400' : 'bg-slate-900 text-white hover:bg-indigo-600 shadow-xl'}`}
                                        >
                                            <Download size={20} className="rotate-180" />
                                            {isSubmitting ? 'Enviando...' : activeAssignment.my_submission ? 'Sustituir Archivo' : 'Subir Archivo de Tarea'}
                                        </label>
                                        <p className="mt-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                            {activeAssignment.my_submission ? 'Puedes subir una nueva versión para reemplazar la anterior' : 'Formatos permitidos: PDF, ZIP, JPG (Máx 10MB)'}
                                        </p>
                                    </div>
                                </div>
                            </section>
                        ) : (
                            <section className="bg-white p-6 lg:p-12 rounded-[2rem] lg:rounded-[3.5rem] border border-slate-100 shadow-sm leading-relaxed">
                                <h3 className="text-xl lg:text-2xl font-black text-slate-900 mb-6 lg:mb-8 flex items-center gap-3">
                                    <FileText className="text-indigo-600" /> Descripción
                                </h3>
                                <div className="prose prose-indigo max-w-none text-slate-600 text-sm lg:text-lg font-medium" dangerouslySetInnerHTML={{ __html: activeLesson?.content }}>
                                </div>
                            </section>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="bg-white p-6 lg:p-10 rounded-[2rem] lg:rounded-[3rem] border border-slate-100 shadow-sm">
                                <h3 className="text-lg lg:text-xl font-black text-slate-900 mb-6 flex items-center gap-3">
                                    <Download className="text-indigo-600" /> Material
                                </h3>
                                <div className="space-y-2 lg:space-y-3">
                                    {activeLesson?.resources?.map(resource => (
                                        <a 
                                            key={resource.id}
                                            href={resource.file}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center justify-between p-3 lg:p-4 bg-slate-50 rounded-2xl hover:bg-indigo-50 group transition-all"
                                        >
                                            <span className="font-bold text-slate-600 group-hover:text-indigo-600 transition-colors text-sm lg:text-base">{resource.title}</span>
                                            <Download size={18} className="text-slate-300 group-hover:text-indigo-400" />
                                        </a>
                                    ))}
                                    {(!activeLesson?.resources || activeLesson.resources.length === 0) && (
                                        <p className="text-slate-400 text-xs lg:text-sm italic font-medium">No hay archivos.</p>
                                    )}
                                </div>
                            </div>

                            <div className="bg-slate-900 p-6 lg:p-10 rounded-[2rem] lg:rounded-[3rem] text-white shadow-2xl relative overflow-hidden">
                                <h3 className="text-lg lg:text-xl font-black mb-6">Detalles</h3>
                                <div className="space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                                            <Clock size={20} className="text-indigo-400" />
                                        </div>
                                        <div>
                                            <p className="text-indigo-200/50 text-[10px] font-black uppercase tracking-widest">Duración</p>
                                            <p className="font-black text-sm lg:text-base">{activeLesson?.duration_minutes || 0} min</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                                            <Users size={20} className="text-indigo-400" />
                                        </div>
                                        <div>
                                            <p className="text-indigo-200/50 text-[10px] font-black uppercase tracking-widest">Instructor</p>
                                            <p className="font-black text-sm lg:text-base">{course.instructor_name || 'Docente'}</p>
                                        </div>
                                    </div>
                                </div>
                                <Sparkles size={200} className="absolute -right-20 -bottom-20 text-white/5" />
                            </div>
                        </div>

                        <div className="flex items-center justify-between pt-12 border-t border-slate-100 pb-12">
                            {(() => {
                                const allLessons = course.modules?.flatMap(m => m.lessons) || [];
                                const currentIndex = allLessons.findIndex(l => l.id === activeLesson?.id);
                                const prevLesson = allLessons[currentIndex - 1];
                                const nextLesson = allLessons[currentIndex + 1];

                                return (
                                    <>
                                        <button 
                                            onClick={() => prevLesson && setActiveLesson(prevLesson)}
                                            disabled={!prevLesson}
                                            className={`flex items-center gap-2 font-black transition-all group ${prevLesson ? 'text-slate-400 hover:text-slate-900' : 'text-slate-200 cursor-not-allowed'}`}
                                        >
                                            <ChevronLeft size={20} className={prevLesson ? "group-hover:-translate-x-1 transition-transform" : ""} />
                                            Anterior
                                        </button>
                                        <button 
                                            onClick={() => nextLesson && setActiveLesson(nextLesson)}
                                            disabled={!nextLesson}
                                            className={`flex items-center gap-2 font-black transition-all group ${nextLesson ? 'text-indigo-600 hover:scale-105' : 'text-slate-200 cursor-not-allowed'}`}
                                        >
                                            Siguiente Lección
                                            <ArrowRight size={20} className={nextLesson ? "group-hover:translate-x-1 transition-transform" : ""} />
                                        </button>
                                    </>
                                );
                            })()}
                        </div>
                    </div>
                </div>
            </div>

            {/* Sidebar Derecha: AI Assistant */}
            <div className={`bg-slate-900 border-l border-white/5 flex flex-col transition-all duration-500 overflow-hidden shadow-2xl z-40 fixed lg:relative inset-y-0 right-0 ${isAiOpen ? 'w-full lg:w-96' : 'w-0 translate-x-full lg:translate-x-0 lg:w-0'}`}>
                <div className="p-6 lg:p-8 border-b border-white/5 flex items-center justify-between bg-slate-950/50">
                    <div className="flex items-center gap-3 text-indigo-400">
                        <Sparkles size={20} className="animate-pulse" />
                        <h2 className="font-black text-xs lg:text-sm uppercase tracking-widest">Eduka AI Assistant</h2>
                    </div>
                    <button onClick={() => setIsAiOpen(false)} className="text-white/40 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                <div className="flex-grow overflow-y-auto p-6 space-y-6 flex flex-col">
                    <div className="bg-white/5 p-6 rounded-3xl border border-white/5 mb-4">
                        <p className="text-indigo-100/70 text-sm font-medium leading-relaxed">
                            ¡Hola! Soy tu asistente de aprendizaje. Puedo ayudarte a resumir esta lección, aclarar dudas o darte ejercicios de práctica.
                        </p>
                    </div>
                    
                    <div className="space-y-4 flex-grow">
                        {aiMessages.map((msg, idx) => (
                            <div key={idx} className={`p-4 rounded-2xl text-sm font-medium leading-relaxed ${msg.role === 'user' ? 'bg-indigo-600/20 text-indigo-100 ml-8 border border-indigo-500/20' : 'bg-white/5 text-slate-300 mr-8 border border-white/5'}`}>
                                {msg.content}
                            </div>
                        ))}
                        {isAiLoading && (
                            <div className="flex gap-2 p-4 bg-white/5 rounded-2xl w-24 border border-white/5">
                                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce delay-100"></div>
                                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce delay-200"></div>
                            </div>
                        )}
                    </div>
                    
                    <div className="space-y-4">
                        <p className="text-[10px] font-black text-white/20 uppercase tracking-widest ml-2">¿En qué puedo ayudarte?</p>
                        <button 
                            onClick={handleAiSummarize}
                            disabled={isAiLoading}
                            className="w-full text-left p-4 bg-white/5 border border-white/5 rounded-2xl text-white text-sm font-bold hover:bg-indigo-600 transition-all disabled:opacity-50"
                        >
                            Resumir esta lección
                        </button>
                    </div>
                </div>

                <div className="p-6 bg-slate-950/50 border-t border-white/5">
                    <form onSubmit={handleAiAsk} className="relative">
                        <input 
                            type="text" 
                            value={aiInput}
                            onChange={(e) => setAiInput(e.target.value)}
                            placeholder="Escribe tu duda aquí..." 
                            className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-6 pr-12 text-white placeholder:text-white/20 focus:outline-none focus:border-indigo-500 transition-all font-medium text-sm"
                        />
                        <button 
                            type="submit"
                            disabled={isAiLoading || !aiInput.trim()}
                            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 text-white rounded-xl shadow-lg shadow-indigo-500/20 disabled:opacity-50"
                        >
                            <ArrowRight size={18} />
                        </button>
                    </form>
                    <p className="text-[10px] text-white/20 text-center mt-4 font-bold uppercase tracking-widest">Potenciado por Claude AI</p>
                </div>
            </div>
        </div>
    );
};

export default CoursePlayerPage;
