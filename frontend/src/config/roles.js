/**
 * Matriz de Permisos por Rol - Eduka360 SaaS
 * Centraliza la visibilidad y acceso para facilitar auditorías y escalabilidad.
 */

export const MODULES = {
  ACADEMIC: 'Académico',
  TREASURY: 'Tesorería / Ventas',
  ACCOUNTING: 'Contabilidad',
  ADMINISTRATION: 'Administración',
  HEALTH: 'Salud y Bienestar',
  LEARNING: 'Campus Virtual',
  MAINTENANCE: 'Mantenimiento (Soporte)',
  PRIVACY: 'Privacidad',
  PURCHASES: 'Compras'
};

export const ROLE_PERMISSIONS = {
  ADMIN: Object.values(MODULES), // Acceso total
  LOCAL_ADMIN: [
    MODULES.ACADEMIC, MODULES.TREASURY, MODULES.ACCOUNTING, 
    MODULES.ADMINISTRATION, MODULES.HEALTH, MODULES.LEARNING, 
    MODULES.PRIVACY, MODULES.PURCHASES
  ],
  RECTOR: [
    MODULES.ACADEMIC, MODULES.TREASURY, MODULES.ACCOUNTING, 
    MODULES.ADMINISTRATION, MODULES.HEALTH, MODULES.LEARNING, 
    MODULES.PRIVACY, MODULES.PURCHASES
  ],
  ACCOUNTANT: [
    MODULES.ACCOUNTING, MODULES.TREASURY, MODULES.PURCHASES,
    MODULES.ACADEMIC, // Ver estudiantes/cursos para facturar
    MODULES.PRIVACY
  ],
  TEACHER: [
    MODULES.ACADEMIC, MODULES.LEARNING, MODULES.HEALTH, // Solo registros de comportamiento
    MODULES.ADMINISTRATION, // Ver trámites (Inbox)
    MODULES.PRIVACY
  ],
  STUDENT: [
    MODULES.ACADEMIC, MODULES.LEARNING, MODULES.ADMINISTRATION, // Solo sus trámites
    MODULES.HEALTH, MODULES.PRIVACY
  ],
  PARENT: [
    MODULES.ACADEMIC, MODULES.LEARNING, MODULES.ADMINISTRATION,
    MODULES.HEALTH, MODULES.PRIVACY
  ],
  SECRETARY: [
    MODULES.ACADEMIC, MODULES.ADMINISTRATION, MODULES.TREASURY
  ]
};

/**
 * Verifica si un rol tiene acceso a un módulo.
 */
export const hasModuleAccess = (role, moduleName) => {
  if (role === 'ADMIN') return true;
  const permissions = ROLE_PERMISSIONS[role] || [];
  return permissions.includes(moduleName);
};
