import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  return (
    <div className="sidebar-container">
      <div className="sidebar-header">
        <h2>Menú</h2>
      </div>
      <ul className="sidebar-nav">
        <li>
          <button onClick={() => navigate('/dashboard')} className="sidebar-nav-button">
            Dashboard
          </button>
        </li>
        <li>
          <button onClick={() => navigate('/users')} className="sidebar-nav-button">
            Usuarios
          </button>
        </li>
        {/* Aquí puedes añadir más enlaces de navegación */}
      </ul>
      <div className="sidebar-footer">
        <button onClick={handleLogout} className="sidebar-logout-button">
          Cerrar Sesión
        </button>
      </div>
    </div>
  );
};

export default Sidebar; 