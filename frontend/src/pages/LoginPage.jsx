import React, { useState } from 'react';
import { useAuthStore } from '../context/authStore';
import { useNavigate } from 'react-router-dom';
import { Lock, User, BookOpen } from 'lucide-react';
import logoEduka360 from '../assets/logo-eduka360.jpg';

const LoginPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login, isLoading } = useAuthStore();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await login(username, password);
            navigate('/dashboard');
        } catch (error) {
            console.error("Fallo de inicio de sesión:", error);
            let msg = 'Credenciales inválidas. Intente nuevamente.';
            if (error.response) {
                // translate common messages if returned by backend as "detail"
                const detail = error.response.data?.detail || JSON.stringify(error.response.data);
                if (detail === "No active account found with the given credentials") {
                    msg = 'No se encontró una cuenta activa con estas credenciales.';
                } else if (detail.includes("No active account")) {
                    msg = 'No se encontró una cuenta activa.';
                } else {
                    msg = `Error (${error.response.status}): ${detail}`;
                }
            } else if (error.message) {
                msg = `Error: ${error.message}`;
            }
            setError(msg);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex font-sans selection:bg-rose-500/30 selection:text-white overflow-hidden">
            {/* Left Side: Impact Visual (Desktop Only) */}
            <div className="hidden lg:flex lg:w-3/5 relative overflow-hidden">
                <div 
                    className="absolute inset-0 bg-cover bg-center transition-transform duration-[10s] hover:scale-110" 
                    style={{ 
                        backgroundImage: 'url("https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&q=80&w=2070")',
                    }}
                />
                <div className="absolute inset-0 bg-gradient-to-r from-rose-950/90 via-rose-900/60 to-transparent" />
                
                <div className="relative z-10 flex flex-col justify-end p-20 w-full animate-fade-in">
                    <div className="flex items-center gap-4 mb-6">
                        <div className="w-16 h-16 bg-white rounded-3xl flex items-center justify-center shadow-2xl">
                            <BookOpen className="h-8 w-8 text-rose-600" />
                        </div>
                        <h1 className="text-5xl font-black text-white tracking-tighter">
                            Eduka<span className="text-rose-400">360</span>
                        </h1>
                    </div>
                    <p className="text-2xl text-rose-100/80 font-medium max-w-xl leading-relaxed italic">
                        "La tecnología al servicio de la educación para transformar el mañana."
                    </p>
                    <div className="mt-12 flex gap-8">
                        <div>
                            <p className="text-white text-3xl font-black">100%</p>
                            <p className="text-rose-200/60 text-xs font-bold uppercase tracking-widest">Digital</p>
                        </div>
                        <div>
                            <p className="text-white text-3xl font-black">AI</p>
                            <p className="text-rose-200/60 text-xs font-bold uppercase tracking-widest">Predictiva</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right Side: Login Form */}
            <div className="w-full lg:w-2/5 flex items-center justify-center p-8 bg-slate-900 lg:bg-transparent relative">
                {/* Mobile Background (Subtle) */}
                <div className="lg:hidden absolute inset-0 bg-[url('https://images.unsplash.com/photo-1524178232363-1fb2b075b655?q=80&w=1000')] bg-cover bg-center opacity-20" />
                
                <div className="w-full max-w-md relative z-10 animate-slide-up">
                    <div className="bg-white/10 lg:bg-white/5 backdrop-blur-3xl p-10 lg:p-14 rounded-[3.5rem] border border-white/10 shadow-2xl">
                        <div className="text-center mb-10">
                            <h2 className="text-4xl font-black text-white tracking-tighter mb-2">Iniciar Sesión</h2>
                            <p className="text-rose-400/80 text-xs font-black uppercase tracking-[0.2em]">Panel de Gestión Inteligente</p>
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <label className="block text-[10px] font-black text-rose-100/50 uppercase tracking-[0.2em] ml-2">Usuario Institucional</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-transform group-focus-within:scale-110">
                                        <User className="h-5 w-5 text-rose-400" />
                                    </div>
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="block w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-[1.5rem] text-white placeholder:text-white/20 focus:bg-white/10 focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition-all outline-none font-bold"
                                        placeholder="Ingrese su usuario"
                                        required
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-[10px] font-black text-rose-100/50 uppercase tracking-[0.2em] ml-2">Contraseña Segura</label>
                                <div className="relative group">
                                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-transform group-focus-within:scale-110">
                                        <Lock className="h-5 w-5 text-rose-400" />
                                    </div>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="block w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-[1.5rem] text-white placeholder:text-white/20 focus:bg-white/10 focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition-all outline-none font-bold"
                                        placeholder="••••••••"
                                        required
                                    />
                                </div>
                            </div>

                            {error && (
                                <div className="text-rose-200 text-xs font-bold text-center bg-rose-500/20 py-3 px-4 rounded-2xl border border-rose-500/30 animate-pulse">
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={isLoading}
                                className="w-full flex justify-center py-5 px-4 bg-rose-600 hover:bg-rose-500 text-white rounded-[1.5rem] shadow-2xl shadow-rose-900/40 font-black text-sm tracking-widest uppercase transition-all duration-300 disabled:opacity-50 transform hover:-translate-y-1 active:translate-y-0"
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2">
                                        <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Autenticando...
                                    </span>
                                ) : 'Ingresar al Ecosistema'}
                            </button>
                        </form>
                        
                        <div className="mt-10 text-center">
                            <p className="text-white/30 text-[10px] font-bold uppercase tracking-[0.3em]">
                                &copy; 2026 Eduka360 Technologies
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
