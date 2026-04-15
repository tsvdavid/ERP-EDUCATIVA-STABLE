import React, { useState, useEffect } from 'react';
import { 
    ChevronLeft, ChevronRight, Calendar as CalendarIcon, 
    X, ExternalLink, Clock, MapPin, 
    BookOpen, MonitorPlay, AlertCircle, Sparkles, Layout
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import learningService from '../../services/learningService';

const LMSCalendar = () => {
    const navigate = useNavigate();
    const [events, setEvents] = useState([]);
    const [currentDate, setCurrentDate] = useState(new Date());
    const [loading, setLoading] = useState(true);
    const [selectedEvent, setSelectedEvent] = useState(null);

    useEffect(() => {
        fetchEvents();
    }, []);

    const fetchEvents = async () => {
        try {
            setLoading(true);
            const data = await learningService.getCalendarEvents();
            setEvents(data);
        } catch (error) {
            console.error("Error fetching calendar events:", error);
        } finally {
            setLoading(false);
        }
    };

    const daysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
    const firstDayOfMonth = (year, month) => new Date(year, month, 1).getDay();

    const monthNames = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ];

    const handlePrevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    };

    const handleNextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    };

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const getEventsForDay = (day) => {
        const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        return events.filter(event => {
            const eventDate = event.start.split('T')[0];
            return eventDate === dateString;
        });
    };

    const renderHeader = () => (
        <div className="flex flex-col md:flex-row items-center justify-between mb-8 gap-4 px-4 lg:px-10">
            <div className="flex items-center gap-4">
                <button 
                    onClick={() => navigate('/dashboard')}
                    className="p-4 bg-white text-slate-400 hover:bg-slate-900 hover:text-white rounded-[1.5rem] transition-all flex items-center gap-2 group shadow-sm border border-slate-100"
                >
                    <Layout size={20} className="group-hover:scale-110 transition-transform" />
                    <span className="text-xs font-black">Dashboard</span>
                </button>
                <div className="h-10 w-px bg-slate-100 hidden md:block mx-2"></div>
                <div>
                    <h1 className="text-4xl lg:text-5xl font-black text-slate-900 tracking-tighter flex items-center gap-4">
                        <CalendarIcon size={40} className="text-indigo-600" />
                        Cronograma <span className="text-indigo-600">Académico</span>
                    </h1>
                    <p className="text-slate-400 font-bold uppercase tracking-widest text-[10px] mt-2 ml-14">
                        Organiza tus actividades y clases en vivo
                    </p>
                </div>
            </div>

            <div className="flex items-center gap-4 bg-white p-2 rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100">
                <button 
                    onClick={handlePrevMonth}
                    className="p-3 bg-slate-50 text-slate-400 hover:bg-slate-900 hover:text-white rounded-xl transition-all active:scale-90"
                >
                    <ChevronLeft size={20} />
                </button>
                <div className="px-6 text-lg font-black text-slate-900 min-w-[180px] text-center">
                    {monthNames[month]} {year}
                </div>
                <button 
                    onClick={handleNextMonth}
                    className="p-3 bg-slate-50 text-slate-400 hover:bg-slate-900 hover:text-white rounded-xl transition-all active:scale-90"
                >
                    <ChevronRight size={20} />
                </button>
            </div>
        </div>
    );

    const renderCalendar = () => {
        const totalDays = daysInMonth(year, month);
        const firstDay = firstDayOfMonth(year, month);
        const days = [];

        // Padding for previous month
        for (let i = 0; i < firstDay; i++) {
            days.push(<div key={`pad-${i}`} className="h-32 lg:h-40 bg-slate-50/50 rounded-3xl border border-transparent"></div>);
        }

        // Days of current month
        for (let d = 1; d <= totalDays; d++) {
            const dayEvents = getEventsForDay(d);
            const isToday = new Date().toDateString() === new Date(year, month, d).toDateString();

            days.push(
                <div 
                    key={d} 
                    className={`h-32 lg:h-40 p-4 border rounded-[2rem] transition-all relative overflow-hidden group ${isToday ? 'bg-indigo-50/30 border-indigo-200 border-2 shadow-inner ring-4 ring-indigo-500/5' : 'bg-white border-slate-100 hover:border-indigo-100 hover:shadow-2xl hover:shadow-indigo-100/30'}`}
                >
                    <span className={`text-sm lg:text-lg font-black ${isToday ? 'text-indigo-600' : 'text-slate-400'}`}>
                        {d}
                    </span>
                    
                    <div className="mt-2 space-y-1 overflow-y-auto max-h-[80%] custom-scrollbar">
                        {dayEvents.map(event => (
                            <div 
                                key={event.id}
                                onClick={() => setSelectedEvent(event)}
                                className="px-2 py-1.5 rounded-lg text-[9px] font-black text-white truncate cursor-pointer transform hover:scale-105 transition-transform active:scale-95 shadow-sm"
                                style={{ backgroundColor: event.color }}
                            >
                                {event.title}
                            </div>
                        ))}
                    </div>

                    {isToday && (
                        <div className="absolute top-4 right-4 text-[10px] font-black text-indigo-500 bg-indigo-100 px-2 py-0.5 rounded-full uppercase">Hoy</div>
                    )}
                </div>
            );
        }

        return (
            <div className="grid grid-cols-7 gap-4 lg:gap-6 animate-fade-in px-4 lg:px-10">
                {['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab'].map(day => (
                    <div key={day} className="text-center text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{day}</div>
                ))}
                {days}
            </div>
        );
    };

    return (
        <div className="min-h-screen bg-slate-50/50 pb-20 mt-10">
            {renderHeader()}
            
            <div className="max-w-[1600px] mx-auto">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-[50vh] space-y-4">
                        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                        <p className="font-black text-slate-400 uppercase tracking-widest text-xs">Cargando Cronograma...</p>
                    </div>
                ) : (
                    renderCalendar()
                )}
            </div>

            {/* Event Detail Modal */}
            {selectedEvent && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xl animate-fade-in">
                    <div className="bg-white rounded-[3rem] shadow-2xl w-full max-w-lg overflow-hidden border border-white/20">
                        <div className="h-4 w-full" style={{ backgroundColor: selectedEvent.color }}></div>
                        <div className="p-10 space-y-6">
                            <div className="flex items-center justify-between">
                                <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest text-white`} style={{ backgroundColor: selectedEvent.color }}>
                                    {selectedEvent.type}
                                </span>
                                <button onClick={() => setSelectedEvent(null)} className="p-3 bg-slate-50 text-slate-400 hover:text-red-500 rounded-2xl transition-all">
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="space-y-2">
                                <h3 className="text-3xl font-black text-slate-900 tracking-tight leading-none">{selectedEvent.title}</h3>
                                {selectedEvent.course_name && (
                                    <p className="text-indigo-600 font-bold text-sm">{selectedEvent.course_name}</p>
                                )}
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center gap-4 text-slate-600">
                                    <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center text-slate-400">
                                        <Clock size={20} />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Fecha y Hora</p>
                                        <p className="font-bold">{new Date(selectedEvent.start).toLocaleString('es-ES', { dateStyle: 'long', timeStyle: 'short' })}</p>
                                    </div>
                                </div>

                                {selectedEvent.description && (
                                    <div className="bg-slate-50 p-6 rounded-3xl border border-slate-100">
                                        <p className="text-slate-600 font-medium leading-relaxed">{selectedEvent.description}</p>
                                    </div>
                                )}
                            </div>

                            <div className="pt-6 border-t border-slate-50 flex gap-4">
                                {selectedEvent.url && (
                                    <button 
                                        onClick={() => {
                                            setSelectedEvent(null);
                                            navigate(selectedEvent.url);
                                        }}
                                        className="flex-grow py-4 bg-slate-900 text-white rounded-2xl font-black text-sm flex items-center justify-center gap-3 hover:bg-indigo-600 transition-all shadow-xl shadow-slate-200"
                                    >
                                        {selectedEvent.type === 'meeting' ? <MonitorPlay size={18} /> : <BookOpen size={18} />}
                                        {selectedEvent.type === 'meeting' ? 'Unirse a Clase' : 'Ver Tarea'}
                                    </button>
                                )}
                                <button 
                                    onClick={() => setSelectedEvent(null)}
                                    className="px-8 py-4 bg-slate-50 text-slate-400 rounded-2xl font-black text-sm hover:bg-slate-100 transition-all"
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
};

export default LMSCalendar;
