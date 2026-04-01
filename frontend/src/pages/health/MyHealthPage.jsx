import React, { useState, useEffect, useMemo } from 'react';
import healthService from '../../services/healthService';
import { useAuthStore } from '../../context/authStore';
import { Heart, Activity, FileText, Calendar, Info, Vibrate, Droplet, Pill, Stethoscope, Phone, AlertTriangle, ShieldCheck } from 'lucide-react';

const MyHealthPage = () => {
    const { user } = useAuthStore();
    const [medicalRecords, setMedicalRecords] = useState([]);
    const [medicalVisits, setMedicalVisits] = useState([]);
    const [deceRecords, setDeceRecords] = useState([]);
    const [deceVisits, setDeceVisits] = useState([]);
    const [behaviorRecords, setBehaviorRecords] = useState([]);
    const [loading, setLoading] = useState(true);

    const [selectedStudentId, setSelectedStudentId] = useState(null);
    const [activeTab, setActiveTab] = useState('medical'); // 'medical' | 'dece'

    useEffect(() => {
        const loadMyData = async () => {
            setLoading(true);
            try {
                // By backend rules, this returns ONLY my records or my children's records
                const [medRecs, medVisits, decRecs, decVisits, behavRecs] = await Promise.all([
                    healthService.getMedicalRecords(),
                    healthService.getMedicalVisits(),
                    healthService.getDeceRecords(),
                    healthService.getDeceVisits(),
                    healthService.getBehaviorRecords()
                ]);
                
                const validMedRecs = Array.isArray(medRecs) ? medRecs : [];
                setMedicalRecords(validMedRecs);
                setMedicalVisits(Array.isArray(medVisits) ? medVisits : []);
                setDeceRecords(Array.isArray(decRecs) ? decRecs : []);
                setDeceVisits(Array.isArray(decVisits) ? decVisits : []);
                setBehaviorRecords(Array.isArray(behavRecs) ? behavRecs : []);
                setBehaviorRecords(arguments[0][4] && Array.isArray(arguments[0][4]) ? arguments[0][4] : []);

                // If user is STUDENT, they only have 1 record.
                // If user is PARENT, they might have multiple. Select first by default if exists.
                if (validMedRecs.length > 0) {
                    setSelectedStudentId(validMedRecs[0].student);
                } else if (user?.role === 'STUDENT') {
                    setSelectedStudentId(user.id);
                }
            } catch (error) {
                console.error("Error fetching health data:", error);
            } finally {
                setLoading(false);
            }
        };

        loadMyData();
    }, [user]);

    // Derived states based on selected student
    const currentMedRecord = medicalRecords.find(r => r.student === selectedStudentId || r.student?.id === selectedStudentId);
    const currentMedVisits = medicalVisits.filter(v => v.student === selectedStudentId || v.student?.id === selectedStudentId).sort((a,b) => new Date(b.date) - new Date(a.date));
    
    const currentDeceRecord = deceRecords.find(r => r.student === selectedStudentId || r.student?.id === selectedStudentId);
    const currentDeceVisits = deceVisits.filter(v => v.student === selectedStudentId || v.student?.id === selectedStudentId).sort((a,b) => new Date(b.date) - new Date(a.date));
    const currentBehaviors = behaviorRecords.filter(r => r.student === selectedStudentId || r.student?.id === selectedStudentId).sort((a,b) => new Date(b.date) - new Date(a.date));

    // For Parents, we extract unique students from the fetched records
    const availableStudents = useMemo(() => {
        const studentsMap = new Map();
        medicalRecords.forEach(r => {
            if (r.student_details) studentsMap.set(r.student, r.student_details);
        });
        deceRecords.forEach(r => {
            if (r.student_details) studentsMap.set(r.student, r.student_details);
        });
        return Array.from(studentsMap.values());
    }, [medicalRecords, deceRecords]);

    if (loading) return <div className="p-8 flex justify-center"><div className="w-8 h-8 border-4 border-rose-500 border-t-transparent rounded-full animate-spin"></div></div>;

    const isParent = user?.role === 'PARENT';

    return (
        <div className="space-y-6 max-w-5xl mx-auto h-full pb-10">
            <div className="bg-gradient-to-r from-rose-500 to-indigo-600 rounded-2xl p-6 md:p-8 text-white shadow-lg relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-10"><Heart size={120} /></div>
                <div className="relative z-10">
                    <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
                        <Heart size={32} /> Mi Salud y Bienestar
                    </h1>
                    <p className="text-rose-100 mt-2 max-w-2xl text-lg">
                        {isParent 
                            ? "Consulta el historial médico, contexto psicológico y alertas emitidas por el dispensario de tus representados."
                            : "Tu portal personal para revisar tu historial de atenciones médicas, reportes del dispensario y seguimiento DECE."}
                    </p>
                </div>
            </div>

            {isParent && availableStudents.length > 0 && (
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
                    <span className="font-bold text-slate-700">Seleccionar Estudiante:</span>
                    <div className="flex gap-2 shrink-0 overflow-x-auto pb-1">
                        {availableStudents.map(student => (
                            <button 
                                key={student.id}
                                onClick={() => setSelectedStudentId(student.id)}
                                className={`px-4 py-2 rounded-lg text-sm font-bold border transition-all ${
                                    selectedStudentId === student.id 
                                    ? 'bg-rose-50 border-rose-500 text-rose-700 shadow-sm' 
                                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                                }`}
                            >
                                {student.first_name} {student.last_name}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {!selectedStudentId ? (
                <div className="bg-white p-8 rounded-2xl shadow-sm text-center border border-slate-200 text-slate-500">
                    <Activity size={48} className="mx-auto mb-4 text-slate-300" />
                    <p className="text-lg">No se encontraron registros médicos vinculados a tu cuenta.</p>
                </div>
            ) : (
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="flex border-b border-slate-200 bg-slate-50 overflow-x-auto">
                        <button 
                            onClick={() => setActiveTab('medical')}
                            className={`py-4 px-6 font-bold text-sm border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === 'medical' ? 'border-rose-500 text-rose-700 bg-white' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                        >
                            <Stethoscope size={18} /> Dispensario Médico
                        </button>
                        <button 
                            onClick={() => setActiveTab('dece')}
                            className={`py-4 px-6 font-bold text-sm border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === 'dece' ? 'border-indigo-500 text-indigo-700 bg-white' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                        >
                            <Vibrate size={18} /> Apoyo Socioemocional (DECE)
                        </button>
                        <button 
                            onClick={() => setActiveTab('behavior')}
                            className={`py-4 px-6 font-bold text-sm border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === 'behavior' ? 'border-amber-500 text-amber-700 bg-white' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                        >
                            <Activity size={18} /> Registro Conductual
                        </button>
                    </div>

                    <div className="p-6 md:p-8">
                        {activeTab === 'medical' && (
                            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2">
                                {/* Ficha Medica Banner */}
                                {!currentMedRecord ? (
                                    <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-start gap-3">
                                        <AlertTriangle className="text-amber-500 shrink-0 mt-0.5" size={20} />
                                        <div>
                                            <h4 className="font-bold text-amber-800">Ficha Médica Inválida o Ausente</h4>
                                            <p className="text-sm text-amber-700">El departamento médico aún no ha registrado la ficha física base. Por favor acércate al dispensario.</p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="bg-slate-50 border border-slate-200 p-6 rounded-2xl space-y-4">
                                        <h3 className="text-lg font-black text-slate-800 flex items-center gap-2 border-b border-slate-200 pb-2">
                                            <Info size={18} className="text-rose-500"/> Mi Ficha de Salud
                                        </h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm">
                                                <p className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1 mb-1"><Droplet size={12}/> Tipo Sangre</p>
                                                <p className="text-2xl font-black text-slate-800">{currentMedRecord.blood_type || '--'}</p>
                                            </div>
                                            <div className="lg:col-span-3 bg-red-50 p-4 rounded-xl border border-red-100 shadow-sm">
                                                <p className="text-xs font-bold text-red-400 uppercase flex items-center gap-1 mb-1"><AlertTriangle size={12}/> Alergias</p>
                                                <p className="text-sm font-bold text-red-900 leading-tight">{currentMedRecord.allergies || 'Ninguna'}</p>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm">
                                                <p className="text-xs font-bold text-slate-400 uppercase flex items-center gap-1 mb-1"><Activity size={12}/> Cond. Crónicas</p>
                                                <p className="text-sm text-slate-700 font-medium">{currentMedRecord.chronic_conditions || 'Ninguna preexistente'}</p>
                                            </div>
                                            <div className="bg-white p-4 rounded-xl border border-slate-100 shadow-sm">
                                                <p className="text-xs font-bold text-emerald-400 uppercase flex items-center gap-1 mb-1"><Pill size={12}/> Medicación</p>
                                                <p className="text-sm text-slate-700 font-medium">{currentMedRecord.regular_medication || 'Sin prescripciones'}</p>
                                            </div>
                                        </div>
                                        {currentMedRecord.emergency_contact_name && (
                                            <div className="bg-slate-800 p-4 rounded-xl flex items-center gap-4 text-white">
                                                <Phone className="text-rose-400" size={24} />
                                                <div>
                                                    <p className="text-xs text-slate-300 uppercase font-bold">Contacto de Emergencia Médica Autorizado</p>
                                                    <p className="font-black text-lg">{currentMedRecord.emergency_contact_phone} <span className="text-sm font-normal text-slate-400 ml-2">({currentMedRecord.emergency_contact_name})</span></p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Visitas Medicas */}
                                <div>
                                    <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2"><Calendar size={20} className="text-rose-500" /> Historial de Consultas Médicas ({currentMedVisits.length})</h3>
                                    
                                    {currentMedVisits.length === 0 ? (
                                        <div className="p-6 text-center text-slate-500 bg-slate-50 rounded-xl border border-slate-100 border-dashed">
                                            No hay registros de atenciones médicas.
                                        </div>
                                    ) : (
                                        <div className="space-y-4">
                                            {currentMedVisits.map(visit => (
                                                <div key={visit.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
                                                    <div className="flex justify-between items-start mb-3">
                                                        <div>
                                                            <p className="text-xs font-bold text-slate-400 uppercase">{new Date(visit.date).toLocaleDateString()} - {new Date(visit.date).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</p>
                                                            <h4 className="font-bold text-slate-800 text-lg">{visit.reason}</h4>
                                                        </div>
                                                        <span className="bg-slate-100 text-slate-600 text-xs font-bold px-2 py-1 rounded">Médico: {visit.doctor_name || 'Turno'}</span>
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm mt-3 pt-3 border-t border-slate-100">
                                                        <div>
                                                            <span className="font-bold text-slate-500 block text-xs uppercase mb-1">Diagnóstico</span>
                                                            <p className="font-medium text-slate-800">{visit.diagnosis || '--'}</p>
                                                        </div>
                                                        <div>
                                                            <span className="font-bold text-emerald-500 block text-xs uppercase mb-1">Tratamiento / Observación</span>
                                                            <p className="text-slate-700 bg-emerald-50 p-2 rounded">{visit.treatment || '--'}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}


                        {activeTab === 'behavior' && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2">
                                <h3 className="text-xl font-bold text-slate-800 flex items-center gap-2"><Activity size={20} className="text-amber-500" /> Registro de Conducta</h3>
                                
                                {currentBehaviors.length === 0 ? (
                                    <div className="p-6 text-center text-slate-500 bg-slate-50 rounded-xl border border-slate-100 border-dashed">
                                        No hay reportes de conducta registrados.
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {currentBehaviors.map(record => (
                                            <div key={record.id} className="bg-white border rounded-xl p-5 shadow-sm border-l-4 border-l-amber-500">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div>
                                                        <p className="text-xs font-bold text-slate-400 uppercase">{new Date(record.date).toLocaleDateString()}</p>
                                                        <h4 className="font-bold text-amber-900 text-lg mt-1">{record.category}</h4>
                                                    </div>
                                                    <span className={`px-3 py-1 text-xs font-bold rounded-full ${record.impact === 'NEGATIVE' ? 'bg-red-100 text-red-700' : record.impact === 'POSITIVE' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}`}>
                                                        {record.impact === 'NEGATIVE' ? 'Negativo' : record.impact === 'POSITIVE' ? 'Positivo' : 'Neutro'}
                                                    </span>
                                                </div>
                                                <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 mt-2">
                                                    <p className="text-slate-700 text-sm">"{record.description}"</p>
                                                </div>
                                                <div className="mt-3 text-xs text-slate-500">
                                                    Registrado por: <strong>{record.reported_by_name || 'Personal Docente'}</strong>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'dece' && (
                            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2">
                                {!currentDeceRecord ? (
                                    <div className="bg-slate-50 border border-slate-200 p-6 rounded-2xl flex items-center justify-center gap-3 text-slate-500">
                                        <ShieldCheck size={24} />
                                        <p className="font-medium">No se ha abierto un expediente en el Departamento de Consejería Estudiantil.</p>
                                    </div>
                                ) : (
                                    <div className="space-y-6">
                                        {currentDeceRecord.has_special_needs && (
                                            <div className="bg-indigo-600 p-5 rounded-2xl text-white shadow-lg flex items-start gap-4">
                                                <Info size={28} className="text-indigo-200 shrink-0" />
                                                <div>
                                                    <h3 className="font-bold text-lg">Acompañamiento por Necesidades Educativas Especiales</h3>
                                                    <p className="text-indigo-100 text-sm mt-1">Este estudiante posee adaptaciones y un seguimiento particular bajo la categoría: <strong>{currentDeceRecord.special_needs_details}</strong></p>
                                                </div>
                                            </div>
                                        )}
                                        
                                        <div>
                                            <h3 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2"><FileText size={20} className="text-indigo-500" /> Registro de Seguimiento y Alertas</h3>
                                            
                                            {currentDeceVisits.length === 0 ? (
                                                <div className="p-6 text-center text-slate-500 bg-slate-50 rounded-xl border border-slate-100 border-dashed">
                                                    No hay intervenciones o citaciones registradas.
                                                </div>
                                            ) : (
                                                <div className="space-y-4">
                                                    {currentDeceVisits.map(visit => (
                                                        <div key={visit.id} className="bg-white border border-indigo-100 rounded-xl p-5 shadow-sm border-l-4 border-l-indigo-400">
                                                            <div className="flex justify-between items-start mb-2">
                                                                <div>
                                                                    <p className="text-xs font-bold text-slate-400 uppercase">{new Date(visit.date).toLocaleDateString()} | Orientador: {visit.counselor_name}</p>
                                                                    <h4 className="font-bold text-indigo-900 text-lg mt-1">{visit.reason}</h4>
                                                                </div>
                                                            </div>
                                                            <div className="text-sm mt-3 space-y-3">
                                                                {visit.observations && (
                                                                    <div>
                                                                        <span className="font-bold text-slate-500 block text-xs uppercase mb-1">Observaciones Iniciales</span>
                                                                        <p className="text-slate-700">{visit.observations}</p>
                                                                    </div>
                                                                )}
                                                                {visit.agreements && (
                                                                    <div className="bg-indigo-50 p-3 rounded-lg border border-indigo-100">
                                                                        <span className="font-bold text-indigo-700 block text-xs uppercase mb-1">Acuerdos / Compromisos Pactados</span>
                                                                        <p className="text-indigo-900 font-medium italic">"{visit.agreements}"</p>
                                                                    </div>
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
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default MyHealthPage;
