import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.css'; // Crearemos este archivo después

const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = getStoredUser();
  const isAdmin = user?.role === 'admin';

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
  };

  return (
    <header className="app-header">
      <h1 className="app-title">Lavandería Purimatic</h1>
      <div>
        {isAdmin && (
          <button onClick={() => navigate('/dashboard')} className="dashboard-button">
            Ir al Dashboard
          </button>
        )}
        {isAdmin && location.pathname !== '/esp32-config' && (
          <button onClick={() => navigate('/esp32-config')} className="dashboard-button">
            Placas ESP32
          </button>
        )}
        {location.pathname !== '/sales' && (
          <button onClick={() => navigate('/sales')} className="dashboard-button">
            Ventas
          </button>
        )}
        {location.pathname !== '/transactions' && (
          <button onClick={() => navigate('/transactions')} className="dashboard-button">
            Historial
          </button>
        )}
        <button onClick={handleLogout} className="header-logout-button">
          Cerrar Sesión
        </button>
      </div>
    </header>
  );
};

export default Header;
