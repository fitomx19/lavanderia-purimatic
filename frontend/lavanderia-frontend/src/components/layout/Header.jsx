import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.css'; // Crearemos este archivo después

const Header = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <header className="app-header">
      <h1 className="app-title">Lavandería Purimatic</h1>
      <div>
        <button onClick={() => navigate('/dashboard')} className="dashboard-button">
          Ir al Dashboard
        </button>
        <button onClick={handleLogout} className="header-logout-button">
          Cerrar Sesión
        </button>
      </div>
    </header>
  );
};

export default Header;
