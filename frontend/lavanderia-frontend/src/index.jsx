import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/auth/LoginPage';
import DashboardPage from './pages/dashboard/DashboardPage'; // Lo crearemos en el siguiente paso
import UsersPage from './pages/Users/UsersPage'; // Importar UsersPage
import ClientsPage from './pages/clients/ClientsPage'; // Importar ClientsPage
import MachinePages from './pages/machines/MachinePages'; // Importar MachinePages
import ProductosPages from './pages/productos/ProductosPages'; // Importar ProductosPages
import ServicesPages from './pages/CycleServices/ServicesPages'; // Importar ServicesPages
import SalesPage from './pages/sales/SalesPages'; // Importar SalesPage
import TransactionsPage from './pages/transactions/TransactionsPage'; // Importar TransactionsPage
import Esp32ConfigPage from './pages/esp32/Esp32ConfigPage';
import './index.css'; // Importar los estilos globales

// Obtiene el usuario guardado en localStorage tras iniciar sesión (incluye el rol)
const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

// Ruta "home" según el rol del usuario, usada para redirigir cuando el acceso es denegado
const getHomeRouteForRole = (role) => {
  if (role === 'admin') return '/dashboard';
  if (role === 'empleado') return '/sales';
  return '/';
};

// Componente que protege una ruta: exige sesión iniciada y, opcionalmente, un rol permitido
const RequireRole = ({ allowedRoles, children }) => {
  const token = localStorage.getItem('token');
  const user = getStoredUser();

  // Sin token o sin datos de usuario válidos -> forzar login
  if (!token || !user) {
    return <Navigate to="/" replace />;
  }

  // Rol no autorizado para esta ruta -> redirigir a su página de inicio
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={getHomeRouteForRole(user.role)} replace />;
  }

  return children;
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />

        {/* Rutas exclusivas de administrador */}
        <Route
          path="/dashboard"
          element={
            <RequireRole allowedRoles={['admin']}>
              <DashboardPage />
            </RequireRole>
          }
        />
        <Route
          path="/users"
          element={
            <RequireRole allowedRoles={['admin']}>
              <UsersPage />
            </RequireRole>
          }
        />
        <Route
          path="/clients"
          element={
            <RequireRole allowedRoles={['admin']}>
              <ClientsPage />
            </RequireRole>
          }
        />
        <Route
          path="/machines"
          element={
            <RequireRole allowedRoles={['admin']}>
              <MachinePages />
            </RequireRole>
          }
        />
        <Route
          path="/esp32-config"
          element={
            <RequireRole allowedRoles={['admin']}>
              <Esp32ConfigPage />
            </RequireRole>
          }
        />
        <Route
          path="/productos"
          element={
            <RequireRole allowedRoles={['admin']}>
              <ProductosPages />
            </RequireRole>
          }
        />
        <Route
          path="/service-cycles"
          element={
            <RequireRole allowedRoles={['admin']}>
              <ServicesPages />
            </RequireRole>
          }
        />

        {/* Rutas compartidas: administrador y empleado (generar pedidos de venta + historial) */}
        <Route
          path="/sales"
          element={
            <RequireRole allowedRoles={['admin', 'empleado']}>
              <SalesPage />
            </RequireRole>
          }
        />
        <Route
          path="/transactions"
          element={
            <RequireRole allowedRoles={['admin', 'empleado']}>
              <TransactionsPage />
            </RequireRole>
          }
        />

        {/* Cualquier otra ruta desconocida redirige al login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
