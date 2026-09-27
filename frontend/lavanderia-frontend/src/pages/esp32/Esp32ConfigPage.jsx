import React, { useEffect, useState } from 'react';
import Header from '../../components/layout/Header';
import {
  listEsp32Configs,
  saveEsp32Config,
  updateEsp32Config,
  deactivateEsp32Config,
  testEsp32,
} from '../../services/esp32ConfigService';
import './Esp32ConfigPage.css';

const emptyForm = {
  name: '',
  esp32_url: 'http://192.168.0.110/laundry-update',
};

const Esp32ConfigPage = () => {
  const [configs, setConfigs] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [testIdByBoard, setTestIdByBoard] = useState({});
  const [newMachineByBoard, setNewMachineByBoard] = useState({});

  const showMessage = (text, ok = true) => {
    setMessage({ text, ok });
  };

  const fetchConfigs = async () => {
    try {
      const result = await listEsp32Configs(true);
      const rows = result.data || [];
      setConfigs(rows);
      const defaults = {};
      rows.forEach((item) => {
        const ids = item.esp32_ids || [];
        defaults[item._id] = ids[0] || '';
      });
      setTestIdByBoard((prev) => ({ ...defaults, ...prev }));
    } catch (err) {
      showMessage(err.message || 'No se pudieron cargar las placas', false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleCreateBoard = async (e) => {
    e.preventDefault();
    if (!form.esp32_url.trim()) {
      showMessage('Indica la URL de la placa (ej. http://192.168.0.110/laundry-update)', false);
      return;
    }
    try {
      setBusyId('save');
      const urlNorm = form.esp32_url.trim().replace(/\/$/, '').toLowerCase();
      const already = configs.some(
        (c) => (c.esp32_url || '').trim().replace(/\/$/, '').toLowerCase() === urlNorm
      );
      await saveEsp32Config({
        name: form.name.trim() || 'Placa nueva',
        esp32_url: form.esp32_url.trim(),
        esp32_ids: [],
        is_active: true,
      });
      setForm(emptyForm);
      showMessage(
        already
          ? 'Esa URL ya existía: se unificó en una sola placa. Agrega máquinas abajo.'
          : 'Placa creada. Ahora agrega sus máquinas (esp32_id) abajo.'
      );
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo crear la placa', false);
    } finally {
      setBusyId(null);
    }
  };

  const persistBoard = async (board, overrides = {}) => {
    const merged = { ...board, ...overrides };
    const ids = Array.isArray(merged.esp32_ids) ? merged.esp32_ids : [];
    await updateEsp32Config(merged._id, {
      name: merged.name || '',
      esp32_url: merged.esp32_url,
      esp32_ids: ids,
      is_active: merged.is_active,
    });
  };

  const handleSaveMeta = async (board, overrides = {}) => {
    try {
      setBusyId(board._id + '-save');
      await persistBoard(board, overrides);
      showMessage('Placa actualizada');
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo actualizar', false);
    } finally {
      setBusyId(null);
    }
  };

  const handleAddMachine = async (board) => {
    const raw = (newMachineByBoard[board._id] || '').trim();
    if (!raw) {
      showMessage('Escribe el esp32_id de la máquina (ej. W002)', false);
      return;
    }
    const ids = board.esp32_ids || [];
    if (ids.includes(raw)) {
      showMessage(`La máquina ${raw} ya está en esta placa`, false);
      return;
    }
    try {
      setBusyId(board._id + '-add');
      await persistBoard(board, { esp32_ids: [...ids, raw] });
      setNewMachineByBoard((prev) => ({ ...prev, [board._id]: '' }));
      setTestIdByBoard((prev) => ({ ...prev, [board._id]: raw }));
      showMessage(`Máquina ${raw} agregada. Usa el mismo ID en Equipo.`);
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo agregar la máquina', false);
    } finally {
      setBusyId(null);
    }
  };

  const handleRemoveMachine = async (board, machineId) => {
    if (!window.confirm(`¿Quitar la máquina ${machineId} de esta placa?`)) return;
    try {
      setBusyId(board._id + '-rm-' + machineId);
      const next = (board.esp32_ids || []).filter((id) => id !== machineId);
      await persistBoard(board, { esp32_ids: next });
      showMessage(`Máquina ${machineId} quitada`);
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo quitar la máquina', false);
    } finally {
      setBusyId(null);
    }
  };

  const handleTest = async (boardId, action) => {
    const relayId = testIdByBoard[boardId];
    if (!relayId) {
      showMessage('Agrega al menos una máquina y elígela para probar', false);
      return;
    }
    try {
      setBusyId(boardId + action);
      const result = await testEsp32(boardId, action, relayId);
      showMessage(result.message || (action === 'start' ? 'Encendido enviado' : 'Apagado enviado'));
    } catch (err) {
      showMessage(
        err.message || 'La placa no respondió. Revisa IP, WiFi y que PurimaticNFC esté abierto.',
        false
      );
    } finally {
      setBusyId(null);
    }
  };

  const handleDeactivate = async (boardId, label) => {
    if (!window.confirm(`¿Desactivar la placa ${label}?`)) return;
    try {
      setBusyId(boardId + '-off');
      await deactivateEsp32Config(boardId);
      showMessage('Placa desactivada');
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo desactivar', false);
    } finally {
      setBusyId(null);
    }
  };

  const updateLocal = (boardId, field, value) => {
    setConfigs((prev) =>
      prev.map((item) => (item._id === boardId ? { ...item, [field]: value } : item))
    );
  };

  return (
    <div className="esp32-layout">
      <Header />
      <div className="esp32-content">
        <h1>Placas ESP32</h1>
        <p className="esp32-help">
          <strong>Una IP = una sola placa.</strong> Ejemplo:{' '}
          <code>http://192.168.0.110/laundry-update</code> controla varias máquinas (
          <code>W001</code>, <code>W002</code>…). Si ves varias tarjetas con la misma URL, al
          recargar se unifican solas.
          <br />
          <strong>1)</strong> Crea la placa (nombre + URL).
          <br />
          <strong>2)</strong> Dentro de esa tarjeta, agrega cada máquina con su{' '}
          <code>esp32_id</code> (debe coincidir con Equipo).
          <br />
          <strong>3)</strong> Otra IP distinta = otra placa. Encender/Apagar prueba un relé;
          PurimaticNFC en puerto 5001.
        </p>

        <section className="esp32-create-section">
          <h2>Agregar placa</h2>
          <form className="esp32-form" onSubmit={handleCreateBoard}>
            <input
              name="name"
              placeholder="Nombre (ej. Placa lavadoras 1)"
              value={form.name}
              onChange={handleChange}
            />
            <input
              name="esp32_url"
              placeholder="http://192.168.0.110/laundry-update"
              value={form.esp32_url}
              onChange={handleChange}
              required
            />
            <button className="esp32-save-btn" type="submit" disabled={busyId === 'save'}>
              Crear placa
            </button>
          </form>
        </section>

        {message && (
          <div className={`esp32-message ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>
        )}

        {loading ? (
          <p>Cargando placas...</p>
        ) : configs.length === 0 ? (
          <p className="esp32-empty">Todavía no hay placas. Crea la primera arriba.</p>
        ) : (
          <div className="esp32-cards">
            {configs.map((board) => {
              const ids = board.esp32_ids || [];
              const label = board.name || board.esp32_url || board._id;
              return (
                <article key={board._id} className="esp32-card">
                  <header className="esp32-card-header">
                    <div>
                      <input
                        className="esp32-name-input"
                        value={board.name || ''}
                        placeholder="Nombre de la placa"
                        onChange={(e) => updateLocal(board._id, 'name', e.target.value)}
                        onBlur={(e) => handleSaveMeta(board, { name: e.target.value })}
                      />
                      <span className={`esp32-badge ${board.is_active ? 'on' : 'off'}`}>
                        {board.is_active ? 'activa' : 'inactiva'}
                      </span>
                    </div>
                  </header>

                  <label className="esp32-field-label">
                    URL de la placa
                    <input
                      className="esp32-url-input"
                      value={board.esp32_url || ''}
                      onChange={(e) => updateLocal(board._id, 'esp32_url', e.target.value)}
                      onBlur={(e) => handleSaveMeta(board, { esp32_url: e.target.value })}
                    />
                  </label>

                  <div className="esp32-machines">
                    <h3>Máquinas de esta placa</h3>
                    {ids.length === 0 ? (
                      <p className="esp32-machines-empty">
                        Aún no hay máquinas. Agrega la primera (ej. W001).
                      </p>
                    ) : (
                      <ul className="esp32-machine-list">
                        {ids.map((id) => (
                          <li key={id}>
                            <span className="esp32-chip">{id}</span>
                            <button
                              type="button"
                              className="esp32-rm-btn"
                              disabled={!!busyId}
                              onClick={() => handleRemoveMachine(board, id)}
                            >
                              Quitar
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}

                    <div className="esp32-add-machine">
                      <input
                        placeholder="esp32_id (ej. W002)"
                        value={newMachineByBoard[board._id] || ''}
                        onChange={(e) =>
                          setNewMachineByBoard((prev) => ({
                            ...prev,
                            [board._id]: e.target.value,
                          }))
                        }
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault();
                            handleAddMachine(board);
                          }
                        }}
                      />
                      <button
                        type="button"
                        className="esp32-save-btn"
                        disabled={!!busyId}
                        onClick={() => handleAddMachine(board)}
                      >
                        Agregar máquina
                      </button>
                    </div>
                  </div>

                  <div className="esp32-actions">
                    <select
                      className="esp32-test-select"
                      value={testIdByBoard[board._id] || ids[0] || ''}
                      onChange={(e) =>
                        setTestIdByBoard((prev) => ({
                          ...prev,
                          [board._id]: e.target.value,
                        }))
                      }
                      disabled={ids.length === 0}
                    >
                      {ids.length === 0 && <option value="">Sin máquinas</option>}
                      {ids.map((id) => (
                        <option key={id} value={id}>
                          {id}
                        </option>
                      ))}
                    </select>
                    <button
                      className="esp32-start-btn"
                      type="button"
                      disabled={!!busyId || ids.length === 0}
                      onClick={() => handleTest(board._id, 'start')}
                    >
                      Encender
                    </button>
                    <button
                      className="esp32-stop-btn"
                      type="button"
                      disabled={!!busyId || ids.length === 0}
                      onClick={() => handleTest(board._id, 'stop')}
                    >
                      Apagar
                    </button>
                    {board.is_active && (
                      <button
                        className="esp32-off-btn"
                        type="button"
                        disabled={!!busyId}
                        onClick={() => handleDeactivate(board._id, label)}
                      >
                        Desactivar placa
                      </button>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default Esp32ConfigPage;
