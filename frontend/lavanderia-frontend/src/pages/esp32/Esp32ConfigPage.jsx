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
  esp32_id: '',
  esp32_url: 'http://192.168.1.76/laundry-update',
};

const Esp32ConfigPage = () => {
  const [configs, setConfigs] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [loading, setLoading] = useState(true);

  const showMessage = (text, ok = true) => {
    setMessage({ text, ok });
  };

  const fetchConfigs = async () => {
    try {
      const result = await listEsp32Configs(true);
      setConfigs(result.data || []);
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

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setBusyId('save');
      await saveEsp32Config({
        esp32_id: form.esp32_id.trim(),
        esp32_url: form.esp32_url.trim(),
        is_active: true,
      });
      setForm(emptyForm);
      showMessage('Placa guardada. Usa el mismo esp32_id en Equipo (lavadora/secadora).');
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo guardar', false);
    } finally {
      setBusyId(null);
    }
  };

  const handleUrlSave = async (item) => {
    try {
      setBusyId(item.esp32_id + '-url');
      await updateEsp32Config(item.esp32_id, {
        esp32_url: item.esp32_url,
        is_active: item.is_active,
      });
      showMessage(`URL de ${item.esp32_id} actualizada`);
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo actualizar la URL', false);
    } finally {
      setBusyId(null);
    }
  };

  const handleTest = async (esp32Id, action) => {
    try {
      setBusyId(esp32Id + action);
      const result = await testEsp32(esp32Id, action);
      showMessage(result.message || (action === 'start' ? 'Encendido enviado' : 'Apagado enviado'));
    } catch (err) {
      showMessage(err.message || 'La placa no respondió. Revisa IP, WiFi y que PurimaticNFC esté abierto.', false);
    } finally {
      setBusyId(null);
    }
  };

  const handleDeactivate = async (esp32Id) => {
    if (!window.confirm(`¿Desactivar la placa ${esp32Id}?`)) return;
    try {
      setBusyId(esp32Id + '-off');
      await deactivateEsp32Config(esp32Id);
      showMessage(`Placa ${esp32Id} desactivada`);
      fetchConfigs();
    } catch (err) {
      showMessage(err.message || 'No se pudo desactivar', false);
    } finally {
      setBusyId(null);
    }
  };

  const updateLocalUrl = (esp32Id, value) => {
    setConfigs((prev) =>
      prev.map((item) => (item.esp32_id === esp32Id ? { ...item, esp32_url: value } : item))
    );
  };

  return (
    <div className="esp32-layout">
      <Header />
      <div className="esp32-content">
        <h1>Placas ESP32</h1>
        <p className="esp32-help">
          1) Conéctate a la WiFi de la placa, contraseña <strong>setup123456</strong>, abre{' '}
          <strong>http://192.168.4.1</strong> y carga el WiFi de la tienda.
          2) Anota la IP (ejemplo 192.168.1.76) y regístrala aquí como{' '}
          <code>http://IP/laundry-update</code>.
          3) El <strong>esp32_id</strong> debe ser el mismo que en Equipo.
          4) Encender/Apagar prueba el relé sin hacer una venta. PurimaticNFC debe estar en el puerto 5001.
        </p>

        <form className="esp32-form" onSubmit={handleSave}>
          <input
            name="esp32_id"
            placeholder="esp32_id (ej. 76 o W002)"
            value={form.esp32_id}
            onChange={handleChange}
            required
          />
          <input
            name="esp32_url"
            placeholder="http://192.168.1.76/laundry-update"
            value={form.esp32_url}
            onChange={handleChange}
            required
          />
          <button className="esp32-save-btn" type="submit" disabled={busyId === 'save'}>
            Guardar placa
          </button>
        </form>

        {message && (
          <div className={`esp32-message ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>
        )}

        {loading ? (
          <p>Cargando placas...</p>
        ) : (
          <table className="esp32-table">
            <thead>
              <tr>
                <th>esp32_id</th>
                <th>URL</th>
                <th>Estado</th>
                <th>Prueba / acciones</th>
              </tr>
            </thead>
            <tbody>
              {configs.length === 0 && (
                <tr>
                  <td colSpan="4">Todavía no hay placas. Agrega la primera arriba.</td>
                </tr>
              )}
              {configs.map((item) => (
                <tr key={item.esp32_id}>
                  <td><strong>{item.esp32_id}</strong></td>
                  <td>
                    <input
                      className="esp32-url-input"
                      value={item.esp32_url || ''}
                      onChange={(e) => updateLocalUrl(item.esp32_id, e.target.value)}
                      onBlur={() => handleUrlSave(item)}
                    />
                  </td>
                  <td>
                    <span className={`esp32-badge ${item.is_active ? 'on' : 'off'}`}>
                      {item.is_active ? 'activa' : 'inactiva'}
                    </span>
                  </td>
                  <td>
                    <div className="esp32-actions">
                      <button
                        className="esp32-start-btn"
                        type="button"
                        disabled={!!busyId}
                        onClick={() => handleTest(item.esp32_id, 'start')}
                      >
                        Encender
                      </button>
                      <button
                        className="esp32-stop-btn"
                        type="button"
                        disabled={!!busyId}
                        onClick={() => handleTest(item.esp32_id, 'stop')}
                      >
                        Apagar
                      </button>
                      {item.is_active && (
                        <button
                          className="esp32-off-btn"
                          type="button"
                          disabled={!!busyId}
                          onClick={() => handleDeactivate(item.esp32_id)}
                        >
                          Desactivar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Esp32ConfigPage;
