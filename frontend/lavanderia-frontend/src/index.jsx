import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage'; // Lo crearemos en el siguiente paso
import UsersPage from './pages/Users/UsersPage'; // Importar UsersPage
import ClientsPage from './pages/clients/ClientsPage'; // Importar ClientsPage
import MachinePages from './pages/machines/MachinePages'; // Importar MachinePages
import './index.css'; // Importar los estilos globales

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/users" element={<UsersPage />} /> {/* Añadir la ruta para Usuarios */}
        <Route path="/clients" element={<ClientsPage />} /> {/* Añadir la ruta para Clientes */}
        <Route path="/machines" element={<MachinePages />} /> {/* Añadir la ruta para Máquinas */}
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
); 