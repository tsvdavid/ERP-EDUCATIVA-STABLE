import React, { useState, useEffect } from 'react';
import academicService from '../../services/academicService';
import { Calendar, Plus, Trash2, Clock, MapPin, User as UserIcon, Book } from 'lucide-react';
import toast from 'react-hot-toast';

const DAYS_OF_WEEK = [
    { id: 1, name: 'Lunes' },
    { id: 2, name: 'Martes' },
    { id: 3, name: 'Miércoles' },
    { id: 4, name: 'Jueves' },
    { id: 5, name: 'Viernes' },
];

const CourseScheduleManager = () => {
    const [courses, setCourses] = useState([]);
    const [selectedCourseId, setSelectedCourseId] = useState('');
    const [subjects, setSubjects] = useState([]);
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);

    const [formData, setFormData] = useState({
        subject: '',
        day_of_week: 1,
        start_time: '08:00',
        end_time: '08:45'
    });

    useEffect(() => {
        const fetchBaseData = async () => {
            try {
                const c = await academicService.getCourses();
                setCourses(c);
            } catch (error) {
                toast.error("Error cargando cursos");
            } finally {
                setLoading(false);
            }
        };
        fetchBaseData();
    }, []);

    useEffect(() => {
        if (selectedCourseId) {
            loadCourseData(selectedCourseId);
        } else {
            setSubjects([]);
            setSchedules([]);
        }
    }, [selectedCourseId]);

    const loadCourseData = async (courseId) => {
        setLoading(true);
        try {
            const [subs, scheds] = await Promise.all([
                academicService.getSubjects(),
                academicService.getSchedules(courseId)
            ]);
            setSubjects(subs.filter(s => s.course.id == courseId || s.course == courseId));
            setSchedules(scheds);
        } catch (error) {
            toast.error("Error al cargar los datos del curso");
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        try {
            await academicService.createSchedule(formData);
            toast.success("Bloque de horario creado");
            if (selectedCourseId) {
                loadCourseData(selectedCourseId);
            }
        } catch (error) {
            toast.error("Error al guardar el bloque. Verifica que no existan cruces de hora exactos.");
        }
    };

    const handleDelete = async (id) => {
        try {
            await academicService.deleteSchedule(id);
            toast.success("Bloque eliminado");
            loadCourseData(selectedCourseId);
        } catch (error) {
            toast.error("Error al eliminar el bloque");
        }
    };

    const getSchedulesForDay = (dayId) => {
        return schedules.filter(s => s.day_of_week === dayId).sort((a, b) => a.start_time.localeCompare(b.start_time));
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto h-full pb-10">
            <div className="bg-gradient-to-r from-teal-500 to-emerald-600 rounded-2xl p-6 md:p-8 text-white shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10"><Calendar size={120} /></div>
                <div className="relative z-10">
                    <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
                        <Calendar size={32} /> Configurador de Malla Curricular
                    </h1>
                    <p className="text-teal-100 mt-2 max-w-2xl text-lg">
                        Selecciona un curso y estructura visualmente las horas semanales para cada materia y profesor.
                    </p>
                </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                <span className="font-bold text-slate-700 whitespace-nowrap">Gestionar Curso:</span>
                <select 
                    className="flex-1 max-w-md p-3 border border-slate-300 rounded-lg text-slate-700 focus:ring-2 focus:ring-teal-500 focus:border-teal-500 font-medium"
                    value={selectedCourseId}
                    onChange={(e) => setSelectedCourseId(e.target.value)}
                >
                    <option value="">-- Selecciona un curso --</option>
                    {courses.map(c => (
                        <option key={c.id} value={c.id}>{c.name} {c.parallel} ({c.year})</option>
                    ))}
                </select>
            </div>

            {!selectedCourseId ? (
                <div className="bg-white p-12 rounded-2xl shadow-sm text-center border border-slate-200 text-slate-500">
                    <Clock size={48} className="mx-auto mb-4 text-slate-300" />
                    <p className="text-lg">Selecciona un curso en la parte superior para comenzar a armar su horario.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Panel Agregar */}
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
                        <h3 className="text-lg font-black text-slate-800 flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
                            <Plus size={18} className="text-teal-500"/> Nuevo Bloque
                        </h3>
                        {subjects.length === 0 ? (
                            <div className="text-sm text-amber-600 bg-amber-50 p-4 rounded-lg flex gap-2">
                                Este curso aún no tiene materias asignadas.
                            </div>
                        ) : (
                            <form onSubmit={handleCreate} className="space-y-4">
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Materia</label>
                                    <select 
                                        required
                                        className="w-full p-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500"
                                        value={formData.subject}
                                        onChange={e => setFormData({...formData, subject: e.target.value})}
                                    >
                                        <option value="">Seleccionar Materia...</option>
                                        {subjects.map(s => (
                                            <option key={s.id} value={s.id}>{s.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Día</label>
                                    <select 
                                        required
                                        className="w-full p-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500"
                                        value={formData.day_of_week}
                                        onChange={e => setFormData({...formData, day_of_week: parseInt(e.target.value)})}
                                    >
                                        {DAYS_OF_WEEK.map(d => (
                                            <option key={d.id} value={d.id}>{d.name}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Hora Inicio</label>
                                        <input 
                                            type="time" required
                                            className="w-full p-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500"
                                            value={formData.start_time}
                                            onChange={e => setFormData({...formData, start_time: e.target.value})}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Hora Fin</label>
                                        <input 
                                            type="time" required
                                            className="w-full p-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-teal-500"
                                            value={formData.end_time}
                                            onChange={e => setFormData({...formData, end_time: e.target.value})}
                                        />
                                    </div>
                                </div>
                                <button type="submit" className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3 rounded-xl transition-colors shadow-sm flex items-center justify-center gap-2">
                                    <Plus size={18} /> Agregar al Horario
                                </button>
                            </form>
                        )}
                    </div>

                    {/* Visor Horario */}
                    <div className="lg:col-span-3 bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="p-4 bg-slate-50 border-b border-slate-200">
                            <h3 className="font-bold text-slate-700 flex items-center gap-2"><MapPin size={18} className="text-slate-400" /> Distribución Semanal</h3>
                        </div>
                        {loading ? (
                            <div className="p-8 text-center text-slate-400">Cargando horario...</div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-slate-200">
                                {DAYS_OF_WEEK.map(day => (
                                    <div key={day.id} className="min-h-[500px] bg-slate-50/50">
                                        <div className="bg-slate-100 py-3 text-center border-b border-slate-200">
                                            <span className="font-black text-slate-700 uppercase tracking-wide text-xs">{day.name}</span>
                                        </div>
                                        <div className="p-2 flex flex-col gap-2">
                                            {getSchedulesForDay(day.id).length === 0 ? (
                                                <div className="text-center p-4 text-xs font-medium text-slate-400 border border-dashed border-slate-300 rounded-xl bg-white/50">Libre</div>
                                            ) : (
                                                getSchedulesForDay(day.id).map(sched => (
                                                    <div key={sched.id} className="bg-white border border-teal-100 rounded-xl p-3 shadow-sm hover:shadow-md transition-shadow relative group">
                                                        <button 
                                                            onClick={() => handleDelete(sched.id)}
                                                            className="absolute top-2 right-2 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                                                            title="Eliminar bloque"
                                                        >
                                                            <Trash2 size={16} />
                                                        </button>
                                                        <div className="flex items-center gap-1 mb-1 text-teal-600 font-bold text-xs bg-teal-50 px-2 py-0.5 rounded w-max">
                                                            <Clock size={12} /> {sched.start_time.substring(0,5)} - {sched.end_time.substring(0,5)}
                                                        </div>
                                                        <p className="font-bold text-slate-800 text-sm leading-tight mb-2"><Book className="inline mr-1 text-slate-400" size={12}/>{sched.subject_name}</p>
                                                        <p className="text-xs text-slate-500 font-medium truncate flex items-center gap-1"><UserIcon size={12} className="text-slate-400"/> Prof: {sched.teacher_name || 'Sin Asignar'}</p>
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default CourseScheduleManager;
