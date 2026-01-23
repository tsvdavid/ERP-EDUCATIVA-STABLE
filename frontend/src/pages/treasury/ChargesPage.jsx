import React, { useState, useEffect } from 'react';
import { Calendar, Users, DollarSign, CheckCircle, AlertCircle } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import treasuryService from '../../services/treasuryService';
import academicService from '../../services/academicService';

const ChargesPage = () => {
    const [concepts, setConcepts] = useState([]);
    const [courses, setCourses] = useState([]);

    // Form State
    const [selectedConcept, setSelectedConcept] = useState('');
    const [selectedCourse, setSelectedCourse] = useState('');
    const [dueDate, setDueDate] = useState('');

    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState([]); // Mock history for now

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [cData, courseData] = await Promise.all([
                treasuryService.getConcepts(),
                academicService.getCourses()
            ]);
            setConcepts(cData);
            setCourses(courseData);
        } catch (error) {
            console.error(error);
            toast.error("Error al cargar datos");
        }
    };

    const handleGenerate = async (e) => {
        e.preventDefault();
        if (!selectedConcept || !selectedCourse || !dueDate) {
            return toast.error("Complete todos los campos");
        }

        if (!window.confirm("¿Está seguro de generar estos cargos? Se crearán deudas para todos los estudiantes del curso seleccionado.")) {
            return;
        }

        setLoading(true);
        try {
            const response = await treasuryService.generateCharges({
                concept_id: selectedConcept,
                course_id: selectedCourse,
                due_date: dueDate
            });
            toast.success(response.message || "Cargos generados exitosamente");
            // Add to history log (visual only for now)
            const conceptName = concepts.find(c => c.id == selectedConcept)?.name;
            const courseName = courses.find(c => c.id == selectedCourse)?.name;
            setHistory([{
                date: new Date().toLocaleDateString(),
                desc: `Generado ${conceptName} para ${courseName}`,
                status: 'Success'
            }, ...history]);

            // Reset
            setSelectedConcept('');
            setSelectedCourse('');
            setDueDate('');

        } catch (error) {
            console.error(error);
            toast.error("Error al generar cargos");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <Toaster position="top-right" />

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Generación de Pensiones y Cobros</h1>
                    <p className="text-slate-500">Genere deudas masivas para cursos completos (Ej. Pensión Mensual).</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Generation Form */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                    <h2 className="font-bold text-lg text-slate-700 mb-6 flex items-center gap-2">
                        <DollarSign className="text-indigo-600" /> Nueva Emisión
                    </h2>

                    <form onSubmit={handleGenerate} className="space-y-5">
                        <div>
                            <label className="label-modern">1. Seleccione el Rubro</label>
                            <select
                                className="input-modern w-full"
                                value={selectedConcept}
                                onChange={e => setSelectedConcept(e.target.value)}
                            >
                                <option value="">-- Seleccione Concepto --</option>
                                {concepts.map(c => (
                                    <option key={c.id} value={c.id}>{c.name} - ${c.price}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="label-modern">2. Seleccione el Curso / Grupo</label>
                            <select
                                className="input-modern w-full"
                                value={selectedCourse}
                                onChange={e => setSelectedCourse(e.target.value)}
                            >
                                <option value="">-- Seleccione Curso --</option>
                                {courses.map(c => (
                                    <option key={c.id} value={c.id}>{c.name} {c.parallel}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="label-modern">3. Fecha Máxima de Pago</label>
                            <input
                                type="date"
                                className="input-modern w-full"
                                value={dueDate}
                                onChange={e => setDueDate(e.target.value)}
                            />
                        </div>

                        <div className="pt-4">
                            <button
                                type="submit"
                                disabled={loading}
                                className="btn-primary w-full flex justify-center items-center gap-2 py-3 text-lg"
                            >
                                {loading ? 'Procesando...' : (
                                    <>
                                        <CheckCircle size={20} /> Generar Cargos
                                    </>
                                )}
                            </button>
                            <p className="text-xs text-slate-400 mt-2 text-center">
                                Se generará una deuda pendiente para cada estudiante inscrito en el curso seleccionado.
                            </p>
                        </div>
                    </form>
                </div>

                {/* Info / History */}
                <div className="space-y-6">
                    <div className="bg-indigo-900 text-white p-6 rounded-xl shadow-lg relative overflow-hidden">
                        <div className="absolute -right-6 -top-6 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
                        <h3 className="text-lg font-bold mb-2 relative z-10">¿Cómo funciona?</h3>
                        <p className="text-indigo-200 text-sm relative z-10 space-y-2">
                            Al generar cargos, el sistema crea un registro de "Cuenta por Cobrar" para cada estudiante.
                            <br /><br />
                            Cuando el padre se acerque a pagar a Caja, estos cargos aparecerán automáticamente como "Pendientes".
                        </p>
                    </div>

                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 min-h-[300px]">
                        <h3 className="font-bold text-slate-700 mb-4">Historial Reciente</h3>
                        {history.length === 0 ? (
                            <div className="text-center py-10 text-slate-400">
                                <Users size={40} className="mx-auto mb-2 opacity-50" />
                                <p>No hay emisiones recientes</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {history.map((h, i) => (
                                    <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
                                        <CheckCircle size={18} className="text-green-500 mt-0.5" />
                                        <div>
                                            <p className="font-medium text-slate-800">{h.desc}</p>
                                            <p className="text-xs text-slate-500">{h.date}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChargesPage;
