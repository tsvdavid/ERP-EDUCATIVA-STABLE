import React from 'react';
import { ShieldAlert, CreditCard, LogOut, MessageSquare, Landmark } from 'lucide-react';

const SubscriptionSuspended = () => {
    const institutionName = localStorage.getItem('institution_name') || 'Su Institución';

    const handleLogout = () => {
        localStorage.clear();
        window.location.replace('/login');
    };

    const goToBilling = () => {
        window.location.replace('/dashboard/settings/billing');
    };

    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
            <div className="max-w-xl w-full bg-white rounded-[3rem] shadow-2xl shadow-slate-200/50 overflow-hidden border border-slate-100">
                {/* Header Decoration */}
                <div className="h-2 bg-rose-500 w-full"></div>
                
                <div className="p-12 text-center space-y-8">
                    <div className="flex justify-center">
                        <div className="w-24 h-24 bg-rose-50 rounded-3xl flex items-center justify-center text-rose-500">
                            <ShieldAlert size={48} strokeWidth={2.5} className="animate-pulse" />
                        </div>
                    </div>

                    <div className="space-y-3">
                        <h1 className="text-3xl font-black text-slate-800 tracking-tight">Acceso Restringido</h1>
                        <div className="flex items-center justify-center gap-2 text-rose-600 font-bold bg-rose-50 py-2 px-4 rounded-full w-fit mx-auto text-sm">
                            <Landmark size={16} />
                            ESTADO: SUSPENDIDO
                        </div>
                    </div>

                    <div className="space-y-4">
                        <p className="text-slate-600 text-lg leading-relaxed">
                            La cuenta de <span className="font-black text-slate-800">{institutionName}</span> ha sido suspendida temporalmente por falta de pago o vencimiento de contrato.
                        </p>
                        <div className="p-6 bg-slate-50 rounded-[2rem] text-sm text-slate-500 font-medium border border-slate-100 text-left">
                            Para restablecer el acceso a sus módulos de Contabilidad, Académico y Tesorería, por favor registre un nuevo pago en el panel de facturación o contacte a nuestro equipo comercial.
                        </div>
                    </div>

                    <div className="grid grid-cols-1 gap-4 pt-4">
                        <button 
                            onClick={goToBilling}
                            className="flex items-center justify-center gap-3 bg-indigo-600 hover:bg-indigo-700 text-white py-5 rounded-[1.5rem] font-black shadow-xl shadow-indigo-100 transition-all active:scale-95"
                        >
                            <CreditCard size={20} />
                            Ir a Mi Facturación
                        </button>
                        
                        <div className="grid grid-cols-2 gap-4">
                            <button 
                                onClick={() => window.open('https://wa.me/593999999999', '_blank')}
                                className="flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-600 py-4 rounded-[1.5rem] font-bold transition-all"
                            >
                                <MessageSquare size={18} />
                                Soporte
                            </button>
                            <button 
                                onClick={handleLogout}
                                className="flex items-center justify-center gap-2 bg-slate-50 hover:bg-rose-50 text-slate-400 hover:text-rose-600 py-4 rounded-[1.5rem] font-bold transition-all border border-transparent hover:border-rose-100"
                            >
                                <LogOut size={18} />
                                Salir
                            </button>
                        </div>
                    </div>

                    <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest pt-4">
                        Eduka360 SaaS Engine v2.0
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SubscriptionSuspended;
