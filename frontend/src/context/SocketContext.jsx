import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useAuthStore } from './authStore';

const SocketContext = createContext();

export const useSocket = () => {
    return useContext(SocketContext);
};

export const SocketProvider = ({ children }) => {
    const { isAuthenticated, token } = useAuthStore();
    const [lastMessage, setLastMessage] = useState(null);
    const socketRef = useRef(null);

    useEffect(() => {
        if (isAuthenticated && token) {
            // Connect to WebSocket with token in query string
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
            const wsBase = apiUrl.replace(/^http/, 'ws').replace(/\/api\/?$/, '');
            const wsUrl = `${wsBase}/ws/notifications/?token=${token}`;
            const socket = new WebSocket(wsUrl);

            socket.onopen = () => {
                console.log('WebSocket Connected');
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('WS Message:', data);
                setLastMessage(data);
            };

            socket.onclose = () => {
                console.log('WebSocket Disconnected');
            };

            socketRef.current = socket;

            return () => {
                socket.close();
            };
        }
    }, [isAuthenticated, token]);

    return (
        <SocketContext.Provider value={{ lastMessage }}>
            {children}
        </SocketContext.Provider>
    );
};
