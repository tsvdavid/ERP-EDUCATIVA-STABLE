import React, { useState, useEffect } from 'react';
import academicService from '../../services/academicService';
import { useAuthStore } from '../../context/authStore';
import { Calendar, Clock, MapPin, User as UserIcon, Book, BookOpen } from 'lucide-react';
import toast from 'react-hot-toast';
import userService from '../../services/userService';

const DAYS_OF_WEEK = [
    { id: 1, name: 'Lunes' },
    { id: 2, name: 'Martes' },
    { id: 3, name: 'Miércoles' },
    { id: 4, name: 'Jueves' },
    { id: 5, name: 'Viernes' },
];

const parseTime = (timeStr) => {
    // timeStr shape: "08:00:00"
    if (!timeStr) return '';
    return timeStr.substring(0, 5);
};

const MySchedulePage = () => {
    const { user } = useAuthStore();
    const [schedules, setSchedules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedChildId, setSelectedChildId] = useState(null);
    const [children, setChildren] = useState([]);

    const isParent = user?.role === 'PARENT';

    useEffect(() => {
        // If parent, fetch children info first using getMe equivalent or we can just use user.children if populated
        const init = async () => {
            if (isParent) {
                // Fetch full info of the parent if user.children is just IDs or not populated.
                try {
                    const fullUser = await userService.getMe();
                    if (fullUser.children && fullUser.children.length > 0) {
                        setChildren(fullUser.children);
                        setSelectedChildId(fullUser.children[0].id);
                    } else {
                        setLoading(false); // No children
                    }
                } catch (error) {
                    console.error("Error fetching parent details", error);
                    setLoading(false);
                }
            } else {
                fetchMySchedule();
            }
        };
        init();
    }, [isParent]);

    useEffect(() => {
        if (isParent && selectedChildId) {
            fetchMySchedule(selectedChildId);
        }
    }, [selectedChildId]);

    const fetchMySchedule = async (studentId = null) => {
        setLoading(true);
        try {
            const scheds = await academicService.getSchedules(null, studentId);
            setSchedules(scheds);
        } catch (error) {
            toast.error("Error cargando el horario de clases");
        } finally {
            setLoading(false);
        }
    };

    const getSchedulesForDay = (dayId) => {
        return schedules.filter(s => s.day_of_week === dayId).sort((a, b) => a.start_time.localeCompare(b.start_time));
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto h-full pb-10">
            <div className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-6 md:p-8 text-white shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10"><Calendar size={120} /></div>
                <div className="relative z-10">
                    <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
                        <BookOpen size={32} /> Mi Horario de Clases
                    </h1>
                    <p className="text-teal-100 mt-2 max-w-2xl text-lg">
                        {isParent 
                            ? "Consulta el horario semanal en tiempo real de tus representados."
                            : "Revisa tu planificación semanal y conoce en qué aula o materia debes estar."}
                    </p>
                </div>
            </div>

            {isParent && children.length > 0 && (
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-4">
                    <span className="font-bold text-slate-700 whitespace-nowrap">Ver horario de:</span>
                    <select 
                        className="flex-1 max-w-md p-3 border border-slate-300 rounded-lg text-slate-700 focus:ring-2 focus:ring-teal-500 font-medium"
                        value={selectedChildId || ''}
                        onChange={(e) => setSelectedChildId(e.target.value)}
                    >
                        {children.map(c => (
                            <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>
                        ))}
                    </select>
                </div>
            )}

            {isParent && children.length === 0 && !loading && (
                <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 text-center text-slate-500">
                    <UserIcon size={48} className="mx-auto mb-4 text-slate-300" />
                    <p>No tienes estudiantes vinculados a tu cuenta actualmente.</p>
                </div>
            )}

            {(!isParent || (isParent && selectedChildId)) && (
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="p-4 bg-slate-50 border-b border-slate-200">
                        <h3 className="font-bold text-slate-700 flex items-center gap-2"><MapPin size={18} className="text-slate-400" /> Distribución Semanal</h3>
                    </div>

                    {loading ? (
                        <div className="p-12 text-center text-slate-400">
                            Cargando tu horario...
                        </div>
                    ) : schedules.length === 0 ? (
                        <div className="p-16 text-center">
                            <Calendar size={64} className="mx-auto mb-4 text-slate-200" />
                            <h3 className="text-xl font-bold text-slate-700 mb-2">Horario Pendiente</h3>
                            <p className="text-slate-500 max-w-sm mx-auto">Tu curso aún no tiene un horario oficial cargado en el sistema. Contacta a la secretaría académica si esto es un error.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-5 divide-y md:divide-y-0 md:divide-x divide-slate-200">
                            {DAYS_OF_WEEK.map(day => (
                                <div key={day.id} className="min-h-[600px] bg-slate-50/30">
                                    <div className="bg-slate-100 py-3 text-center border-b border-slate-200">
                                        <span className="font-black text-slate-700 uppercase tracking-wide text-xs">{day.name}</span>
                                    </div>
                                    <div className="p-3 flex flex-col gap-3">
                                        {getSchedulesForDay(day.id).length === 0 ? (
                                            <div className="text-center p-6 text-sm font-medium text-slate-300 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">Día Libre</div>
                                        ) : (
                                            getSchedulesForDay(day.id).map(sched => (
                                                <div 
                                                    key={sched.id} 
                                                    className="bg-white border-l-4 border-l-teal-500 border border-y-slate-200 border-r-slate-200 rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden"
                                                >
                                                    <div className="absolute -right-4 -bottom-4 text-teal-50 opacity-50 pointer-events-none">
                                                        <Book size={64} />
                                                    </div>
                                                    <div className="relative z-10">
                                                        <div className="flex items-center gap-1.5 mb-2 text-teal-600 font-bold bg-teal-50 rounded w-max px-2 py-0.5 text-xs">
                                                            <Clock size={12} /> {parseTime(sched.start_time)} - {parseTime(sched.end_time)}
                                                        </div>
                                                        <h4 className="font-black text-slate-800 text-sm leading-tight mb-2">{sched.subject_name}</h4>
                                                        <p className="text-xs text-slate-600 font-medium flex items-center gap-1.5">
                                                            <UserIcon size={12} className="text-slate-400"/> {sched.teacher_name || 'Docente Pend.'}
                                                        </p>
                                                    </div>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default MySchedulePage;
