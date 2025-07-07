import React, { useState, useEffect } from 'react';
// import Sidebar from '../../components/layout/Sidebar'; // Importación de Sidebar eliminada
import Header from '../../components/layout/Header'; // Importar Header
import { createWasher, getWashersByStoreId, updateWasher, deleteWasher, createDryer, getDryersByStoreId, updateDryer, deleteDryer } from '../../services/machineService';
import './MachinePages.css';

const MachinePages = () => {
  const [washers, setWashers] = useState([]);
  const [dryers, setDryers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [washerFormData, setWasherFormData] = useState({
    marca: '',
    capacidad: '',
    numero: '',
    store_id: 'store_001', // Hardcodeado por ahora
    estado: 'disponible',
  });
  const [dryerFormData, setDryerFormData] = useState({
    marca: '',
    capacidad: '',
    numero: '',
    store_id: 'store_001', // Hardcodeado por ahora
    estado: 'disponible',
  });
  const [editingWasher, setEditingWasher] = useState(null);
  const [editingDryer, setEditingDryer] = useState(null);
  const [showAddWasherForm, setShowAddWasherForm] = useState(false);
  const [showAddDryerForm, setShowAddDryerForm] = useState(false);

  const STORE_ID = 'store_001'; // ID de tienda hardcodeado

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

  const handleCreateWasher = async (e) => {
    e.preventDefault();
    try {
      await createWasher(washerFormData);
      alert('Lavadora creada exitosamente');
      setWasherFormData({
        marca: '',
        capacidad: '',
        numero: '',
        store_id: 'store_001',
        estado: 'disponible',
      });
      setShowAddWasherForm(false);
      fetchMachines();
    } catch (err) {
      setError('Error al crear lavadora: ' + (err.message || err.detail));
    }
  };

  const handleCreateDryer = async (e) => {
    e.preventDefault();
    try {
      await createDryer(dryerFormData);
      alert('Secadora creada exitosamente');
      setDryerFormData({
        marca: '',
        capacidad: '',
        numero: '',
        store_id: 'store_001',
        estado: 'disponible',
      });
      setShowAddDryerForm(false);
      fetchMachines();
    } catch (err) {
      setError('Error al crear secadora: ' + (err.message || err.detail));
    }
  };

  const handleUpdateWasher = async (e, id) => {
    e.preventDefault();
    try {
      await updateWasher(id, editingWasher);
      alert('Lavadora actualizada exitosamente');
      setEditingWasher(null);
      fetchMachines();
    } catch (err) {
      setError('Error al actualizar lavadora: ' + (err.message || err.detail));
    }
  };

  const handleUpdateDryer = async (e, id) => {
    e.preventDefault();
    try {
      await updateDryer(id, editingDryer);
      alert('Secadora actualizada exitosamente');
      setEditingDryer(null);
      fetchMachines();
    } catch (err) {
      setError('Error al actualizar secadora: ' + (err.message || err.detail));
    }
  };

  const handleDeleteWasher = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta lavadora?')) {
      try {
        await deleteWasher(id);
        alert('Lavadora eliminada exitosamente');
        fetchMachines();
      } catch (err) {
        setError('Error al eliminar lavadora: ' + (err.message || err.detail));
      }
    }
  };

  const handleDeleteDryer = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta secadora?')) {
      try {
        await deleteDryer(id);
        alert('Secadora eliminada exitosamente');
        fetchMachines();
      } catch (err) {
        setError('Error al eliminar secadora: ' + (err.message || err.detail));
      }
    }
  };

  if (loading) return <div className="loading-message">Cargando máquinas...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  return (
    <div className="machines-layout">
      <Header /> {/* Añadir el Header aquí */}
      <div className="machines-content">
        <h1>Gestión de Máquinas</h1>

        <section className="machines-section">
          <h2>Lavadoras</h2>
          {!showAddWasherForm && (
            <button onClick={() => setShowAddWasherForm(true)} className="toggle-add-form-button">
              Agregar Nueva Lavadora
            </button>
          )}
          {showAddWasherForm && (
            <form onSubmit={handleCreateWasher} className="machine-form">
              <h3>Agregar Nueva Lavadora</h3>
              <input type="text" name="marca" placeholder="Marca" value={washerFormData.marca} onChange={handleWasherChange} required />
              <input type="number" name="capacidad" placeholder="Capacidad" value={washerFormData.capacidad} onChange={handleWasherChange} required />
              <input type="number" name="numero" placeholder="Número" value={washerFormData.numero} onChange={handleWasherChange} required />
              <select name="estado" value={washerFormData.estado} onChange={handleWasherChange}>
                <option value="disponible">Disponible</option>
                <option value="ocupada">Ocupada</option>
                <option value="mantenimiento">Mantenimiento</option>
              </select>
              <div className="form-actions">
                <button type="submit">Agregar Lavadora</button>
                <button type="button" onClick={() => setShowAddWasherForm(false)} className="cancel-button">Cancelar</button>
              </div>
            </form>
          )}

          <div className="machine-list">
            {washers.length > 0 ? (
              washers.map((washer) => (
                <div key={washer._id} className="machine-card">
                  {editingWasher && editingWasher._id === washer._id ? (
                    <form onSubmit={(e) => handleUpdateWasher(e, washer._id)} className="edit-form">
                      <input type="text" name="marca" value={editingWasher.marca} onChange={(e) => setEditingWasher({ ...editingWasher, marca: e.target.value })} />
                      <input type="number" name="capacidad" value={editingWasher.capacidad} onChange={(e) => setEditingWasher({ ...editingWasher, capacidad: e.target.value })} />
                      <input type="number" name="numero" value={editingWasher.numero} onChange={(e) => setEditingWasher({ ...editingWasher, numero: e.target.value })} />
                      <select name="estado" value={editingWasher.estado} onChange={(e) => setEditingWasher({ ...editingWasher, estado: e.target.value })}>
                        <option value="disponible">Disponible</option>
                        <option value="ocupada">Ocupada</option>
                        <option value="mantenimiento">Mantenimiento</option>
                      </select>
                      <button type="submit">Guardar</button>
                      <button type="button" onClick={() => setEditingWasher(null)}>Cancelar</button>
                    </form>
                  ) : (
                    <>
                      <h3>Lavadora #{washer.numero}</h3>
                      <p>Marca: {washer.marca}</p>
                      <p>Capacidad: {washer.capacidad} kg</p>
                      <p>Estado: {washer.estado}</p>
                      <div className="card-actions">
                        <button onClick={() => setEditingWasher(washer)}>Editar</button>
                        <button onClick={() => handleDeleteWasher(washer._id)}>Eliminar</button>
                      </div>
                    </>
                  )}
                </div>
              ))
            ) : (
              <p>No hay lavadoras registradas.</p>
            )}
          </div>
        </section>

        <section className="machines-section">
          <h2>Secadoras</h2>
          {!showAddDryerForm && (
            <button onClick={() => setShowAddDryerForm(true)} className="toggle-add-form-button">
              Agregar Nueva Secadora
            </button>
          )}
          {showAddDryerForm && (
            <form onSubmit={handleCreateDryer} className="machine-form">
              <h3>Agregar Nueva Secadora</h3>
              <input type="text" name="marca" placeholder="Marca" value={dryerFormData.marca} onChange={handleDryerChange} required />
              <input type="number" name="capacidad" placeholder="Capacidad" value={dryerFormData.capacidad} onChange={handleDryerChange} required />
              <input type="number" name="numero" placeholder="Número" value={dryerFormData.numero} onChange={handleDryerChange} required />
              <select name="estado" value={dryerFormData.estado} onChange={handleDryerChange}>
                <option value="disponible">Disponible</option>
                <option value="ocupada">Ocupada</option>
                <option value="mantenimiento">Mantenimiento</option>
              </select>
              <div className="form-actions">
                <button type="submit">Agregar Secadora</button>
                <button type="button" onClick={() => setShowAddDryerForm(false)} className="cancel-button">Cancelar</button>
              </div>
            </form>
          )}

          <div className="machine-list">
            {dryers.length > 0 ? (
              dryers.map((dryer) => (
                <div key={dryer._id} className="machine-card">
                  {editingDryer && editingDryer._id === dryer._id ? (
                    <form onSubmit={(e) => handleUpdateDryer(e, dryer._id)} className="edit-form">
                      <input type="text" name="marca" value={editingDryer.marca} onChange={(e) => setEditingDryer({ ...editingDryer, marca: e.target.value })} />
                      <input type="number" name="capacidad" value={editingDryer.capacidad} onChange={(e) => setEditingDryer({ ...editingDryer, capacidad: e.target.value })} />
                      <input type="number" name="numero" value={editingDryer.numero} onChange={(e) => setEditingDryer({ ...editingDryer, numero: e.target.value })} />
                      <select name="estado" value={editingDryer.estado} onChange={(e) => setEditingDryer({ ...editingDryer, estado: e.target.value })}>
                        <option value="disponible">Disponible</option>
                        <option value="ocupada">Ocupada</option>
                        <option value="mantenimiento">Mantenimiento</option>
                      </select>
                      <button type="submit">Guardar</button>
                      <button type="button" onClick={() => setEditingDryer(null)}>Cancelar</button>
                    </form>
                  ) : (
                    <>
                      <h3>Secadora #{dryer.numero}</h3>
                      <p>Marca: {dryer.marca}</p>
                      <p>Capacidad: {dryer.capacidad} kg</p>
                      <p>Estado: {dryer.estado}</p>
                      <div className="card-actions">
                        <button onClick={() => setEditingDryer(dryer)}>Editar</button>
                        <button onClick={() => handleDeleteDryer(dryer._id)}>Eliminar</button>
                      </div>
                    </>
                  )}
                </div>
              ))
            ) : (
              <p>No hay secadoras registradas.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
};

export default MachinePages;
