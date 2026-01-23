import React, { useState } from 'react';
import { useAuthStore } from '../context/authStore';
import { useNavigate } from 'react-router-dom';
import { Lock, User, BookOpen } from 'lucide-react';

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
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="bg-primary p-8 text-center">
                    <div className="mx-auto bg-white/20 w-16 h-16 rounded-full flex items-center justify-center mb-4 backdrop-blur-sm">
                        <BookOpen className="w-8 h-8 text-white" />
                    </div>
                    <h2 className="text-3xl font-bold text-white mb-2">ERP Educativa</h2>
                    <p className="text-blue-100">Sistema de Gestión Institucional</p>
                </div>

                <div className="p-8">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Usuario</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <User className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary transition-colors"
                                    placeholder="Ingrese su usuario"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Contraseña</label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                    <Lock className="h-5 w-5 text-gray-400" />
                                </div>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-primary focus:border-primary transition-colors"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="text-red-500 text-sm text-center bg-red-50 p-2 rounded">
                                {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary transition-colors disabled:opacity-50"
                        >
                            {isLoading ? 'Iniciando sesión...' : 'Ingresar al Sistema'}
                        </button>
                    </form>
                </div>

                <div className="bg-gray-50 px-8 py-4 text-center text-xs text-gray-500">
                    &copy; 2026 ERP Educativa. Todos los derechos reservados.
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
