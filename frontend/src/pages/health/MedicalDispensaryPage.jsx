import React, { useState, useEffect, useMemo } from 'react';
import userService from '../../services/userService';
import healthService from '../../services/healthService';
import { useAuthStore } from '../../context/authStore';
import { Search, Activity, FileText, Plus, User, Calendar, X, Edit, Save, Info, Vibrate, Droplet, Pill, Stethoscope, Phone, AlertTriangle, ClipboardList } from 'lucide-react';

const MedicalDispensaryPage = () => {
    const { user } = useAuthStore();
    const [students, setStudents] = useState([]);
    const [medicalRecords, setMedicalRecords] = useState([]);
    const [medicalVisits, setMedicalVisits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [showStudentModal, setShowStudentModal] = useState(false);
    const [activeTab, setActiveTab] = useState('ficha');
    const [studentCases, setStudentCases] = useState([]);
    const [showDeriveModal, setShowDeriveModal] = useState(false);
    const [deriveData, setDeriveData] = useState({ area: 'DECE', reason: '' });
    const [selectedCase, setSelectedCase] = useState(null);
    const [toast, setToast] = useState(null);
    const [editingFicha, setEditingFicha] = useState(false);
    const [fichaData, setFichaData] = useState({ id:null, blood_type:'', allergies:'', chronic_conditions:'', regular_medication:'', emergency_contact_name:'', emergency_contact_phone:'', emergency_contact_relationship:'' });
    const [showVisitModal, setShowVisitModal] = useState(false);
    const [visitData, setVisitData] = useState({ reason:'', symptoms:'', diagnosis:'', treatment:'', notes:'' });

    useEffect(() => { loadData(); }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [studentsData, recordsData, visitsData] = await Promise.all([
                userService.getUsers('STUDENT'),
                healthService.getMedicalRecords(),
                healthService.getMedicalVisits()
            ]);
            setStudents(Array.isArray(studentsData) ? studentsData : []);
            setMedicalRecords(Array.isArray(recordsData) ? recordsData : []);
            setMedicalVisits(Array.isArray(visitsData) ? visitsData : []);
        } catch (error) { console.error(error); }
        finally { setLoading(false); }
    };

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type });
        setTimeout(() => setToast(null), 3000);
    };

    const getStudentRecord = (studentId) => medicalRecords.find(r => r.student === studentId || r.student?.id === studentId);
    const getStudentVisits = (studentId) => medicalVisits.filter(v => v.student === studentId || v.student?.id === studentId).sort((a,b) => new Date(b.date) - new Date(a.date));

    const openStudentProfile = async (student) => {
        setSelectedStudent(student);
        const record = getStudentRecord(student.id);
        setFichaData(record ? {
            id: record.id, blood_type: record.blood_type||'', allergies: record.allergies||'',
            chronic_conditions: record.chronic_conditions||'', regular_medication: record.regular_medication||'',
            emergency_contact_name: record.emergency_contact_name||'', emergency_contact_phone: record.emergency_contact_phone||'',
            emergency_contact_relationship: record.emergency_contact_relationship||''
        } : { id:null, blood_type:'', allergies:'', chronic_conditions:'', regular_medication:'', emergency_contact_name:'', emergency_contact_phone:'', emergency_contact_relationship:'' });
        setEditingFicha(false);
        setActiveTab('ficha');
        setShowStudentModal(true);
        try {
            const cs = await healthService.getBehaviorCases({ student: student.id, area: 'MEDICAL' });
            setStudentCases(Array.isArray(cs) ? cs : cs.results || []);
        } catch { setStudentCases([]); }
    };

    const saveMedicalRecord = async (e) => {
        e.preventDefault();
        try {
            const payload = { ...fichaData, student: selectedStudent.id };
            if (fichaData.id) await healthService.updateMedicalRecord(fichaData.id, payload);
            else await healthService.createMedicalRecord(payload);
            showToast('Ficha Médica guardada correctamente');
            setEditingFicha(false);
            loadData();
        } catch { showToast('Error al guardar la Ficha Médica', 'error'); }
    };

    const saveVisit = async (e) => {
        e.preventDefault();
        try {
            await healthService.createMedicalVisit({ ...visitData, student: selectedStudent.id });
            showToast('Consulta registrada correctamente');
            setShowVisitModal(false);
            setVisitData({ reason:'', symptoms:'', diagnosis:'', treatment:'', notes:'' });
            loadData();
        } catch { showToast('Error al registrar la consulta', 'error'); }
    };

    const handleDerive = async () => {
        if (!selectedCase) return;
        try {
            await healthService.deriveCase(selectedCase.id, deriveData);
            showToast('Caso derivado a DECE correctamente');
            setShowDeriveModal(false);
            setSelectedCase(null);
            const cs = await healthService.getBehaviorCases({ student: selectedStudent.id, area: 'MEDICAL' });
            setStudentCases(Array.isArray(cs) ? cs : cs.results || []);
        } catch { showToast('Error al derivar el caso', 'error'); }
    };

    const filteredStudents = useMemo(() => students.filter(s => {
        const name = `${s.first_name} ${s.last_name}`.toLowerCase();
        return name.includes(searchTerm.toLowerCase()) || s.username.toLowerCase().includes(searchTerm.toLowerCase());
    }), [students, searchTerm]);

    const getAvatarColor = (name) => {
        const colors = ['bg-blue-500','bg-indigo-500','bg-purple-500','bg-pink-500','bg-emerald-500','bg-orange-500'];
        let hash = 0;
        for (let i = 0; i < name?.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
        return colors[Math.abs(hash) % colors.length];
    };

    if (loading) return <div className="p-8 flex justify-center"><div className="w-8 h-8 border-4 border-rose-500 border-t-transparent rounded-full animate-spin"></div></div>;

    return (
        <div className="space-y-6 flex flex-col h-full">
            {/* Toast */}
            {toast && (
                <div className={`fixed top-5 right-5 z-[100] px-5 py-3 rounded-xl text-white font-semibold shadow-xl ${toast.type === 'error' ? 'bg-red-500' : 'bg-emerald-500'}`}>
                    {toast.msg}
                </div>
            )}

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shrink-0">
                <div>
                    <h1 className="text-3xl font-bold text-slate-800 tracking-tight flex items-center gap-3">
                        <Activity className="text-rose-500" size={32} /> Dispensario Médico
                    </h1>
                    <p className="text-slate-500 mt-1">Gestión de fichas médicas y consultas sanitarias de estudiantes.</p>
                </div>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex gap-4 shrink-0">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input type="text" placeholder="Buscar estudiante..." className="input-modern pl-10 w-full"
                        value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-10">
                {filteredStudents.length === 0 ? (
                    <div className="col-span-full p-12 text-center text-slate-500 bg-white rounded-xl border border-slate-200">No se encontraron estudiantes.</div>
                ) : filteredStudents.map(student => {
                    const record = getStudentRecord(student.id);
                    const visits = getStudentVisits(student.id);
                    return (
                        <div key={student.id} onClick={() => openStudentProfile(student)}
                            className="card-premium p-5 cursor-pointer hover:border-rose-300 transition-all group relative overflow-hidden">
                            <div className="flex items-center gap-4 mb-4">
                                <div className={`w-12 h-12 rounded-full ${getAvatarColor(student.first_name)} flex items-center justify-center text-white font-bold shadow-md text-lg shrink-0`}>
                                    {student.first_name?.charAt(0)}
                                </div>
                                <div className="overflow-hidden">
                                    <div className="font-bold text-slate-800 group-hover:text-rose-600 transition-colors truncate">{student.first_name} {student.last_name}</div>
                                    <div className="text-xs text-slate-500 truncate">@{student.username}</div>
                                </div>
                            </div>
                            <div className="text-sm text-slate-600 space-y-2 mt-4 pt-4 border-t border-slate-100">
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400 flex items-center gap-1"><Droplet size={14}/> Tipo Sangre:</span>
                                    <span className="font-bold text-slate-700">{record?.blood_type || '--'}</span>
                                </div>
                                <div className="flex items-center justify-between mt-1">
                                    <span className="text-slate-400 flex items-center gap-1"><FileText size={14}/> Ficha:</span>
                                    <span className={record ? 'text-emerald-600 font-medium' : 'text-slate-400'}>{record ? 'Lista' : 'Faltante'}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                    <span className="text-slate-400 flex items-center gap-1"><Activity size={14}/> Consultas:</span>
                                    <span className="font-medium text-slate-700">{visits.length}</span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Modal Principal */}
            {showStudentModal && selectedStudent && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-end">
                    <div className="bg-white w-full max-w-2xl h-full shadow-2xl flex flex-col">
                        <div className="p-6 border-b border-slate-100 bg-slate-50 flex justify-between items-start shrink-0">
                            <div>
                                <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-3">
                                    <div className={`w-10 h-10 rounded-full ${getAvatarColor(selectedStudent.first_name)} flex items-center justify-center text-white text-base shadow-sm`}>
                                        {selectedStudent.first_name?.charAt(0)}
                                    </div>
                                    {selectedStudent.first_name} {selectedStudent.last_name}
                                </h2>
                                <p className="text-slate-500 text-sm mt-1 flex items-center gap-2"><User size={14} /> @{selectedStudent.username}</p>
                            </div>
                            <button onClick={() => setShowStudentModal(false)} className="p-2 text-slate-400 hover:bg-slate-200 rounded-full transition-colors"><X size={20} /></button>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-slate-200 px-6 shrink-0 bg-white">
                            {[
                                { id:'ficha',   label:'Ficha Médica',  icon:<Info size={16}/> },
                                { id:'visitas', label:`Consultas (${getStudentVisits(selectedStudent.id).length})`, icon:<Stethoscope size={16}/> },
                                { id:'casos',   label:'Casos Médicos', icon:<ClipboardList size={16}/>, badge: studentCases.filter(c=>c.status!=='CLOSED').length },
                            ].map(tab => (
                                <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                                    className={`py-4 px-4 font-medium text-sm border-b-2 transition-colors flex items-center gap-2 ${activeTab===tab.id ? 'border-rose-500 text-rose-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
                                    {tab.icon} {tab.label}
                                    {tab.badge > 0 && <span className="bg-rose-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">{tab.badge}</span>}
                                </button>
                            ))}
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
                            {/* FICHA */}
                            {activeTab === 'ficha' && (
                                <div className="space-y-6">
                                    <div className="flex justify-between items-center mb-4">
                                        <h3 className="text-lg font-bold text-slate-800">Ficha y Antecedentes</h3>
                                        {!editingFicha && <button onClick={() => setEditingFicha(true)} className="btn-secondary text-xs flex items-center gap-2 border-rose-200 text-rose-700 hover:bg-rose-50"><Edit size={14}/> Editar Ficha</button>}
                                    </div>
                                    {editingFicha ? (
                                        <form onSubmit={saveMedicalRecord} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-slate-700 mb-1">Tipo de Sangre</label>
                                                <select className="input-modern p-3 w-full" value={fichaData.blood_type} onChange={e => setFichaData({...fichaData, blood_type:e.target.value})}>
                                                    <option value="">No especificado</option>
                                                    {['A+','A-','B+','B-','AB+','AB-','O+','O-'].map(t => <option key={t} value={t}>{t}</option>)}
                                                </select>
                                            </div>
                                            {[['allergies','Alergias'],['chronic_conditions','Condiciones Crónicas'],['regular_medication','Medicación Regular']].map(([field,label]) => (
                                                <div key={field}>
                                                    <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
                                                    <textarea className="input-modern w-full p-3 h-20" value={fichaData[field]} onChange={e => setFichaData({...fichaData,[field]:e.target.value})} />
                                                </div>
                                            ))}
                                            <h4 className="font-bold text-slate-800 pt-4 border-t border-slate-100 flex items-center gap-2"><Phone size={16} className="text-rose-500"/> Contacto de Emergencia</h4>
                                            <div className="grid grid-cols-2 gap-4">
                                                <div><label className="block text-sm font-medium text-slate-700 mb-1">Nombre</label><input type="text" className="input-modern p-3 w-full" value={fichaData.emergency_contact_name} onChange={e => setFichaData({...fichaData,emergency_contact_name:e.target.value})} /></div>
                                                <div><label className="block text-sm font-medium text-slate-700 mb-1">Teléfono</label><input type="text" className="input-modern p-3 w-full" value={fichaData.emergency_contact_phone} onChange={e => setFichaData({...fichaData,emergency_contact_phone:e.target.value})} /></div>
                                                <div className="col-span-2"><label className="block text-sm font-medium text-slate-700 mb-1">Parentesco</label><input type="text" className="input-modern p-3 w-full" value={fichaData.emergency_contact_relationship} onChange={e => setFichaData({...fichaData,emergency_contact_relationship:e.target.value})} /></div>
                                            </div>
                                            <div className="flex justify-end gap-3 pt-4">
                                                <button type="button" onClick={() => setEditingFicha(false)} className="btn-secondary">Cancelar</button>
                                                <button type="submit" className="btn-primary bg-rose-600 hover:bg-rose-700 flex items-center gap-2"><Save size={16}/> Guardar Ficha</button>
                                            </div>
                                        </form>
                                    ) : (
                                        <div className="space-y-4">
                                            <div className="grid grid-cols-2 gap-4">
                                                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                                                    <h4 className="font-semibold text-slate-400 text-xs uppercase tracking-wider mb-2 flex items-center gap-1"><Droplet size={14} className="text-red-500"/> Grupo Sanguíneo</h4>
                                                    <p className="text-3xl font-black text-slate-800">{fichaData.blood_type || <span className="text-slate-300 font-medium text-lg">N/A</span>}</p>
                                                </div>
                                                <div className="bg-rose-50 p-5 rounded-xl border border-rose-200 shadow-sm">
                                                    <h4 className="font-semibold text-rose-800 text-xs uppercase tracking-wider mb-2 flex items-center gap-1"><AlertTriangle size={14}/> Alergias</h4>
                                                    <p className="text-sm font-bold text-rose-900">{fichaData.allergies || <span className="font-medium text-rose-400">Sin alergias registradas</span>}</p>
                                                </div>
                                            </div>
                                            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                                                <h4 className="font-semibold text-slate-800 mb-2 border-b border-slate-100 pb-2 flex items-center gap-2"><Vibrate size={16} className="text-indigo-500"/> Condiciones Crónicas</h4>
                                                <p className="text-slate-600 text-sm">{fichaData.chronic_conditions || <span className="italic text-slate-400">Ninguna.</span>}</p>
                                            </div>
                                            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                                                <h4 className="font-semibold text-slate-800 mb-2 border-b border-slate-100 pb-2 flex items-center gap-2"><Pill size={16} className="text-emerald-500"/> Medicación Regular</h4>
                                                <p className="text-slate-600 text-sm">{fichaData.regular_medication || <span className="italic text-slate-400">Ninguna.</span>}</p>
                                            </div>
                                            <div className="bg-slate-800 p-5 rounded-xl shadow-lg">
                                                <h4 className="font-bold text-white mb-3 flex items-center gap-2"><Phone size={16} className="text-amber-400"/> Contacto de Emergencia</h4>
                                                <div className="flex justify-between items-center">
                                                    <div>
                                                        <p className="font-bold text-slate-100 text-lg">{fichaData.emergency_contact_name || 'No especificado'}</p>
                                                        <p className="text-sm text-slate-400 capitalize">{fichaData.emergency_contact_relationship || '--'}</p>
                                                    </div>
                                                    <p className="font-bold text-amber-400 text-2xl tracking-widest">{fichaData.emergency_contact_phone || '---'}</p>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* VISITAS */}
                            {activeTab === 'visitas' && (
                                <div>
                                    <div className="flex justify-between items-center mb-6">
                                        <h3 className="text-lg font-bold text-slate-800">Historial del Paciente</h3>
                                        <button onClick={() => setShowVisitModal(true)} className="btn-primary bg-rose-600 hover:bg-rose-700 text-xs flex items-center gap-2"><Plus size={14}/> Nueva Consulta</button>
                                    </div>
                                    <div className="space-y-4">
                                        {getStudentVisits(selectedStudent.id).map(visit => (
                                            <div key={visit.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                                                <div className="flex justify-between items-start mb-3">
                                                    <span className="text-sm font-bold text-rose-600">{new Date(visit.date).toLocaleDateString()} {new Date(visit.date).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</span>
                                                    <span className="text-xs bg-slate-100 text-slate-500 font-bold px-2 py-1 rounded">Por: {visit.doctor_name || 'Médico'}</span>
                                                </div>
                                                <p className="font-bold text-slate-800 mb-2">{visit.reason}</p>
                                                <div className="grid grid-cols-2 gap-3 text-sm">
                                                    {visit.symptoms && <div className="bg-rose-50 p-2 rounded"><p className="text-xs font-bold text-rose-500 uppercase mb-1">Síntomas</p><p className="text-slate-600 text-xs">{visit.symptoms}</p></div>}
                                                    {visit.diagnosis && <div className="bg-indigo-50 p-2 rounded"><p className="text-xs font-bold text-indigo-500 uppercase mb-1">Diagnóstico</p><p className="text-slate-700 text-xs font-medium">{visit.diagnosis}</p></div>}
                                                </div>
                                                {visit.treatment && <div className="mt-3 bg-emerald-50 p-3 rounded border border-emerald-100"><p className="text-xs font-bold text-emerald-600 uppercase mb-1">Tratamiento</p><p className="text-slate-700 text-sm">{visit.treatment}</p></div>}
                                                {visit.notes && <p className="text-xs text-slate-400 mt-2 italic">Nota: {visit.notes}</p>}
                                            </div>
                                        ))}
                                        {getStudentVisits(selectedStudent.id).length === 0 && (
                                            <div className="text-center p-8 text-slate-400 border border-dashed rounded-xl">
                                                <Stethoscope size={40} className="text-slate-200 mb-3 mx-auto"/>
                                                <p className="font-medium text-slate-500">Sin consultas registradas</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* CASOS MÉDICOS */}
                            {activeTab === 'casos' && (
                                <div className="space-y-4">
                                    <h3 className="text-lg font-bold text-slate-800">Casos Médicos Derivados</h3>
                                    {studentCases.length === 0 ? (
                                        <div className="text-center p-8 text-slate-400 border border-dashed rounded-xl flex flex-col items-center">
                                            <ClipboardList size={40} className="text-slate-200 mb-3"/>
                                            <p className="font-medium text-slate-500">Sin casos médicos</p>
                                            <p className="text-sm">No hay casos derivados al dispensario para este estudiante.</p>
                                        </div>
                                    ) : studentCases.map(c => {
                                        const sc = c.status==='OPEN'?'bg-blue-100 text-blue-700':c.status==='IN_PROGRESS'?'bg-amber-100 text-amber-700':'bg-slate-100 text-slate-500';
                                        const pc = c.priority==='CRITICAL'?'text-red-600':c.priority==='HIGH'?'text-amber-600':'text-slate-500';
                                        return (
                                            <div key={c.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                                                <div className="flex justify-between items-start gap-2 mb-2">
                                                    <div>
                                                        <p className="font-bold text-slate-800 text-sm">{c.title}</p>
                                                        <p className={`text-xs font-bold mt-1 ${pc}`}>{c.priority_display || c.priority}</p>
                                                    </div>
                                                    <span className={`text-xs font-bold px-2 py-1 rounded-full whitespace-nowrap ${sc}`}>{c.status_display || c.status}</span>
                                                </div>
                                                <p className="text-xs text-slate-500 mb-3">{c.description?.slice(0,120)}...</p>
                                                {c.status !== 'CLOSED' && (
                                                    <button
                                                        onClick={() => { setSelectedCase(c); setDeriveData({area:'DECE',reason:''}); setShowDeriveModal(true); }}
                                                        className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 px-3 py-1.5 rounded-lg font-semibold hover:bg-indigo-100 flex items-center gap-1"
                                                    >
                                                        ↗ Derivar a DECE
                                                    </button>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Modal Nueva Visita */}
            {showVisitModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl p-6 md:p-8 max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex justify-between items-center mb-6 border-b border-slate-100 pb-4">
                            <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2"><Plus size={20} className="text-rose-500"/> Atender Paciente</h2>
                            <button onClick={() => setShowVisitModal(false)} className="text-slate-400 hover:bg-slate-100 p-2 rounded-full"><X size={20}/></button>
                        </div>
                        <form onSubmit={saveVisit} className="space-y-5">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Motivo de Consulta <span className="text-red-500">*</span></label>
                                <input type="text" required className="input-modern p-3 w-full" placeholder="Ej. Dolor de cabeza, raspón en la rodilla..." value={visitData.reason} onChange={e => setVisitData({...visitData,reason:e.target.value})} />
                            </div>
                            <div className="grid grid-cols-2 gap-5">
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Síntomas / Triaje</label>
                                    <textarea className="input-modern p-3 w-full h-24 text-sm" value={visitData.symptoms} onChange={e => setVisitData({...visitData,symptoms:e.target.value})} />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-slate-700 mb-1">Diagnóstico</label>
                                    <textarea className="input-modern p-3 w-full h-24 text-sm bg-indigo-50/50" value={visitData.diagnosis} onChange={e => setVisitData({...visitData,diagnosis:e.target.value})} />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Tratamiento / Decisión Médica</label>
                                <textarea className="input-modern p-3 w-full h-24 text-sm border-emerald-200" value={visitData.treatment} onChange={e => setVisitData({...visitData,treatment:e.target.value})} />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1">Notas Adicionales</label>
                                <textarea className="input-modern p-3 w-full h-16 text-sm" value={visitData.notes} onChange={e => setVisitData({...visitData,notes:e.target.value})} />
                            </div>
                            <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                                <button type="button" onClick={() => setShowVisitModal(false)} className="btn-secondary">Cancelar</button>
                                <button type="submit" className="btn-primary bg-rose-600 hover:bg-rose-700 px-8">Guardar Consulta</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal Derivar a DECE */}
            {showDeriveModal && selectedCase && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[70] flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
                        <h3 className="text-lg font-bold text-slate-800 mb-4">↗ Derivar Caso a DECE</h3>
                        <p className="text-sm text-slate-500 mb-4">Caso: <span className="font-semibold">{selectedCase.title}</span></p>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Motivo de derivación</label>
                        <textarea className="input-modern p-3 w-full h-24 text-sm" placeholder="Describe el motivo para derivar este caso al DECE..."
                            value={deriveData.reason} onChange={e => setDeriveData({...deriveData,reason:e.target.value})} />
                        <div className="flex justify-end gap-3 mt-5">
                            <button onClick={() => setShowDeriveModal(false)} className="btn-secondary">Cancelar</button>
                            <button onClick={handleDerive} className="btn-primary bg-indigo-600 hover:bg-indigo-700">Derivar a DECE</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MedicalDispensaryPage;
