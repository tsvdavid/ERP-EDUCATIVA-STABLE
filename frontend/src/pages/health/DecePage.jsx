import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import healthService from '../../services/healthService';
import academicService from '../../services/academicService';
import BehaviorQuickModal from '../../components/BehaviorQuickModal';

// ── Constantes ───────────────────────────────────────────────────────────────
const RISK_CONFIG = {
  GREEN:  { label: '🟢 Bien',    color: '#22c55e', bg: '#f0fdf4' },
  YELLOW: { label: '🟡 Riesgo',  color: '#f59e0b', bg: '#fffbeb' },
  RED:    { label: '🔴 Crítico', color: '#ef4444', bg: '#fef2f2' },
};
const STATUS_CONFIG = {
  OPEN:        { label: 'Abierto',        color: '#3b82f6', bg: '#eff6ff' },
  IN_PROGRESS: { label: 'En Seguimiento', color: '#f59e0b', bg: '#fffbeb' },
  CLOSED:      { label: 'Cerrado',        color: '#6b7280', bg: '#f9fafb' },
};
const PRIORITY_CONFIG = {
  LOW:      { label: 'Baja',    color: '#6b7280' },
  MEDIUM:   { label: 'Media',   color: '#3b82f6' },
  HIGH:     { label: 'Alta',    color: '#f59e0b' },
  CRITICAL: { label: 'Crítica', color: '#ef4444' },
};
const AREA_COLORS = { DECE: '#6366f1', MEDICAL: '#14b8a6', EXTERNAL: '#f97316' };

