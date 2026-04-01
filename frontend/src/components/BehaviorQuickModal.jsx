import React, { useState, useEffect } from 'react';
import healthService from '../services/healthService';
import academicService from '../services/academicService';

// Main UI categories (simplified)
const UI_TYPES = [
  { value: 'POSITIVE', label: '👍 Positiva', color: '#22c55e' },
  { value: 'NEGATIVE', label: '⚠️ Negativa', color: '#f59e0b' },
  { value: 'ACADEMIC', label: '📝 Académica', color: '#3b82f6' },
];

const SUGGESTIONS = {
  POSITIVE: ['Participa activamente', 'Buen comportamiento', 'Ayuda a compañeros', 'Excelente presentación'],
  NEGATIVE: ['Interrumpe la clase', 'Pelea / agresión', 'Acoso escolar', 'Llegada tardía', 'Uso de celular', 'Indisciplina', 'Falta de respeto'],
  ACADEMIC: ['Entrega tareas con éxito', 'No entrega tareas', 'Bajo rendimiento', 'No trabaja en clase', 'No trae material'],
};

export default function BehaviorQuickModal({ existingRecord, allowedTypes = ['POSITIVE', 'NEGATIVE', 'ACADEMIC'], student, studentId, studentName, academicYear, courseId, subjectId, onClose, onSaved }) {
  // Construct a fallback student if the full object isn't passed
  const activeStudent = student || { 
    id: studentId, 
    first_name: studentName ? studentName.split(' ')[0] : 'Estudiante', 
    last_name: studentName && studentName.split(' ').length > 1 ? studentName.split(' ').slice(1).join(' ') : '' 
  };

  const [activeYear, setActiveYear] = useState(academicYear);
  const [uiType, setUiType] = useState(allowedTypes[0] || 'POSITIVE');
  const [severity, setSeverity] = useState('NEGATIVE_MILD'); // Solo usado si uiType === 'NEGATIVE'
  
  const [newText, setNewText] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    if (!activeYear) {
      academicService.getAcademicYears()
        .then(years => {
          const current = years.find(y => y.is_active);
          if (current) setActiveYear(current.id);
        })
        .catch(e => console.error(e));
    }
  }, [activeYear]);

  // Handle suggestion click
  const handleSuggestionClick = (text) => {
    if (newText) {
      setNewText(newText + ' - ' + text);
    } else {
      setNewText(text);
    }
  };

  const handleSave = async () => {
    if (!newText.trim()) {
      setAlert("Escribe un detalle de lo sucedido.");
      return;
    }

    setLoading(true);
    try {
      // Determine final backend record_type
      let finalRecordType = uiType;
      if (uiType === 'NEGATIVE') {
        finalRecordType = severity;
      }

      // Append mode logic
      let finalDescription = newText.trim();
      if (existingRecord) {
         const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
         finalDescription = `${existingRecord.description}

[${timestamp}]: ${finalDescription}`;
         finalRecordType = existingRecord.record_type; // Maintain original base type when appending, per preference, though this could be overridden if the backend requires it.
      }

      const payload = {
        student: activeStudent.id,
        academic_year: activeYear,
        record_type: finalRecordType,
        template: 'OTHER', // Make everything dynamic using the OTHER template
        description: finalDescription,
        ...(courseId && { course: courseId }),
        ...(subjectId && { subject: subjectId }),
      };

      let result;
      if (existingRecord) {
         result = await healthService.updateBehaviorRecord(existingRecord.id, payload);
      } else {
         result = await healthService.quickCreateBehavior(payload);
      }
      
      if (result.alert_triggered) {
        setAlert(`⚠️ Alerta generada: se creó un caso automático (${result.cases_created} caso${result.cases_created > 1 ? 's' : ''}).`);
        setTimeout(() => { onSaved && onSaved(result); onClose(); }, 2500);
      } else {
        onSaved && onSaved(result);
        onClose();
      }
    } catch (e) {
      setAlert('Error Backend: ' + JSON.stringify(e.response?.data || e.message));
    } finally {
      setLoading(false);
    }
  };

  const selectedColor = existingRecord ? '#475569' : (UI_TYPES.find(t => t.value === uiType)?.color || '#22c55e');
  const currentSuggestions = SUGGESTIONS[uiType] || [];

  return (
    <div style={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={styles.modal}>
        {/* Header */}
        <div style={{ ...styles.header, background: selectedColor }}>
          <span style={styles.headerTitle}>{existingRecord ? '⚡ Añadir al Registro de Conducta' : '⚡ Registro Rápido de Conducta'}</span>
          <button style={styles.closeBtn} onClick={onClose}>✕</button>
        </div>

        <div style={styles.body}>
          {/* Estudiante Badge */}
          <div style={styles.studentBadge}>
            <span style={styles.studentAvatar}>
              {activeStudent.first_name?.[0]}{activeStudent.last_name?.[0]}
            </span>
            <div>
              <div style={styles.studentName}>{activeStudent.first_name} {activeStudent.last_name}</div>
              {activeStudent.course_name && <div style={styles.studentCourse}>{activeStudent.course_name}</div>}
            </div>
          </div>

          {existingRecord && (
             <div style={{background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0'}}>
                <span style={{fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase'}}>Historial de hoy</span>
                <p style={{fontSize: '0.85rem', color: '#334155', marginTop: '4px', whiteSpace: 'pre-wrap'}}>{existingRecord.description}</p>
             </div>
          )}

          {!existingRecord && (
             <>
                {/* Categoría General */}
                <label style={styles.label}>Categoría Inicial</label>
                <div style={styles.typeRow}>
                    {UI_TYPES.filter(t => allowedTypes.includes(t.value)).map(t => (
                    <button
                        key={t.value}
                        style={{ ...styles.typeBtn, ...(uiType === t.value ? { background: t.color, color: '#fff', borderColor: t.color } : {}) }}
                        onClick={() => { setUiType(t.value); setAlert(null); }}
                    >
                        {t.label}
                    </button>
                    ))}
                </div>

                {/* Sub-Categoría (Leve / Grave) */}
                {uiType === 'NEGATIVE' && (
                    <div style={{marginTop: '-2px', display: 'flex', gap: '16px', paddingLeft: '4px', background: '#fffbeb', padding: '10px', borderRadius: '8px', border: '1px solid #fef3c7'}}>
                    <label style={{...styles.label, display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', textTransform: 'none', margin: 0, fontWeight: 700}}>
                        <input 
                        type="radio" 
                        name="severity" 
                        value="NEGATIVE_MILD"
                        checked={severity === 'NEGATIVE_MILD'} 
                        onChange={() => setSeverity('NEGATIVE_MILD')} 
                        />
                        Falta Leve
                    </label>
                    <label style={{...styles.label, display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', textTransform: 'none', color: '#dc2626', margin: 0, fontWeight: 700}}>
                        <input 
                        type="radio" 
                        name="severity" 
                        value="NEGATIVE_SEVERE"
                        checked={severity === 'NEGATIVE_SEVERE'} 
                        onChange={() => setSeverity('NEGATIVE_SEVERE')} 
                        />
                        Falta Grave (Reporte D.E.C.E)
                    </label>
                    </div>
                )}
             </>
          )}

          {/* Dinámico: Descripción & Sugerencias */}
          <label style={{...styles.label, marginTop: '8px'}}>Detalle a Añadir</label>
          <div style={styles.suggestionsRow}>
            {currentSuggestions.map(s => (
              <button 
                key={s} 
                style={styles.suggestionBadge} 
                onClick={() => handleSuggestionClick(s)}
              >
                + {s}
              </button>
            ))}
          </div>
          <textarea
            style={styles.textarea}
            placeholder={existingRecord ? "Añade una nueva observación aquí..." : "Haz clic en las sugerencias de arriba o escribe..."}
            value={newText}
            onChange={e => setNewText(e.target.value)}
            rows={4}
          />

          {/* Alerta Visual */}
          {alert && (
            <div style={{ ...styles.alertBox, background: alert.startsWith('⚠️') ? '#fff7ed' : '#fef2f2', borderColor: alert.startsWith('⚠️') ? '#f59e0b' : '#ef4444' }}>
              {alert}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          <button style={styles.cancelBtn} onClick={onClose}>Cancelar</button>
          <button
            style={{ ...styles.saveBtn, background: selectedColor, opacity: (loading || !newText.trim()) ? 0.6 : 1 }}
            onClick={handleSave}
            disabled={loading || !newText.trim()}
          >
            {loading ? 'Guardando...' : existingRecord ? '💾 Actualizar Registro' : '💾 Registrar Conducta'}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  overlay:  { position:'fixed', inset:0, background:'rgba(0,0,0,0.55)', display:'flex', alignItems:'center', justifyContent:'center', zIndex:9999, backdropFilter:'blur(4px)' },
  modal:    { background:'#fff', borderRadius:'16px', width:'min(96vw,520px)', boxShadow:'0 25px 60px rgba(0,0,0,0.3)', overflow:'hidden', display:'flex', flexDirection:'column' },
  header:   { display:'flex', alignItems:'center', justifyContent:'space-between', padding:'16px 20px', transition:'background 0.3s' },
  headerTitle: { color:'#fff', fontWeight:700, fontSize:'1rem' },
  closeBtn: { background:'rgba(255,255,255,0.25)', border:'none', borderRadius:'8px', color:'#fff', width:28, height:28, cursor:'pointer', fontSize:'0.9rem', display:'flex', alignItems:'center', justifyContent:'center' },
  body:     { padding:'20px', display:'flex', flexDirection:'column', gap:'12px', maxHeight:'80vh', overflowY:'auto' },
  studentBadge: { display:'flex', alignItems:'center', gap:'12px', background:'#f8fafc', borderRadius:'10px', padding:'10px 14px' },
  studentAvatar: { width:36, height:36, borderRadius:'50%', background:'#6366f1', color:'#fff', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:700, fontSize:'0.85rem' },
  studentName: { fontWeight:600, fontSize:'0.95rem', color:'#1e293b' },
  studentCourse: { fontSize:'0.78rem', color:'#64748b' },
  label:    { fontSize:'0.8rem', fontWeight:600, color:'#475569', textTransform:'uppercase', letterSpacing:'0.05em' },
  typeRow:  { display:'flex', gap:'8px', flexWrap:'wrap' },
  typeBtn:  { padding:'8px 16px', borderRadius:'999px', border:'2px solid #e2e8f0', background:'#fff', cursor:'pointer', fontSize:'0.85rem', fontWeight:700, color:'#475569', transition:'all 0.2s' },
  suggestionsRow: { display:'flex', flexWrap:'wrap', gap:'6px', marginBottom:'4px' },
  suggestionBadge: { padding:'6px 10px', borderRadius:'6px', border:'1px solid #cbd5e1', background:'#f0f9ff', fontSize:'0.75rem', color:'#0369a1', cursor:'pointer', transition:'background 0.2s', fontWeight: 600 },
  textarea: { width:'100%', padding:'12px', borderRadius:'10px', border:'2px solid #e2e8f0', fontSize:'0.9rem', resize:'vertical', outline:'none', boxSizing:'border-box', fontFamily:'inherit', backgroundColor: '#fcfcfc' },
  alertBox: { padding:'10px 14px', borderRadius:'8px', border:'2px solid', fontSize:'0.85rem', color:'#1e293b', fontWeight:600 },
  footer:   { padding:'16px 20px', borderTop:'1px solid #f1f5f9', display:'flex', justifyContent:'flex-end', gap:'10px', background:'#fafafa' },
  cancelBtn:{ padding:'10px 20px', borderRadius:'8px', border:'2px solid #e2e8f0', background:'#fff', cursor:'pointer', fontWeight:600, color:'#64748b' },
  saveBtn:  { padding:'10px 24px', borderRadius:'8px', border:'none', color:'#fff', cursor:'pointer', fontWeight:700, fontSize:'0.95rem', transition:'opacity 0.2s' },
};
