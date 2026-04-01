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
import TreasuryCreditNotesPage from './pages/treasury/TreasuryCreditNotesPage';
import TreasuryCreditNoteForm from './pages/treasury/TreasuryCreditNoteForm';
import TreasuryDebitNotesPage from './pages/treasury/TreasuryDebitNotesPage';
import TreasuryDebitNoteForm from './pages/treasury/TreasuryDebitNoteForm';
import MassBillingPage from './pages/treasury/MassBillingPage';
import TransferVerificationsPage from './pages/admin/TransferVerificationsPage';
import MyAccountPage from './pages/treasury/MyAccountPage';
import AccountsPage from './pages/accounting/AccountsPage';
import JournalEntriesPage from './pages/accounting/JournalEntriesPage';
import JournalEntryForm from './pages/accounting/JournalEntryForm';
import LedgerPage from './pages/accounting/LedgerPage';
import ReportsPage from './pages/accounting/ReportsPage';
import ComingSoonPage from './pages/accounting/ComingSoonPage';
import DashboardHome from './pages/DashboardHome';
import FiscalYearsPage from './pages/accounting/FiscalYearsPage';
import AttendancePage from './pages/AttendancePage';
import InstitutionPage from './pages/InstitutionPage';
import CourseScheduleManager from './pages/academic/CourseScheduleManager';
import MySchedulePage from './pages/academic/MySchedulePage';
import SuppliersPage from './pages/purchases/SuppliersPage';
import PurchasesPage from './pages/purchases/PurchasesPage';
import PurchaseForm from './pages/purchases/PurchaseForm';
import CreditNotesPage from './pages/purchases/CreditNotesPage';
import CreditNoteForm from './pages/purchases/CreditNoteForm';
import DebitNotesPage from './pages/purchases/DebitNotesPage';
import LiquidationsPage from './pages/purchases/LiquidationsPage';
import LiquidationForm from './pages/purchases/LiquidationForm';
import DebitNoteForm from './pages/purchases/DebitNoteForm';
import BanksPage from './pages/accounting/BanksPage';
import BankAccountsPage from './pages/accounting/BankAccountsPage';
import AssetsPage from './pages/accounting/AssetsPage';
import AssetForm from './pages/accounting/AssetForm';
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
import AcademicReportsPage from './pages/academic/AcademicReportsPage';
import PaymentGatewaysConfigPage from './pages/admin/PaymentGatewaysConfigPage';
import ProcedureTemplatesPage from './pages/procedures/ProcedureTemplatesPage';
import RequestsInboxPage from './pages/procedures/RequestsInboxPage';
import StudentRequestsPage from './pages/procedures/StudentRequestsPage';
import GlobalReportsPage from './pages/academic/GlobalReportsPage';
import CampusVirtualPage from './pages/learning/CampusVirtualPage';
import CoursePlayerPage from './pages/learning/CoursePlayerPage';
import InstructorDashboard from './pages/learning/InstructorDashboard';
import ResourceCenterPage from './pages/knowledge/ResourceCenterPage';
import AIConfigPage from './pages/admin/AIConfigPage';
import MedicalDispensaryPage from './pages/health/MedicalDispensaryPage';
import DecePage from './pages/health/DecePage';
import MyHealthPage from './pages/health/MyHealthPage';
import BehaviorReportsPage from './pages/health/BehaviorReportsPage';
import logoEduka360 from './assets/logo-eduka360.jpg';

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
            <Route path="/dashboard/campus-virtual/player/:courseId" element={
              <ProtectedRoute>
                <CoursePlayerPage />
              </ProtectedRoute>
            } />

            <Route path="/dashboard" element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }>
              <Route index element={<DashboardHome />} />
              <Route path="academic-years" element={<AcademicYearPage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="subjects" element={<SubjectsPage />} />
              <Route path="academic/schedules-manager" element={<CourseScheduleManager />} />
              <Route path="students" element={<StudentsPage />} />
              <Route path="grades" element={<GradesPage />} />
              <Route path="student-grades" element={<StudentGradesPage />} />
              <Route path="my-schedule" element={<MySchedulePage />} />
              <Route path="communication" element={<CommunicationPage />} />
              <Route path="my-account" element={<MyAccountPage />} />
              <Route path="procedures/templates" element={<ProcedureTemplatesPage />} />
              <Route path="procedures/inbox" element={<RequestsInboxPage />} />
              <Route path="procedures/student" element={<StudentRequestsPage />} />
              <Route path="parent" element={<ParentDashboard />} />
              <Route path="parent/student/:studentId" element={<StudentAcademicDetail />} />
              <Route path="users" element={<UsersPage />} />
              <Route path="teachers" element={<TeachersPage />} />
              <Route path="attendance" element={<AttendancePage />} />
              <Route path="academic/reports" element={<AcademicReportsPage />} />
              <Route path="academic/global-reports" element={<GlobalReportsPage />} />
              <Route path="institution" element={<InstitutionPage />} />
              <Route path="treasury/concepts" element={<ConceptsPage />} />
              <Route path="treasury/payments" element={<PaymentsPage />} />
              <Route path="treasury/mass-billing" element={<MassBillingPage />} />
              <Route path="treasury/transfers" element={<TransferVerificationsPage />} />
              <Route path="treasury/invoices" element={<InvoicesPage />} />
              <Route path="treasury/credit-notes" element={<TreasuryCreditNotesPage />} />
              <Route path="treasury/credit-notes/new" element={<TreasuryCreditNoteForm />} />
              <Route path="treasury/debit-notes" element={<TreasuryDebitNotesPage />} />
              <Route path="treasury/debit-notes/new" element={<TreasuryDebitNoteForm />} />
              <Route path="accounting/accounts" element={<AccountsPage />} />
              <Route path="accounting/entries" element={<JournalEntriesPage />} />
              <Route path="accounting/entries/new" element={<JournalEntryForm />} />
              <Route path="accounting/ledger" element={<LedgerPage />} />
              <Route path="accounting/reports" element={<ReportsPage />} />

              {/* Nuevas Opciones de Contabilidad (Módulos Pendientes de Desarrollar) */}
              <Route path="accounting/dashboard" element={<ComingSoonPage title="Dashboard Contable" />} />
              <Route path="accounting/taxes" element={<ComingSoonPage title="IVA y Tributos" />} />
              <Route path="accounting/coming-soon/bank-reconciliation" element={<ComingSoonPage title="Conciliación Bancaria" />} />
              <Route path="accounting/closing" element={<FiscalYearsPage />} />
              <Route path="accounting/analysis" element={<ComingSoonPage title="Análisis y Reportes" />} />
              <Route path="accounting/integrations" element={<ComingSoonPage title="Integraciones y Automatizaciones" />} />
              <Route path="accounting/settings" element={<ComingSoonPage title="Configuración y Seguridad Contable" />} />
              <Route path="accounting/banks" element={<BanksPage />} />
              <Route path="accounting/bank-accounts" element={<BankAccountsPage />} />
              <Route path="accounting/assets" element={<AssetsPage />} />
              <Route path="accounting/assets/new" element={<AssetForm />} />
              <Route path="purchases/suppliers" element={<SuppliersPage />} />
              <Route path="purchases/invoices" element={<PurchasesPage />} />
              <Route path="purchases/invoices/new" element={<PurchaseForm />} />
              <Route path="purchases/credit-notes" element={<CreditNotesPage />} />
              <Route path="purchases/credit-notes/new" element={<CreditNoteForm />} />
              <Route path="purchases/debit-notes" element={<DebitNotesPage />} />
              <Route path="purchases/liquidations" element={<LiquidationsPage />} />
              <Route path="purchases/liquidations/new" element={<LiquidationForm />} />
              <Route path="purchases/debit-notes/new" element={<DebitNoteForm />} />
              <Route path="helpdesk/tickets" element={<TicketPortal />} />
              <Route path="helpdesk/tickets/:id" element={<MyTicketDetail />} />
              <Route path="helpdesk/tickets/agent/:id" element={<TicketDetail />} />
              <Route path="helpdesk/agent" element={<AgentDashboard />} />
              <Route path="privacy/consents" element={<ConsentManager />} />
              <Route path="maintenance/backup" element={<BackupRestorePage />} />
              <Route path="maintenance/users" element={<UserMaintenancePage />} />
              <Route path="maintenance/log" element={<LogPage />} />
              <Route path="maintenance/reset" element={<ResetPage />} />
              <Route path="admin/payment-gateways" element={<PaymentGatewaysConfigPage />} />
              <Route path="admin/ai-config" element={<AIConfigPage />} />
              <Route path="campus-virtual" element={<CampusVirtualPage />} />
              <Route path="campus-virtual/instructor" element={<InstructorDashboard />} />
              <Route path="recursos" element={<ResourceCenterPage />} />
              <Route path="health/medical-dispensary" element={<MedicalDispensaryPage />} />
              <Route path="health/dece" element={<DecePage />} />
              <Route path="health/my-health" element={<MyHealthPage />} />
              <Route path="health/behavior-records" element={<BehaviorReportsPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </SocketProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
