import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header';
import { getServiceCycles, createServiceCycle, deleteServiceCycle } from '../../services/cycleService';
import { getAllActiveWashers, getAllActiveDryers } from '../../services/machineService';
import { ToastContainer, toast } from 'react-toastify'; // Importar ToastContainer y toast
import 'react-toastify/dist/ReactToastify.css'; // Importar el CSS de react-toastify
import './ServicesPages.css';

const ServicesPages = () => {
  const [cycles, setCycles] = useState([]);
  const [washers, setWashers] = useState([]);
  const [dryers, setDryers] = useState([]);
  const [filteredWashers, setFilteredWashers] = useState([]); // Nuevo estado para lavadoras filtradas
  const [filteredDryers, setFilteredDryers] = useState([]); // Nuevo estado para secadoras filtradas
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [currentStep, setCurrentStep] = useState(1); // Nuevo estado para controlar los pasos
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    service_type: 'lavado', // Valor por defecto
    duration_minutes: '',
    price: '',
    allowed_machines: [],
    is_active: true,
  });

  // Efecto para cargar datos iniciales: ciclos, lavadoras y secadoras
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const cyclesResponse = await getServiceCycles(currentPage, 10);
        setCycles(cyclesResponse.data);
        setTotalPages(cyclesResponse.pagination.total_pages);

        const allWashersResponse = await getAllActiveWashers();
        setWashers(allWashersResponse.data);
        
        const allDryersResponse = await getAllActiveDryers();
        setDryers(allDryersResponse.data);

        setError(null);
      } catch (err) {
        setError(err.message || 'Error al cargar datos.');
        toast.error('Error al cargar los ciclos de servicio: ' + (err.message || 'Error desconocido'));
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [currentPage]);

  // Efecto para filtrar máquinas según el tipo de servicio seleccionado
  useEffect(() => {
    const currentServiceType = formData.service_type;
    let tempFilteredWashers = [];
    let tempFilteredDryers = [];

    if (currentServiceType === 'lavado' || currentServiceType === 'encargo_lavado') {
      tempFilteredWashers = washers;
    } else if (currentServiceType === 'secado' || currentServiceType === 'encargo_secado') {
      tempFilteredDryers = dryers;
    } else if (currentServiceType === 'combo' || currentServiceType === 'mixto' || currentServiceType === 'mixto_encargo') {
      tempFilteredWashers = washers;
      tempFilteredDryers = dryers;
    }

    setFilteredWashers(tempFilteredWashers);
    setFilteredDryers(tempFilteredDryers);

    // Limpiar allowed_machines si el tipo de servicio cambia para evitar incompatibilidades
    setFormData(prevData => ({ ...prevData, allowed_machines: [] }));

  }, [formData.service_type, washers, dryers]); // Dependencias para re-filtrar cuando cambian

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleMachineSelectionChange = (e) => {
    const { value, checked } = e.target; 
    const [machineId, machineNumber] = value.split('-'); 

    setFormData((prevData) => {
      const newAllowedMachines = checked
        ? [...prevData.allowed_machines, { _id: machineId, name: machineNumber }]
        : prevData.allowed_machines.filter((machine) => machine._id !== machineId);
      return { ...prevData, allowed_machines: newAllowedMachines };
    });
  };

  const handleNextStep = () => {
    // Validar el paso actual antes de avanzar
    if (currentStep === 1) {
      if (!formData.name || !formData.description || !formData.duration_minutes || !formData.price) {
        toast.error('Por favor, completa todos los campos del primer paso.');
        return;
      }
    }
    setCurrentStep(prevStep => prevStep + 1);
  };

  const handlePreviousStep = () => {
    setCurrentStep(prevStep => prevStep - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Solo enviar el formulario si estamos en el último paso
    if (currentStep !== 2) {
      return;
    }

    try {
      await createServiceCycle(formData); 
      setShowForm(false);
      toast.success('Ciclo de servicio creado exitosamente!'); // Notificación de éxito
      setFormData({
        name: '',
        description: '',
        service_type: 'lavado',
        duration_minutes: '',
        price: '',
        allowed_machines: [],
        is_active: true,
      });
      setCurrentStep(1); // Resetear a la primera página después de la creación
      // Refrescar los datos después de una creación exitosa
      const updatedData = await getServiceCycles(currentPage, 10);
      setCycles(updatedData.data);
      setTotalPages(updatedData.pagination.total_pages);

      const allWashersResponse = await getAllActiveWashers();
      setWashers(allWashersResponse.data);
      const allDryersResponse = await getAllActiveDryers();
      setDryers(allDryersResponse.data);

    } catch (err) {
      // Cerrar el modal y mostrar el mensaje de error del backend
      setShowForm(false); 
      const errorMessage = err.response && err.response.data && err.response.data.message 
                           ? err.response.data.message 
                           : 'Error al guardar el ciclo de servicio.';
      setError(errorMessage);
      toast.error(errorMessage); // Notificación de error
      setCurrentStep(1); // Resetear a la primera página si hay un error
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este ciclo de servicio?')) {
      try {
        await deleteServiceCycle(id);
        toast.success('Ciclo de servicio eliminado exitosamente!'); // Notificación de éxito
        // Refrescar los datos después de una eliminación exitosa
        const updatedData = await getServiceCycles(currentPage, 10);
        setCycles(updatedData.data);
        setTotalPages(updatedData.pagination.total_pages);

        const allWashersResponse = await getAllActiveWashers();
        setWashers(allWashersResponse.data);
        const allDryersResponse = await getAllActiveDryers();
        setDryers(allDryersResponse.data);

      } catch (err) {
        // Mostrar el mensaje de error del backend
        const errorMessage = err.response && err.response.data && err.response.data.message 
                           ? err.response.data.message 
                           : 'Error al eliminar el ciclo de servicio.';
        setError(errorMessage);
        toast.error(errorMessage); // Notificación de error
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
        <button onClick={() => { setShowForm(true); setCurrentStep(1); }} className="add-service-button">
          Agregar Nuevo Ciclo de Servicio
        </button>

        {showForm && (
          <div className={`service-form-modal ${showForm ? 'show' : ''}`}> {/* Aquí se aplica la clase 'show' */}
            <div className="service-form-content">
              <h2>Agregar Ciclo de Servicio - Paso {currentStep} de 2</h2> {/* Título dinámico */}
              <div className="step-indicator">
                <span className={`step-dot ${currentStep === 1 ? 'active' : ''}`}></span>
                <span className={`step-dot ${currentStep === 2 ? 'active' : ''}`}></span>
              </div>

              <form onSubmit={handleSubmit}>
                {currentStep === 1 && (
                  <div className="form-step-1">
                    <div className="form-group">
                      <label htmlFor="cycle-name">Nombre:</label>
                      <input type="text" id="cycle-name" name="name" value={formData.name} onChange={handleInputChange} required />
                    </div>
                    <div className="form-group">
                      <label htmlFor="cycle-description">Descripción:</label>
                      <input type="text" id="cycle-description" name="description" value={formData.description} onChange={handleInputChange} required />
                    </div>
                    <div className="form-group">
                      <label htmlFor="service-type">Tipo de Servicio:</label>
                      <select id="service-type" name="service_type" value={formData.service_type} onChange={handleInputChange} required>
                        <option value="lavado">Lavado</option>
                        <option value="secado">Secado</option>
                        <option value="combo">Combo</option>
                        <option value="encargo_lavado">Encargo Lavado</option>
                        <option value="encargo_secado">Encargo Secado</option>
                        <option value="mixto">Mixto</option>
                        <option value="mixto_encargo">Mixto Encargo</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label htmlFor="duration-minutes">Duración (minutos):</label>
                      <input type="number" id="duration-minutes" name="duration_minutes" value={formData.duration_minutes} onChange={handleInputChange} required />
                    </div>
                    <div className="form-group">
                      <label htmlFor="price">Precio:</label>
                      <input type="number" id="price" name="price" value={formData.price} onChange={handleInputChange} step="0.01" required />
                    </div>
                    <div className="form-group">
                      <label htmlFor="is-active">
                        <input type="checkbox" id="is-active" name="is_active" checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })} /> Activo
                      </label>
                    </div>
                    <div className="form-actions">
                      <button type="button" onClick={handleNextStep} className="submit-button">Siguiente</button>
                      <button type="button" onClick={() => { setShowForm(false); setCurrentStep(1); }} className="cancel-button">Cancelar</button>
                    </div>
                  </div>
                )}

                {currentStep === 2 && (
                  <div className="form-step-2">
                    <div className="form-group">
                      <label>Máquinas Permitidas:</label>
                      <div className="machine-selection-grid">
                        {filteredWashers.length > 0 && (
                          <div className="machine-type-section">
                            <h3>Lavadoras:</h3>
                            <div className="machine-list">
                              {filteredWashers.map((washer) => (
                                <label key={washer._id} className="machine-checkbox-label">
                                  <input
                                    type="checkbox"
                                    value={`${washer._id}-${washer.numero}`}
                                    checked={formData.allowed_machines.some((machine) => machine._id === washer._id)}
                                    onChange={handleMachineSelectionChange}
                                  />
                                  <span className="machine-info">Lavadora {washer.numero} ({washer.marca} - {washer.capacidad} kg)</span>
                                </label>
                              ))}
                            </div>
                          </div>
                        )}
                        {filteredDryers.length > 0 && (
                          <div className="machine-type-section">
                            <h3>Secadoras:</h3>
                            <div className="machine-list">
                              {filteredDryers.map((dryer) => (
                                <label key={dryer._id} className="machine-checkbox-label">
                                  <input
                                    type="checkbox"
                                    value={`${dryer._id}-${dryer.numero}`}
                                    checked={formData.allowed_machines.some((machine) => machine._id === dryer._id)}
                                    onChange={handleMachineSelectionChange}
                                  />
                                  <span className="machine-info">Secadora {dryer.numero} ({dryer.marca} - {dryer.capacidad} kg)</span>
                                </label>
                              ))}
                            </div>
                          </div>
                        )}
                        {filteredWashers.length === 0 && filteredDryers.length === 0 && ( /* Mensaje si no hay máquinas */
                          <p className="no-machines-message">No hay máquinas disponibles para este tipo de servicio.</p>
                        )}
                      </div>
                    </div>
                    <div className="form-actions">
                      <button type="button" onClick={handlePreviousStep} className="cancel-button">Anterior</button>
                      <button type="submit" className="submit-button">Crear Ciclo</button>
                    </div>
                  </div>
                )}
              </form>
            </div>
          </div>
        )}

        {loading && <p className="loading-message">Cargando ciclos de servicio...</p>}
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
                  <th>Máquinas Permitidas</th> 
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
                    <td>{cycle.allowed_machines.map(machine => machine.name).join(', ')}</td>
                    <td>{cycle.is_active ? 'Sí' : 'No'}</td>
                    <td>
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
      <ToastContainer position="bottom-right" autoClose={5000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
    </div>
  );
};

export default ServicesPages;
