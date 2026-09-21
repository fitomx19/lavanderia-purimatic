import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header';
import { createWasher, getWashersByStoreId, updateWasher, deleteWasher, createDryer, getDryersByStoreId, updateDryer, deleteDryer } from '../../services/machineService';
import './MachinePages.css';

const MachinePages = () => {
  const [washers, setWashers] = useState([]);
  const [dryers, setDryers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedMachine, setSelectedMachine] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addFormType, setAddFormType] = useState('washer');
  const [editingMachine, setEditingMachine] = useState(null);
  
  const [washerFormData, setWasherFormData] = useState({
    marca: '',
    capacidad: '',
    numero: '',
    store_id: 'store_001',
    estado: 'disponible',
    esp32_id: '',
  });
  
  const [dryerFormData, setDryerFormData] = useState({
    marca: '',
    capacidad: '',
    numero: '',
    store_id: 'store_001',
    estado: 'disponible',
    esp32_id: '',
  });

  const STORE_ID = 'store_001';

  useEffect(() => {
    fetchMachines();
  }, []);

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

  const handleWasherChange = (e) => {
    const { name, value } = e.target;
    setWasherFormData({ ...washerFormData, [name]: value });
  };

  const handleDryerChange = (e) => {
    const { name, value } = e.target;
    setDryerFormData({ ...dryerFormData, [name]: value });
  };

  const withEsp32Id = (data) => ({
    ...data,
    esp32_id: (data.esp32_id || '').trim() || null,
  });

  const handleCreateWasher = async (e) => {
    e.preventDefault();
    try {
      await createWasher(withEsp32Id(washerFormData));
      setWasherFormData({
        marca: '',
        capacidad: '',
        numero: '',
        store_id: 'store_001',
        estado: 'disponible',
        esp32_id: '',
      });
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
      setDryerFormData({
        marca: '',
        capacidad: '',
        numero: '',
        store_id: 'store_001',
        estado: 'disponible',
        esp32_id: '',
      });
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
    if (window.confirm('¿Estás seguro de que quieres eliminar esta lavadora?')) {
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
    if (window.confirm('¿Estás seguro de que quieres eliminar esta secadora?')) {
      try {
        await deleteDryer(id);
        fetchMachines();
        setSelectedMachine(null);
      } catch (err) {
        setError('Error al eliminar secadora: ' + (err.message || err.detail));
      }
    }
  };

  const getStatusColor = (estado) => {
    switch (estado) {
      case 'disponible': return '#28a745';
      case 'ocupada': return '#ffc107';
      case 'mantenimiento': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const getStatusIcon = (estado) => {
    switch (estado) {
      case 'disponible': return '✓';
      case 'ocupada': return '⏱';
      case 'mantenimiento': return '⚠';
      default: return '?';
    }
  };

  const openAddForm = (type) => {
    setAddFormType(type);
    setShowAddForm(true);
  };

  if (loading) return <div className="loading-message">Cargando máquinas...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  return (
    <div className="machines-layout">
      <Header />
      <div className="machines-content">
        <div className="machines-header">
          <h1>🏭 Centro de Control de Máquinas</h1>
          <div className="quick-stats">
            <div className="stat-card">
              <div className="stat-icon">🌊</div>
              <div className="stat-info">
                <span className="stat-number">{washers.length}</span>
                <span className="stat-label">Lavadoras</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🌪</div>
              <div className="stat-info">
                <span className="stat-number">{dryers.length}</span>
                <span className="stat-label">Secadoras</span>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">⚡</div>
              <div className="stat-info">
                <span className="stat-number">{washers.filter(w => w.estado === 'disponible').length + dryers.filter(d => d.estado === 'disponible').length}</span>
                <span className="stat-label">Disponibles</span>
              </div>
            </div>
          </div>
        </div>

        <div className="machines-grid">
          {/* Lavadoras */}
          {washers.map((washer) => (
            <div key={washer._id} className={`machine-card ${selectedMachine?._id === washer._id ? 'selected' : ''}`}>
              <div className="machine-icon washer-icon">
                🌊
              </div>
              <div className="machine-info">
                <h3>Lavadora #{washer.numero}</h3>
                <div className="machine-status" style={{ backgroundColor: getStatusColor(washer.estado) }}>
                  <span className="status-icon">{getStatusIcon(washer.estado)}</span>
                  <span className="status-text">{washer.estado}</span>
                </div>
              </div>
              <div className="machine-actions">
                <button 
                  className="action-btn details-btn"
                  onClick={() => setSelectedMachine(selectedMachine?._id === washer._id ? null : washer)}
                >
                  {selectedMachine?._id === washer._id ? '▼' : '▶'}
                </button>
              </div>
              
              {selectedMachine?._id === washer._id && (
                <div className="machine-details">
                  <div className="details-grid">
                    <div className="detail-item">
                      <span className="detail-label">Marca:</span>
                      <span className="detail-value">{washer.marca}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Capacidad:</span>
                      <span className="detail-value">{washer.capacidad} kg</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">ESP32:</span>
                      <span className="detail-value">{washer.esp32_id || 'sin placa'}</span>
                    </div>
                  </div>
                  
                  {editingMachine?._id === washer._id ? (
                    <form onSubmit={(e) => handleUpdateWasher(e, washer._id)} className="edit-form">
                      <div className="form-row">
                        <input 
                          type="text" 
                          placeholder="Marca"
                          value={editingMachine.marca} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, marca: e.target.value })} 
                        />
                        <input 
                          type="number" 
                          placeholder="Capacidad"
                          value={editingMachine.capacidad} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, capacidad: e.target.value })} 
                        />
                      </div>
                      <div className="form-row">
                        <input 
                          type="number" 
                          placeholder="Número"
                          value={editingMachine.numero} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, numero: e.target.value })} 
                        />
                        <select 
                          value={editingMachine.estado} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, estado: e.target.value })}
                        >
                          <option value="disponible">Disponible</option>
                          <option value="ocupada">Ocupada</option>
                          <option value="mantenimiento">Mantenimiento</option>
                        </select>
                      </div>
                      <div className="form-row">
                        <input 
                          type="text" 
                          placeholder="esp32_id (ej. 76)"
                          value={editingMachine.esp32_id || ''} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, esp32_id: e.target.value })} 
                        />
                      </div>
                      <div className="form-actions">
                        <button type="submit" className="save-btn">💾 Guardar</button>
                        <button type="button" onClick={() => setEditingMachine(null)} className="cancel-btn">❌ Cancelar</button>
                      </div>
                    </form>
                  ) : (
                    <div className="machine-controls">
                      <button 
                        className="control-btn edit-btn"
                        onClick={() => setEditingMachine(washer)}
                      >
                        ✏️ Editar
                      </button>
                      <button 
                        className="control-btn delete-btn"
                        onClick={() => handleDeleteWasher(washer._id)}
                      >
                        🗑️ Eliminar
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Secadoras */}
          {dryers.map((dryer) => (
            <div key={dryer._id} className={`machine-card ${selectedMachine?._id === dryer._id ? 'selected' : ''}`}>
              <div className="machine-icon dryer-icon">
                🌪
              </div>
              <div className="machine-info">
                <h3>Secadora #{dryer.numero}</h3>
                <div className="machine-status" style={{ backgroundColor: getStatusColor(dryer.estado) }}>
                  <span className="status-icon">{getStatusIcon(dryer.estado)}</span>
                  <span className="status-text">{dryer.estado}</span>
                </div>
              </div>
              <div className="machine-actions">
                <button 
                  className="action-btn details-btn"
                  onClick={() => setSelectedMachine(selectedMachine?._id === dryer._id ? null : dryer)}
                >
                  {selectedMachine?._id === dryer._id ? '▼' : '▶'}
                </button>
              </div>
              
              {selectedMachine?._id === dryer._id && (
                <div className="machine-details">
                  <div className="details-grid">
                    <div className="detail-item">
                      <span className="detail-label">Marca:</span>
                      <span className="detail-value">{dryer.marca}</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Capacidad:</span>
                      <span className="detail-value">{dryer.capacidad} kg</span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">ESP32:</span>
                      <span className="detail-value">{dryer.esp32_id || 'sin placa'}</span>
                    </div>
                  </div>
                  
                  {editingMachine?._id === dryer._id ? (
                    <form onSubmit={(e) => handleUpdateDryer(e, dryer._id)} className="edit-form">
                      <div className="form-row">
                        <input 
                          type="text" 
                          placeholder="Marca"
                          value={editingMachine.marca} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, marca: e.target.value })} 
                        />
                        <input 
                          type="number" 
                          placeholder="Capacidad"
                          value={editingMachine.capacidad} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, capacidad: e.target.value })} 
                        />
                      </div>
                      <div className="form-row">
                        <input 
                          type="number" 
                          placeholder="Número"
                          value={editingMachine.numero} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, numero: e.target.value })} 
                        />
                        <select 
                          value={editingMachine.estado} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, estado: e.target.value })}
                        >
                          <option value="disponible">Disponible</option>
                          <option value="ocupada">Ocupada</option>
                          <option value="mantenimiento">Mantenimiento</option>
                        </select>
                      </div>
                      <div className="form-row">
                        <input 
                          type="text" 
                          placeholder="esp32_id (ej. 76)"
                          value={editingMachine.esp32_id || ''} 
                          onChange={(e) => setEditingMachine({ ...editingMachine, esp32_id: e.target.value })} 
                        />
                      </div>
                      <div className="form-actions">
                        <button type="submit" className="save-btn">💾 Guardar</button>
                        <button type="button" onClick={() => setEditingMachine(null)} className="cancel-btn">❌ Cancelar</button>
                      </div>
                    </form>
                  ) : (
                    <div className="machine-controls">
                      <button 
                        className="control-btn edit-btn"
                        onClick={() => setEditingMachine(dryer)}
                      >
                        ✏️ Editar
                      </button>
                      <button 
                        className="control-btn delete-btn"
                        onClick={() => handleDeleteDryer(dryer._id)}
                      >
                        🗑️ Eliminar
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Botones para agregar nuevas máquinas */}
          <div className="add-machine-card" onClick={() => openAddForm('washer')}>
            <div className="add-icon">➕</div>
            <div className="add-text">
              <h3>Agregar Lavadora</h3>
              <p>Nueva máquina lavadora</p>
            </div>
          </div>

          <div className="add-machine-card" onClick={() => openAddForm('dryer')}>
            <div className="add-icon">➕</div>
            <div className="add-text">
              <h3>Agregar Secadora</h3>
              <p>Nueva máquina secadora</p>
            </div>
          </div>
        </div>

        {/* Modal para agregar máquinas */}
        {showAddForm && (
          <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>➕ Agregar Nueva {addFormType === 'washer' ? 'Lavadora' : 'Secadora'}</h2>
                <button className="close-btn" onClick={() => setShowAddForm(false)}>✕</button>
              </div>
              
              <form onSubmit={addFormType === 'washer' ? handleCreateWasher : handleCreateDryer} className="add-form">
                <div className="form-row">
                  <input 
                    type="text" 
                    name="marca" 
                    placeholder="Marca de la máquina"
                    value={addFormType === 'washer' ? washerFormData.marca : dryerFormData.marca}
                    onChange={addFormType === 'washer' ? handleWasherChange : handleDryerChange}
                    required 
                  />
                  <input 
                    type="number" 
                    name="capacidad" 
                    placeholder="Capacidad (kg)"
                    value={addFormType === 'washer' ? washerFormData.capacidad : dryerFormData.capacidad}
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
                  <input 
                    type="text" 
                    name="esp32_id" 
                    placeholder="esp32_id (el mismo de Placas ESP32)"
                    value={addFormType === 'washer' ? washerFormData.esp32_id : dryerFormData.esp32_id}
                    onChange={addFormType === 'washer' ? handleWasherChange : handleDryerChange}
                  />
                </div>
                <div className="form-actions">
                  <button type="submit" className="save-btn">💾 Crear {addFormType === 'washer' ? 'Lavadora' : 'Secadora'}</button>
                  <button type="button" onClick={() => setShowAddForm(false)} className="cancel-btn">❌ Cancelar</button>
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
