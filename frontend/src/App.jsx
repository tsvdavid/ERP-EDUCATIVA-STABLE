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
import CustomersPage from './pages/treasury/CustomersPage';
import PaymentsPage from './pages/treasury/PaymentsPage';
import InvoicesPage from './pages/treasury/InvoicesPage';
import SriMonitoringPage from './pages/treasury/SriMonitoringPage';
import TreasuryCreditNotesPage from './pages/treasury/TreasuryCreditNotesPage';
import TreasuryCreditNoteForm from './pages/treasury/TreasuryCreditNoteForm';
import TreasuryDebitNotesPage from './pages/treasury/TreasuryDebitNotesPage';
import TreasuryDebitNoteForm from './pages/treasury/TreasuryDebitNoteForm';
import MassBillingPage from './pages/treasury/MassBillingPage';
import TransferVerificationsPage from './pages/admin/TransferVerificationsPage';
import MyAccountPage from './pages/treasury/MyAccountPage';
import CommercialDashboard from './pages/treasury/CommercialDashboard';
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
import LMSCalendar from './pages/learning/LMSCalendar';
import ResourceCenterPage from './pages/knowledge/ResourceCenterPage';
import AIConfigPage from './pages/admin/AIConfigPage';
import MedicalDispensaryPage from './pages/health/MedicalDispensaryPage';
import DecePage from './pages/health/DecePage';
import MyHealthPage from './pages/health/MyHealthPage';
import BehaviorReportsPage from './pages/health/BehaviorReportsPage';
import InstitutionsManagementPage from './pages/admin/InstitutionsManagementPage';
import EmailCenter from './pages/notifications/EmailCenter';
import EmployeeList from './pages/payroll/EmployeeList';
import PayrollDashboard from './pages/payroll/PayrollDashboard';
import AttendanceCalendar from './pages/payroll/AttendanceCalendar';
import SetupWizard from './pages/setup/SetupWizard';
import SaaSDashboard from './pages/admin/SaaSDashboard';
import BillingPage from './pages/settings/BillingPage';
import SaaSObservability from './pages/admin/SaaSObservability';
import PlansManagementPage from './pages/admin/PlansManagementPage';
import SubscriptionsManagementPage from './pages/admin/SubscriptionsManagementPage';
import SaaSSettingsPage from './pages/admin/SaaSSettingsPage';
import SubscriptionSuspended from './pages/public/SubscriptionSuspended';

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
        <div className="p-10 text-center bg-slate-900 min-h-screen text-white flex flex-col items-center justify-center">
          <h1 className="text-2xl font-bold text-rose-500 mb-4">Error Crítico Detectado</h1>
          <p className="text-slate-400 mb-6">La aplicación ha encontrado un problema inesperado.</p>
          <pre className="bg-slate-800 p-4 rounded text-left overflow-auto text-xs text-rose-300 border border-rose-900/50 mb-8 max-w-2xl w-full">
            {this.state.error?.toString()}
          </pre>
          <button
            onClick={() => window.location.reload()}
            className="px-8 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all font-bold shadow-lg shadow-indigo-900/20 active:scale-95"
          >
            Reiniciar Aplicación
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const SetupGuard = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();
  if (isAuthenticated && user && !user.wizard_completed && 
      ['ADMIN', 'RECTOR', 'LOCAL_ADMIN'].includes(user.role) && 
      !window.location.pathname.includes('/setup-wizard')) {
    return <Navigate to="/setup-wizard" replace />;
  }
  return children;
};

