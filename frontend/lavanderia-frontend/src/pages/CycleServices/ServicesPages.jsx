import React, { useState, useEffect, useRef } from 'react';
import Header from '../../components/layout/Header';
import {
  getServiceCycles,
  createServiceCycle,
  updateServiceCycle,
  deleteServiceCycle,
} from '../../services/cycleService';
import { getAllActiveWashers, getAllActiveDryers } from '../../services/machineService';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './ServicesPages.css';

const EMPTY_FORM = {
  name: '',
  description: '',
  service_type: 'lavado',
  duration_minutes: '',
  price: '',
  price_per_kg: '',
  price_tarjeta: '',
  price_per_kg_tarjeta: '',
  allowed_machines: [],
  is_active: true,
};

const TYPE_LABELS = {
  lavado: 'Lavado',
  secado: 'Secado',
  encargo_lavado: 'Encargo',
};

const ServicesPages = () => {
  const [cycles, setCycles] = useState([]);
  const [washers, setWashers] = useState([]);
  const [dryers, setDryers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [typeFilter, setTypeFilter] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editingCycle, setEditingCycle] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [expandedId, setExpandedId] = useState(null);
  const prevServiceType = useRef(formData.service_type);

  const fetchData = async () => {
    setLoading(true);
    try {
      const cyclesResponse = await getServiceCycles(currentPage, 12);
      setCycles(cyclesResponse.data || []);
      setTotalPages(cyclesResponse.pagination?.total_pages || 1);

      const [washersRes, dryersRes] = await Promise.all([
        getAllActiveWashers(),
        getAllActiveDryers(),
      ]);
      setWashers(washersRes.data || []);
      setDryers(dryersRes.data || []);
      setError(null);
    } catch (err) {
      const msg = err.message || 'Error al cargar ciclos de servicio.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [currentPage]);

  useEffect(() => {
    if (prevServiceType.current !== formData.service_type) {
      prevServiceType.current = formData.service_type;
      setFormData((prev) => ({ ...prev, allowed_machines: [] }));
    }
  }, [formData.service_type]);

  const filteredWashers =
    formData.service_type === 'lavado' || formData.service_type === 'encargo_lavado'
      ? washers
      : [];
  const filteredDryers =
    formData.service_type === 'secado' || formData.service_type === 'encargo_lavado'
      ? dryers
      : [];

  const visibleCycles =
    typeFilter === 'all'
      ? cycles
      : cycles.filter((c) => c.service_type === typeFilter);

  const stats = {
    total: cycles.length,
    lavado: cycles.filter((c) => c.service_type === 'lavado').length,
    secado: cycles.filter((c) => c.service_type === 'secado').length,
    encargo: cycles.filter((c) => c.service_type === 'encargo_lavado').length,
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleMachineSelectionChange = (e) => {
    const { value, checked } = e.target;
    const [machineId, machineNumber] = value.split('-');

    setFormData((prev) => {
      const next = checked
        ? [...prev.allowed_machines, { _id: machineId, name: machineNumber }]
        : prev.allowed_machines.filter((m) => m._id !== machineId);
      return { ...prev, allowed_machines: next };
    });
  };

  const resetForm = () => {
    setFormData(EMPTY_FORM);
    prevServiceType.current = 'lavado';
    setEditingCycle(null);
    setCurrentStep(1);
    setShowForm(false);
  };

  const openCreate = () => {
    setEditingCycle(null);
    setFormData(EMPTY_FORM);
    prevServiceType.current = 'lavado';
    setCurrentStep(1);
    setShowForm(true);
  };

  const openEdit = (cycle) => {
    setEditingCycle(cycle);
    const next = {
      name: cycle.name || '',
      description: cycle.description || '',
      service_type: cycle.service_type || 'lavado',
      duration_minutes: cycle.duration_minutes ?? '',
      price: cycle.price != null ? String(cycle.price) : '',
      price_per_kg: cycle.price_per_kg != null ? String(cycle.price_per_kg) : '',
      price_tarjeta: cycle.price_tarjeta != null ? String(cycle.price_tarjeta) : '',
      price_per_kg_tarjeta:
        cycle.price_per_kg_tarjeta != null ? String(cycle.price_per_kg_tarjeta) : '',
      allowed_machines: Array.isArray(cycle.allowed_machines)
        ? cycle.allowed_machines.map((m) => ({
            _id: m._id,
            name: String(m.name),
          }))
        : [],
      is_active: cycle.is_active !== false,
    };
    prevServiceType.current = next.service_type;
    setFormData(next);
    setCurrentStep(1);
    setShowForm(true);
  };

  const validateStep1 = () => {
    const { name, description, duration_minutes, service_type, price, price_per_kg } = formData;

    if (!name?.trim() || !description?.trim() || !duration_minutes) {
      toast.error('Completa nombre, descripción y duración.');
      return false;
    }

    if (service_type === 'encargo_lavado') {
      if (!price_per_kg || parseFloat(price_per_kg) <= 0) {
        toast.error('Ingresa un precio por kilogramo válido.');
        return false;
      }
    } else if (!price || parseFloat(price) <= 0) {
      toast.error('Ingresa un precio válido.');
      return false;
    }

    return true;
  };

  const prepareFormDataForSubmit = () => {
    const submitData = {
      name: formData.name.trim(),
      description: formData.description.trim(),
      service_type: formData.service_type,
      duration_minutes: parseInt(formData.duration_minutes, 10),
      allowed_machines: formData.allowed_machines,
      is_active: formData.is_active,
    };

    if (formData.service_type === 'encargo_lavado') {
      submitData.price_per_kg = parseFloat(formData.price_per_kg);
      if (formData.price_per_kg_tarjeta !== '' && formData.price_per_kg_tarjeta != null) {
        submitData.price_per_kg_tarjeta = parseFloat(formData.price_per_kg_tarjeta);
      }
    } else {
      submitData.price = parseFloat(formData.price);
      if (formData.price_tarjeta !== '' && formData.price_tarjeta != null) {
        submitData.price_tarjeta = parseFloat(formData.price_tarjeta);
      }
    }

    return submitData;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (currentStep !== 2) return;

    if (!formData.allowed_machines.length) {
      toast.error('Selecciona al menos una máquina permitida.');
      return;
    }

    try {
      setSaving(true);
      const submitData = prepareFormDataForSubmit();

      if (editingCycle) {
        await updateServiceCycle(editingCycle._id, submitData);
        toast.success('Ciclo actualizado.');
      } else {
        await createServiceCycle(submitData);
        toast.success('Ciclo creado.');
      }

      resetForm();
      await fetchData();
    } catch (err) {
      const errorMessage =
        err.message ||
        err.errors ||
        'Error al guardar el ciclo de servicio.';
      toast.error(typeof errorMessage === 'string' ? errorMessage : 'Error de validación.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Eliminar este ciclo de servicio?')) return;
    try {
      await deleteServiceCycle(id);
      toast.success('Ciclo eliminado.');
      if (expandedId === id) setExpandedId(null);
      await fetchData();
    } catch (err) {
      toast.error(err.message || 'Error al eliminar el ciclo.');
    }
  };

  const formatPrice = (cycle) => {
    if (cycle.service_type === 'encargo_lavado') {
      const base = `$${parseFloat(cycle.price_per_kg || 0).toFixed(2)}/kg`;
      if (cycle.price_per_kg_tarjeta != null) {
        return `${base} · tarjeta $${parseFloat(cycle.price_per_kg_tarjeta).toFixed(2)}/kg`;
      }
      return base;
    }
    const base = `$${parseFloat(cycle.price || 0).toFixed(2)}`;
    if (cycle.price_tarjeta != null) {
      return `${base} · tarjeta $${parseFloat(cycle.price_tarjeta).toFixed(2)}`;
    }
    return base;
  };

  const machineLabel = (ref) => {
    const washer = washers.find((w) => w._id === ref._id);
    if (washer) return `Lavadora #${washer.numero}`;
    const dryer = dryers.find((d) => d._id === ref._id);
    if (dryer) return `Secadora #${dryer.numero}`;
    return ref.name ? `#${ref.name}` : 'Máquina';
  };

  return (
    <div className="cycles-layout">
      <Header />
      <main className="cycles-content">
        <div className="cycles-header">
          <div>
            <h1>Ciclos de servicio</h1>
            <p className="cycles-subtitle">
              Define precios, duración y máquinas permitidas para lavado, secado y encargo.
            </p>
          </div>
          <div className="cycles-stats">
            <div className="cycles-stat">
              <span className="cycles-stat-num">{stats.total}</span>
              <span className="cycles-stat-label">Total</span>
            </div>
            <div className="cycles-stat">
              <span className="cycles-stat-num">{stats.lavado}</span>
              <span className="cycles-stat-label">Lavado</span>
            </div>
            <div className="cycles-stat">
              <span className="cycles-stat-num">{stats.secado}</span>
              <span className="cycles-stat-label">Secado</span>
            </div>
            <div className="cycles-stat">
              <span className="cycles-stat-num">{stats.encargo}</span>
              <span className="cycles-stat-label">Encargo</span>
            </div>
          </div>
        </div>

        <div className="cycles-toolbar">
          <div className="cycles-filters">
            {[
              { id: 'all', label: 'Todos' },
              { id: 'lavado', label: 'Lavado' },
              { id: 'secado', label: 'Secado' },
              { id: 'encargo_lavado', label: 'Encargo' },
            ].map((f) => (
              <button
                key={f.id}
                type="button"
                className={`cycles-chip ${typeFilter === f.id ? 'is-active' : ''}`}
                onClick={() => setTypeFilter(f.id)}
              >
                {f.label}
              </button>
            ))}
          </div>
          <button type="button" className="cycles-btn-primary" onClick={openCreate}>
            Nuevo ciclo
          </button>
        </div>

        {error && (
          <div className="cycles-error" role="alert">
            <span>{error}</span>
            <button type="button" onClick={() => setError(null)}>
              Cerrar
            </button>
          </div>
        )}

        {loading && <p className="cycles-loading">Cargando ciclos…</p>}

        {!loading && visibleCycles.length === 0 && (
          <div className="cycles-empty">
            <p>No hay ciclos{typeFilter !== 'all' ? ' de este tipo' : ''}.</p>
            <button type="button" className="cycles-btn-primary" onClick={openCreate}>
              Crear el primero
            </button>
          </div>
        )}

        {!loading && visibleCycles.length > 0 && (
          <div className="cycles-grid">
            {visibleCycles.map((cycle) => {
              const open = expandedId === cycle._id;
              return (
                <article
                  key={cycle._id}
                  className={`cycle-card cycle-card--${cycle.service_type} ${open ? 'is-open' : ''}`}
                >
                  <div className="cycle-card-top">
                    <div>
                      <span className="cycle-type">{TYPE_LABELS[cycle.service_type] || cycle.service_type}</span>
                      <h3>{cycle.name}</h3>
                      <p className="cycle-desc">{cycle.description}</p>
                    </div>
                    <span className={`cycle-status ${cycle.is_active ? 'on' : 'off'}`}>
                      {cycle.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>

                  <div className="cycle-meta">
                    <div>
                      <span className="meta-label">Duración</span>
                      <span className="meta-value">{cycle.duration_minutes} min</span>
                    </div>
                    <div>
                      <span className="meta-label">Precio</span>
                      <span className="meta-value">{formatPrice(cycle)}</span>
                    </div>
                    <div>
                      <span className="meta-label">Máquinas</span>
                      <span className="meta-value">
                        {(cycle.allowed_machines || []).length}
                      </span>
                    </div>
                  </div>

                  <div className="cycle-actions">
                    <button
                      type="button"
                      className="cycles-btn-ghost"
                      onClick={() => setExpandedId(open ? null : cycle._id)}
                    >
                      {open ? 'Ocultar' : 'Detalle'}
                    </button>
                    <button
                      type="button"
                      className="cycles-btn-edit"
                      onClick={() => openEdit(cycle)}
                    >
                      Editar
                    </button>
                    <button
                      type="button"
                      className="cycles-btn-danger"
                      onClick={() => handleDelete(cycle._id)}
                    >
                      Eliminar
                    </button>
                  </div>

                  {open && (
                    <div className="cycle-detail">
                      <h4>Máquinas permitidas</h4>
                      {(cycle.allowed_machines || []).length === 0 ? (
                        <p className="cycles-muted">Ninguna asignada</p>
                      ) : (
                        <ul className="cycle-machine-list">
                          {(cycle.allowed_machines || []).map((m) => (
                            <li key={m._id}>{machineLabel(m)}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}

        {!loading && totalPages > 1 && (
          <div className="cycles-pagination">
            <button
              type="button"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => p - 1)}
            >
              Anterior
            </button>
            <span>
              Página {currentPage} de {totalPages}
            </span>
            <button
              type="button"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
            >
              Siguiente
            </button>
          </div>
        )}
      </main>

      {showForm && (
        <div className="cycles-modal" role="dialog" aria-modal="true">
          <div className="cycles-modal-panel">
            <div className="cycles-modal-head">
              <div>
                <h2>{editingCycle ? 'Editar ciclo' : 'Nuevo ciclo'}</h2>
                <p>Paso {currentStep} de 2</p>
              </div>
              <button type="button" className="cycles-modal-close" onClick={resetForm}>
                Cerrar
              </button>
            </div>

            <div className="cycles-steps">
              <span className={currentStep >= 1 ? 'is-active' : ''} />
              <span className={currentStep >= 2 ? 'is-active' : ''} />
            </div>

            <form onSubmit={handleSubmit}>
              {currentStep === 1 && (
                <div className="cycles-form">
                  <label>
                    Nombre
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />
                  </label>
                  <label>
                    Descripción
                    <input
                      type="text"
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      required
                    />
                  </label>
                  <div className="cycles-form-row">
                    <label>
                      Tipo
                      <select
                        name="service_type"
                        value={formData.service_type}
                        onChange={handleInputChange}
                        required
                      >
                        <option value="lavado">Lavado</option>
                        <option value="secado">Secado</option>
                        <option value="encargo_lavado">Encargo lavado</option>
                      </select>
                    </label>
                    <label>
                      Duración (min)
                      <input
                        type="number"
                        name="duration_minutes"
                        min="1"
                        max="180"
                        value={formData.duration_minutes}
                        onChange={handleInputChange}
                        required
                      />
                    </label>
                  </div>

                  {formData.service_type === 'encargo_lavado' ? (
                    <div className="cycles-form-row">
                      <label>
                        Precio / kg
                        <input
                          type="number"
                          name="price_per_kg"
                          step="0.01"
                          min="0.01"
                          value={formData.price_per_kg}
                          onChange={handleInputChange}
                          required
                        />
                      </label>
                      <label>
                        Precio / kg tarjeta (opc.)
                        <input
                          type="number"
                          name="price_per_kg_tarjeta"
                          step="0.01"
                          min="0"
                          value={formData.price_per_kg_tarjeta}
                          onChange={handleInputChange}
                          placeholder="Mismo precio"
                        />
                      </label>
                    </div>
                  ) : (
                    <div className="cycles-form-row">
                      <label>
                        Precio
                        <input
                          type="number"
                          name="price"
                          step="0.01"
                          min="0.01"
                          value={formData.price}
                          onChange={handleInputChange}
                          required
                        />
                      </label>
                      <label>
                        Precio tarjeta (opc.)
                        <input
                          type="number"
                          name="price_tarjeta"
                          step="0.01"
                          min="0"
                          value={formData.price_tarjeta}
                          onChange={handleInputChange}
                          placeholder="Mismo precio"
                        />
                      </label>
                    </div>
                  )}

                  <label className="cycles-check">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) =>
                        setFormData((prev) => ({ ...prev, is_active: e.target.checked }))
                      }
                    />
                    Ciclo activo
                  </label>

                  <div className="cycles-form-actions">
                    <button type="button" className="cycles-btn-ghost" onClick={resetForm}>
                      Cancelar
                    </button>
                    <button
                      type="button"
                      className="cycles-btn-primary"
                      onClick={() => {
                        if (validateStep1()) setCurrentStep(2);
                      }}
                    >
                      Siguiente
                    </button>
                  </div>
                </div>
              )}

              {currentStep === 2 && (
                <div className="cycles-form">
                  <p className="cycles-help">
                    Elige las máquinas donde puede usarse este ciclo
                    {formData.service_type === 'lavado' && ' (lavadoras)'}.
                    {formData.service_type === 'secado' && ' (secadoras)'}.
                    {formData.service_type === 'encargo_lavado' && ' (lavadoras y secadoras)'}.
                  </p>

                  <div className="cycles-machines">
                    {filteredWashers.length > 0 && (
                      <section>
                        <h3>Lavadoras</h3>
                        <div className="cycles-machine-checks">
                          {filteredWashers.map((w) => (
                            <label key={w._id} className="cycles-machine-item">
                              <input
                                type="checkbox"
                                value={`${w._id}-${w.numero}`}
                                checked={formData.allowed_machines.some((m) => m._id === w._id)}
                                onChange={handleMachineSelectionChange}
                              />
                              <span>
                                #{w.numero} · {w.marca} · {w.capacidad} kg
                              </span>
                            </label>
                          ))}
                        </div>
                      </section>
                    )}
                    {filteredDryers.length > 0 && (
                      <section>
                        <h3>Secadoras</h3>
                        <div className="cycles-machine-checks">
                          {filteredDryers.map((d) => (
                            <label key={d._id} className="cycles-machine-item">
                              <input
                                type="checkbox"
                                value={`${d._id}-${d.numero}`}
                                checked={formData.allowed_machines.some((m) => m._id === d._id)}
                                onChange={handleMachineSelectionChange}
                              />
                              <span>
                                #{d.numero} · {d.marca} · {d.capacidad} kg
                              </span>
                            </label>
                          ))}
                        </div>
                      </section>
                    )}
                    {filteredWashers.length === 0 && filteredDryers.length === 0 && (
                      <p className="cycles-muted">No hay máquinas activas para este tipo.</p>
                    )}
                  </div>

                  <div className="cycles-form-actions">
                    <button
                      type="button"
                      className="cycles-btn-ghost"
                      onClick={() => setCurrentStep(1)}
                    >
                      Anterior
                    </button>
                    <button type="submit" className="cycles-btn-primary" disabled={saving}>
                      {saving
                        ? 'Guardando…'
                        : editingCycle
                          ? 'Guardar cambios'
                          : 'Crear ciclo'}
                    </button>
                  </div>
                </div>
              )}
            </form>
          </div>
        </div>
      )}

      <ToastContainer
        position="bottom-right"
        autoClose={4000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        pauseOnHover
      />
    </div>
  );
};

export default ServicesPages;
