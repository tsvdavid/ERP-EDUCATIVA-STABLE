import React from 'react';
import { Calendar as CalendarIcon, Clock, ChevronLeft, ChevronRight } from 'lucide-react';

const AttendanceCalendar = () => {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-700">
      <header>
        <h1 className="text-4xl font-black text-slate-900 tracking-tight">Calendario de Asistencias</h1>
        <p className="text-slate-500 mt-2 font-medium">Control visual de puntualidad, ausencias y permisos.</p>
      </header>

      <div className="bg-white rounded-3xl shadow-sm border border-slate-100 overflow-hidden min-h-[600px] flex flex-col">
        <div className="p-6 border-b border-slate-50 flex justify-between items-center bg-slate-50/50">
          <div className="flex items-center gap-4">
            <h2 className="font-black text-xl text-slate-800">Abril 2026</h2>
            <div className="flex gap-1">
              <button className="p-2 hover:bg-slate-200 rounded-lg transition-colors"><ChevronLeft size={20} /></button>
              <button className="p-2 hover:bg-slate-200 rounded-lg transition-colors"><ChevronRight size={20} /></button>
            </div>
          </div>
          <div className="flex gap-4">
            <LegendItem color="bg-emerald-500" label="Puntual" />
            <LegendItem color="bg-amber-500" label="Atraso" />
            <LegendItem color="bg-rose-500" label="Falta" />
            <LegendItem color="bg-indigo-500" label="Permiso" />
          </div>
        </div>
        
        <div className="flex-1 grid grid-cols-7 grid-rows-5 border-l border-t border-slate-50">
          {/* Calendar Header */}
          {['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'].map(day => (
            <div key={day} className="p-4 text-center text-xs font-black text-slate-400 uppercase tracking-widest border-r border-b border-slate-50 bg-slate-50/30">
              {day}
            </div>
          ))}
          
          {/* Calendar Cells (Static for Demo) */}
          {Array.from({ length: 35 }).map((_, i) => {
            const day = i - 2; // Offset for April 2026 starting on Wednesday
            const isCurrentMonth = day > 0 && day <= 30;
            return (
              <div key={i} className={`p-4 border-r border-b border-slate-50 min-h-[120px] transition-colors hover:bg-slate-50/50 ${!isCurrentMonth ? 'bg-slate-50/20' : ''}`}>
                {isCurrentMonth && (
                  <>
                    <span className="font-bold text-slate-400">{day}</span>
                    {day === 15 && <AttendanceMarker color="bg-amber-500" time="08:15" label="Atraso" />}
                    {day < 15 && day > 0 && <AttendanceMarker color="bg-emerald-500" time="07:55" label="Puntual" />}
                  </>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const LegendItem = ({ color, label }) => (
  <div className="flex items-center gap-2 text-xs font-bold text-slate-500">
    <div className={`w-3 h-3 rounded-full ${color}`}></div>
    {label}
  </div>
);

const AttendanceMarker = ({ color, time, label }) => (
  <div className={`mt-2 p-2 rounded-xl ${color} bg-opacity-10 border border-current border-opacity-20 flex flex-col gap-1`}>
    <span className={`text-[10px] font-black uppercase ${color.replace('bg-', 'text-')}`}>{label}</span>
    <div className="flex items-center gap-1 text-[10px] font-bold text-slate-600">
      <Clock size={10} /> {time}
    </div>
  </div>
);

export default AttendanceCalendar;