// ── Componente principal ─────────────────────────────────────────────────────
export default function DecePage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeYear, setActiveYear] = useState(null);
  const [years, setYears]           = useState([]);
  const [stats, setStats]           = useState(null);
  const [profiles, setProfiles]     = useState([]);
  const [cases, setCases]           = useState([]);
  const [alertRules, setAlertRules] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [followUps, setFollowUps]       = useState([]);
  const [loading, setLoading]           = useState(false);
  const [searchText, setSearchText]     = useState('');
  const [filterRisk, setFilterRisk]     = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [showDeriveModal, setShowDeriveModal] = useState(false);
  const [showCloseModal, setShowCloseModal]   = useState(false);
  const [showRuleForm, setShowRuleForm]       = useState(false);
  const [deriveData, setDeriveData]   = useState({ area: 'MEDICAL', reason: '' });
  const [closeData, setCloseData]     = useState({ summary: '' });
  const [ruleForm, setRuleForm]       = useState({ name:'', negative_count_threshold:3, days_window:7, auto_create_case:true, target_area:'DECE', notify_dece:true, notify_tutor:true, notify_parents:false, is_active:true });
  const [toast, setToast]             = useState(null);
  const [newFollowUp, setNewFollowUp] = useState({ follow_up_type:'NOTE', content:'', agreements:'', is_confidential:false, attachment:null });

  // ── Carga inicial ──────────────────────────────────────────────────────────
  useEffect(() => {
    async function init() {
      try {
        const yrs = await academicService.getAcademicYears();
        setYears(yrs);
        const active = yrs.find(y => y.is_active) || yrs[0];
        if (active) setActiveYear(active);
      } catch {}
    }
    init();
  }, []);

  const loadAll = useCallback(async () => {
    if (!activeYear) return;
    setLoading(true);
    try {
      const [st, pr, cs, ar] = await Promise.all([
        healthService.getDashboardStats(activeYear.id),
        healthService.getRiskProfiles({ academic_year: activeYear.id }),
        healthService.getBehaviorCases({ academic_year: activeYear.id }),
        healthService.getAlertRules(),
      ]);
      setStats(st);
      setProfiles(Array.isArray(pr) ? pr : pr.results || []);
      setCases(Array.isArray(cs) ? cs : cs.results || []);
      setAlertRules(Array.isArray(ar) ? ar : ar.results || []);
    } catch {}
    setLoading(false);
  }, [activeYear]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  // ── Acciones de caso ───────────────────────────────────────────────────────
  const openCase = async (c) => {
    setSelectedCase(c);
    try {
      const full = await healthService.getBehaviorCase(c.id);
      setSelectedCase(full);
      const fu = await healthService.getCaseFollowUps(c.id);
      setFollowUps(Array.isArray(fu) ? fu : fu.results || []);
    } catch {}
  };

  const handleDerive = async () => {
    try {
      await healthService.deriveCase(selectedCase.id, deriveData);
      showToast('Caso derivado correctamente');
      setShowDeriveModal(false);
      setSelectedCase(null);
      loadAll();
    } catch { showToast('Error al derivar', 'error'); }
  };

  const handleClose = async () => {
    try {
      await healthService.closeCase(selectedCase.id, closeData);
      showToast('Caso cerrado');
      setShowCloseModal(false);
      setSelectedCase(null);
      loadAll();
    } catch { showToast('Error al cerrar', 'error'); }
  };

  const handleAddFollowUp = async () => {
    if (!newFollowUp.content.trim()) return;
    try {
      const fd = new FormData();
      fd.append('case', selectedCase.id);
      fd.append('follow_up_type', newFollowUp.follow_up_type);
      fd.append('content', newFollowUp.content);
      fd.append('agreements', newFollowUp.agreements);
      fd.append('is_confidential', newFollowUp.is_confidential);
      if (newFollowUp.attachment) fd.append('attachment', newFollowUp.attachment);
      
      await healthService.createFollowUp(fd);
      const fu = await healthService.getCaseFollowUps(selectedCase.id);
      setFollowUps(Array.isArray(fu) ? fu : fu.results || []);
      setNewFollowUp({ follow_up_type:'NOTE', content:'', agreements:'', is_confidential:false, attachment:null });
      showToast('Seguimiento agregado');
    } catch { showToast('Error al guardar', 'error'); }
  };

  const handleSaveRule = async () => {
    try {
      await healthService.createAlertRule(ruleForm);
      showToast('Regla creada');
      setShowRuleForm(false);
      setRuleForm({ name:'', negative_count_threshold:3, days_window:7, auto_create_case:true, target_area:'DECE', notify_dece:true, notify_tutor:true, notify_parents:false, is_active:true });
      loadAll();
    } catch { showToast('Error al guardar regla', 'error'); }
  };

  const handleDeleteRule = async (id) => {
    if (!window.confirm('¿Eliminar esta regla?')) return;
    try { await healthService.deleteAlertRule(id); showToast('Regla eliminada'); loadAll(); }
    catch { showToast('Error al eliminar', 'error'); }
  };

  // ── Filtros ────────────────────────────────────────────────────────────────
  const filteredProfiles = profiles.filter(p => {
    const name = (p.student_name || '').toLowerCase();
    if (searchText && !name.includes(searchText.toLowerCase())) return false;
    if (filterRisk && p.overall_risk !== filterRisk) return false;
    return true;
  });

  const filteredCases = cases.filter(c => {
    const name = (c.student_name || '').toLowerCase();
    if (searchText && !name.includes(searchText.toLowerCase())) return false;
    if (filterStatus && c.status !== filterStatus) return false;
    if (filterPriority && c.priority !== filterPriority) return false;
    return true;
  });

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={S.page}>
      {/* Toast */}
      {toast && (
        <div style={{ ...S.toast, background: toast.type === 'error' ? '#ef4444' : '#22c55e' }}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={S.header}>
        <div>
          <h1 style={S.title}>🧠 Panel DECE</h1>
          <p style={S.subtitle}>Seguimiento conductual y bienestar estudiantil</p>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <button style={S.btnPrimary} onClick={() => navigate('/dashboard/health/behavior-records')}>
             📊 Ir a Reportes
          </button>
          <select style={S.yearSelect} value={activeYear?.id || ''} onChange={e => setActiveYear(years.find(y => y.id == e.target.value))}>
            {years.map(y => <option key={y.id} value={y.id}>{y.name}</option>)}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div style={S.tabs}>
        {[
          { id:'dashboard', label:'📊 Dashboard'  },
          { id:'students',  label:'👥 Estudiantes' },
          { id:'cases',     label:'📋 Casos'       },
          { id:'config',    label:'⚙️ Reglas'      },
        ].map(tab => (
          <button key={tab.id} style={{ ...S.tab, ...(activeTab === tab.id ? S.tabActive : {}) }}
            onClick={() => setActiveTab(tab.id)}>{tab.label}</button>
        ))}
      </div>

      <div style={S.content}>
        {loading && <div style={S.loadingBar} />}

        {/* ── Tab Dashboard ── */}
        {activeTab === 'dashboard' && stats && (
          <div style={S.dashGrid}>
            {/* KPI cards */}
            {[
              { label:'Casos Abiertos',      value: stats.open_cases,       color:'#3b82f6', icon:'📂' },
              { label:'En Seguimiento',       value: stats.in_progress_cases, color:'#f59e0b', icon:'🔄' },
              { label:'Estudiantes 🟢 Bien',  value: stats.risk_summary?.green  || 0, color:'#22c55e', icon:'🟢' },
              { label:'Estudiantes 🔴 Críticos', value: stats.risk_summary?.red || 0, color:'#ef4444', icon:'🔴' },
            ].map((k, i) => (
              <div key={i} style={{ ...S.kpiCard, borderTop:`4px solid ${k.color}` }}>
                <div style={S.kpiIcon}>{k.icon}</div>
                <div style={{ ...S.kpiValue, color: k.color }}>{k.value ?? '—'}</div>
                <div style={S.kpiLabel}>{k.label}</div>
              </div>
            ))}

            {/* Semáforo */}
            <div style={{ ...S.card, gridColumn:'span 2' }}>
              <div style={S.cardTitle}>Distribución de Riesgo</div>
              <div style={S.riskBar}>
                {['GREEN','YELLOW','RED'].map(r => {
                  const cnt = stats.risk_summary?.[r.toLowerCase()] || 0;
                  const total = stats.total_students || 1;
                  const pct = Math.round(cnt / total * 100);
                  return (
                    <div key={r} style={{ ...S.riskSegment, flex: cnt || 1, background: RISK_CONFIG[r].color }}
                         title={`${RISK_CONFIG[r].label}: ${cnt} estudiantes (${pct}%)`}>
                      {cnt > 0 && <span style={S.riskSegmentLabel}>{cnt}</span>}
                    </div>
                  );
                })}
              </div>
              <div style={S.riskLegend}>
                {['GREEN','YELLOW','RED'].map(r => (
                  <span key={r} style={S.legendItem}>
                    <span style={{ ...S.legendDot, background: RISK_CONFIG[r].color }} />
                    {RISK_CONFIG[r].label}: {stats.risk_summary?.[r.toLowerCase()] || 0}
                  </span>
                ))}
              </div>
            </div>

            {/* Registros últimos 7 días */}
            <div style={{ ...S.card, gridColumn:'span 2' }}>
              <div style={S.cardTitle}>Registros últimos 7 días</div>
              {(stats.records_last_7d || []).length === 0
                ? <div style={S.empty}>Sin registros recientes</div>
                : stats.records_last_7d.map(r => {
                  const typeDict = { 'ACADEMIC': 'Académico', 'POSITIVE': 'Positivo (Destaque)', 'NEGATIVE_MILD': 'Falta Leve', 'NEGATIVE_SEVERE': 'Falta Grave' };
                  const typeLabel = typeDict[r.record_type] || r.record_type;
                  return (
                  <div key={r.record_type} style={S.statRow}>
                    <span>{typeLabel}</span>
                    <div style={S.statBarWrap}>
                      <div style={{ ...S.statBarFill, width:`${Math.min(100,(r.count/10)*100)}%`, background:'#6366f1' }} />
                    </div>
                    <span style={S.statCount}>{r.count}</span>
                  </div>
                );})
              }
            </div>
          </div>
        )}

        {/* ── Tab Estudiantes ── */}
        {activeTab === 'students' && (
          <div>
            <div style={S.toolbar}>
              <input style={S.search} placeholder="🔍 Buscar estudiante..." value={searchText} onChange={e => setSearchText(e.target.value)} />
              <select style={S.filter} value={filterRisk} onChange={e => setFilterRisk(e.target.value)}>
                <option value="">Todos los semáforos</option>
                {Object.entries(RISK_CONFIG).map(([k,v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
              <button style={S.btnSecondary} onClick={() => healthService.recalculateRiskProfiles({ academic_year: activeYear?.id }).then(() => { showToast('Perfiles recalculados'); loadAll(); })}>
                🔄 Recalcular
              </button>
            </div>
            <div style={S.tableWrap}>
              <table style={S.table}>
                <thead>
                  <tr style={S.thead}>
                    <th style={S.th}>Estudiante</th>
                    <th style={S.th}>Semáforo</th>
                    <th style={S.th}>Conducta</th>
                    <th style={S.th}>Asistencia</th>
                    <th style={S.th}>Académico</th>
                    <th style={S.th}>7 días neg.</th>
                    <th style={S.th}>Caso abierto</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProfiles.length === 0
                    ? <tr><td colSpan={7} style={S.empty}>Sin datos. Presiona Recalcular.</td></tr>
                    : filteredProfiles.map(p => {
                      const rc = RISK_CONFIG[p.overall_risk] || RISK_CONFIG.GREEN;
                      return (
                        <tr key={p.id} style={S.tr}>
                          <td style={S.td}><span style={S.studentName}>{p.student_name}</span></td>
                          <td style={S.td}><span style={{ ...S.badge, background: rc.bg, color: rc.color }}>{rc.label}</span></td>
                          <td style={S.td}><ScoreBar value={p.behavior_score} /></td>
                          <td style={S.td}><ScoreBar value={p.attendance_score} /></td>
                          <td style={S.td}><ScoreBar value={p.academic_score} /></td>
                          <td style={S.td}><span style={{ color: p.negative_count_7d > 0 ? '#ef4444' : '#22c55e', fontWeight:700 }}>{p.negative_count_7d}</span></td>
                          <td style={S.td}>{p.has_open_case ? <span style={{ color:'#f59e0b' }}>⚠️ Sí</span> : <span style={{ color:'#22c55e' }}>✓ No</span>}</td>
                        </tr>
                      );
                    })
                  }
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Tab Casos ── */}
        {activeTab === 'cases' && (
          <div>
            <div style={S.toolbar}>
              <input style={S.search} placeholder="🔍 Buscar estudiante..." value={searchText} onChange={e => setSearchText(e.target.value)} />
              <select style={S.filter} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
                <option value="">Todos los estados</option>
                {Object.entries(STATUS_CONFIG).map(([k,v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
              <select style={S.filter} value={filterPriority} onChange={e => setFilterPriority(e.target.value)}>
                <option value="">Todas las prioridades</option>
                {Object.entries(PRIORITY_CONFIG).map(([k,v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>
            <div style={S.tableWrap}>
              <table style={S.table}>
                <thead>
                  <tr style={S.thead}>
                    <th style={S.th}>Título</th>
                    <th style={S.th}>Estudiante</th>
                    <th style={S.th}>Área</th>
                    <th style={S.th}>Prioridad</th>
                    <th style={S.th}>Estado</th>
                    <th style={S.th}>Seguimientos</th>
                    <th style={S.th}>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCases.length === 0
                    ? <tr><td colSpan={7} style={S.empty}>Sin casos registrados</td></tr>
                    : filteredCases.map(c => {
                      const sc = STATUS_CONFIG[c.status]   || STATUS_CONFIG.OPEN;
                      const pc = PRIORITY_CONFIG[c.priority] || PRIORITY_CONFIG.MEDIUM;
                      return (
                        <tr key={c.id} style={{ ...S.tr, cursor:'pointer' }} onClick={() => openCase(c)}>
                          <td style={S.td}><span style={S.caseTitle}>{c.title}</span></td>
                          <td style={S.td}>{c.student_name}</td>
                          <td style={S.td}><span style={{ ...S.badge, background: AREA_COLORS[c.area]+'22', color: AREA_COLORS[c.area] }}>{c.area_display || c.area}</span></td>
                          <td style={S.td}><span style={{ color: pc.color, fontWeight:700 }}>{pc.label}</span></td>
                          <td style={S.td}><span style={{ ...S.badge, background: sc.bg, color: sc.color }}>{sc.label}</span></td>
                          <td style={S.td}>{c.follow_up_count ?? '—'}</td>
                          <td style={S.td} onClick={e => e.stopPropagation()}>
                            <button style={S.btnXs} onClick={() => openCase(c)}>Ver</button>
                          </td>
                        </tr>
                      );
                    })
                  }
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Tab Config ── */}
        {activeTab === 'config' && (
          <div>
            <div style={{ display:'flex', justifyContent:'flex-end', marginBottom:16 }}>
              <button style={S.btnPrimary} onClick={() => setShowRuleForm(true)}>+ Nueva Regla</button>
            </div>
            {alertRules.length === 0
              ? <div style={S.emptyState}>No hay reglas configuradas. Crea una para activar alertas automáticas.</div>
              : alertRules.map(rule => (
                <div key={rule.id} style={{ ...S.ruleCard, opacity: rule.is_active ? 1 : 0.5 }}>
                  <div style={S.ruleHeader}>
                    <span style={S.ruleName}>{rule.name}</span>
                    <div style={{ display:'flex', gap:8 }}>
                      <span style={{ ...S.badge, background: rule.is_active ? '#f0fdf4':'#f9fafb', color: rule.is_active ? '#22c55e':'#6b7280' }}>
                        {rule.is_active ? '✓ Activa' : 'Inactiva'}
                      </span>
                      <button style={S.btnDanger} onClick={() => handleDeleteRule(rule.id)}>Eliminar</button>
                    </div>
                  </div>
                  <div style={S.ruleDetail}>
                    📊 {rule.negative_count_threshold} negativas en {rule.days_window} días →
                    Crear caso en <strong>{rule.target_area}</strong>
                    {rule.include_low_grades && ` | Incluye notas < ${rule.grade_threshold}`}
                    {rule.include_absences && ` | Incluye > ${rule.absence_threshold} faltas`}
                  </div>
                </div>
              ))
            }
            {/* Formulario regla */}
            {showRuleForm && (
              <div style={S.modal}>
                <div style={S.modalBox}>
                  <h3 style={{ marginTop:0 }}>Nueva Regla de Alerta</h3>
                  <div style={S.formGrid}>
                    <div>
                      <label style={S.formLabel}>Nombre</label>
                      <input style={S.input} value={ruleForm.name} onChange={e => setRuleForm({...ruleForm, name:e.target.value})} />
                    </div>
                    <div>
                      <label style={S.formLabel}>Observaciones negativas</label>
                      <input type="number" style={S.input} value={ruleForm.negative_count_threshold} onChange={e => setRuleForm({...ruleForm, negative_count_threshold:+e.target.value})} />
                    </div>
                    <div>
                      <label style={S.formLabel}>Ventana (días)</label>
                      <input type="number" style={S.input} value={ruleForm.days_window} onChange={e => setRuleForm({...ruleForm, days_window:+e.target.value})} />
                    </div>
                    <div>
                      <label style={S.formLabel}>Área destino</label>
                      <select style={S.input} value={ruleForm.target_area} onChange={e => setRuleForm({...ruleForm, target_area:e.target.value})}>
                        <option value="DECE">DECE</option>
                        <option value="MEDICAL">Dispensario Médico</option>
                        <option value="EXTERNAL">Institución Externa</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display:'flex', gap:12, marginTop:16 }}>
                    <label style={S.checkLabel}><input type="checkbox" checked={ruleForm.notify_dece} onChange={e => setRuleForm({...ruleForm, notify_dece:e.target.checked})} /> Notif. DECE</label>
                    <label style={S.checkLabel}><input type="checkbox" checked={ruleForm.notify_tutor} onChange={e => setRuleForm({...ruleForm, notify_tutor:e.target.checked})} /> Notif. Tutor</label>
                    <label style={S.checkLabel}><input type="checkbox" checked={ruleForm.notify_parents} onChange={e => setRuleForm({...ruleForm, notify_parents:e.target.checked})} /> Notif. Padres</label>
                  </div>
                  <div style={{ display:'flex', justifyContent:'flex-end', gap:10, marginTop:20 }}>
                    <button style={S.btnSecondary} onClick={() => setShowRuleForm(false)}>Cancelar</button>
                    <button style={S.btnPrimary} onClick={handleSaveRule}>Guardar</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Modal Detalle de Caso ── */}
      {selectedCase && (
        <div style={S.modal}>
          <div style={{ ...S.modalBox, maxWidth:700, maxHeight:'90vh', overflowY:'auto' }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
              <div>
                <div style={S.caseTitle}>{selectedCase.title}</div>
                <div style={{ color:'#64748b', fontSize:'0.85rem' }}>{selectedCase.student_name} · {selectedCase.area_display}</div>
              </div>
              <button style={S.closeBtn} onClick={() => setSelectedCase(null)}>✕</button>
            </div>
            <p style={{ color:'#475569', fontSize:'0.9rem' }}>{selectedCase.description}</p>
            <div style={{ display:'flex', gap:8, flexWrap:'wrap', marginBottom:16 }}>
              {selectedCase.status !== 'CLOSED' && (
                <>
                  <button style={{ ...S.btnSmall, background:'#6366f1' }} onClick={() => setShowDeriveModal(true)}>↗ Derivar</button>
                  <button style={{ ...S.btnSmall, background:'#ef4444' }} onClick={() => setShowCloseModal(true)}>✓ Cerrar caso</button>
                </>
              )}
              {selectedCase.status === 'CLOSED' && (
                <button style={{ ...S.btnSmall, background:'#22c55e' }} onClick={async () => { await healthService.reopenCase(selectedCase.id); setSelectedCase(null); loadAll(); }}>↩ Reabrir</button>
              )}
            </div>

            {/* Timeline de seguimientos */}
            <div style={S.cardTitle}>📋 Seguimientos ({followUps.length})</div>
            <div style={{ display:'flex', flexDirection:'column', gap:10, maxHeight:260, overflowY:'auto', marginBottom:16 }}>
              {followUps.length === 0
                ? <div style={S.empty}>Sin seguimientos aún</div>
                : followUps.map(fu => (
                  <div key={fu.id} style={{ ...S.followUpItem, borderLeft:`3px solid ${fu.is_confidential ? '#f59e0b' : '#6366f1'}` }}>
                    <div style={{ display:'flex', justifyContent:'space-between' }}>
                      <span style={{ fontWeight:600, fontSize:'0.85rem' }}>{fu.follow_up_type_display || fu.follow_up_type}</span>
                      <span style={{ fontSize:'0.75rem', color:'#94a3b8' }}>{fu.created_by_name} · {new Date(fu.created_at).toLocaleDateString()}</span>
                    </div>
                    <div style={{ color:'#475569', fontSize:'0.88rem', marginTop:4 }}>{fu.content}</div>
                    {fu.agreements && <div style={{ color:'#64748b', fontSize:'0.82rem', marginTop:4 }}>📝 {fu.agreements}</div>}
                    {fu.attachment && <div style={{ marginTop:6 }}><a href={fu.attachment} target="_blank" rel="noreferrer" style={{ fontSize:'0.8rem', color:'#3b82f6', textDecoration:'none', fontWeight:600 }}>📎 Ver Archivo Adjunto</a></div>}
                    {fu.is_confidential && <div style={{ color:'#f59e0b', fontSize:'0.75rem', marginTop:4 }}>🔒 Confidencial</div>}
                  </div>
                ))
              }
            </div>

            {/* Nuevo seguimiento */}
            {selectedCase.status !== 'CLOSED' && (
              <div style={S.newFollowUp}>
                <div style={S.cardTitle}>+ Nuevo seguimiento</div>
                <select style={{ ...S.input, marginBottom:8 }} value={newFollowUp.follow_up_type} onChange={e => setNewFollowUp({...newFollowUp, follow_up_type:e.target.value})}>
                  <option value="NOTE">Nota Interna</option>
                  <option value="INTERVIEW_STUDENT">Entrevista Estudiante</option>
                  <option value="INTERVIEW_PARENT">Entrevista Representante</option>
                  <option value="OBSERVATION">Observación</option>
                  <option value="AGREEMENT">Acuerdo/Compromiso</option>
                  <option value="REFERRAL">Derivación</option>
                </select>
                <textarea style={{ ...S.input, minHeight:80, resize:'vertical' }} placeholder="Contenido del seguimiento..." value={newFollowUp.content} onChange={e => setNewFollowUp({...newFollowUp, content:e.target.value})} />
                <textarea style={{ ...S.input, minHeight:50, resize:'vertical', marginTop:6 }} placeholder="Acuerdos / compromisos (opcional)..." value={newFollowUp.agreements} onChange={e => setNewFollowUp({...newFollowUp, agreements:e.target.value})} />
                <input type="file" style={{ ...S.input, marginTop:6, fontSize:'0.8rem' }} onChange={e => setNewFollowUp({...newFollowUp, attachment:e.target.files[0]})} accept=".pdf,.doc,.docx,.jpg,.png" />
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:8 }}>
                  <label style={S.checkLabel}><input type="checkbox" checked={newFollowUp.is_confidential} onChange={e => setNewFollowUp({...newFollowUp, is_confidential:e.target.checked})} /> 🔒 Confidencial</label>
                  <button style={S.btnPrimary} onClick={handleAddFollowUp}>Guardar seguimiento</button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Modal Derivar ── */}
      {showDeriveModal && (
        <div style={S.modal}>
          <div style={{ ...S.modalBox, maxWidth:400 }}>
            <h3 style={{ marginTop:0 }}>↗ Derivar Caso</h3>
            <label style={S.formLabel}>Derivar a</label>
            <select style={S.input} value={deriveData.area} onChange={e => setDeriveData({...deriveData, area:e.target.value})}>
              <option value="DECE">DECE</option>
              <option value="MEDICAL">Dispensario Médico</option>
              <option value="EXTERNAL">Institución Externa</option>
            </select>
            <label style={{ ...S.formLabel, marginTop:12 }}>Motivo de derivación</label>
            <textarea style={{ ...S.input, minHeight:80 }} value={deriveData.reason} onChange={e => setDeriveData({...deriveData, reason:e.target.value})} />
            <div style={{ display:'flex', justifyContent:'flex-end', gap:10, marginTop:16 }}>
              <button style={S.btnSecondary} onClick={() => setShowDeriveModal(false)}>Cancelar</button>
              <button style={S.btnPrimary} onClick={handleDerive}>Derivar</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal Cerrar Caso ── */}
      {showCloseModal && (
        <div style={S.modal}>
          <div style={{ ...S.modalBox, maxWidth:400 }}>
            <h3 style={{ marginTop:0 }}>✓ Cerrar Caso</h3>
            <label style={S.formLabel}>Resumen de cierre</label>
            <textarea style={{ ...S.input, minHeight:100 }} placeholder="Describe el resultado y acciones tomadas..." value={closeData.summary} onChange={e => setCloseData({...closeData, summary:e.target.value})} />
            <div style={{ display:'flex', justifyContent:'flex-end', gap:10, marginTop:16 }}>
              <button style={S.btnSecondary} onClick={() => setShowCloseModal(false)}>Cancelar</button>
              <button style={{ ...S.btnPrimary, background:'#ef4444' }} onClick={handleClose}>Cerrar caso</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sub-componente ScoreBar ──────────────────────────────────────────────────
function ScoreBar({ value }) {
  const v = Math.round(value || 0);
  const color = v >= 70 ? '#22c55e' : v >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
      <div style={{ flex:1, height:6, background:'#f1f5f9', borderRadius:3, overflow:'hidden' }}>
        <div style={{ width:`${v}%`, height:'100%', background:color, borderRadius:3, transition:'width 0.4s' }} />
      </div>
      <span style={{ fontSize:'0.75rem', color:'#64748b', minWidth:28 }}>{v}%</span>
    </div>
  );
}

// ── Estilos ──────────────────────────────────────────────────────────────────
const S = {
  page:     { minHeight:'100vh', background:'#f8fafc', fontFamily:"'Inter',sans-serif", padding:'24px' },
  header:   { display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:24 },
  title:    { margin:0, fontSize:'1.8rem', fontWeight:800, color:'#1e293b' },
  subtitle: { margin:'4px 0 0', color:'#64748b', fontSize:'0.9rem' },
  yearSelect: { padding:'8px 14px', borderRadius:8, border:'2px solid #e2e8f0', fontSize:'0.9rem', background:'#fff', cursor:'pointer' },
  tabs:     { display:'flex', gap:4, marginBottom:24, background:'#fff', borderRadius:12, padding:4, border:'1px solid #e2e8f0', width:'fit-content' },
  tab:      { padding:'8px 20px', borderRadius:8, border:'none', background:'transparent', cursor:'pointer', fontWeight:600, color:'#64748b', fontSize:'0.9rem', transition:'all 0.2s' },
  tabActive:{ background:'#6366f1', color:'#fff' },
  content:  { position:'relative' },
  loadingBar: { height:3, background:'linear-gradient(90deg,#6366f1,#818cf8)', borderRadius:9, marginBottom:16, animation:'pulse 1.5s infinite' },
  dashGrid: { display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:16 },
  kpiCard:  { background:'#fff', borderRadius:12, padding:20, boxShadow:'0 1px 3px rgba(0,0,0,0.05)' },
  kpiIcon:  { fontSize:'1.5rem', marginBottom:8 },
  kpiValue: { fontSize:'2.2rem', fontWeight:800, lineHeight:1 },
  kpiLabel: { color:'#64748b', fontSize:'0.82rem', marginTop:6 },
  card:     { background:'#fff', borderRadius:12, padding:20, boxShadow:'0 1px 3px rgba(0,0,0,0.05)' },
  cardTitle:{ fontWeight:700, color:'#1e293b', marginBottom:12, fontSize:'0.95rem' },
  riskBar:  { display:'flex', height:32, borderRadius:8, overflow:'hidden', marginBottom:12 },
  riskSegment: { display:'flex', alignItems:'center', justifyContent:'center', transition:'flex 0.4s', minWidth:4 },
  riskSegmentLabel: { color:'#fff', fontWeight:700, fontSize:'0.85rem' },
  riskLegend: { display:'flex', gap:20 },
  legendItem: { display:'flex', alignItems:'center', gap:6, fontSize:'0.85rem', color:'#475569' },
  legendDot:  { width:10, height:10, borderRadius:'50%' },
  statRow:    { display:'flex', alignItems:'center', gap:10, marginBottom:8 },
  statBarWrap:{ flex:1, height:8, background:'#f1f5f9', borderRadius:4, overflow:'hidden' },
  statBarFill:{ height:'100%', borderRadius:4, transition:'width 0.4s' },
  statCount:  { minWidth:28, textAlign:'right', fontWeight:700, color:'#475569' },
  toolbar:  { display:'flex', gap:10, marginBottom:16, flexWrap:'wrap' },
  search:   { flex:1, minWidth:200, padding:'8px 14px', borderRadius:8, border:'2px solid #e2e8f0', fontSize:'0.9rem', outline:'none' },
  filter:   { padding:'8px 14px', borderRadius:8, border:'2px solid #e2e8f0', fontSize:'0.9rem', background:'#fff', cursor:'pointer' },
  tableWrap:{ background:'#fff', borderRadius:12, overflow:'hidden', boxShadow:'0 1px 3px rgba(0,0,0,0.05)' },
  table:    { width:'100%', borderCollapse:'collapse' },
  thead:    { background:'#f8fafc' },
  th:       { padding:'12px 16px', textAlign:'left', fontSize:'0.78rem', fontWeight:700, color:'#64748b', textTransform:'uppercase', letterSpacing:'0.05em', whiteSpace:'nowrap' },
  tr:       { borderBottom:'1px solid #f1f5f9', transition:'background 0.15s' },
  td:       { padding:'12px 16px', fontSize:'0.88rem', color:'#334155', verticalAlign:'middle' },
  empty:    { textAlign:'center', padding:'32px', color:'#94a3b8' },
  emptyState:{ background:'#fff', borderRadius:12, padding:40, textAlign:'center', color:'#94a3b8', fontSize:'0.95rem' },
  badge:    { padding:'3px 10px', borderRadius:999, fontSize:'0.78rem', fontWeight:600 },
  studentName: { fontWeight:600, color:'#1e293b' },
  caseTitle:{ fontWeight:700, color:'#1e293b', fontSize:'1rem' },
  btnPrimary:  { padding:'8px 20px', borderRadius:8, border:'none', background:'#6366f1', color:'#fff', fontWeight:700, cursor:'pointer', fontSize:'0.9rem' },
  btnSecondary:{ padding:'8px 20px', borderRadius:8, border:'2px solid #e2e8f0', background:'#fff', color:'#475569', fontWeight:600, cursor:'pointer', fontSize:'0.9rem' },
  btnDanger:   { padding:'6px 14px', borderRadius:8, border:'none', background:'#fef2f2', color:'#ef4444', fontWeight:600, cursor:'pointer', fontSize:'0.82rem' },
  btnSmall:    { padding:'6px 14px', borderRadius:8, border:'none', color:'#fff', fontWeight:600, cursor:'pointer', fontSize:'0.82rem' },
  btnXs:       { padding:'4px 12px', borderRadius:6, border:'2px solid #e2e8f0', background:'#fff', color:'#6366f1', fontWeight:600, cursor:'pointer', fontSize:'0.78rem' },
  modal:    { position:'fixed', inset:0, background:'rgba(0,0,0,0.5)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000, backdropFilter:'blur(4px)' },
  modalBox: { background:'#fff', borderRadius:16, padding:28, width:'min(95vw,600px)', boxShadow:'0 25px 60px rgba(0,0,0,0.25)' },
  closeBtn: { background:'#f1f5f9', border:'none', borderRadius:8, width:32, height:32, cursor:'pointer', fontSize:'1rem', display:'flex', alignItems:'center', justifyContent:'center' },
  followUpItem: { background:'#f8fafc', borderRadius:8, padding:'12px 14px', marginLeft:4 },
  newFollowUp:  { background:'#f8fafc', borderRadius:10, padding:16 },
  formGrid: { display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 },
  formLabel:{ fontSize:'0.8rem', fontWeight:600, color:'#475569', display:'block', marginBottom:4 },
  input:    { width:'100%', padding:'8px 12px', borderRadius:8, border:'2px solid #e2e8f0', fontSize:'0.9rem', outline:'none', boxSizing:'border-box', fontFamily:'inherit' },
  checkLabel: { display:'flex', alignItems:'center', gap:6, fontSize:'0.85rem', color:'#475569', cursor:'pointer' },
  ruleCard: { background:'#fff', borderRadius:12, padding:'16px 20px', marginBottom:10, boxShadow:'0 1px 3px rgba(0,0,0,0.05)' },
  ruleHeader: { display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 },
  ruleName: { fontWeight:700, color:'#1e293b' },
  ruleDetail: { color:'#64748b', fontSize:'0.85rem' },
  toast:    { position:'fixed', top:20, right:20, padding:'12px 20px', borderRadius:10, color:'#fff', fontWeight:600, zIndex:9999, fontSize:'0.9rem', boxShadow:'0 4px 20px rgba(0,0,0,0.2)' },
};
