import React from 'react';
import { Hammer, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const ComingSoonPage = ({ title = "Módulo en Construcción" }) => {
    const navigate = useNavigate();

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 space-y-6">
            <div className="bg-indigo-100 p-6 rounded-full inline-block mb-4">
                <Hammer className="text-indigo-600" size={64} />
            </div>
            <h1 className="text-3xl font-bold text-slate-800">{title}</h1>
            <p className="text-slate-500 max-w-md">
                Estamos trabajando arduamente para traerte esta nueva funcionalidad pronto.
                Los próximos despliegues activarán este módulo.
            </p>
            <button
                onClick={() => navigate(-1)}
                className="btn-primary flex items-center justify-center gap-2 mt-4"
            >
                <ArrowLeft size={18} /> Volver a Atrás
            </button>
        </div>
    );
};

export default ComingSoonPage;
