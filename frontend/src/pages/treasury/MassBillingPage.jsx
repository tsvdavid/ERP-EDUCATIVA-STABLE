import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import treasuryService from '../../services/treasuryService';
import userService from '../../services/userService';
import academicService from '../../services/academicService';
import { Users, FilePlus, Search, CheckSquare, Square, Filter } from 'lucide-react';

const MassBillingPage = () => {
    const navigate = useNavigate();
    const [students, setStudents] = useState([]);
    const [concepts, setConcepts] = useState([]);
    const [methods, setMethods] = useState([]);
    const [courses, setCourses] = useState([]);
    const [enrollments, setEnrollments] = useState([]);

    // Form State
    const [selectedStudentIds, setSelectedStudentIds] = useState([]);
    const [selectedConcept, setSelectedConcept] = useState('');
    const [selectedMethod, setSelectedMethod] = useState('');
    const [selectedCourse, setSelectedCourse] = useState('');
    const [searchTerm, setSearchTerm] = useState('');

    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        const loadInitialData = async () => {
            try {
                // Fetch Students
                const usersResponse = await userService.getUsers('STUDENT');
                // En backend DRF las busquedas con role pueden venir paginadas
                const studentsList = Array.isArray(usersResponse) ? usersResponse : (usersResponse.results || []);
                setStudents(studentsList);

                // Fetch concepts
                const cons = await treasuryService.getConcepts();
                setConcepts(cons);

                // Fetch payment methods
                const mets = await treasuryService.getMethods();
                setMethods(mets);

                // Fetch Academic Data
                const coursesResp = await academicService.getCourses();
                setCourses(coursesResp);

                const enrollResp = await academicService.getEnrollments();
                setEnrollments(enrollResp);

                // Select defaults
                if (mets.length > 0) {
                    setSelectedMethod(mets[0].id);
                }
            } catch (error) {
                console.error("Error al cargar datos base", error);
            } finally {
                setLoading(false);
            }
        };

        loadInitialData();
    }, []);

    const getStudentsByCourse = () => {
        if (!selectedCourse) return students;
        const validStudentIds = enrollments
            .filter(e => e.course.toString() === selectedCourse.toString())
            .map(e => e.student);
        return students.filter(s => validStudentIds.includes(s.id));
    };

    const courseFilteredStudents = getStudentsByCourse();

    const filteredStudents = courseFilteredStudents.filter(student => {
        const full_name = `${student.first_name || ''} ${student.last_name || ''}`.toLowerCase();
        const ced = (student.cedula || '').toLowerCase();
        const search = searchTerm.toLowerCase();
        return full_name.includes(search) || ced.includes(search);
    });

    const toggleStudent = (id) => {
        if (selectedStudentIds.includes(id)) {
            setSelectedStudentIds(prev => prev.filter(sId => sId !== id));
        } else {
            setSelectedStudentIds(prev => [...prev, id]);
        }
    };

    const toggleAll = () => {
        if (selectedStudentIds.length === filteredStudents.length && filteredStudents.length > 0) {
            setSelectedStudentIds([]); // Deselect all currently filtered
        } else {
            setSelectedStudentIds(filteredStudents.map(s => s.id)); // Select all currently filtered
        }
    };

    const isAllSelected = filteredStudents.length > 0 && selectedStudentIds.length === filteredStudents.length;

    const handleMassBilling = async () => {
        if (selectedStudentIds.length === 0) {
            alert("Seleccione al menos un estudiante para facturar.");
            return;
        }
        if (!selectedConcept) {
            alert("Debe seleccionar el Concepto a cobrar.");
            return;
        }

        if (!window.confirm(`¿Está seguro de generar facturas (Pendiente) a ${selectedStudentIds.length} estudiante(s)?`)) {
            return;
        }

        setProcessing(true);
        try {
            const payload = {
                student_ids: selectedStudentIds,
                concept_id: selectedConcept,
                payment_method_id: selectedMethod || null
            };

            const response = await treasuryService.createMassBilling(payload);
            alert(response.message || "Facturación masiva completada con éxito.");

            // Redirigir a listado de facturas o limpiar form
            navigate('/dashboard/treasury/invoices');
        } catch (error) {
            console.error("Error en facturación masiva", error);
            alert(error.response?.data?.error || "Ocurrió un error en el proceso masivo.");
        } finally {
            setProcessing(false);
        }
    };

    if (loading) {
        return <div className="p-8 text-center text-slate-500">Cargando datos del sistema...</div>;
    }

    const selectedConceptObj = concepts.find(c => c.id.toString() === selectedConcept.toString());
    const totalEstimado = selectedConceptObj ? (parseFloat(selectedConceptObj.price) * selectedStudentIds.length) : 0;

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                        <Users className="text-blue-600" /> Facturación Masiva a Estudiantes
                    </h1>
                    <p className="text-sm text-slate-500 mt-1">
                        Generación automática de Cuentas por Cobrar (Pendiente).
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">

                {/* Panel Lateral: Parámetros */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
                        <h3 className="font-semibold text-slate-800 border-b border-slate-100 pb-3 mb-4 flex items-center gap-2">
                            <FilePlus size={18} className="text-blue-500" /> Parámetros de Emisión
                        </h3>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                    Concepto a Cobrar <span className="text-red-500">*</span>
                                </label>
                                <select
                                    className="w-full border-slate-300 rounded-lg shadow-sm text-sm p-2.5 focus:border-blue-500 focus:ring-blue-500"
                                    value={selectedConcept}
                                    onChange={(e) => setSelectedConcept(e.target.value)}
                                >
                                    <option value="">-- Seleccionar rubro --</option>
                                    {concepts.map(c => (
                                        <option key={c.id} value={c.id}>{c.name} - ${c.price}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                                    Forma de Pago Registrada
                                </label>
                                <select
                                    className="w-full border-slate-300 rounded-lg shadow-sm text-sm p-2.5 focus:border-blue-500 focus:ring-blue-500"
                                    value={selectedMethod}
                                    onChange={(e) => setSelectedMethod(e.target.value)}
                                >
                                    <option value="">-- Defecto (Otros SF) --</option>
                                    {methods.map(m => (
                                        <option key={m.id} value={m.id}>{m.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Resumen Box */}
                    <div className="bg-blue-50 rounded-xl shadow-sm border border-blue-100 p-5">
                        <h3 className="font-semibold text-blue-800 mb-3 block">Resumen de Operación</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between text-blue-700">
                                <span>Alumnos Seleccionados:</span>
                                <strong>{selectedStudentIds.length}</strong>
                            </div>
                            <div className="flex justify-between text-blue-700">
                                <span>Valor Unitario:</span>
                                <strong>${selectedConceptObj ? parseFloat(selectedConceptObj.price).toFixed(2) : '0.00'}</strong>
                            </div>
                            <div className="flex justify-between font-bold text-blue-900 border-t border-blue-200 pt-2 mt-2 text-base">
                                <span>Total Estimado a Emitir:</span>
                                <span>${totalEstimado.toFixed(2)}</span>
                            </div>
                        </div>

                        <button
                            onClick={handleMassBilling}
                            disabled={processing || selectedStudentIds.length === 0 || !selectedConcept}
                            className={`w-full mt-5 py-3 rounded-lg font-bold shadow-sm transition-all flex items-center justify-center gap-2
                                ${processing || selectedStudentIds.length === 0 || !selectedConcept
                                    ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                                    : 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow'}`}
                        >
                            {processing ? (
                                <>Procesando facturas...</>
                            ) : (
                                <>Generar Facturas y Saldos</>
                            )}
                        </button>
                    </div>
                </div>

                {/* Panel Principal: Estudiantes (Checklist) */}
                <div className="lg:col-span-3">
                    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[calc(100vh-140px)]">
                        {/* Toolbar Búsqueda y Filtros */}
                        <div className="p-4 border-b border-slate-100 bg-slate-50 flex flex-col md:flex-row gap-4 items-center justify-between">
                            <div className="flex w-full md:w-auto gap-3 flex-1 max-w-2xl">
                                <div className="relative w-1/2">
                                    <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                    <select
                                        className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white"
                                        value={selectedCourse}
                                        onChange={(e) => {
                                            setSelectedCourse(e.target.value);
                                            // Opcionalmente podemos resetear checkboxes al cambiar de curso
                                            // setSelectedStudentIds([]);
                                        }}
                                    >
                                        <option value="">Filtro: Todos los cursos</option>
                                        {courses.map(c => (
                                            <option key={c.id} value={c.id}>{c.name} {c.parallel} ({c.year})</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="relative w-1/2">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                    <input
                                        type="text"
                                        placeholder="Buscar alumno..."
                                        className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:ring-blue-500 focus:border-blue-500"
                                        value={searchTerm}
                                        onChange={(e) => setSearchTerm(e.target.value)}
                                    />
                                </div>
                            </div>
                            <div className="text-sm font-medium text-slate-600 whitespace-nowrap">
                                {filteredStudents.length} registros listados
                            </div>
                        </div>

                        {/* Tabla */}
                        <div className="overflow-y-auto flex-1 p-0">
                            <table className="min-w-full text-sm text-left">
                                <thead className="text-xs text-slate-500 uppercase bg-slate-100 sticky top-0 z-10 shadow-sm">
                                    <tr>
                                        <th scope="col" className="px-4 py-3 w-16 text-center">
                                            <button
                                                onClick={toggleAll}
                                                className="text-slate-500 hover:text-blue-600 flex justify-center w-full"
                                                title={isAllSelected ? "Deseleccionar Todos" : "Seleccionar Todos"}
                                            >
                                                {isAllSelected ? <CheckSquare size={18} className="text-blue-600" /> : <Square size={18} />}
                                            </button>
                                        </th>
                                        <th scope="col" className="px-6 py-3">Apellidos y Nombres</th>
                                        <th scope="col" className="px-6 py-3">Cédula</th>
                                        <th scope="col" className="px-6 py-3">Correo Electrónico</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {filteredStudents.length > 0 ? (
                                        filteredStudents.map(student => {
                                            const isSelected = selectedStudentIds.includes(student.id);
                                            return (
                                                <tr
                                                    key={student.id}
                                                    className={`hover:bg-blue-50/50 cursor-pointer transition-colors ${isSelected ? 'bg-blue-50' : ''}`}
                                                    onClick={() => toggleStudent(student.id)}
                                                >
                                                    <td className="px-4 py-3 text-center">
                                                        {isSelected ? (
                                                            <CheckSquare size={18} className="text-blue-600 mx-auto" />
                                                        ) : (
                                                            <Square size={18} className="text-slate-300 mx-auto" />
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-3 font-medium text-slate-900 border-l border-transparent">
                                                        {student.last_name} {student.first_name}
                                                    </td>
                                                    <td className="px-6 py-3 text-slate-600 border-l border-transparent">
                                                        {student.cedula || 'N/A'}
                                                    </td>
                                                    <td className="px-6 py-3 text-slate-500 border-l border-transparent">
                                                        {student.email || 'N/A'}
                                                    </td>
                                                </tr>
                                            );
                                        })
                                    ) : (
                                        <tr>
                                            <td colSpan="4" className="px-6 py-12 text-center text-slate-500">
                                                No se encontraron estudiantes con ese criterio.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default MassBillingPage;
