import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import treasuryService from '../services/treasuryService';
import { ChevronLeft, Book, Calendar, AlertCircle, DollarSign } from 'lucide-react';
import CheckoutModal from '../components/payments/CheckoutModal';

const StudentAcademicDetail = () => {
    const { studentId } = useParams();
    const navigate = useNavigate();
    const [stats, setStats] = useState({ grades: [], attendance: [], observations: [] });
    const [charges, setCharges] = useState([]);
    const [loading, setLoading] = useState(true);
    const [studentName, setStudentName] = useState('');
    const [isCheckoutOpen, setIsCheckoutOpen] = useState(false);
    const [cartPayload, setCartPayload] = useState(null);

    useEffect(() => {
        loadData();
    }, [studentId]);

    const loadData = async () => {
        try {
            // Fetch student info just to get name if not passed in state
            // Simplified: fetch grades and extract student name or fetch user
            const userRes = await api.get(`/users/${studentId}/`);
            setStudentName(userRes.data.first_name + ' ' + userRes.data.last_name);

            const [gradesRes, attendanceRes, chargesList] = await Promise.all([
                api.get(`/academic/grades/?student_id=${studentId}`),
                api.get(`/academic/attendance/?student_id=${studentId}`),
                treasuryService.getCharges({ student_id: studentId, pending: 'true' })
            ]);

            setStats({
                grades: gradesRes.data,
                attendance: attendanceRes.data,
                observations: [] // Placeholder until endpoint exists
            });
            setCharges(chargesList || []);

        } catch (error) {
            console.error("Error loading detail", error);
        } finally {
            setLoading(false);
        }
    };

    const handlePayDebt = (charge) => {
        // Setup payload and open checkout modal
        const payload = {
            student_id: studentId,
            amount: parseFloat(charge.amount),
            currency: 'USD', // Could be dynamic from charge
            description: `Pago de: ${charge.concept_detail?.name || 'Deuda'}`,
            reference_id: charge.id,
            concepts: [
                {
                    concept_id: charge.concept_detail?.id,
                    quantity: 1,
                    charge_id: charge.id
                }
            ]
        };
        setCartPayload(payload);
        setIsCheckoutOpen(true);
    };

    const onPaymentSuccess = () => {
        setIsCheckoutOpen(false);
        loadData(); // reload charges
    };

    if (loading) return <div className="p-8 text-center">Cargando detalle...</div>;

    return (
        <div className="space-y-6">
            <button
                onClick={() => navigate(-1)}
                className="flex items-center text-slate-500 hover:text-indigo-600 transition-colors"
            >
                <ChevronLeft size={20} /> Volver
            </button>

            <div>
                <h1 className="text-2xl font-bold text-slate-800">Detalle Académico</h1>
                <p className="text-slate-500">Estudiante: {studentName}</p>
            </div>

            {/* Admin / My Account Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden mb-6">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                    <div className="flex items-center gap-2">
                        <DollarSign size={18} className="text-indigo-600" />
                        <h3 className="font-semibold text-slate-700">Administrativo / Mi Cuenta</h3>
                    </div>
                </div>
                <div className="p-4 space-y-3">
                    {charges.length === 0 ? (
                        <p className="text-slate-500 italic text-sm">Estás al día. No hay facturas o deudas pendientes en este momento.</p>
                    ) : (
                        charges.map(charge => (
                            <div key={charge.id} className="flex justify-between items-center bg-white p-3 rounded-lg border border-red-100 shadow-sm">
                                <div>
                                    <p className="font-bold text-slate-800">{charge.concept_detail?.name || 'Deuda'}</p>
                                    <p className="text-xs text-red-500">Vence: {charge.due_date}</p>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="font-bold text-slate-700">${parseFloat(charge.amount).toFixed(2)}</span>
                                    <button
                                        onClick={() => handlePayDebt(charge)}
                                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 transition-colors flex items-center gap-2 shadow-md shadow-indigo-200"
                                    >
                                        <DollarSign size={16} /> Pagar Ahora
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Grades Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <Book size={18} className="text-indigo-600" />
                    <h3 className="font-semibold text-slate-700">Calificaciones Recientes</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-slate-50/50 text-slate-500">
                            <tr>
                                <th className="p-4 font-medium">Materia</th>
                                <th className="p-4 font-medium">Evaluación</th>
                                <th className="p-4 font-medium">Calificación</th>
                                <th className="p-4 font-medium">Fecha</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                            {stats.grades.map((grade) => (
                                <tr key={grade.id} className="hover:bg-slate-50 transition-colors">
                                    <td className="p-4 font-medium text-slate-800">{grade.enrollment_detail?.subject_name || 'Materia'}</td>
                                    <td className="p-4 text-slate-600">{grade.description || 'Evaluación'}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded font-bold ${parseFloat(grade.score) >= 7 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                            {grade.score}
                                        </span>
                                    </td>
                                    <td className="p-4 text-slate-500">{new Date(grade.date_recorded).toLocaleDateString()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {stats.grades.length === 0 && <p className="p-6 text-center text-slate-400">No hay calificaciones registradas.</p>}
                </div>
            </div>

            {/* Attendance Section */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <Calendar size={18} className="text-indigo-600" />
                    <h3 className="font-semibold text-slate-700">Historial de Asistencia</h3>
                </div>
                <div className="p-4 grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Calendar-like view could go here, for list view: */}
                    {stats.attendance.slice(0, 10).map((att) => (
                        <div key={att.id} className="flex items-center justify-between p-3 border border-slate-100 rounded-lg">
                            <div className="text-sm">
                                <p className="font-medium text-slate-700">{new Date(att.date).toLocaleDateString()}</p>
                                <p className="text-xs text-slate-400">{att.status === 'PRESENT' ? 'Presente' : 'Ausente'}</p>
                            </div>
                            <div className={`w-3 h-3 rounded-full ${att.status === 'PRESENT' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                        </div>
                    ))}
                </div>
                {stats.attendance.length === 0 && <p className="p-6 text-center text-slate-400">No hay registros de asistencia.</p>}
            </div>

            {/* Observations Section (Placeholder) */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2">
                    <AlertCircle size={18} className="text-amber-500" />
                    <h3 className="font-semibold text-slate-700">Observaciones</h3>
                </div>
                <div className="p-6 text-center text-slate-400">
                    Funcionalidad de observaciones en desarrollo.
                </div>
            </div>

            {/* Payment Modal */}
            {cartPayload && (
                <CheckoutModal
                    isOpen={isCheckoutOpen}
                    onClose={() => setIsCheckoutOpen(false)}
                    cartPayload={cartPayload}
                    onPaymentSuccess={onPaymentSuccess}
                />
            )}
        </div>
    );
};

export default StudentAcademicDetail;