const RoleGuard = ({ children, allowedRoles }) => {
  const { isAuthenticated, user, isLoading } = useAuthStore();
  if (isLoading) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white font-bold">Cargando...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    console.warn(`Access denied for role ${user?.role}. Allowed: ${allowedRoles}`);
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

const DevRouteGuard = ({ children }) => {
  const { isAuthenticated, user, isLoading } = useAuthStore();
  if (isLoading) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white font-bold">Verificando acceso...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  
  const isGlobal = user?.role === 'GLOBAL' || user?.is_superuser === true;
  if (!isGlobal) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();
  if (isLoading) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white font-bold">Verificando sesión...</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
};

function App() {
  const checkAuth = useAuthStore(state => state.checkAuth);
  const isLoading = useAuthStore(state => state.isLoading);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) return <div className="flex items-center justify-center h-screen bg-slate-900 text-white font-bold">Cargando ecosistema...</div>;

  return (
    <BrowserRouter>
      <ErrorBoundary>
        <SocketProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/subscription-suspended" element={<SubscriptionSuspended />} />
            <Route path="/setup-wizard" element={
              <ProtectedRoute>
                <SetupWizard />
              </ProtectedRoute>
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <SetupGuard>
                  <DashboardLayout />
                </SetupGuard>
              </ProtectedRoute>
            }>
              <Route index element={<DashboardHome />} />
              <Route path="academic-year" element={<AcademicYearPage />} />
              <Route path="courses" element={<CoursesPage />} />
              <Route path="subjects" element={<SubjectsPage />} />
              <Route path="students" element={<StudentsPage />} />
              <Route path="students/:id" element={<StudentAcademicDetail />} />
              <Route path="grades" element={<GradesPage />} />
              <Route path="grades/student/:studentId" element={<StudentGradesPage />} />
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
              <Route path="admin/institutions" element={<InstitutionsManagementPage />} />
              <Route path="admin/institutions/new" element={<InstitutionPage />} />
              <Route path="admin/institutions/:id" element={<InstitutionPage />} />
              <Route path="treasury/concepts" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><ConceptsPage /></RoleGuard>} />
              <Route path="treasury/customers" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><CustomersPage /></RoleGuard>} />
              <Route path="treasury/payments" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><PaymentsPage /></RoleGuard>} />
              <Route path="treasury/mass-billing" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><MassBillingPage /></RoleGuard>} />
              <Route path="treasury/transfers" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><TransferVerificationsPage /></RoleGuard>} />
              <Route path="treasury/invoices" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><InvoicesPage /></RoleGuard>} />
              <Route path="treasury/sri-monitoring" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><SriMonitoringPage /></RoleGuard>} />
              <Route path="treasury/commercial-dashboard" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><CommercialDashboard /></RoleGuard>} />
              <Route path="treasury/credit-notes" element={<TreasuryCreditNotesPage />} />
              <Route path="treasury/credit-notes/new" element={<TreasuryCreditNoteForm />} />
              <Route path="treasury/debit-notes" element={<TreasuryDebitNotesPage />} />
              <Route path="treasury/debit-notes/new" element={<TreasuryDebitNoteForm />} />
              <Route path="accounting/accounts" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><AccountsPage /></RoleGuard>} />
              <Route path="accounting/entries" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><JournalEntriesPage /></RoleGuard>} />
              <Route path="accounting/entries/new" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><JournalEntryForm /></RoleGuard>} />
              <Route path="accounting/ledger" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><LedgerPage /></RoleGuard>} />
               <Route path="accounting/reports" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><ReportsPage /></RoleGuard>} />
              <Route path="accounting/dashboard" element={<DevRouteGuard><ComingSoonPage title="Dashboard Contable" /></DevRouteGuard>} />
              <Route path="accounting/taxes" element={<DevRouteGuard><ComingSoonPage title="IVA y Tributos" /></DevRouteGuard>} />
              <Route path="accounting/coming-soon/bank-reconciliation" element={<DevRouteGuard><ComingSoonPage title="Conciliación Bancaria" /></DevRouteGuard>} />
              <Route path="accounting/closing" element={<FiscalYearsPage />} />
              <Route path="accounting/analysis" element={<DevRouteGuard><ComingSoonPage title="Análisis y Reportes" /></DevRouteGuard>} />
              <Route path="accounting/integrations" element={<DevRouteGuard><ComingSoonPage title="Integraciones y Automatizaciones" /></DevRouteGuard>} />
              <Route path="accounting/settings" element={<DevRouteGuard><ComingSoonPage title="Configuración y Seguridad Contable" /></DevRouteGuard>} />
              <Route path="accounting/banks" element={<BanksPage />} />
              <Route path="accounting/bank-accounts" element={<BankAccountsPage />} />
              <Route path="accounting/assets" element={<AssetsPage />} />
              <Route path="accounting/assets/new" element={<AssetForm />} />
              <Route path="purchases/suppliers" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><SuppliersPage /></RoleGuard>} />
              <Route path="purchases/invoices" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><PurchasesPage /></RoleGuard>} />
              <Route path="purchases/invoices/new" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><PurchaseForm /></RoleGuard>} />
              <Route path="purchases/credit-notes" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><CreditNotesPage /></RoleGuard>} />
              <Route path="purchases/credit-notes/new" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><CreditNoteForm /></RoleGuard>} />
              <Route path="purchases/debit-notes" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><DebitNotesPage /></RoleGuard>} />
              <Route path="purchases/liquidations" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><LiquidationsPage /></RoleGuard>} />
              <Route path="purchases/liquidations/new" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><LiquidationForm /></RoleGuard>} />
              <Route path="purchases/debit-notes/new" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><DebitNoteForm /></RoleGuard>} />
              <Route path="helpdesk/tickets" element={<TicketPortal />} />
              <Route path="helpdesk/tickets/:id" element={<MyTicketDetail />} />
              <Route path="helpdesk/tickets/agent/:id" element={<TicketDetail />} />
              <Route path="helpdesk/agent" element={<AgentDashboard />} />
              <Route path="privacy/consents" element={<ConsentManager />} />
              <Route path="maintenance/backup" element={<RoleGuard allowedRoles={['ADMIN']}><BackupRestorePage /></RoleGuard>} />
              <Route path="maintenance/users" element={<RoleGuard allowedRoles={['ADMIN']}><UserMaintenancePage /></RoleGuard>} />
              <Route path="maintenance/log" element={<RoleGuard allowedRoles={['ADMIN']}><LogPage /></RoleGuard>} />
              <Route path="maintenance/reset" element={<RoleGuard allowedRoles={['ADMIN']}><ResetPage /></RoleGuard>} />
              <Route path="admin/payment-gateways" element={<RoleGuard allowedRoles={['ADMIN']}><PaymentGatewaysConfigPage /></RoleGuard>} />
              <Route path="admin/saas-dashboard" element={<RoleGuard allowedRoles={['ADMIN']}><SaaSDashboard /></RoleGuard>} />
              <Route path="admin/saas-monitoring" element={<RoleGuard allowedRoles={['ADMIN']}><SaaSObservability /></RoleGuard>} />
              <Route path="admin/saas-plans" element={<RoleGuard allowedRoles={['ADMIN']}><PlansManagementPage /></RoleGuard>} />
              <Route path="admin/subscriptions" element={<RoleGuard allowedRoles={['ADMIN']}><SubscriptionsManagementPage /></RoleGuard>} />
              <Route path="admin/saas-settings" element={<RoleGuard allowedRoles={['ADMIN']}><SaaSSettingsPage /></RoleGuard>} />
              <Route path="settings/billing" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR']}><BillingPage /></RoleGuard>} />
              <Route path="admin/ai-config" element={<RoleGuard allowedRoles={['ADMIN']}><AIConfigPage /></RoleGuard>} />
              <Route path="campus-virtual" element={<CampusVirtualPage />} />
              <Route path="campus-virtual/calendario" element={<LMSCalendar />} />
              <Route path="campus-virtual/instructor" element={<InstructorDashboard />} />
              <Route path="campus-virtual/player/:id" element={<CoursePlayerPage />} />
              <Route path="recursos" element={<ResourceCenterPage />} />
              <Route path="health/medical-dispensary" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'MEDICO']}><MedicalDispensaryPage /></RoleGuard>} />
              <Route path="health/dece" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'DECE']}><DecePage /></RoleGuard>} />
              <Route path="health/my-health" element={<MyHealthPage />} />
              <Route path="health/behavior-records" element={<BehaviorReportsPage />} />
              <Route path="notifications/email-center" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT']}><EmailCenter /></RoleGuard>} />
              <Route path="payroll/employees" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'HR_MANAGER']}><EmployeeList /></RoleGuard>} />
              <Route path="payroll/dashboard" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'ACCOUNTANT', 'HR_MANAGER']}><PayrollDashboard /></RoleGuard>} />
              <Route path="payroll/attendance-calendar" element={<RoleGuard allowedRoles={['ADMIN', 'LOCAL_ADMIN', 'RECTOR', 'HR_MANAGER']}><AttendanceCalendar /></RoleGuard>} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </SocketProvider>
      </ErrorBoundary>
    </BrowserRouter>
  );
}

export default App;
