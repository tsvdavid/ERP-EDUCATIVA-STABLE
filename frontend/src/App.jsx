import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './context/authStore';
import LoginPage from './pages/LoginPage';
import DashboardLayout from './layouts/DashboardLayout';
import CoursesPage from './pages/CoursesPage';
import SubjectsPage from './pages/SubjectsPage';
import StudentsPage from './pages/StudentsPage';
import StudentGradesPage from './pages/StudentGradesPage';
import GradesPage from './pages/GradesPage';
import CommunicationPage from './pages/CommunicationPage';
import ParentDashboard from './pages/ParentDashboard';
import StudentAcademicDetail from './pages/StudentAcademicDetail';
import UsersPage from './pages/UsersPage';
import TeachersPage from './pages/TeachersPage';
import ConceptsPage from './pages/treasury/ConceptsPage';
import PaymentsPage from './pages/treasury/PaymentsPage';
import InvoicesPage from './pages/treasury/InvoicesPage';
import AccountsPage from './pages/accounting/AccountsPage';
import JournalEntriesPage from './pages/accounting/JournalEntriesPage';
import ReportsPage from './pages/accounting/ReportsPage';
import AttendancePage from './pages/AttendancePage';
import InstitutionPage from './pages/InstitutionPage';
import SuppliersPage from './pages/purchases/SuppliersPage';
import PurchasesPage from './pages/purchases/PurchasesPage';
import PurchaseForm from './pages/purchases/PurchaseForm';
import TicketPortal from './pages/helpdesk/TicketPortal';
import AgentDashboard from './pages/helpdesk/AgentDashboard';
import TicketDetail from './pages/helpdesk/TicketDetail';
import MyTicketDetail from './pages/helpdesk/MyTicketDetail';
import ConsentManager from './pages/privacy/ConsentManager';
import { SocketProvider } from './context/SocketContext';
import AcademicYearPage from './pages/AcademicYearPage';
import BackupRestorePage from './pages/maintenance/BackupRestorePage';
import UserMaintenancePage from './pages/maintenance/UserMaintenancePage';
import LogPage from './pages/maintenance/LogPage';
import ResetPage from './pages/maintenance/ResetPage';

// Simple Error Boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-10 text-center">
          <h1 className="text-2xl font-bold text-red-600">Algo salió mal.</h1>
          <p className="text-slate-500 mb-4">La aplicación ha encontrado un error inesperado.</p>
          <pre className="bg-slate-100 p-4 rounded text-left overflow-auto text-xs text-red-800 border border-red-200">
            {this.state.error?.toString()}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Recargar Página
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return <div className="flex items-center justify-center h-screen">Cargando...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

function App() {
  const checkAuth = useAuthStore(state => state.checkAuth);
  const user = useAuthStore(state => state.user);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <SocketProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route path="/dashboard" element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }>
              <Route index element={
                <div className="flex flex-col items-center justify-center h-[60vh] text-center">
                  <div className="bg-white p-10 rounded-3xl shadow-xl shadow-indigo-100 border border-indigo-50 max-w-2xl w-full">
                    <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-6">
                      <span className="text-4xl">🎓</span>
                    </div>
                    <h2 className="text-3xl font-bold text-slate-800 mb-4">¡Bienvenido a EduERP!</h2>
                    <p className="text-slate-500 text-lg mb-8">
                      Tu plataforma de gestión educativa integral. <br />
                      Selecciona una opción del menú lateral para comenzar.
                    </p>
                    <div className="grid grid-cols-2 gap-4 text-left">
                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase">Estado del Sistema</p>
                        <p className="text-green-600 font-medium flex items-center gap-2">● En Línea</p>
                      </div>
                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                        <p className="text-xs font-bold text-slate-400 uppercase">Tu Rol</p>
                        <p className="text-indigo-600 font-medium">
                          {(() => {
                            const role = user?.role;
                            const roles = {
                              'ADMIN': 'Administrador',
                              'RECTOR': 'Rector/Supervisor',
                              'TEACHER': 'Profesor',
                              'PARENT': 'Padre',
                              'STUDENT': 'Estudiante'
                            };
                            return roles[role] || role || 'Cargando...';
                          })()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              } />
              <Route path="academic-years" element={<AcademicYearPage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="subjects" element={<SubjectsPage />} />
              <Route path="students" element={<StudentsPage />} />
              <Route path="grades" element={<GradesPage />} />
              <Route path="student-grades" element={<StudentGradesPage />} />
              <Route path="communication" element={<CommunicationPage />} />
              <Route path="parent" element={<ParentDashboard />} />
              <Route path="parent/student/:studentId" element={<StudentAcademicDetail />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="teachers" element={<TeachersPage />} />
              <Route path="attendance" element={<AttendancePage />} />
              <Route path="institution" element={<InstitutionPage />} />
              <Route path="treasury/concepts" element={<ConceptsPage />} />
              <Route path="treasury/payments" element={<PaymentsPage />} />
              <Route path="treasury/invoices" element={<InvoicesPage />} />
              <Route path="accounting/accounts" element={<AccountsPage />} />
              <Route path="accounting/entries" element={<JournalEntriesPage />} />
              <Route path="accounting/reports" element={<ReportsPage />} />
              <Route path="purchases/suppliers" element={<SuppliersPage />} />
              <Route path="purchases/invoices" element={<PurchasesPage />} />
              <Route path="purchases/invoices/new" element={<PurchaseForm />} />
              <Route path="helpdesk/tickets" element={<TicketPortal />} />
              <Route path="helpdesk/tickets/:id" element={<MyTicketDetail />} />
              <Route path="helpdesk/tickets/agent/:id" element={<TicketDetail />} />
              <Route path="helpdesk/agent" element={<AgentDashboard />} />
              <Route path="privacy/consents" element={<ConsentManager />} />
              <Route path="maintenance/backup" element={<BackupRestorePage />} />
              <Route path="maintenance/users" element={<UserMaintenancePage />} />
              <Route path="maintenance/log" element={<LogPage />} />
              <Route path="maintenance/reset" element={<ResetPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </SocketProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
