import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import communicationService from '../services/communicationService';
import academicService from '../services/academicService';
import userService from '../services/userService';
import { Mail, Send, Bell, Inbox, FileText, User, PlusCircle, X, Calendar as CalendarIcon, Paperclip, Download } from 'lucide-react';
import { useAuthStore } from '../context/authStore';
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import format from 'date-fns/format';
import parse from 'date-fns/parse';
import startOfWeek from 'date-fns/startOfWeek';
import getDay from 'date-fns/getDay';
import enUS from 'date-fns/locale/en-US';
import es from 'date-fns/locale/es';
import 'react-big-calendar/lib/css/react-big-calendar.css';

const locales = {
    'es': es,
};

const localizer = dateFnsLocalizer({
    format,
    parse,
    startOfWeek,
    getDay,
    locales,
});

const CommunicationPage = () => {
    const { user } = useAuthStore();
    const [activeTab, setActiveTab] = useState('inbox');
    const location = useLocation(); // Import useLocation
    const [messages, setMessages] = useState([]);
    const [notices, setNotices] = useState([]);

    // Check for query param on mount or change
    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const tabParam = params.get('tab');
        if (tabParam && ['inbox', 'sent', 'notices', 'compose'].includes(tabParam)) {
            setActiveTab(tabParam);
        }
    }, [location.search]);

    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(true);

    // Filter State
    const [searchTerm, setSearchTerm] = useState('');
    const [viewMode, setViewMode] = useState('calendar'); // Default to calendar

    // Compose State
    const [recipientUsername, setRecipientUsername] = useState('');
    const [subject, setSubject] = useState('');
    const [body, setBody] = useState('');

    // Create/Edit Notice State
    const [showCreateNotice, setShowCreateNotice] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [currentNoticeId, setCurrentNoticeId] = useState(null);

    const [courses, setCourses] = useState([]);
    const [students, setStudents] = useState([]);
    const [noticeForm, setNoticeForm] = useState({
        title: '',
        content: '',
        target_role: 'ALL',
        target_course: '',
        target_students: [],
        event_date: '',
        event_end_date: '',
        attachment: null,
        create_alert: false // New field for alerts
    });

    // Holidays state
    const [holidays, setHolidays] = useState([]);

    // Student Search state
    const [studentSearch, setStudentSearch] = useState('');

    // Holiday Management State
    const [showHolidayModal, setShowHolidayModal] = useState(false);
    const [holidayForm, setHolidayForm] = useState({ name: '', date: '' });

    // Message attachment state
    const [messageAttachment, setMessageAttachment] = useState(null);

    const [usersList, setUsersList] = useState([]);

    // Read-only View Notice Modal State
    const [viewNotice, setViewNotice] = useState(null);
    const [currentDate, setCurrentDate] = useState(new Date()); // Calendar Date State

    useEffect(() => {
        loadData();
    }, [activeTab]);

    const loadData = async () => {
        setLoading(true);
        try {
            if (activeTab === 'inbox') {
                const data = await communicationService.getInbox();
                setMessages(data);
            } else if (activeTab === 'sent') {
                const data = await communicationService.getSent();
                setMessages(data);
            } else if (activeTab === 'notices') {
                const [noticesData, notificationsData] = await Promise.all([
                    communicationService.getNotices(),
                    communicationService.getNotifications()
                ]);
                setNotices(noticesData);
                setNotices(noticesData);
                setNotifications(notificationsData);

                // Load holidays
                try {
                    const holidaysData = await communicationService.getHolidays();
                    setHolidays(holidaysData);
                } catch (e) {
                    console.error("Error loading holidays", e);
                    // Try populating if empty (optional, or just leave empty)
                }

                // Load courses and students if user has privileges
                if (user.role === 'TEACHER' || user.role === 'ADMIN' || user.role === 'RECTOR') {
                    try {
                        const coursesData = await academicService.getCourses();
                        setCourses(coursesData);
                        const studentsData = await userService.getUsers('STUDENT');
                        setStudents(studentsData);
                    } catch (e) { console.error("Error loading targeting data", e); }
                }
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('recipient_username', recipientUsername);
            formData.append('subject', subject);
            formData.append('body', body);
            if (messageAttachment) formData.append('attachment', messageAttachment);

            await communicationService.sendMessage(formData);
            alert('Mensaje enviado');
            setActiveTab('sent');
            setSubject(''); setBody(''); setRecipientUsername(''); setMessageAttachment(null);
        } catch (error) {
            console.error(error);
            alert('Error al enviar');
        }
    };

    const openCreateModal = async () => {
        setIsEditing(false);
        setCurrentNoticeId(null);
        setNoticeForm({ title: '', content: '', target_role: 'ALL', target_course: '', target_students: [], event_date: '', event_end_date: '', attachment: null });
        setShowCreateNotice(true);

        // Ensure data is loaded
        if (courses.length === 0 || students.length === 0) {
            if (user.role === 'TEACHER' || user.role === 'ADMIN' || user.role === 'RECTOR') {
                try {
                    const [cData, sData] = await Promise.all([
                        academicService.getCourses(),
                        userService.getUsers('STUDENT')
                    ]);
                    setCourses(cData);
                    setStudents(sData);
                } catch (e) { console.error(e); }
            }
        }
    };


    const openEditModal = (notice) => {
        setIsEditing(true);
        setCurrentNoticeId(notice.id);
        setNoticeForm({
            title: notice.title,
            content: notice.content,
            target_role: notice.target_role || 'ALL',
            target_course: notice.target_course || '',
            target_students: notice.target_students || [],
            event_date: notice.event_date ? notice.event_date.substring(0, 16) : '',
            event_end_date: notice.event_end_date ? notice.event_end_date.substring(0, 16) : '',
            attachment: null // Don't reload file
        });
        setShowCreateNotice(true);
    };

    const handleDeleteNotice = async (id) => {
        if (!window.confirm("¿Estás seguro de que deseas eliminar este aviso?")) return;
        try {
            await communicationService.deleteNotice(id);
            setNotices(notices.filter(n => n.id !== id));
        } catch (error) {
            console.error(error);
            alert('Error al eliminar aviso');
        }
    };

    const handleSubmitNotice = async (e) => {
        e.preventDefault();
        try {
            const formData = new FormData();
            formData.append('title', noticeForm.title);
            formData.append('content', noticeForm.content);
            formData.append('target_role', noticeForm.target_role);
            if (noticeForm.target_course) formData.append('target_course', noticeForm.target_course);
            if (noticeForm.target_students.length > 0) {
                noticeForm.target_students.forEach(id => formData.append('target_students', id));
            }
            if (noticeForm.event_date) formData.append('event_date', noticeForm.event_date);
            if (noticeForm.event_end_date) formData.append('event_end_date', noticeForm.event_end_date);
            if (noticeForm.attachment) formData.append('attachment', noticeForm.attachment);
            if (noticeForm.create_alert) formData.append('create_alert', 'true');


            if (isEditing) {
                await communicationService.updateNotice(currentNoticeId, formData);
                alert('Aviso actualizado con éxito');
            } else {
                await communicationService.createNotice(formData);
                alert('Aviso publicado con éxito');
            }
            setShowCreateNotice(false);
            loadData();
        } catch (error) {
            console.error(error);
            alert('Error al guardar aviso: ' + JSON.stringify(error.response?.data || error.message));
        }
    };

    const handleCreateHoliday = async (e) => {
        e.preventDefault();
        try {
            await communicationService.createHoliday(holidayForm);
            alert('Feriado agregado');
            setHolidayForm({ name: '', date: '' });
            // Reload holidays
            const h = await communicationService.getHolidays();
            setHolidays(h);
        } catch (error) {
            console.error(error);
            alert('Error al crear feriado');
        }
    };

    const handleDeleteHoliday = async (id) => {
        if (!window.confirm("¿Eliminar este feriado?")) return;
        try {
            await communicationService.deleteHoliday(id);
            setHolidays(holidays.filter(h => h.id !== id));
        } catch (error) {
            console.error(error);
            alert('Error al eliminar feriado');
        }
    };

    // Filter notices
    const filteredNotices = notices.filter(notice =>
        notice.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        notice.content.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const canManageNotice = (notice) => {
        return user.role === 'ADMIN' || user.role === 'RECTOR' || (user.role === 'TEACHER' && notice.author === user.id); // Assuming author ID is available directly or needs check
    };
    // Note: serializer returns `author` as ID usually. If author_name is present, check `author` field.
    // NoticeSerializer has `author` as read_only (returns ID) and `author_name`. 

    // Compose Recipient Logic
    const [allowedRecipients, setAllowedRecipients] = useState([]);

    useEffect(() => {
        if (activeTab === 'compose' && user.role === 'STUDENT') {
            loadAllowedRecipients();
        }
    }, [activeTab]);

    const loadAllowedRecipients = async () => {
        try {
            // Fetch Teachers and Rectors/Admins
            // Ideally backend endpoint for "available recipients"
            // For now, parallel fetch
            const [teachers, rectors, admins] = await Promise.all([
                userService.getUsers('TEACHER'),
                userService.getUsers('RECTOR'),
                userService.getUsers('ADMIN')
            ]);
            // Filter out self? Users list usually doesn't include secrets, but good to filter.
            const combined = [...teachers, ...rectors, ...admins].filter(u => u.id !== user.id);
            // Remove duplicates if any
            const unique = Array.from(new Set(combined.map(a => a.id))).map(id => {
                return combined.find(a => a.id === id);
            });
            setAllowedRecipients(unique);
        } catch (error) {
            console.error("Error loading recipients", error);
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Centro de Comunicación</h1>
            {/* ... (Tabs) ... */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="flex border-b border-slate-200">
                    {['inbox', 'sent', 'notices', 'compose'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`flex-1 p-4 flex items-center justify-center gap-2 font-medium transition-colors ${activeTab === tab ? 'text-indigo-600 border-b-2 border-indigo-600 bg-indigo-50' : 'text-slate-500 hover:bg-slate-50'}`}
                        >
                            {tab === 'inbox' && <Inbox size={18} />}
                            {tab === 'sent' && <Send size={18} />}
                            {tab === 'notices' && <Bell size={18} />}
                            {tab === 'compose' && <PlusCircle size={18} />}
                            <span className="capitalize">{tab === 'notices' ? 'Avisos' : tab === 'compose' ? 'Redactar' : tab === 'inbox' ? 'Recibidos' : 'Enviados'}</span>
                        </button>
                    ))}
                </div>

                <div className="p-6 min-h-[400px]">
                    {loading ? (
                        <div className="flex justify-center p-8"><div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div></div>
                    ) : (
                        <>
                            {(activeTab === 'inbox' || activeTab === 'sent') && (
                                <div className="space-y-3">
                                    {messages.length === 0 ? <p className="text-center text-slate-400 py-8">No hay mensajes.</p> : messages.map(msg => (
                                        <div key={msg.id} className="p-4 border border-slate-100 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer group">
                                            <div className="flex justify-between items-start mb-1">
                                                <h3 className="font-semibold text-slate-800 group-hover:text-indigo-600">{msg.subject}</h3>
                                                <span className="text-xs text-slate-400">{new Date(msg.created_at).toLocaleDateString()}</span>
                                            </div>
                                            <p className="text-sm text-slate-600 line-clamp-2">{msg.body}</p>
                                            <div className="mt-2 text-xs text-slate-400 flex items-center gap-1">
                                                <User size={12} /> {activeTab === 'inbox' ? `De: ${msg.sender_detail?.username || msg.sender}` : `Para: ${msg.recipient_detail?.username || msg.recipient}`}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {activeTab === 'notices' && (
                                <div className="space-y-6">
                                    <div className="flex justify-between gap-4">
                                        <input
                                            type="text"
                                            placeholder="Buscar avisos..."
                                            className="input-modern flex-1 max-w-sm"
                                            value={searchTerm}
                                            onChange={(e) => setSearchTerm(e.target.value)}
                                        />

                                        {(user.role === 'TEACHER' || user.role === 'ADMIN' || user.role === 'RECTOR') && (
                                            <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
                                                <PlusCircle size={18} /> Crear Aviso
                                            </button>
                                        )}
                                        {user.role === 'ADMIN' && (
                                            <button onClick={() => setShowHolidayModal(true)} className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2 font-medium">
                                                <CalendarIcon size={18} /> Feriados
                                            </button>
                                        )}
                                    </div>

                                    {/* Modal */}
                                    {showCreateNotice && (
                                        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                                            <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                                <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                                                    <h3 className="font-bold text-slate-700">{isEditing ? 'Editar Aviso' : 'Nuevo Aviso'}</h3>
                                                    <button onClick={() => setShowCreateNotice(false)} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
                                                </div>
                                                <form onSubmit={handleSubmitNotice} className="p-6 space-y-4">
                                                    <div>
                                                        <label className="block text-sm font-medium text-slate-700 mb-1">Título</label>
                                                        <input required type="text" className="input-modern w-full" value={noticeForm.title} onChange={e => setNoticeForm({ ...noticeForm, title: e.target.value })} />
                                                    </div>
                                                    <div>
                                                        <label className="block text-sm font-medium text-slate-700 mb-1">Contenido</label>
                                                        <textarea required rows="4" className="input-modern w-full" value={noticeForm.content} onChange={e => setNoticeForm({ ...noticeForm, content: e.target.value })}></textarea>
                                                    </div>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <input type="datetime-local" className="input-modern w-full" value={noticeForm.event_date} onChange={e => setNoticeForm({ ...noticeForm, event_date: e.target.value })} />
                                                    </div>
                                                    <div>
                                                        <label className="block text-sm font-medium text-slate-700 mb-1">Fecha Fin (Opcional)</label>
                                                        <input type="datetime-local" className="input-modern w-full" value={noticeForm.event_end_date} onChange={e => setNoticeForm({ ...noticeForm, event_end_date: e.target.value })} />
                                                    </div>
                                                    <div>
                                                        <label className="block text-sm font-medium text-slate-700 mb-1">Adjunto (Max 5MB)</label>
                                                        <div className="flex items-center gap-2">
                                                            <input type="file" className="input-modern w-full text-sm" onChange={e => setNoticeForm({ ...noticeForm, attachment: e.target.files[0] })} />
                                                        </div>
                                                    </div>


                                                    {/* Create Alert Option (Admin/Rector only) */}
                                                    {(user.role === 'ADMIN' || user.role === 'RECTOR') && (
                                                        <div className="flex items-center gap-2 bg-red-50 p-2 rounded border border-red-100">
                                                            <input
                                                                type="checkbox"
                                                                id="create_alert"
                                                                className="w-4 h-4 text-red-600 rounded"
                                                                checked={noticeForm.create_alert || false}
                                                                onChange={e => setNoticeForm({ ...noticeForm, create_alert: e.target.checked })}
                                                            />
                                                            <label htmlFor="create_alert" className="text-sm font-medium text-red-700 cursor-pointer">
                                                                Enviar también como Alerta <span className="text-xs font-normal text-red-500">(Notificación prioritaria en rojo)</span>
                                                            </label>
                                                        </div>
                                                    )}


                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div>
                                                            <label className="block text-sm font-medium text-slate-700 mb-1">Dirigido a</label>
                                                            <select className="input-modern w-full" value={noticeForm.target_role} onChange={e => setNoticeForm({ ...noticeForm, target_role: e.target.value })}>
                                                                <option value="ALL">Todos</option>
                                                                <option value="STUDENT">Estudiantes</option>
                                                                <option value="TEACHER">Profesores</option>
                                                            </select>
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-slate-700 mb-1">Curso (Opcional)</label>
                                                            <select className="input-modern w-full" value={noticeForm.target_course} onChange={e => setNoticeForm({ ...noticeForm, target_course: e.target.value })}>
                                                                <option value="">-- General --</option>
                                                                {courses.map(c => <option key={c.id} value={c.id}>{c.name} {c.level}-{c.parallel}</option>)}
                                                            </select>
                                                        </div>
                                                    </div>
                                                    {noticeForm.target_role === 'STUDENT' && (
                                                        <div>
                                                            <label className="block text-sm font-medium text-slate-700 mb-1">Estudiantes (Opcional)</label>
                                                            <input
                                                                type="text"
                                                                placeholder="Filtrar estudiante..."
                                                                className="input-modern w-full mb-2 text-xs"
                                                                value={studentSearch}
                                                                onChange={e => setStudentSearch(e.target.value)}
                                                            />
                                                            <select multiple className="input-modern w-full h-32" value={noticeForm.target_students} onChange={e => setNoticeForm({ ...noticeForm, target_students: Array.from(e.target.selectedOptions, o => o.value) })}>
                                                                {students.filter(s =>
                                                                    `${s.first_name} ${s.last_name}`.toLowerCase().includes(studentSearch.toLowerCase()) ||
                                                                    s.username.toLowerCase().includes(studentSearch.toLowerCase())
                                                                ).map(s => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
                                                            </select>
                                                        </div>
                                                    )}
                                                    <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                                                        <button type="button" onClick={() => setShowCreateNotice(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
                                                        <button type="submit" className="btn-primary">{isEditing ? 'Guardar Cambios' : 'Publicar'}</button>
                                                    </div>
                                                </form>
                                            </div>
                                        </div>
                                    )}

                                    {/* Holiday Management Modal */}
                                    {showHolidayModal && (
                                        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                                            <div className="bg-white rounded-xl shadow-xl max-w-md w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                                <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-purple-50">
                                                    <h3 className="font-bold text-purple-800">Gestionar Feriados</h3>
                                                    <button onClick={() => setShowHolidayModal(false)} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
                                                </div>
                                                <div className="p-6 space-y-6">
                                                    {/* Add New */}
                                                    <form onSubmit={handleCreateHoliday} className="space-y-3 bg-slate-50 p-4 rounded-lg">
                                                        <h4 className="text-sm font-bold text-slate-700">Agregar Nuevo</h4>
                                                        <input required type="text" placeholder="Nombre del Feriado" className="input-modern w-full" value={holidayForm.name} onChange={e => setHolidayForm({ ...holidayForm, name: e.target.value })} />
                                                        <input required type="date" className="input-modern w-full" value={holidayForm.date} onChange={e => setHolidayForm({ ...holidayForm, date: e.target.value })} />
                                                        <button type="submit" className="w-full py-2 bg-purple-600 text-white rounded hover:bg-purple-700 font-medium text-sm">Agregar</button>
                                                    </form>

                                                    {/* List */}
                                                    <div>
                                                        <h4 className="text-sm font-bold text-slate-700 mb-2">Feriados Existentes ({holidays.length})</h4>
                                                        <div className="max-h-60 overflow-y-auto space-y-2">
                                                            {holidays.map(h => (
                                                                <div key={h.id} className="flex justify-between items-center text-sm p-2 bg-white border border-slate-100 rounded shadow-sm">
                                                                    <div>
                                                                        <span className="font-semibold text-slate-700 block">{h.name}</span>
                                                                        <span className="text-xs text-slate-500">{h.date}</span>
                                                                    </div>
                                                                    <button onClick={() => handleDeleteHoliday(h.id)} className="text-red-400 hover:text-red-600 p-1"><X size={16} /></button>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Notifications */}
                                    {notifications.length > 0 && (
                                        <div className="space-y-3">
                                            {notifications.map(notif => (
                                                <div key={notif.id} className="bg-red-50 border border-red-100 rounded-lg p-4 flex gap-4">
                                                    <div className="bg-red-100 p-2 rounded-full h-fit text-red-600"><Bell size={20} /></div>
                                                    <div>
                                                        <h4 className="font-bold text-red-800">{notif.title}</h4>
                                                        <p className="text-red-700 text-sm">{notif.message}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* Section 2: Non-Event Notices (Green Alerts) */}
                                    {(() => {
                                        const now = new Date();
                                        const datedNotices = notices.filter(n => {
                                            if (!n.event_date) return false; // Handled by General Notices section? No, let's keep dated ones here.

                                            // Check expiration
                                            if (n.event_end_date) {
                                                const end = new Date(n.event_end_date);
                                                if (now > end) return false; // Expired
                                            }
                                            // If no end date, we assume it's valid (or maybe 1 day? users said "put start and expiration", so expiration matters)
                                            // If only Start Date is present (Event), we show it. 
                                            // Ideally we might hide it if it's WAY in the past (e.g. event was last week), but without end date hard to say.
                                            // Logic: Show all dated notices that aren't expired.
                                            return true;
                                        });

                                        if (datedNotices.length === 0) return null;

                                        return (
                                            <div className="space-y-3 mb-6">
                                                <h4 className="text-xs font-bold text-green-700 uppercase tracking-widest pl-1">Agenda y Eventos</h4>
                                                {datedNotices.map(notice => {
                                                    const start = new Date(notice.event_date);
                                                    const isFuture = start > now;

                                                    return (
                                                        <div key={notice.id} className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-4 relative group">
                                                            {(user.role === 'ADMIN' || user.role === 'RECTOR' || user.id === notice.author) && (
                                                                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <button onClick={() => openEditModal(notice)} className="p-1 bg-blue-200 text-blue-800 rounded hover:bg-blue-300" title="Editar"><FileText size={14} /></button>
                                                                    <button onClick={() => handleDeleteNotice(notice.id)} className="p-1 bg-red-200 text-red-800 rounded hover:bg-red-300" title="Eliminar"><X size={14} /></button>
                                                                </div>
                                                            )}

                                                            <div className="bg-blue-100 p-2 rounded-full h-fit text-blue-600 shrink-0"><CalendarIcon size={20} /></div>
                                                            <div className="flex-1">
                                                                <div className="flex justify-between items-start">
                                                                    <h4 className="font-bold text-blue-800">{notice.title}</h4>
                                                                    <div className="flex flex-col items-end gap-1">
                                                                        <span className="text-xs text-blue-600 bg-blue-100 px-2 py-0.5 rounded-full">
                                                                            {new Date(notice.created_at).toLocaleDateString()}
                                                                        </span>
                                                                        <span className={`text-[10px] px-2 py-0.5 rounded-full border flex items-center gap-1 ${isFuture ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-green-100 text-green-700 border-green-200'}`}>
                                                                            <CalendarIcon size={10} />
                                                                            {isFuture ? 'Evento: ' : 'En curso: '}
                                                                            {start.toLocaleDateString()} {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                                <p className="text-blue-900/80 text-sm mt-1 whitespace-pre-wrap">{notice.content}</p>
                                                                {notice.attachment && (
                                                                    <a href={notice.attachment} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs text-blue-700 hover:text-blue-900 mt-2 hover:underline">
                                                                        <Paperclip size={12} /> Ver Adjunto
                                                                    </a>
                                                                )}
                                                                <div className="mt-2 text-xs text-blue-600">
                                                                    Por: {notice.author_name}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        );
                                    })()}

                                    {/* Modal Logic (Create Notice, Holiday) - kept same */}
                                    {/* ... existing modal logic ... */}
                                    {/* REPLACING ONLY CALENDAR BLOCK & COMPOSE BLOCK via Context */}

                                    {/* ... */}

                                    {/* Notices List & Calendar */}
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Tablón de Anuncios</h3>
                                            <div className="flex gap-2">
                                                <button onClick={() => setViewMode('list')} className={`p-2 rounded ${viewMode === 'list' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-400'}`} title="Lista"><FileText size={18} /></button>
                                                <button onClick={() => setViewMode('calendar')} className={`p-2 rounded ${viewMode === 'calendar' ? 'bg-indigo-100 text-indigo-700' : 'text-slate-400'}`} title="Calendario"><CalendarIcon size={18} /></button>
                                            </div>
                                        </div>

                                        {viewMode === 'calendar' ? (
                                            <div className="bg-white p-4 rounded-xl border border-slate-200 h-[600px]">
                                                <Calendar
                                                    localizer={localizer}
                                                    events={[
                                                        ...notices.filter(n => n.event_date).map(n => ({
                                                            title: n.title,
                                                            start: new Date(n.event_date),
                                                            end: n.event_end_date ? new Date(n.event_end_date) : new Date(new Date(n.event_date).getTime() + 60 * 60 * 1000),
                                                            resource: n,
                                                            type: 'notice'
                                                        })),
                                                        ...holidays.map(h => ({
                                                            title: h.name,
                                                            start: new Date(h.date + 'T00:00:00'),
                                                            end: new Date(h.date + 'T23:59:59'),
                                                            resource: h,
                                                            type: 'holiday'
                                                        }))
                                                    ]}
                                                    views={['month', 'week', 'day', 'agenda']}
                                                    defaultView="month"
                                                    date={currentDate}
                                                    onNavigate={setCurrentDate}
                                                    eventPropGetter={(event) => {
                                                        const style = {
                                                            backgroundColor: event.type === 'holiday' ? '#9333ea' : '#3b82f6',
                                                            borderRadius: '4px',
                                                            opacity: 0.8,
                                                            color: 'white',
                                                            border: '0px',
                                                            display: 'block'
                                                        };
                                                        return { style };
                                                    }}
                                                    startAccessor="start"
                                                    endAccessor="end"
                                                    culture='es'
                                                    messages={{
                                                        next: "Sig",
                                                        previous: "Ant",
                                                        today: "Hoy",
                                                        month: "Mes",
                                                        week: "Semana",
                                                        day: "Día",
                                                        agenda: "Agenda"
                                                    }}
                                                    onSelectEvent={event => {
                                                        if (event.type === 'notice') {
                                                            if (user.role === 'ADMIN' || user.role === 'RECTOR' || user.id === event.resource.author) {
                                                                openEditModal(event.resource);
                                                            } else {
                                                                setViewNotice(event.resource);
                                                            }
                                                        } else if (event.type === 'holiday') {
                                                            alert(`Feriado: ${event.title}\nFecha: ${event.resource.date}`);
                                                        }
                                                    }}
                                                />
                                            </div>
                                        ) : (
                                            <div className="space-y-4">
                                                {/* List View Content - Kept Same */}
                                                {filteredNotices.length === 0 ? <p className="text-center text-slate-400 py-4">No se encontraron avisos.</p> : filteredNotices.map(notice => (
                                                    <div key={notice.id} className="bg-amber-50 border border-amber-100 rounded-lg p-5 group relative">
                                                        {(user.role === 'ADMIN' || user.role === 'RECTOR' || user.id === notice.author) && (
                                                            <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                <button onClick={() => openEditModal(notice)} className="p-1.5 bg-amber-200 text-amber-800 rounded hover:bg-amber-300" title="Editar"><FileText size={16} /></button>
                                                                <button onClick={() => handleDeleteNotice(notice.id)} className="p-1.5 bg-red-200 text-red-800 rounded hover:bg-red-300" title="Eliminar"><X size={16} /></button>
                                                            </div>
                                                        )}
                                                        <div className="flex justify-between items-start mb-3 pr-16">
                                                            <h3 className="font-bold text-amber-800 text-lg">{notice.title}</h3>
                                                            <div className="flex gap-2 text-xs">
                                                                <span className="bg-amber-100 text-amber-700 px-2 py-1 rounded-full">{new Date(notice.created_at).toLocaleDateString()}</span>
                                                                {notice.event_date && (
                                                                    <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full flex items-center gap-1"><CalendarIcon size={12} /> {new Date(notice.event_date).toLocaleString()}</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <p className="text-amber-900/80 whitespace-pre-wrap">{notice.content}</p>
                                                        {notice.attachment && <div className="mt-3"><a href={notice.attachment} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-sm text-indigo-600 bg-white/50 px-3 py-1.5 rounded-lg border border-indigo-100"><Paperclip size={14} /> <span>Ver Adjunto</span></a></div>}
                                                        <div className="mt-4 pt-3 border-t border-amber-200/50 text-xs text-amber-600 font-medium">Publicado por: {notice.author_name}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                        {viewNotice && (
                                            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                                                <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                                                    <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                                                        <h3 className="font-bold text-slate-700">Detalles del Aviso</h3>
                                                        <button onClick={() => setViewNotice(null)} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
                                                    </div>
                                                    <div className="p-6 space-y-4">
                                                        <div><h4 className="font-bold text-xl text-slate-800">{viewNotice.title}</h4><div className="text-xs text-slate-500 mt-1">Por: {viewNotice.author_name}</div></div>
                                                        <p className="text-slate-700 whitespace-pre-wrap">{viewNotice.content}</p>
                                                        {viewNotice.event_date && <div className="bg-blue-50 text-blue-800 p-3 rounded-lg text-sm flex items-center gap-2"><CalendarIcon size={16} /><span>{new Date(viewNotice.event_date).toLocaleString()}</span></div>}
                                                        {viewNotice.attachment && <div className="pt-4 border-t border-slate-100"><a href={viewNotice.attachment} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-indigo-600 font-medium p-3 bg-indigo-50 rounded-lg hover:bg-indigo-100"><Paperclip size={18} /><span>Descargar Adjunto</span></a></div>}
                                                    </div>
                                                    <div className="p-4 bg-slate-50 text-right"><button onClick={() => setViewNotice(null)} className="btn-secondary">Cerrar</button></div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'compose' && (
                                <form onSubmit={handleSend} className="max-w-2xl mx-auto space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">Usuario Destinatario (Login)</label>
                                        {user.role === 'STUDENT' ? (
                                            <select
                                                required
                                                className="input-modern w-full"
                                                value={recipientUsername}
                                                onChange={e => setRecipientUsername(e.target.value)}
                                            >
                                                <option value="">-- Seleccionar Destinatario --</option>
                                                {allowedRecipients.map(u => (
                                                    <option key={u.id} value={u.username}>{u.first_name} {u.last_name} ({u.role}) - @{u.username}</option>
                                                ))}
                                            </select>
                                        ) : (
                                            <input type="text" required className="input-modern w-full" value={recipientUsername} onChange={e => setRecipientUsername(e.target.value)} />
                                        )}
                                        {user.role === 'STUDENT' && <p className="text-xs text-slate-500 mt-1">Solo puedes contactar a Profesores y Directivos.</p>}
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">Asunto</label>
                                        <input type="text" required className="input-modern w-full" value={subject} onChange={e => setSubject(e.target.value)} />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">Mensaje</label>
                                        <textarea required rows="6" className="input-modern w-full" value={body} onChange={e => setBody(e.target.value)}></textarea>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-700">Adjunto (Max 2MB)</label>
                                        <input type="file" className="input-modern w-full text-sm" onChange={e => setMessageAttachment(e.target.files[0])} />
                                    </div>
                                    <button type="submit" className="btn-primary w-full">Enviar Mensaje</button>
                                </form>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CommunicationPage;
