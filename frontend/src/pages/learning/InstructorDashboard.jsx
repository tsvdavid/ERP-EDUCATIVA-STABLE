import React, { useState, useEffect } from 'react';
import { 
    FileDown, FileText, Plus, BookOpen, Users, 
    ArrowRight, Star, Clock, Trash2, Edit, Edit3,
    ChevronRight, ChevronDown, CheckCircle, CheckCircle2, Info, Sparkles,
    Layout, Filter, Settings, ShieldCheck, Tag, PlusCircle,
    LayoutDashboard, BarChart3, X, Video, Trophy, Save, Download, Link, Calendar
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import learningService from '../../services/learningService';
import academicService from '../../services/academicService';

const InstructorDashboard = () => {
    const navigate = useNavigate();
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
    const [activeTab, setActiveTab] = useState('dashboard'); // Default to dashboard
    const [user, setUser] = useState(null);

    useEffect(() => {
        const userData = localStorage.getItem('user');
        if (userData) {
            const parsedUser = JSON.parse(userData);
            console.log("EDUKA_DEBUG - Datos de Usuario:", parsedUser); // Log para diagnóstico
            setUser(parsedUser);
        }
    }, []);

    const [quizData, setQuizData] = useState({ title: '', questions: [], passing_score: 70 });
    const [assignmentData, setAssignmentData] = useState({ title: '', description: '', due_date: '', max_score: 10 });
    const [isAddingAssignment, setIsAddingAssignment] = useState(false);
    const [editingAssignment, setEditingAssignment] = useState(null);
    const [submissions, setSubmissions] = useState([]);
    const [isViewingSubmissions, setIsViewingSubmissions] = useState(false);
    const [selectedAssignmentSub, setSelectedAssignmentSub] = useState(null);
    const [gradingData, setGradingData] = useState({ score: '', teacher_feedback: '' });
    const [isSubmittingGrade, setIsSubmittingGrade] = useState(false);
    const [courseGroups, setCourseGroups] = useState([]);
    const [tags, setTags] = useState([]);
    const [selectedGroup, setSelectedGroup] = useState('');
    const [courseGroupFilter, setCourseGroupFilter] = useState('all');
    const [courseEnrollments, setCourseEnrollments] = useState([]);
    const [isSyncingStudents, setIsSyncingStudents] = useState(false);
    const [unifiedSubmissions, setUnifiedSubmissions] = useState([]);
    const [isExporting, setIsExporting] = useState(false);
    const [evaluationCategories, setEvaluationCategories] = useState([]);
    const [isCreatingGroup, setIsCreatingGroup] = useState(false);
    const [newGroup, setNewGroup] = useState({ name: '', description: '', icon: 'Tag' });
    const [isCreatingTag, setIsCreatingTag] = useState(false);
    const [newTag, setNewTag] = useState({ group: '', name: '', description: '' });
    const [stats, setStats] = useState({
        total_courses: 0,
        total_students: 0,
        active_students: 0,
        pending_assignments: 0,
        active_year_name: 'N/A'
    });

    // Validar si el usuario tiene privilegios administrativos
    const checkIsAdmin = (u) => {
        if (!u) return false;
        // Detección ultra-permisiva para asegurar visualización
        const r = String(u.role || u.role_name || '').toUpperCase();
        const isStaff = u.is_staff === true || u.is_superuser === true || u.username === 'admin';
        const isAdminRole = r.includes('ADMIN') || r.includes('ADMINISTRADOR');
        return isAdminRole || isStaff;
    };

    const isAdmin = checkIsAdmin(user);

    useEffect(() => {
        fetchCourses();
        fetchStats();
        fetchGroups();
    }, []);

    const fetchGroups = async () => {
        try {
            const [groups, allTags] = await Promise.all([
                learningService.getGroups(),
                learningService.getTags()
            ]);
            setCourseGroups(groups);
            setTags(allTags);
        } catch (error) {
            console.error("Error fetching groups:", error);
        }
    };

    const fetchTagsByGroup = async (groupId) => {
        try {
            const data = await learningService.getTags(groupId);
            setTags(data);
        } catch (error) {
            console.error("Error fetching tags:", error);
        }
    };

    useEffect(() => {
        if (selectedGroup) {
            fetchTagsByGroup(selectedGroup);
        }
    }, [selectedGroup]);

    const fetchStats = async () => {
        try {
            const data = await learningService.getInstructorStats();
            setStats(data);
        } catch (error) {
            console.error("Error fetching stats:", error);
        }
    };

    const fetchUnifiedSubmissions = async (courseId = null) => {
        try {
            const data = await learningService.getUnifiedSubmissions(courseId);
            setUnifiedSubmissions(data);
        } catch (error) {
            console.error("Error fetching unified submissions:", error);
        }
    };

    useEffect(() => {
        if (activeTab === 'all_submissions') {
            fetchUnifiedSubmissions();
        }
    }, [activeTab]);

    const handleExport = async (format) => {
        try {
            setIsExporting(true);
            await learningService.exportInstructorData(format);
        } catch (error) {
            console.error(`Error exporting ${format}:`, error);
            alert('Error al generar el reporte');
        } finally {
            setIsExporting(false);
        }
    };

    const fetchCourses = async () => {
        try {
            setLoading(true);
            const data = await learningService.getCourses(); // Instructor filter is handled by backend get_queryset or params
            setCourses(data);
        } catch (error) {
            console.error("Error fetching instructor courses:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveCourse = async () => {
        try {
            const courseData = {
                ...newCourse,
                tag_id: newCourse.tag_id || null
            };
            if (editingCourse) {
                await learningService.updateCourse(editingCourse.id, courseData);
            } else {
                await learningService.createCourse(courseData);
            }
            setIsCreating(false);
            setEditingCourse(null);
            setSelectedGroup('');
            setNewCourse({ title: '', subtitle: '', description: '', price: 0, is_public: false, is_active: true });
            fetchCourses();
        } catch (error) {
            console.error("Error saving course:", error);
            alert("Error al guardar el curso. Verifique los campos obligatorios.");
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

    useEffect(() => {
        if ((isAddingAssignment || editingAssignment) && managingCourse?.subject) {
            fetchAcademicCategories(managingCourse.subject);
        }
    }, [isAddingAssignment, editingAssignment, managingCourse]);

    const fetchAcademicCategories = async (subjectId) => {
        try {
            const categories = await academicService.getEvaluationCategories(subjectId);
            setEvaluationCategories(categories);
        } catch (error) {
            console.error("Error fetching academic categories:", error);
        }
    };

    useEffect(() => {
        if (activeTab === 'students' && managingCourse) {
            fetchCourseEnrollments();
        }
    }, [activeTab, managingCourse]);

    const fetchCourseEnrollments = async () => {
        try {
            const data = await learningService.getCourseEnrollments(managingCourse.id);
            setCourseEnrollments(data);
        } catch (error) {
            console.error("Error fetching course enrollments:", error);
        }
    };

    const handleSyncStudents = async () => {
        try {
            setIsSyncingStudents(true);
            const result = await learningService.syncCourseStudents(managingCourse.id);
            alert(`Sincronización completada. ${result.new_enrollments} alumnos nuevos añadidos.`);
            fetchCourseEnrollments();
        } catch (error) {
            console.error("Error syncing students:", error);
            alert("Error al sincronizar alumnos.");
        } finally {
            setIsSyncingStudents(false);
        }
    };

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
            alert('Error al guardar el quiz. Revisa la consola.');
        }
    };

    const handleSaveAssignment = async (e) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('module', activeModule.id);
            formData.append('title', assignmentData.title);
            formData.append('description', assignmentData.description);
            formData.append('due_date', assignmentData.due_date);
            formData.append('max_score', assignmentData.max_score);
            
            if (assignmentData.file) {
                formData.append('attachment', assignmentData.file);
            }

            if (editingAssignment) {
                await learningService.updateAssignment(editingAssignment.id, formData);
            } else {
                await learningService.createAssignment(formData);
            }

            const updated = await learningService.getCourse(managingCourse.id);
            setManagingCourse(updated);
            setActiveModule(updated.modules.find(m => m.id === activeModule.id));
            setIsAddingAssignment(false);
            setEditingAssignment(null);
            setAssignmentData({ title: '', description: '', due_date: '', max_score: 10 });
            alert('Tarea guardada exitosamente');
        } catch (error) {
            console.error("Error saving assignment:", error);
            alert('Error al guardar la tarea');
        }
    };

    const handleDeleteAssignment = async (id) => {
        if (!window.confirm('¿Eliminar esta tarea?')) return;
        try {
            await learningService.deleteAssignment(id);
            const updated = await learningService.getCourse(managingCourse.id);
            setManagingCourse(updated);
            setActiveModule(updated.modules.find(m => m.id === activeModule.id));
        } catch (error) {
            console.error("Error deleting assignment:", error);
        }
    };

    const handleSaveGroup = async () => {
        if (!newGroup.name) return;
        
        let institutionId = user?.institution?.id || user?.institution || user?.institution_id || localStorage.getItem('institution_id');
        
        if (!institutionId && (user?.username === 'admin' || user?.role === 'ADMIN')) {
            institutionId = 1; 
        }

        try {
            const groupData = {
                ...newGroup,
                institution: institutionId
            };
            
            await learningService.createGroup(groupData);
            setIsCreatingGroup(false);
            setNewGroup({ name: '', description: '', icon: 'Tag' });
            fetchGroups();
            alert("Grupo creado con éxito");
        } catch (error) {
            console.error("Error creating group:", error);
            const serverMsg = error.response?.data ? JSON.stringify(error.response.data) : error.message;
            alert("Error al crear grupo: " + serverMsg);
        }
    };

    const handleDeleteGroup = async (id) => {
        if (!window.confirm("¿Seguro que deseas eliminar este grupo? Esto afectará la organización de los cursos.")) return;
        try {
            await learningService.deleteGroup(id);
            fetchGroups();
        } catch (error) {
            console.error("Error deleting group:", error);
            alert("Error al eliminar grupo.");
        }
    };

    const handleSaveTag = async () => {
        if (!newTag.name || !newTag.group) return;
        try {
            await learningService.createTag(newTag);
            setIsCreatingTag(false);
            setNewTag({ group: '', name: '', description: '' });
            fetchGroups();
        } catch (error) {
            console.error("Error creating tag:", error);
            alert("Error al crear etiqueta.");
        }
    };

    const handleDeleteTag = async (id) => {
        if (!window.confirm("¿Seguro que deseas eliminar esta etiqueta?")) return;
        try {
            await learningService.deleteTag(id);
            fetchGroups();
        } catch (error) {
            console.error("Error deleting tag:", error);
            alert(`Error al eliminar etiqueta: ${error.response?.data ? JSON.stringify(error.response.data) : error.message}`);
        }
    };

    const [editingGroup, setEditingGroup] = useState(null);
    const [editGroupData, setEditGroupData] = useState({ name: '', description: '' });
    const [editingTag, setEditingTag] = useState(null);
    const [editTagData, setEditTagData] = useState({ name: '', description: '' });

    const handleEditGroup = (group) => {
        setEditingGroup(group);
        setEditGroupData({ name: group.name, description: group.description });
    };

    const handleUpdateGroup = async () => {
        if (!editGroupData.name) return;
        try {
            await learningService.updateGroup(editingGroup.id, editGroupData);
            setEditingGroup(null);
            fetchGroups();
        } catch (error) {
            console.error('Error updating group:', error);
            alert(`Error al actualizar grupo: ${error.response?.data ? JSON.stringify(error.response.data) : error.message}`);
        }
    };

    const handleEditTag = (tag) => {
        setEditingTag(tag);
        setEditTagData({ name: tag.name, description: tag.description || '' });
    };

    const handleUpdateTag = async () => {
        if (!editTagData.name) return;
        try {
            await learningService.updateTag(editingTag.id, editTagData);
            setEditingTag(null);
            fetchGroups();
        } catch (error) {
            console.error('Error updating tag:', error);
            alert(`Error al actualizar etiqueta: ${error.response?.data ? JSON.stringify(error.response.data) : error.message}`);
        }
    };

    const renderGroups = () => (
        <div className="space-y-12 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-white p-10 rounded-[3rem] border border-slate-100 shadow-xl shadow-slate-200/20">
                <div>
                    <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-2">Editor de <span className="text-indigo-600">Grupos y Etiquetas</span></h2>
                    <p className="text-slate-400 font-medium italic">Organiza los cursos por grupos temáticos y etiquetas específicas.</p>
                </div>
                <div className="flex gap-4">
                    <button 
                        onClick={() => setIsCreatingGroup(true)}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-2xl text-xs font-black hover:bg-slate-900 transition-all shadow-xl shadow-indigo-100 flex items-center gap-2"
                    >
                        <PlusCircle size={18} /> Nuevo Grupo
                    </button>
                    <button 
                        onClick={() => setIsCreatingTag(true)}
                        className="px-6 py-3 bg-slate-100 text-slate-600 rounded-2xl text-xs font-black hover:bg-slate-200 transition-all flex items-center gap-2"
                    >
                        <PlusCircle size={18} /> Nueva Etiqueta
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {courseGroups.length > 0 ? (
                    courseGroups.map(group => (
                        <div key={group.id} className="bg-white rounded-[3rem] p-10 border border-slate-100 shadow-sm hover:shadow-2xl transition-all group relative overflow-hidden">
                            <div className="flex items-start justify-between mb-8">
                                <div className="w-16 h-16 bg-indigo-50 rounded-[1.5rem] flex items-center justify-center text-indigo-600 group-hover:bg-indigo-600 group-hover:text-white transition-all shadow-lg shadow-indigo-50">
                                    <Tag size={28} />
                                </div>
                                <div className="flex gap-2">
                                    <button 
                                        onClick={() => handleEditGroup(group)}
                                        className="p-3 text-slate-300 hover:text-indigo-500 hover:bg-indigo-50 rounded-xl transition-all"
                                    >
                                        <Edit size={20} />
                                    </button>
                                    <button 
                                        onClick={() => handleDeleteGroup(group.id)}
                                        className="p-3 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
                                    >
                                        <Trash2 size={20} />
                                    </button>
                                </div>
                            </div>
                            <h3 className="text-2xl font-black text-slate-900 mb-2 uppercase tracking-tighter">{group.name}</h3>
                            <p className="text-slate-400 text-sm font-bold line-clamp-2 mb-8">{group.description || 'Sin descripción detallada'}</p>
                            
                            <div className="space-y-3 pt-8 border-t border-slate-50">
                                <div className="flex items-center justify-between mb-2">
                                    <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Etiquetas</p>
                                    <span className="text-[10px] font-black text-indigo-400">{tags.filter(t => t.group === group.id).length}</span>
                                </div>
                                {tags.filter(t => t.group === group.id).length > 0 ? (
                                    tags.filter(t => t.group === group.id).map(tag => (
                                        <div key={tag.id} className="flex items-center justify-between bg-slate-50 hover:bg-indigo-50 rounded-xl px-4 py-2.5 transition-all group/tag">
                                            <span className="text-sm font-bold text-slate-600 group-hover/tag:text-indigo-700">{tag.name}</span>
                                            <div className="flex gap-1 opacity-0 group-hover/tag:opacity-100 transition-opacity">
                                                <button onClick={() => handleEditTag(tag)} className="p-1.5 rounded-lg hover:bg-indigo-100 text-indigo-400 transition-all">
                                                    <Edit size={13} />
                                                </button>
                                                <button onClick={() => handleDeleteTag(tag.id)} className="p-1.5 rounded-lg hover:bg-red-100 text-red-400 transition-all">
                                                    <X size={13} />
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <p className="text-[10px] font-bold text-slate-300 italic text-center py-4">Sin etiquetas &mdash; crea una arriba</p>
                                )}
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="col-span-full py-32 flex flex-col items-center justify-center bg-white rounded-[4rem] border-2 border-dashed border-slate-100 animate-fade-in">
                        <div className="w-24 h-24 bg-slate-50 text-slate-200 rounded-full flex items-center justify-center mb-6">
                            <Tag size={48} />
                        </div>
                        <h3 className="text-3xl font-black text-slate-900 mb-2">Sin Grupos creados</h3>
                        <p className="text-slate-400 font-medium mb-10 max-w-sm text-center">Organiza tus cursos por grupos temáticos para mejorar la navegación.</p>
                        <button 
                            onClick={() => setIsCreatingGroup(true)}
                            className="px-10 py-5 bg-indigo-600 text-white rounded-[2rem] font-black text-sm hover:bg-slate-900 transition-all shadow-2xl shadow-indigo-100 flex items-center gap-3"
                        >
                            <Plus size={20} /> Crear mi primer Grupo
                        </button>
                    </div>
                )}
            </div>

            {editingTag && (
                <div className="fixed inset-0 z-[500] flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xl">
                    <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-md overflow-hidden border border-white/20 animate-zoom-in">
                        <div className="bg-slate-900 p-10 text-white">
                            <h3 className="text-4xl font-black tracking-tighter mb-1">Editar Etiqueta</h3>
                            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest">{editingTag.group_name}</p>
                        </div>
                        <div className="p-10 space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre</label>
                                <input
                                    type="text"
                                    value={editTagData.name}
                                    onChange={(e) => setEditTagData({...editTagData, name: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción</label>
                                <input
                                    type="text"
                                    value={editTagData.description}
                                    onChange={(e) => setEditTagData({...editTagData, description: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all"
                                />
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button onClick={handleUpdateTag} className="flex-grow py-5 bg-indigo-600 text-white rounded-[1.5rem] font-black text-sm hover:bg-slate-900 transition-all shadow-xl shadow-indigo-100">
                                    Guardar Cambios
                                </button>
                                <button onClick={() => setEditingTag(null)} className="px-8 py-5 bg-slate-100 text-slate-400 rounded-[1.5rem] font-black text-sm hover:bg-slate-200 transition-all">
                                    Cancelar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {editingGroup && (
                <div className="fixed inset-0 z-[500] flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xl">
                    <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-lg overflow-hidden border border-white/20 animate-zoom-in">
                        <div className="bg-indigo-600 p-10 text-white">
                            <h3 className="text-4xl font-black tracking-tighter mb-1">Editar Grupo</h3>
                            <p className="text-indigo-200 text-[10px] font-black uppercase tracking-widest">{editingGroup.name}</p>
                        </div>
                        <div className="p-10 space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre del Grupo</label>
                                <input 
                                    type="text"
                                    value={editGroupData.name}
                                    onChange={(e) => setEditGroupData({...editGroupData, name: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción</label>
                                <textarea 
                                    value={editGroupData.description}
                                    onChange={(e) => setEditGroupData({...editGroupData, description: e.target.value})}
                                    rows="3"
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all"
                                />
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button 
                                    onClick={handleUpdateGroup}
                                    className="flex-grow py-5 bg-indigo-600 text-white rounded-[1.5rem] font-black text-sm hover:bg-slate-900 transition-all shadow-xl shadow-indigo-100"
                                >
                                    Guardar Cambios
                                </button>
                                <button 
                                    onClick={() => setEditingGroup(null)}
                                    className="px-8 py-5 bg-slate-100 text-slate-400 rounded-[1.5rem] font-black text-sm hover:bg-slate-200 transition-all"
                                >
                                    Cancelar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {isCreatingGroup && (
                <div className="fixed inset-0 z-[500] flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xl">
                    <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-lg overflow-hidden border border-white/20 animate-zoom-in">
                        <div className="bg-slate-900 p-10 text-white">
                            <h3 className="text-4xl font-black tracking-tighter mb-1">Nuevo Grupo</h3>
                            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest">Organización Temática de Cursos</p>
                        </div>
                        <div className="p-10 space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre del Grupo</label>
                                <input 
                                    type="text"
                                    value={newGroup.name}
                                    onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                                    placeholder="Ej: Ciencias, Humanidades, Tecnología"
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all placeholder:text-slate-300"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción</label>
                                <textarea 
                                    value={newGroup.description}
                                    onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                                    rows="3"
                                    placeholder="Describe brevemente de qué trata este grupo..."
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all placeholder:text-slate-300"
                                />
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button 
                                    onClick={handleSaveGroup}
                                    className="flex-grow py-5 bg-indigo-600 text-white rounded-[1.5rem] font-black text-sm hover:bg-slate-900 transition-all shadow-xl shadow-indigo-100"
                                >
                                    Crear Grupo
                                </button>
                                <button 
                                    onClick={() => setIsCreatingGroup(false)}
                                    className="px-8 py-5 bg-slate-100 text-slate-400 rounded-[1.5rem] font-black text-sm hover:bg-slate-200 transition-all"
                                >
                                    Cerrar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {isCreatingTag && (
                <div className="fixed inset-0 z-[500] flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xl">
                    <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-lg overflow-hidden border border-white/20 animate-zoom-in">
                        <div className="bg-slate-900 p-10 text-white">
                            <h3 className="text-4xl font-black tracking-tighter mb-1">Nueva Etiqueta</h3>
                            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest">Especialización de Contenido</p>
                        </div>
                        <div className="p-10 space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Vincular a Grupo</label>
                                <select 
                                    value={newTag.group}
                                    onChange={(e) => setNewTag({...newTag, group: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all appearance-none cursor-pointer"
                                >
                                    <option value="">Seleccione un grupo...</option>
                                    {courseGroups.map(g => (
                                        <option key={g.id} value={g.id}>{g.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre de la Etiqueta</label>
                                <input 
                                    type="text"
                                    value={newTag.name}
                                    onChange={(e) => setNewTag({...newTag, name: e.target.value})}
                                    placeholder="Ej: Matemáticas, Programación, Arte"
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black text-slate-700 outline-none transition-all placeholder:text-slate-300"
                                />
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button 
                                    onClick={handleSaveTag}
                                    className="flex-grow py-5 bg-indigo-600 text-white rounded-[1.5rem] font-black text-sm hover:bg-slate-900 transition-all shadow-xl shadow-indigo-100"
                                >
                                    Guardar Etiqueta
                                </button>
                                <button 
                                    onClick={() => setIsCreatingTag(false)}
                                    className="px-8 py-5 bg-slate-100 text-slate-400 rounded-[1.5rem] font-black text-sm hover:bg-slate-200 transition-all"
                                >
                                    Cerrar
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

    if (loading) return <div className="p-20 text-center">Cargando panel de instructor...</div>;

    return (
        <div className="min-h-screen bg-slate-50 relative flex flex-col">
            {/* Main Header */}
            <header className="bg-white border-b border-slate-100 sticky top-0 z-[100] px-6 lg:px-10 py-6">
                <div className="max-w-[1600px] mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-6">
                        <button 
                            onClick={() => navigate('/dashboard')}
                            className="p-4 bg-slate-50 text-slate-400 hover:bg-slate-900 hover:text-white rounded-[1.5rem] transition-all flex items-center gap-2 group shadow-sm"
                        >
                            <LayoutDashboard size={20} className="group-hover:scale-110 transition-transform" />
                            <span className="text-xs font-black">Dashboard</span>
                        </button>
                        <div className="h-10 w-px bg-slate-100 hidden md:block"></div>
                        <div>
                            <h1 className="text-3xl lg:text-4xl font-black text-slate-900 tracking-tighter flex items-center gap-4">
                                <Settings size={32} className="text-indigo-600" />
                                Panel <span className="text-indigo-600">Docente</span>
                            </h1>
                            <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mt-1 ml-12">
                                Gestión de Cursos y Seguimiento Académico
                            </p>
                        </div>
                    </div>

                    <div className="flex bg-slate-50 p-2 rounded-[2rem] border border-slate-100 shadow-inner">
                        <button 
                            onClick={() => setActiveTab('dashboard')}
                            className={`px-8 py-3 rounded-[1.5rem] text-xs font-black transition-all flex items-center gap-2 ${activeTab === 'dashboard' ? 'bg-white shadow-xl text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                            <BarChart3 size={16} /> Dashboard
                        </button>
                        <button 
                            onClick={() => setActiveTab('courses')}
                            className={`px-8 py-3 rounded-[1.5rem] text-xs font-black transition-all flex items-center gap-2 ${activeTab === 'courses' ? 'bg-white shadow-xl text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                            <BookOpen size={16} /> Mis Cursos
                        </button>
                        <button 
                            onClick={() => setActiveTab('groups')}
                            className={`px-8 py-3 rounded-[1.5rem] text-xs font-black transition-all flex items-center gap-2 ${activeTab === 'groups' ? 'bg-white shadow-xl text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                            <Tag size={16} /> Grupos
                        </button>
                        <button 
                            onClick={() => setActiveTab('all_submissions')}
                            className={`px-8 py-3 rounded-[1.5rem] text-xs font-black transition-all flex items-center gap-2 ${activeTab === 'all_submissions' ? 'bg-white shadow-xl text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                            <FileText size={16} /> Todas las Tareas
                        </button>
                        {isAdmin && (
                            <button 
                                onClick={() => setActiveTab('groups')}
                                className={`px-8 py-3 rounded-[1.5rem] text-xs font-black transition-all flex items-center gap-2 ${activeTab === 'groups' ? 'bg-white shadow-xl text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                            >
                                <Tag size={16} /> Grupos
                            </button>
                        )}
                    </div>

                    <div className="hidden lg:flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest leading-none">Año Lectivo</p>
                            <p className="font-black text-indigo-600 text-sm">{stats.active_year_name}</p>
                        </div>
                        <button 
                            onClick={() => setIsCreating(true)}
                            className="bg-indigo-600 text-white px-8 py-4 rounded-[1.5rem] font-black text-xs hover:bg-slate-900 transition-all shadow-xl shadow-indigo-100 flex items-center gap-3"
                        >
                            <Plus size={20} /> Crear Curso
                        </button>
                    </div>
                </div>
            </header>

            <main className="flex-grow p-6 lg:p-10 max-w-[1600px] mx-auto w-full">

                {activeTab === 'dashboard' && (
                    <div className="space-y-10 animate-fade-in">
                        {/* Stats Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                            {[
                                { label: 'Mis Cursos', value: stats.total_courses, icon: BookOpen, color: 'bg-indigo-50 text-indigo-600', sub: 'Programas Activos' },
                                { label: 'Alumnos Activos', value: stats.active_students, icon: Users, color: 'bg-emerald-50 text-emerald-600', sub: `De ${stats.total_students} matriculados` },
                                { label: 'Tareas Pendientes', value: stats.pending_assignments, icon: Clock, color: 'bg-amber-50 text-amber-600', sub: 'Por calificar' },
                                { label: 'Progreso Promedio', value: '78%', icon: Trophy, color: 'bg-purple-50 text-purple-600', sub: 'Nivel del Centro' },
                            ].map((card, i) => (
                                <div key={i} className="bg-white rounded-[3rem] p-10 border border-slate-100 shadow-xl shadow-slate-200/20 hover:scale-105 transition-all group">
                                    <div className={`w-14 h-14 ${card.color} rounded-2xl flex items-center justify-center mb-6 group-hover:rotate-12 transition-transform`}>
                                        <card.icon size={24} />
                                    </div>
                                    <h3 className="text-5xl font-black text-slate-900 tracking-tighter mb-2">{card.value}</h3>
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{card.label}</p>
                                    <p className="text-xs font-bold text-slate-300 mt-1">{card.sub}</p>
                                </div>
                            ))}
                        </div>

                        {/* Visual Analytics / Promotion */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
                            <div className="lg:col-span-2 bg-white rounded-[3rem] p-12 border border-slate-100 shadow-2xl shadow-slate-200/10">
                                <div className="flex items-center justify-between mb-10">
                                    <h3 className="text-3xl font-black text-slate-900 tracking-tight">Estatus de Participación</h3>
                                    <div className="flex gap-2">
                                        <button className="px-5 py-2 bg-slate-50 text-[10px] font-black text-slate-400 border border-slate-100 rounded-xl hover:bg-slate-100">Hoy</button>
                                        <button className="px-5 py-2 bg-indigo-50 text-[10px] font-black text-indigo-600 border border-indigo-100 rounded-xl">Año Lectivo</button>
                                    </div>
                                </div>
                                <div className="h-64 flex items-center justify-center border-2 border-dashed border-slate-100 rounded-[2rem]">
                                    <p className="text-slate-300 font-bold uppercase tracking-widest text-xs">Visión General del Rendimiento Alumnos Registrados</p>
                                </div>
                            </div>

                            <div className="bg-indigo-600 rounded-[3rem] p-12 text-white shadow-2xl shadow-indigo-200 flex flex-col justify-between">
                                <div>
                                    <Sparkles className="text-indigo-200 mb-6" size={40} />
                                    <h3 className="text-4xl font-black tracking-tighter leading-none mb-4">Eduka AI <br/>Analytics</h3>
                                    <p className="text-indigo-100/70 font-medium leading-relaxed">Próximamente: Obtén reportes detallados y predicciones de deserción basados en el comportamiento de tus alumnos.</p>
                                </div>
                                <button className="mt-8 w-full py-4 bg-white/10 hover:bg-white/20 border border-white/20 rounded-2xl font-black text-xs transition-all">Configurar Notificaciones AI</button>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'courses' && (
                    <div className="space-y-8 animate-fade-in">

            {/* Group Dropdown Filter + Table */}
            <div className="bg-white rounded-[4rem] border border-slate-100 shadow-sm overflow-hidden">
                <div className="p-10 border-b border-slate-50 flex flex-wrap items-center gap-4 justify-between">
                    <div className="flex items-center gap-4">
                        <h2 className="text-2xl font-black text-slate-900 tracking-tight">Mis Cursos</h2>
                        <select
                            value={courseGroupFilter}
                            onChange={(e) => setCourseGroupFilter(e.target.value)}
                            className="bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl px-5 py-2.5 font-bold text-slate-600 outline-none transition-all text-xs appearance-none cursor-pointer"
                        >
                            <option value="all">Todos los Grupos</option>
                            {courseGroups.map(g => (
                                <option key={g.id} value={String(g.id)}>{g.name}</option>
                            ))}
                        </select>
                        {courseGroupFilter !== 'all' && (
                            <span className="text-[10px] font-black text-slate-300 uppercase tracking-widest">
                                {courses.filter(c => tags.filter(t => t.group === Number(courseGroupFilter)).some(t => t.id === c.tag_id || t.id === c.tag)).length} cursos
                            </span>
                        )}
                    </div>
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
                            {courses
                              .filter(course => {
                                if (courseGroupFilter === 'all') return true;
                                const groupTags = tags.filter(t => t.group === Number(courseGroupFilter));
                                return groupTags.some(t => t.id === course.tag_id || t.id === course.tag);
                              })
                              .map(course => (
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
        </div>
    )}

                {activeTab === 'all_submissions' && (
                    <div className="space-y-8 animate-fade-in">
                        <div className="flex items-center justify-between">
                            <div>
                                <h2 className="text-3xl font-black text-slate-900 tracking-tight">Centro de <span className="text-indigo-600">Tareas</span></h2>
                                <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mt-1">Gestión Centralizada de Entregas</p>
                            </div>
                            <div className="flex gap-4">
                                <button 
                                    onClick={() => handleExport('csv')}
                                    disabled={isExporting}
                                    className="px-6 py-3 bg-white border border-slate-100 rounded-2xl text-xs font-black text-slate-600 hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm"
                                >
                                    <FileDown size={18} /> Exportar CSV
                                </button>
                                <button 
                                    onClick={() => handleExport('excel')}
                                    disabled={isExporting}
                                    className="px-6 py-3 bg-white border border-slate-100 rounded-2xl text-xs font-black text-slate-600 hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm"
                                >
                                    <FileDown size={18} /> Exportar Excel
                                </button>
                                <button 
                                    onClick={() => handleExport('pdf')}
                                    disabled={isExporting}
                                    className="px-6 py-3 bg-white border border-slate-100 rounded-2xl text-xs font-black text-slate-600 hover:bg-slate-50 transition-all flex items-center gap-2 shadow-sm"
                                >
                                    <FileText size={18} /> Reporte PDF
                                </button>
                            </div>
                        </div>

                        <div className="bg-white rounded-[3rem] border border-slate-100 shadow-xl overflow-hidden p-10">
                            <div className="flex items-center justify-between mb-8">
                                <div className="flex gap-4">
                                    <select
                                        className="bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl px-6 py-3 font-bold text-slate-700 outline-none transition-all text-xs appearance-none cursor-pointer"
                                        onChange={(e) => fetchUnifiedSubmissions(e.target.value || null)}
                                    >
                                        <option value="">Todos los Grupos</option>
                                        {courseGroups.map(g => (
                                            <option key={g.id} value={g.id}>{g.name}</option>
                                        ))}
                                    </select>
                                    <select className="bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl px-6 py-3 font-bold text-slate-700 outline-none transition-all text-xs appearance-none cursor-pointer">
                                        <option>Solo Pendientes</option>
                                        <option>Calificados</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-slate-50">
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Alumno</th>
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Tarea / Curso</th>
                                            <th className="px-6 py-4 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Fecha Envío</th>
                                            <th className="px-6 py-4 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">Acciones</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-50">
                                        {unifiedSubmissions.length > 0 ? (
                                            unifiedSubmissions.map((sub) => (
                                                <tr key={sub.id} className="group hover:bg-slate-50/50 transition-all">
                                                    <td className="px-6 py-4 font-black text-slate-700 text-xs">
                                                        {sub.student_name}
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <p className="font-bold text-slate-900 text-xs">{sub.assignment_title}</p>
                                                        <p className="text-[10px] text-indigo-500 font-black">{sub.course_title}</p>
                                                    </td>
                                                    <td className="px-6 py-4 text-xs text-slate-400 font-bold">
                                                        {new Date(sub.submitted_at).toLocaleDateString()}
                                                    </td>
                                                    <td className="px-6 py-4 text-right">
                                                        <button 
                                                            onClick={() => {
                                                                setSelectedAssignmentSub(sub);
                                                                setIsViewingSubmissions(true);
                                                                setSubmissions([sub]); // Show this specific one in modal
                                                                setGradingData({ score: sub.score || '', teacher_feedback: sub.teacher_feedback || '' });
                                                            }}
                                                            className={`px-4 py-2 rounded-xl text-[10px] font-black transition-all ${sub.score === null ? 'bg-amber-500 text-white hover:bg-slate-900 shadow-lg shadow-amber-100' : 'bg-slate-100 text-slate-400'}`}
                                                        >
                                                            {sub.score === null ? 'Calificar' : `Nota: ${sub.score}`}
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr className="group hover:bg-slate-50/50 transition-all">
                                                <td className="px-6 py-6" colSpan="4">
                                                    <div className="flex flex-col items-center py-20 opacity-20">
                                                        <Clock size={48} className="mb-4" />
                                                        <p className="font-black">No hay tareas pendientes por procesar</p>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'groups' && renderGroups()}
            </main>

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
                                            <button 
                                                onClick={() => setActiveTab('assignments')}
                                                className={`px-6 py-2 rounded-lg text-xs font-black transition-all ${activeTab === 'assignments' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                                            >
                                                Tareas
                                            </button>
                                            <button 
                                                onClick={() => setActiveTab('students')}
                                                className={`px-6 py-2 rounded-lg text-xs font-black transition-all ${activeTab === 'students' ? 'bg-white shadow-sm text-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}
                                            >
                                                Estudiantes
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
                                        ) : activeTab === 'quiz' ? (
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
                                        ) : activeTab === 'students' ? (
                                            /* Students Management Section */
                                            <div className="space-y-6 animate-fade-in pb-20">
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <h4 className="text-xl font-black text-slate-900 tracking-tight">Gestión de Alumnos</h4>
                                                        <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1">Total: {courseEnrollments.length} inscritos</p>
                                                    </div>
                                                    <button 
                                                        onClick={handleSyncStudents}
                                                        disabled={isSyncingStudents}
                                                        className="px-6 py-3 bg-emerald-500 text-white rounded-2xl font-black text-xs flex items-center gap-3 hover:bg-emerald-600 transition-all shadow-lg active:scale-95 disabled:opacity-50"
                                                    >
                                                        <Users size={18} /> {isSyncingStudents ? 'Sincronizando...' : 'Sincronizar Alumnos Académicos'}
                                                    </button>
                                                </div>

                                                <div className="bg-white rounded-[2.5rem] border border-slate-100 shadow-xl overflow-hidden">
                                                    <table className="w-full border-collapse">
                                                        <thead>
                                                            <tr className="bg-slate-50/50 border-b border-slate-100">
                                                                <th className="px-8 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Alumno</th>
                                                                <th className="px-8 py-6 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Progreso</th>
                                                                <th className="px-8 py-6 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest">Última Actividad</th>
                                                                <th className="px-8 py-6 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">Estado</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody className="divide-y divide-slate-50">
                                                            {courseEnrollments.map((enr) => (
                                                                <tr key={enr.id} className="hover:bg-slate-50/30 transition-colors">
                                                                    <td className="px-8 py-6">
                                                                        <div className="flex items-center gap-4">
                                                                            <div className="w-12 h-12 bg-indigo-100 rounded-2xl flex items-center justify-center font-black text-indigo-600">
                                                                                {enr.student_name?.[0] || 'U'}
                                                                            </div>
                                                                            <div>
                                                                                <div className="font-black text-slate-900">{enr.student_name}</div>
                                                                                <div className="text-[10px] text-slate-400 font-bold">{enr.student_email}</div>
                                                                            </div>
                                                                        </div>
                                                                    </td>
                                                                    <td className="px-8 py-6 w-1/4">
                                                                        <div className="space-y-2">
                                                                            <div className="flex items-center justify-between text-[10px] font-black mr-2">
                                                                                <span className="text-indigo-600">{enr.progress_percentage}%</span>
                                                                            </div>
                                                                            <div className="h-2 bg-slate-100 rounded-full overflow-hidden mr-2">
                                                                                <div 
                                                                                    className="h-full bg-indigo-500 rounded-full transition-all duration-1000"
                                                                                    style={{ width: `${enr.progress_percentage}%` }}
                                                                                ></div>
                                                                            </div>
                                                                        </div>
                                                                    </td>
                                                                    <td className="px-8 py-6 text-center">
                                                                        <div className="text-xs font-bold text-slate-600">
                                                                            {enr.last_activity ? new Date(enr.last_activity).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'No ha iniciado'}
                                                                        </div>
                                                                    </td>
                                                                    <td className="px-8 py-6 text-right">
                                                                        <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-tighter ${
                                                                            enr.status === 'active' ? 'bg-emerald-100 text-emerald-600' : 
                                                                            enr.status === 'completed' ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-400'
                                                                        }`}>
                                                                            {enr.status}
                                                                        </span>
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                            {courseEnrollments.length === 0 && (
                                                                <tr>
                                                                    <td colSpan="4" className="px-8 py-20 text-center">
                                                                        <div className="flex flex-col items-center opacity-20">
                                                                            <Users size={64} className="mb-4" />
                                                                            <p className="text-xl font-bold">No hay alumnos inscritos en este curso</p>
                                                                        </div>
                                                                    </td>
                                                                </tr>
                                                            )}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        ) : (
                                            /* Assignments Section */
                                            <div className="space-y-6 animate-fade-in pb-20">
                                                <div className="flex items-center justify-between">
                                                    <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">Tareas del Módulo</h4>
                                                    <button 
                                                        onClick={() => {
                                                            setAssignmentData({ title: '', description: '', due_date: '', max_score: 10 });
                                                            setIsAddingAssignment(true);
                                                        }}
                                                        className="px-6 py-3 bg-indigo-600 text-white rounded-2xl font-black text-[10px] flex items-center gap-2 hover:bg-slate-900 transition-all shadow-xl"
                                                    >
                                                        <Plus size={14} /> Nueva Tarea
                                                    </button>
                                                </div>

                                                <div className="grid grid-cols-1 gap-6">
                                                    {activeModule.assignments?.length > 0 ? (
                                                        activeModule.assignments.map((assignment, idx) => (
                                                            <div key={assignment.id} className="bg-white rounded-[2.5rem] p-8 border border-slate-100 shadow-sm flex items-center justify-between group">
                                                                <div className="flex items-center gap-6">
                                                                    <div className="w-14 h-14 bg-amber-50 rounded-2xl flex items-center justify-center text-amber-600">
                                                                        <Calendar size={24} />
                                                                    </div>
                                                                    <div>
                                                                        <h5 className="text-xl font-black text-slate-900">{assignment.title}</h5>
                                                                        <div className="flex items-center gap-4 mt-1">
                                                                            <span className="text-[10px] font-black text-slate-400 uppercase">Vence: {new Date(assignment.due_date).toLocaleDateString()}</span>
                                                                            <span className="text-[10px] font-black text-indigo-500 uppercase">Pts: {assignment.max_score}</span>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-3">
                                                                    <button 
                                                                        onClick={() => fetchSubmissions(assignment)}
                                                                        className="p-3 bg-indigo-50 text-indigo-400 hover:text-indigo-700 rounded-xl transition-all flex items-center gap-2"
                                                                        title="Ver Entregas"
                                                                    >
                                                                        <Users size={18} />
                                                                        {assignment.submissions_count > 0 && <span className="text-[10px] font-black">{assignment.submissions_count}</span>}
                                                                    </button>
                                                                    <button 
                                                                        onClick={() => {
                                                                            setEditingAssignment(assignment);
                                                                            setAssignmentData(assignment);
                                                                            setIsAddingAssignment(true);
                                                                        }}
                                                                        className="p-3 bg-slate-50 text-slate-400 hover:text-indigo-600 rounded-xl transition-all"
                                                                    >
                                                                        <Edit size={18} />
                                                                    </button>
                                                                    <button 
                                                                        onClick={() => handleDeleteAssignment(assignment.id)}
                                                                        className="p-3 bg-slate-50 text-slate-400 hover:text-red-500 rounded-xl transition-all"
                                                                    >
                                                                        <Trash2 size={18} />
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        ))
                                                    ) : (
                                                        <div className="py-20 text-center bg-white rounded-[3rem] border border-dashed border-slate-200">
                                                            <FileText size={48} className="mx-auto text-slate-200 mb-4" />
                                                            <p className="text-slate-400 font-bold">No hay tareas creadas aún.</p>
                                                        </div>
                                                    )}
                                                </div>
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
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Grupo</label>
                                    <select 
                                        value={selectedGroup}
                                        onChange={(e) => setSelectedGroup(e.target.value)}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all appearance-none"
                                    >
                                        <option value="">Seleccionar Grupo</option>
                                        {courseGroups.map(g => (
                                            <option key={g.id} value={g.id}>{g.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Etiqueta</label>
                                    <select 
                                        value={newCourse.tag_id || ''}
                                        onChange={(e) => setNewCourse({...newCourse, tag_id: e.target.value})}
                                        className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-bold text-slate-700 outline-none transition-all appearance-none"
                                        disabled={!selectedGroup}
                                    >
                                        <option value="">Seleccionar Etiqueta</option>
                                        {tags.map(tag => (
                                            <option key={tag.id} value={tag.id}>{tag.name}</option>
                                        ))}
                                    </select>
                                </div>
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
                                    rows="3"
                                    defaultValue={editingLesson?.content}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl p-3 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="Describe brevemente los objetivos de esta lección..."
                                ></textarea>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black text-indigo-500 uppercase tracking-widest ml-1 font-black">Enlace Clase en Vivo (Zoom/Meet)</label>
                                    <div className="relative">
                                        <Link size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-400" />
                                        <input 
                                            id="lesson-meeting-url"
                                            type="url" 
                                            defaultValue={editingLesson?.meeting_url}
                                            className="w-full bg-indigo-50/30 border-2 border-transparent focus:border-indigo-500 rounded-xl py-3 pl-11 pr-4 font-bold text-slate-700 outline-none transition-all"
                                            placeholder="https://zoom.us/j/..."
                                        />
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-black text-indigo-500 uppercase tracking-widest ml-1 font-black">Fecha y Hora Programada</label>
                                    <input 
                                        id="lesson-meeting-date"
                                        type="datetime-local" 
                                        defaultValue={editingLesson?.meeting_date ? new Date(editingLesson.meeting_date).toISOString().slice(0, 16) : ''}
                                        className="w-full bg-indigo-50/30 border-2 border-transparent focus:border-indigo-500 rounded-xl p-3 font-bold text-slate-700 outline-none transition-all"
                                    />
                                </div>
                            </div>
                        </div>
                        <div className="p-8 border-t border-slate-50 bg-slate-50 flex gap-3">
                            <button 
                                onClick={() => {
                                    const title = document.getElementById('lesson-title').value;
                                    const video_url = document.getElementById('lesson-video').value;
                                    const content = document.getElementById('lesson-content').value;
                                    const meeting_url = document.getElementById('lesson-meeting-url').value;
                                    const meeting_date = document.getElementById('lesson-meeting-date').value;
                                    handleSaveLesson({ title, video_url, content, meeting_url, meeting_date });
                                }}
                                className="flex-grow py-3 bg-slate-900 text-white rounded-2xl font-black hover:bg-indigo-600 transition-all shadow-lg"
                            >
                                <Save size={18} className="inline-block mr-2" /> Guardar Lección
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Assignment Editor Modal */}
            {isAddingAssignment && (
                <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-xl flex items-center justify-center z-[300] p-6 overflow-y-auto">
                    <form onSubmit={handleSaveAssignment} className="bg-white w-full max-w-xl rounded-[3rem] shadow-2xl overflow-hidden animate-zoom-in my-auto">
                        <div className="p-8 border-b border-slate-50 bg-slate-50 flex items-center justify-between">
                            <h3 className="text-xl font-black tracking-tight">{editingAssignment ? 'Editar Tarea' : 'Nueva Tarea'}</h3>
                            <button type="button" onClick={() => { setIsAddingAssignment(false); setEditingAssignment(null); }} className="p-2 hover:bg-white rounded-full transition-all"><X size={20}/></button>
                        </div>
                        <div className="p-8 space-y-6">
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Título de la Tarea</label>
                                <input 
                                    type="text" 
                                    required
                                    value={assignmentData.title}
                                    onChange={(e) => setAssignmentData({...assignmentData, title: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl p-4 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="Ej: Ensayo sobre la Revolución Industrial"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Fecha de Entrega</label>
                                <input 
                                    type="datetime-local" 
                                    required
                                    value={assignmentData.due_date ? new Date(assignmentData.due_date).toISOString().slice(0, 16) : ''}
                                    onChange={(e) => setAssignmentData({...assignmentData, due_date: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl p-4 font-bold text-slate-700 outline-none transition-all"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Puntaje Máximo</label>
                                <input 
                                    type="number" 
                                    required
                                    value={assignmentData.max_score}
                                    onChange={(e) => setAssignmentData({...assignmentData, max_score: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl p-4 font-bold text-slate-700 outline-none transition-all"
                                />
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Instrucciones</label>
                                <textarea 
                                    rows="4"
                                    value={assignmentData.description}
                                    onChange={(e) => setAssignmentData({...assignmentData, description: e.target.value})}
                                    className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-xl p-4 font-bold text-slate-700 outline-none transition-all"
                                    placeholder="Instrucciones detalladas para los alumnos..."
                                ></textarea>
                            </div>
                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1 text-indigo-600 font-black">Sincronización Académica (Opcional)</label>
                                <select 
                                    value={assignmentData.academic_category || ''}
                                    onChange={(e) => setAssignmentData({...assignmentData, academic_category: e.target.value})}
                                    className="w-full bg-indigo-50/50 border-2 border-dashed border-indigo-100 focus:border-indigo-500 rounded-xl p-4 font-bold text-slate-700 outline-none transition-all appearance-none"
                                >
                                    <option value="">Solo LMS (No se pasa al registro oficial)</option>
                                    {evaluationCategories.map(cat => (
                                        <option key={cat.id} value={cat.id}>
                                            {cat.name} ({cat.weight}%) {cat.trimester ? `- Trimestre ${cat.trimester}` : ''}
                                        </option>
                                    ))}
                                </select>
                                <p className="text-[9px] text-slate-400 mt-1 px-1">
                                    Vincular con un aporte académico oficial para pasar las notas automáticamente.
                                </p>
                            </div>

                            <div className="space-y-1">
                                <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Material de Apoyo (Opcional)</label>
                                <input 
                                    type="file" 
                                    onChange={(e) => setAssignmentData({...assignmentData, file: e.target.files[0]})}
                                    className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-[10px] file:font-black file:bg-indigo-50 file:text-indigo-600 hover:file:bg-indigo-100"
                                />
                            </div>
                        </div>
                        <div className="p-8 border-t border-slate-50 bg-slate-50">
                            <button 
                                type="submit"
                                className="w-full py-4 bg-slate-900 text-white rounded-2xl font-black hover:bg-indigo-600 transition-all shadow-lg flex items-center justify-center gap-2"
                            >
                                <Save size={18} /> Guardar Tarea
                            </button>
                        </div>
                    </form>
                </div>
            )}
            {/* Submissions Grading Modal */}
            {isViewingSubmissions && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 lg:p-12">
                    <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-xl" onClick={() => setIsViewingSubmissions(false)}></div>
                    <div className="relative bg-white w-full max-w-6xl h-full max-h-[90vh] rounded-[3.5rem] shadow-2xl flex flex-col overflow-hidden animate-spring-up">
                        <div className="p-8 lg:p-12 border-b border-slate-50 flex items-center justify-between bg-slate-50/50">
                            <div>
                                <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-2">Entregas de Estudiantes</h2>
                                <p className="text-slate-400 font-bold uppercase text-xs tracking-widest">{selectedAssignmentSub?.title}</p>
                            </div>
                            <button onClick={() => setIsViewingSubmissions(false)} className="w-14 h-14 bg-white border border-slate-100 rounded-3xl flex items-center justify-center text-slate-400 hover:text-slate-900 hover:shadow-xl transition-all">
                                <X size={24} />
                            </button>
                        </div>
                        
                        <div className="flex-grow overflow-y-auto p-8 lg:p-12">
                            {submissions.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center opacity-30">
                                    <Users size={80} className="mb-6" />
                                    <p className="text-xl font-bold">Aún no hay entregas para calificar</p>
                                </div>
                            ) : (
                                <div className="space-y-6">
                                    <div className="grid grid-cols-12 gap-6 pb-4 border-b border-slate-50 px-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                        <div className="col-span-3">Estudiante</div>
                                        <div className="col-span-3">Archivo</div>
                                        <div className="col-span-2 text-center">Enviado</div>
                                        <div className="col-span-2 text-center">Calificación</div>
                                        <div className="col-span-2 text-right">Acciones</div>
                                    </div>
                                    
                                    {submissions.map((sub) => (
                                        <div key={sub.id} className="grid grid-cols-12 gap-6 items-center p-6 bg-slate-50/50 rounded-3xl border border-slate-50 hover:bg-white hover:shadow-xl hover:border-indigo-100 transition-all group">
                                            <div className="col-span-3 font-black text-slate-700">{sub.student_name}</div>
                                            <div className="col-span-3">
                                                <a href={sub.file} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-indigo-600 font-black text-sm hover:underline decoration-2">
                                                    <Download size={16} /> Ver Trabajo
                                                </a>
                                            </div>
                                            <div className="col-span-2 text-center text-[10px] font-black text-slate-400">
                                                {new Date(sub.submitted_at).toLocaleDateString()}
                                            </div>
                                            <div className="col-span-2 flex justify-center">
                                                {sub.score !== null ? (
                                                    <span className="px-4 py-1.5 bg-emerald-500 text-white rounded-xl text-xs font-black shadow-lg shadow-emerald-500/20">
                                                        {sub.score} / {selectedAssignmentSub.max_score}
                                                    </span>
                                                ) : (
                                                    <span className="px-4 py-1.5 bg-slate-200 text-slate-500 rounded-xl text-xs font-black uppercase tracking-widest">Pendiente</span>
                                                )}
                                            </div>
                                            <div className="col-span-2 flex justify-end">
                                                <button 
                                                    onClick={() => {
                                                        setGradingData({ score: sub.score || '', teacher_feedback: sub.teacher_feedback || '' });
                                                        // Inlined quick form or toggle
                                                        const el = document.getElementById(`grading-form-${sub.id}`);
                                                        el.classList.toggle('hidden');
                                                    }}
                                                    className="px-6 py-2 bg-slate-900 text-white rounded-xl font-black text-[10px] hover:bg-indigo-600 transition-all shadow-md"
                                                >
                                                    {sub.score !== null ? 'Editar' : 'Calificar'}
                                                </button>
                                            </div>
                                            
                                            {/* Grading Quick Form */}
                                            <div id={`grading-form-${sub.id}`} className="col-span-12 mt-6 p-8 bg-white rounded-[2rem] border border-indigo-100 shadow-inner hidden animate-fade-in">
                                                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                                                    <div className="space-y-3">
                                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Nota / {selectedAssignmentSub.max_score}</label>
                                                        <input 
                                                            type="number"
                                                            value={gradingData.score}
                                                            onChange={(e) => setGradingData({...gradingData, score: e.target.value})}
                                                            className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black outline-none transition-all"
                                                            max={selectedAssignmentSub.max_score}
                                                        />
                                                    </div>
                                                    <div className="md:col-span-2 space-y-3">
                                                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Feedback / Observaciones</label>
                                                        <input 
                                                            type="text"
                                                            value={gradingData.teacher_feedback}
                                                            onChange={(e) => setGradingData({...gradingData, teacher_feedback: e.target.value})}
                                                            className="w-full bg-slate-50 border-2 border-transparent focus:border-indigo-500 rounded-2xl p-4 font-black outline-none transition-all"
                                                            placeholder="Buen trabajo..."
                                                        />
                                                    </div>
                                                    <div className="flex items-end">
                                                        <button 
                                                            onClick={() => handleUpdateGrade(sub.id)}
                                                            disabled={isSubmittingGrade}
                                                            className="w-full py-4 bg-indigo-600 text-white rounded-2xl font-black text-sm shadow-xl shadow-indigo-500/20 hover:bg-slate-900 transition-all disabled:opacity-50"
                                                        >
                                                            {isSubmittingGrade ? 'Guardando...' : 'Guardar Calificación'}
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default InstructorDashboard;
