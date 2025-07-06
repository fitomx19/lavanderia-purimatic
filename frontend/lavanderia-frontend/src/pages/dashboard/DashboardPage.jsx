import React from 'react';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token'); // Eliminar el token del localStorage
    navigate('/'); // Redirigir a la página de login
  };

  return (
    <div style={dashboardContainerStyle}>
      <h1>Bienvenido al Dashboard!</h1>
      <div style={cardsContainerStyle}>
        <div style={cardStyle} onClick={() => navigate('/users')}>
          <h2>Usuarios</h2>
          <p>Gestionar empleados y clientes</p>
        </div>
        <div style={cardStyle}>
          <h2>Equipo</h2>
          <p>Gestionar lavadoras y secadoras</p>
        </div>
        <div style={cardStyle}>
          <h2>Productos</h2>
          <p>Gestionar productos disponibles</p>
        </div>
        <div style={cardStyle}>
          <h2>Ventas</h2>
          <p>Ver historial de ventas</p>
        </div>
        <div style={cardStyle}>
          <h2>Clientes</h2>
          <p>Gestionar información de clientes</p>
        </div>
      </div>
      <button 
        onClick={handleLogout}
        style={logoutButtonStyle}
      >
        Cerrar Sesión
      </button>
    </div>
  );
};

const dashboardContainerStyle = {
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  minHeight: '100vh',
  backgroundColor: '#e0f7fa',
  fontSize: '1.2em',
  color: '#00796b',
  padding: '20px'
};

const cardsContainerStyle = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
  gap: '20px',
  marginTop: '40px',
  width: '80%',
  maxWidth: '1200px'
};

const cardStyle = {
  backgroundColor: '#ffffff',
  borderRadius: '10px',
  boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
  padding: '25px',
  textAlign: 'center',
  cursor: 'pointer',
  transition: 'transform 0.2s, box-shadow 0.2s',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'space-between',
  alignItems: 'center'
};

const logoutButtonStyle = {
  padding: '10px 20px',
  fontSize: '0.6em',
  marginTop: '40px',
  backgroundColor: '#d32f2f',
  color: 'white',
  border: 'none',
  borderRadius: '5px',
  cursor: 'pointer',
  transition: 'background-color 0.2s'
};

export default DashboardPage; 