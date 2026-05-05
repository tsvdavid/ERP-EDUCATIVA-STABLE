import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useAuthStore } from './authStore';

const SocketContext = createContext();

export const useSocket = () => {
    const context = useContext(SocketContext);
    return context || { lastMessage: null };
};

export const SocketProvider = ({ children }) => {
    const isAuthenticated = useAuthStore(state => state.isAuthenticated);
    const [lastMessage, setLastMessage] = useState(null);
    const socketRef = useRef(null);

    useEffect(() => {
        let socket = null;

        if (isAuthenticated) {
            const token = localStorage.getItem('access_token');
            
            if (token) {
                // Connect to WebSocket with token in query string
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
                const wsBase = apiUrl.replace(/^http/, 'ws').replace(/\/api\/?$/, '');
                const wsUrl = `${wsBase}/ws/notifications/?token=${token}`;
                
                try {
                    socket = new WebSocket(wsUrl);

                    socket.onopen = () => {
                        console.log('WebSocket Connected');
                    };

                    socket.onmessage = (event) => {
                        try {
                            const data = JSON.parse(event.data);
                            console.log('WS Message:', data);
                            setLastMessage(data);
                        } catch (e) {
                            console.error('WS JSON Parse Error:', e);
                        }
                    };

                    socket.onclose = () => {
                        console.log('WebSocket Disconnected');
                    };

                    socket.onerror = (err) => {
                        console.error('WebSocket Error:', err);
                    };

                    socketRef.current = socket;
                } catch (err) {
                    console.error('WebSocket Connection Error:', err);
                }
            }
        }

        return () => {
            if (socket) {
                socket.close();
            }
        };
    }, [isAuthenticated]);

    return (
        <SocketContext.Provider value={{ lastMessage }}>
            {children}
        </SocketContext.Provider>
    );
};
