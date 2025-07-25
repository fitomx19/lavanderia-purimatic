import React from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../../components/layout/Sidebar'; // Importar Sidebar
import { deactivateMachines } from '../../services/salesService'; // Importar la función para desactivar máquinas
import './DashboardPage.css'; // Importar el archivo CSS para el dashboard

const DashboardPage = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token'); // Eliminar el token del localStorage
    navigate('/'); // Redirigir a la página de login
  };

  const handleDeactivateMachinesClick = async () => {
    try {
      const response = await deactivateMachines();
      alert(response.message);
    } catch (error) {
      alert(`Error al reactivar máquinas: ${error.response ? error.response.data.message : error.message}`);
    }
  };

  return (
    <div className="dashboard-layout">
      <Sidebar />
      <div className="dashboard-content">
        <h1>Bienvenido al Dashboard!</h1>
        <div className="cards-container">
          <div className="dashboard-card" onClick={() => navigate('/users')}>
            <h2>Usuarios</h2>
            <p>Gestionar empleados </p>
          </div>
          <div className="dashboard-card" onClick={() => navigate('/machines')}>
            <h2>Equipo</h2>
            <p>Gestionar lavadoras y secadoras</p>
          </div>
          <div className="dashboard-card" onClick={() => navigate('/productos')}>
            <h2>Productos</h2>
            <p>Gestionar productos disponibles</p>
          </div>
          <div className="dashboard-card" onClick={() => navigate('/sales')}>
            <h2>Ventas</h2>
            <p>Ver historial de ventas</p>
          </div>
          <div className="dashboard-card" onClick={() => navigate('/service-cycles')}>
            <h2>Ciclos de servicio</h2>
            <p>Gestionar ciclos de servicio</p>
          </div>
          <div className="dashboard-card" onClick={() => navigate('/clients')}>
            <h2>Clientes</h2>
            <p>Gestionar información de clientes</p>
          </div>
          <div className="dashboard-card" onClick={handleDeactivateMachinesClick}>
            <h2>Reactivar Máquinas</h2>
            <p>Liberar máquinas con ciclos finalizados</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage; 