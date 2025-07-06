import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage'; // Lo crearemos en el siguiente paso
import UsersPage from './pages/Users/UsersPage'; // Importar UsersPage

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/users" element={<UsersPage />} /> {/* Añadir la ruta para Usuarios */}
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
); 