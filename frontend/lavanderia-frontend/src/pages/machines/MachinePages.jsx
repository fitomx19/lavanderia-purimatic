import React, { useState, useEffect, useMemo } from 'react';
import Header from '../../components/layout/Header';
import {
  createWasher,
  getWashersByStoreId,
  updateWasher,
  deleteWasher,
  createDryer,
  getDryersByStoreId,
  updateDryer,
  deleteDryer,
} from '../../services/machineService';
import { listEsp32Configs } from '../../services/esp32ConfigService';
import './MachinePages.css';

const STORE_ID = 'store_001';

const emptyWasherForm = {
  marca: '',
  capacidad: '',
  numero: '',
  store_id: STORE_ID,
  estado: 'disponible',
  esp32_id: '',
};

const emptyDryerForm = {
  marca: '',
  capacidad: '',
  numero: '',
  store_id: STORE_ID,
  estado: 'disponible',
  esp32_id: '',
};

const MachinePages = () => {
  const [washers, setWashers] = useState([]);
  const [dryers, setDryers] = useState([]);
  const [availableEsp32Ids, setAvailableEsp32Ids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addFormType, setAddFormType] = useState('washer');
  const [editingMachine, setEditingMachine] = useState(null);

  const [washerFormData, setWasherFormData] = useState(emptyWasherForm);
  const [dryerFormData, setDryerFormData] = useState(emptyDryerForm);

  useEffect(() => {
    fetchMachines();
    fetchEsp32Ids();
  }, []);

  const fetchEsp32Ids = async () => {
    try {
      const result = await listEsp32Configs(true);
      const boards = result.data || [];
      const ids = [
        ...new Set(
          boards
            .filter((board) => board.is_active !== false)
            .flatMap((board) => board.esp32_ids || [])
            .map((id) => String(id).trim())
            .filter(Boolean)
        ),
      ].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
      setAvailableEsp32Ids(ids);
    } catch {
      setAvailableEsp32Ids([]);
    }
  };

  const fetchMachines = async () => {
    try {
      setLoading(true);
      const washersData = await getWashersByStoreId(STORE_ID);
      setWashers(washersData.data.washers);
      const dryersData = await getDryersByStoreId(STORE_ID);
      setDryers(dryersData.data.dryers);
    } catch (err) {
      setError('Error al cargar las máquinas: ' + (err.message || err.detail));
    } finally {
      setLoading(false);
    }
  };

  const assignedEsp32Ids = useMemo(() => {
    const used = new Set();
    washers.forEach((w) => {
      if (w.esp32_id) used.add(String(w.esp32_id));
    });
    dryers.forEach((d) => {
      if (d.esp32_id) used.add(String(d.esp32_id));
    });
    return used;
  }, [washers, dryers]);

  const optionsForSelect = (currentId) => {
    const current = (currentId || '').trim();
    return availableEsp32Ids.filter(
      (id) => !assignedEsp32Ids.has(id) || id === current
    );
  };

  const handleWasherChange = (e) => {
    const { name, value } = e.target;
    setWasherFormData({ ...washerFormData, [name]: value });
  };

  const handleDryerChange = (e) => {
    const { name, value } = e.target;
    setDryerFormData({ ...dryerFormData, [name]: value });
  };

  const withEsp32Id = (data) => {
    const id = (data.esp32_id || '').trim();
    if (!id) return { ...data, esp32_id: null };
    if (!availableEsp32Ids.includes(id)) {
      throw new Error(
        'El ID ESP32 debe existir en Placas ESP32. No se permiten valores inventados.'
      );
    }
    return { ...data, esp32_id: id };
  };

  const handleCreateWasher = async (e) => {
    e.preventDefault();
    try {
      await createWasher(withEsp32Id(washerFormData));
      setWasherFormData(emptyWasherForm);
      setShowAddForm(false);
      fetchMachines();
    } catch (err) {
      setError('Error al crear lavadora: ' + (err.message || err.detail));
    }
  };

  const handleCreateDryer = async (e) => {
    e.preventDefault();
    try {
      await createDryer(withEsp32Id(dryerFormData));
      setDryerFormData(emptyDryerForm);
      setShowAddForm(false);
      fetchMachines();
    } catch (err) {
      setError('Error al crear secadora: ' + (err.message || err.detail));
    }
  };

  const handleUpdateWasher = async (e, id) => {
    e.preventDefault();
    try {
      await updateWasher(id, withEsp32Id(editingMachine));
      setEditingMachine(null);
      fetchMachines();
    } catch (err) {
      setError('Error al actualizar lavadora: ' + (err.message || err.detail));
    }
  };

  const handleUpdateDryer = async (e, id) => {
    e.preventDefault();
    try {
      await updateDryer(id, withEsp32Id(editingMachine));
      setEditingMachine(null);
      fetchMachines();
    } catch (err) {
      setError('Error al actualizar secadora: ' + (err.message || err.detail));
    }
  };

  const handleDeleteWasher = async (id) => {
    if (window.confirm('¿Eliminar esta lavadora?')) {
      try {
        await deleteWasher(id);
        fetchMachines();
        setSelectedMachine(null);
      } catch (err) {
        setError('Error al eliminar lavadora: ' + (err.message || err.detail));
      }
    }
  };

  const handleDeleteDryer = async (id) => {
    if (window.confirm('¿Eliminar esta secadora?')) {
      try {
        await deleteDryer(id);
        fetchMachines();
        setSelectedMachine(null);
      } catch (err) {
        setError('Error al eliminar secadora: ' + (err.message || err.detail));
      }
    }
  };

  const statusClass = (estado) => {
    switch (estado) {
      case 'disponible':
        return 'status-disponible';
      case 'ocupada':
        return 'status-ocupada';
      case 'mantenimiento':
        return 'status-mantenimiento';
      default:
        return 'status-default';
    }
  };

  const startEditing = (machine) => {
    const current = (machine.esp32_id || '').trim();
    setEditingMachine({
      ...machine,
      esp32_id: availableEsp32Ids.includes(current) ? current : '',
    });
  };

  const openAddForm = (type) => {
    setAddFormType(type);
    setShowAddForm(true);
  };

  const renderEsp32Select = (value, onChange) => {
    const options = optionsForSelect(value);
    const current = (value || '').trim();
    const isOrphan = current && !availableEsp32Ids.includes(current);
    return (
      <div className="esp32-select-wrap">
        <select
          name="esp32_id"
          value={isOrphan ? '' : current}
          onChange={onChange}
          className="esp32-select"
        >
          <option value="">{isOrphan ? 'Reasignar ID ESP32 (requerido)' : 'Sin ID ESP32'}</option>
          {options.map((id) => (
            <option key={id} value={id}>
              {id}
            </option>
          ))}
        </select>
        {isOrphan && (
          <p className="form-hint">
            El ID actual ({current}) no está registrado en Placas ESP32. Elige uno válido o déjalo sin asignar.
          </p>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="machines-layout">
        <Header />
        <div className="machines-content">
          <p className="machines-loading">Cargando máquinas...</p>
        </div>
      </div>
    );
  }

  const disponibles =
    washers.filter((w) => w.estado === 'disponible').length +
    dryers.filter((d) => d.estado === 'disponible').length;

  return (
    <div className="machines-layout">
      <Header />
      <div className="machines-content">
        <div className="machines-header">
          <div>
            <h1>Equipo</h1>
            <p className="machines-subtitle">
              Gestión de lavadoras y secadoras. El ID ESP32 solo puede elegirse entre los registrados en Placas ESP32.
            </p>
          </div>
          <div className="quick-stats">
            <div className="stat-card">
              <span className="stat-number">{washers.length}</span>
              <span className="stat-label">Lavadoras</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">{dryers.length}</span>
              <span className="stat-label">Secadoras</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">{disponibles}</span>
              <span className="stat-label">Disponibles</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="machines-error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={() => setError(null)}>
              Cerrar
            </button>
          </div>
        )}

        {availableEsp32Ids.length === 0 && (
          <div className="machines-notice">
            No hay IDs ESP32 registrados. Configúralos primero en Placas ESP32 antes de asignarlos a una máquina.
          </div>
        )}

        <div className="machines-grid">
          {washers.map((washer) => (
            <div
              key={washer._id}
              className={`machine-card machine-card--washer ${selectedMachine?._id === washer._id ? 'selected' : ''}`}
            >
              <div className="machine-card-top">
                <div className="machine-info">
                  <span className="machine-type">Lavadora</span>
                  <h3>#{washer.numero}</h3>
                  <span className={`machine-status ${statusClass(washer.estado)}`}>
                    {washer.estado}
                  </span>
                </div>
                <button
                  type="button"
                  className="action-btn details-btn"
                  onClick={() =>
                    setSelectedMachine(selectedMachine?._id === washer._id ? null : washer)
                  }
                >
                  {selectedMachine?._id === washer._id ? 'Ocultar' : 'Detalle'}
                </button>
              </div>

              {selectedMachine?._id === washer._id && (
                <div className="machine-details">
                  <div className="details-grid">
                    <div className="detail-item">
                      <span className="detail-label">Marca</span>
                      <span className="detail-value">{washer.marca}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Capacidad</span>
                      <span className="detail-value">{washer.capacidad} kg</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">ID ESP32</span>
                      <span className="detail-value">{washer.esp32_id || 'Sin asignar'}</span>
                    </div>
                  </div>

                  {editingMachine?._id === washer._id ? (
                    <form onSubmit={(e) => handleUpdateWasher(e, washer._id)} className="edit-form">
                      <div className="form-row">
                        <input
                          type="text"
                          placeholder="Marca"
                          value={editingMachine.marca}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, marca: e.target.value })
                          }
                        />
                        <input
                          type="number"
                          placeholder="Capacidad"
                          value={editingMachine.capacidad}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, capacidad: e.target.value })
                          }
                        />
                      </div>
                      <div className="form-row">
                        <input
                          type="number"
                          placeholder="Número"
                          value={editingMachine.numero}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, numero: e.target.value })
                          }
                        />
                        <select
                          value={editingMachine.estado}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, estado: e.target.value })
                          }
                        >
                          <option value="disponible">Disponible</option>
                          <option value="ocupada">Ocupada</option>
                          <option value="mantenimiento">Mantenimiento</option>
                        </select>
                      </div>
                      <div className="form-row">
                        {renderEsp32Select(editingMachine.esp32_id || '', (e) =>
                          setEditingMachine({ ...editingMachine, esp32_id: e.target.value })
                        )}
                      </div>
                      <div className="form-actions">
                        <button type="submit" className="save-btn">
                          Guardar
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingMachine(null)}
                          className="cancel-btn"
                        >
                          Cancelar
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="machine-controls">
                      <button
                        type="button"
                        className="control-btn edit-btn"
                        onClick={() => startEditing(washer)}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="control-btn delete-btn"
                        onClick={() => handleDeleteWasher(washer._id)}
                      >
                        Eliminar
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {dryers.map((dryer) => (
            <div
              key={dryer._id}
              className={`machine-card machine-card--dryer ${selectedMachine?._id === dryer._id ? 'selected' : ''}`}
            >
              <div className="machine-card-top">
                <div className="machine-info">
                  <span className="machine-type">Secadora</span>
                  <h3>#{dryer.numero}</h3>
                  <span className={`machine-status ${statusClass(dryer.estado)}`}>
                    {dryer.estado}
                  </span>
                </div>
                <button
                  type="button"
                  className="action-btn details-btn"
                  onClick={() =>
                    setSelectedMachine(selectedMachine?._id === dryer._id ? null : dryer)
                  }
                >
                  {selectedMachine?._id === dryer._id ? 'Ocultar' : 'Detalle'}
                </button>
              </div>

              {selectedMachine?._id === dryer._id && (
                <div className="machine-details">
                  <div className="details-grid">
                    <div className="detail-item">
                      <span className="detail-label">Marca</span>
                      <span className="detail-value">{dryer.marca}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Capacidad</span>
                      <span className="detail-value">{dryer.capacidad} kg</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">ID ESP32</span>
                      <span className="detail-value">{dryer.esp32_id || 'Sin asignar'}</span>
                    </div>
                  </div>

                  {editingMachine?._id === dryer._id ? (
                    <form onSubmit={(e) => handleUpdateDryer(e, dryer._id)} className="edit-form">
                      <div className="form-row">
                        <input
                          type="text"
                          placeholder="Marca"
                          value={editingMachine.marca}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, marca: e.target.value })
                          }
                        />
                        <input
                          type="number"
                          placeholder="Capacidad"
                          value={editingMachine.capacidad}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, capacidad: e.target.value })
                          }
                        />
                      </div>
                      <div className="form-row">
                        <input
                          type="number"
                          placeholder="Número"
                          value={editingMachine.numero}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, numero: e.target.value })
                          }
                        />
                        <select
                          value={editingMachine.estado}
                          onChange={(e) =>
                            setEditingMachine({ ...editingMachine, estado: e.target.value })
                          }
                        >
                          <option value="disponible">Disponible</option>
                          <option value="ocupada">Ocupada</option>
                          <option value="mantenimiento">Mantenimiento</option>
                        </select>
                      </div>
                      <div className="form-row">
                        {renderEsp32Select(editingMachine.esp32_id || '', (e) =>
                          setEditingMachine({ ...editingMachine, esp32_id: e.target.value })
                        )}
                      </div>
                      <div className="form-actions">
                        <button type="submit" className="save-btn">
                          Guardar
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingMachine(null)}
                          className="cancel-btn"
                        >
                          Cancelar
                        </button>
                      </div>
                    </form>
                  ) : (
                    <div className="machine-controls">
                      <button
                        type="button"
                        className="control-btn edit-btn"
                        onClick={() => startEditing(dryer)}
                      >
                        Editar
                      </button>
                      <button
                        type="button"
                        className="control-btn delete-btn"
                        onClick={() => handleDeleteDryer(dryer._id)}
                      >
                        Eliminar
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          <button type="button" className="add-machine-card" onClick={() => openAddForm('washer')}>
            <h3>Agregar lavadora</h3>
            <p>Registrar nueva lavadora</p>
          </button>

          <button type="button" className="add-machine-card" onClick={() => openAddForm('dryer')}>
            <h3>Agregar secadora</h3>
            <p>Registrar nueva secadora</p>
          </button>
        </div>

        {showAddForm && (
          <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>Nueva {addFormType === 'washer' ? 'lavadora' : 'secadora'}</h2>
                <button type="button" className="close-btn" onClick={() => setShowAddForm(false)}>
                  Cerrar
                </button>
              </div>

              <form
                onSubmit={addFormType === 'washer' ? handleCreateWasher : handleCreateDryer}
                className="add-form"
              >
                <div className="form-row">
                  <input
                    type="text"
                    name="marca"
                    placeholder="Marca"
                    value={addFormType === 'washer' ? washerFormData.marca : dryerFormData.marca}
                    onChange={addFormType === 'washer' ? handleWasherChange : handleDryerChange}
                    required
                  />
                  <input
                    type="number"
                    name="capacidad"
                    placeholder="Capacidad (kg)"
                    value={
                      addFormType === 'washer' ? washerFormData.capacidad : dryerFormData.capacidad
                    }
                    onChange={addFormType === 'washer' ? handleWasherChange : handleDryerChange}
                    required
                  />
                </div>
                <div className="form-row">
                  <input
                    type="number"
                    name="numero"
                    placeholder="Número de máquina"
                    value={addFormType === 'washer' ? washerFormData.numero : dryerFormData.numero}
                    onChange={addFormType === 'washer' ? handleWasherChange : handleDryerChange}
                    required
                  />
                  <select
                    name="estado"
                    value={addFormType === 'washer' ? washerFormData.estado : dryerFormData.estado}
                    onChange={addFormType === 'washer' ? handleWasherChange : handleDryerChange}
                  >
                    <option value="disponible">Disponible</option>
                    <option value="ocupada">Ocupada</option>
                    <option value="mantenimiento">Mantenimiento</option>
                  </select>
                </div>
                <div className="form-row">
                  {renderEsp32Select(
                    addFormType === 'washer' ? washerFormData.esp32_id : dryerFormData.esp32_id,
                    addFormType === 'washer' ? handleWasherChange : handleDryerChange
                  )}
                </div>
                {availableEsp32Ids.length === 0 && (
                  <p className="form-hint">
                    Primero registra los IDs en Placas ESP32 para poder asignarlos aquí.
                  </p>
                )}
                <div className="form-actions">
                  <button type="submit" className="save-btn">
                    Crear {addFormType === 'washer' ? 'lavadora' : 'secadora'}
                  </button>
                  <button type="button" onClick={() => setShowAddForm(false)} className="cancel-btn">
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MachinePages;
