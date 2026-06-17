console.log("MAIN.JSX EXECUTING (MINIMAL)");
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import './index.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
} else {
  console.error("Root element not found!");
}
