import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header';
import { getServiceCycles, createServiceCycle, deleteServiceCycle } from '../../services/cycleService';
import './ServicesPages.css';

const ServicesPages = () => {
  const [cycles, setCycles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    service_type: 'lavado', // Valor por defecto
    duration_minutes: '',
    price: '',
    machine_types_allowed: [],
    is_active: true,
  });

  useEffect(() => {
    fetchServiceCycles();
  }, [currentPage]);

  const fetchServiceCycles = async () => {
    try {
      setLoading(true);
      const response = await getServiceCycles(currentPage, 10);
      setCycles(response.data);
      setTotalPages(response.pagination.total_pages);
      setError(null);
    } catch (err) {
      setError(err.message || 'Error al cargar ciclos de servicio.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleMachineTypeChange = (e) => {
    const { value, checked } = e.target;
    setFormData((prevData) => {
      const newMachineTypes = checked
        ? [...prevData.machine_types_allowed, value]
        : prevData.machine_types_allowed.filter((type) => type !== value);
      return { ...prevData, machine_types_allowed: newMachineTypes };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createServiceCycle(formData);
      setShowForm(false);
      setFormData({
        name: '',
        description: '',
        service_type: 'lavado',
        duration_minutes: '',
        price: '',
        machine_types_allowed: [],
        is_active: true,
      });
      fetchServiceCycles();
    } catch (err) {
      setError(err.message || 'Error al guardar el ciclo de servicio.');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este ciclo de servicio?')) {
      try {
        await deleteServiceCycle(id);
        fetchServiceCycles();
      } catch (err) {
        setError(err.message || 'Error al eliminar el ciclo de servicio.');
      }
    }
  };

  const handlePageChange = (newPage) => {
    if (newPage > 0 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="services-page">
      <Header />
      <div className="services-container">
        <h1>Gestión de Ciclos de Servicio</h1>
        <button onClick={() => { setShowForm(true); setFormData({ name: '', description: '', service_type: 'lavado', duration_minutes: '', price: '', machine_types_allowed: [], is_active: true }); }} className="add-service-button">
          Agregar Nuevo Ciclo de Servicio
        </button>

        {showForm && (
          <div className="service-form-modal">
            <div className="service-form-content">
              <h2>Agregar Ciclo de Servicio</h2>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Nombre:</label>
                  <input type="text" name="name" value={formData.name} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Descripción:</label>
                  <input type="text" name="description" value={formData.description} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Tipo de Servicio:</label>
                  <select name="service_type" value={formData.service_type} onChange={handleInputChange} required>
                    <option value="lavado">Lavado</option>
                    <option value="secado">Secado</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Duración (minutos):</label>
                  <input type="number" name="duration_minutes" value={formData.duration_minutes} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Precio:</label>
                  <input type="number" name="price" value={formData.price} onChange={handleInputChange} step="0.01" required />
                </div>
                <div className="form-group">
                  <label>Tipos de Máquina Permitidos:</label>
                  <div>
                    <label>
                      <input type="checkbox" name="machine_types_allowed" value="chica" checked={formData.machine_types_allowed.includes('chica')} onChange={handleMachineTypeChange} /> Chica
                    </label>
                    <label>
                      <input type="checkbox" name="machine_types_allowed" value="grande" checked={formData.machine_types_allowed.includes('grande')} onChange={handleMachineTypeChange} /> Grande
                    </label>
                  </div>
                </div>
                <div className="form-group">
                  <label>
                    <input type="checkbox" name="is_active" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} /> Activo
                  </label>
                </div>
                <div className="form-actions">
                  <button type="submit">Crear</button>
                  <button type="button" onClick={() => setShowForm(false)}>Cancelar</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {loading && <p>Cargando ciclos de servicio...</p>}
        {error && <p className="error-message">{error}</p>}

        {!loading && !error && cycles.length === 0 && <p>No hay ciclos de servicio disponibles.</p>}

        {!loading && !error && cycles.length > 0 && (
          <div className="services-table-container">
            <table className="services-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Descripción</th>
                  <th>Tipo</th>
                  <th>Duración (min)</th>
                  <th>Precio</th>
                  <th>Tipos de Máquina</th>
                  <th>Activo</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {cycles.map((cycle) => (
                  <tr key={cycle._id}>
                    <td>{cycle.name}</td>
                    <td>{cycle.description}</td>
                    <td>{cycle.service_type}</td>
                    <td>{cycle.duration_minutes}</td>
                    <td>${parseFloat(cycle.price).toFixed(2)}</td>
                    <td>{cycle.machine_types_allowed.join(', ')}</td>
                    <td>{cycle.is_active ? 'Sí' : 'No'}</td>
                    <td>
                      {/* <button onClick={() => handleEdit(cycle)} className="edit-button">Editar</button> */}
                      <button onClick={() => handleDelete(cycle._id)} className="delete-button">Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pagination-controls">
              <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>
                Anterior
              </button>
              <span>Página {currentPage} de {totalPages}</span>
              <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ServicesPages;
