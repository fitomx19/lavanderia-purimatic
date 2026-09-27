import React from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../../components/layout/Header';
import { deactivateMachines } from '../../services/salesService';
import './DashboardPage.css';

const DashboardPage = () => {
  const navigate = useNavigate();

  const handleDeactivateMachinesClick = async () => {
    try {
      const response = await deactivateMachines();
      alert(response.message);
    } catch (error) {
      alert(`Error al reactivar máquinas: ${error.response ? error.response.data.message : error.message}`);
    }
  };

  return (
    <div className="dashboard-page">
      <Header />
      <main className="dashboard-content">
        <header className="dashboard-intro">
          <h1>Panel de administración</h1>
          <p>Accede a ventas y gestiona el resto de módulos desde aquí.</p>
        </header>

        <section className="dashboard-hero" aria-label="Aplicación de ventas">
          <button
            type="button"
            className="dashboard-hero-card"
            onClick={() => navigate('/sales')}
          >
            <span className="dashboard-hero-label">Módulo principal</span>
            <h2>Aplicación Ventas</h2>
            <p>Abrir la app de ventas para cobrar, activar máquinas y atender pedidos.</p>
            <span className="dashboard-hero-cta">Ir a Ventas</span>
          </button>
        </section>

        <section className="dashboard-section" aria-label="Operación rápida">
          <h3 className="dashboard-section-title">Operación rápida</h3>
          <div className="dashboard-grid dashboard-grid--ops">
            <button
              type="button"
              className="dashboard-card dashboard-card--compact"
              onClick={() => navigate('/transactions')}
            >
              <h4>Transacciones</h4>
              <p>Historial de tarjetas</p>
            </button>
            <button
              type="button"
              className="dashboard-card dashboard-card--compact"
              onClick={() => navigate('/encargos')}
            >
              <h4>Encargos</h4>
              <p>Kilos, servicios y estatus</p>
            </button>
          </div>
        </section>

        <section className="dashboard-section" aria-label="Gestión">
          <h3 className="dashboard-section-title">Gestión</h3>
          <div className="dashboard-grid dashboard-grid--gestion">
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/users')}>
              <h4>Usuarios</h4>
              <p>Empleados</p>
            </button>
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/machines')}>
              <h4>Equipo</h4>
              <p>Lavadoras y secadoras</p>
            </button>
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/productos')}>
              <h4>Productos</h4>
              <p>Catálogo</p>
            </button>
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/service-cycles')}>
              <h4>Ciclos</h4>
              <p>Servicios</p>
            </button>
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/clients')}>
              <h4>Clientes</h4>
              <p>Información</p>
            </button>
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/encargos-precios')}>
              <h4>Precios encargos</h4>
              <p>Kg, servicios y etiqueta</p>
            </button>
          </div>
        </section>

        <section className="dashboard-section" aria-label="Técnico">
          <h3 className="dashboard-section-title">Técnico</h3>
          <div className="dashboard-grid dashboard-grid--tecnico">
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/esp32-config')}>
              <h4>Placas ESP32</h4>
              <p>IPs, WiFi y pruebas</p>
            </button>
            <button type="button" className="dashboard-card dashboard-card--compact" onClick={() => navigate('/ticket-settings')}>
              <h4>Ticket 80mm</h4>
              <p>Logo, WiFi e impresora</p>
            </button>
            <button
              type="button"
              className="dashboard-card dashboard-card--compact dashboard-card--action"
              onClick={handleDeactivateMachinesClick}
            >
              <h4>Reactivar máquinas</h4>
              <p>Liberar ciclos finalizados</p>
            </button>
          </div>
        </section>
      </main>
    </div>
  );
};

export default DashboardPage;
