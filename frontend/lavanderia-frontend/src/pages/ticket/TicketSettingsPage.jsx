import React, { useEffect, useState } from 'react';
import Header from '../../components/layout/Header';
import {
  getTicketSettings,
  saveTicketSettings,
  listTicketPrinters,
  testTicketPrint,
} from '../../services/ticketSettingsService';
import './TicketSettingsPage.css';

const DAY_ROWS = [
  { day: 'lun', label: 'Lunes' },
  { day: 'mar', label: 'Martes' },
  { day: 'mie', label: 'Miércoles' },
  { day: 'jue', label: 'Jueves' },
  { day: 'vie', label: 'Viernes' },
  { day: 'sab', label: 'Sábado' },
  { day: 'dom', label: 'Domingo' },
];

const defaultHours = () =>
  DAY_ROWS.map(({ day }) => ({
    day,
    open: day === 'sab' || day === 'dom' ? '08:00' : '07:00',
    close: day === 'sab' || day === 'dom' ? '15:00' : '22:00',
    closed: false,
  }));

const emptyForm = {
  store_name: '',
  address: '',
  wifi_ssid: '',
  wifi_password: '',
  promo_mes: '',
  footer_thanks: 'Gracias por tu compra',
  printer_name: '',
  hours: defaultHours(),
};

const TicketSettingsPage = () => {
  const [form, setForm] = useState(emptyForm);
  const [logoPreview, setLogoPreview] = useState(null);
  const [logoBase64, setLogoBase64] = useState(null);
  const [logoMime, setLogoMime] = useState(null);
  const [clearLogo, setClearLogo] = useState(false);
  const [hasLogo, setHasLogo] = useState(false);
  const [printers, setPrinters] = useState([]);
  const [defaultPrinter, setDefaultPrinter] = useState('');
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const showMessage = (text, ok = true) => setMessage({ text, ok });

  const normalizeHours = (hours) => {
    const byDay = {};
    (hours || []).forEach((h) => {
      if (h?.day) byDay[h.day] = h;
    });
    return DAY_ROWS.map(({ day }) => {
      const existing = byDay[day];
      if (existing) {
        return {
          day,
          open: existing.open || '07:00',
          close: existing.close || '22:00',
          closed: !!existing.closed,
        };
      }
      return defaultHours().find((h) => h.day === day);
    });
  };

  const load = async () => {
    try {
      setLoading(true);
      const [settingsRes, printersRes] = await Promise.all([
        getTicketSettings(true),
        listTicketPrinters().catch(() => ({ data: { printers: [], default: '' } })),
      ]);
      const data = settingsRes.data || {};
      setForm({
        store_name: data.store_name || '',
        address: data.address || '',
        wifi_ssid: data.wifi_ssid || '',
        wifi_password: data.wifi_password || '',
        promo_mes: data.promo_mes || '',
        footer_thanks: data.footer_thanks || 'Gracias por tu compra',
        printer_name: data.printer_name || '',
        hours: normalizeHours(data.hours),
      });
      setHasLogo(!!data.has_logo);
      if (data.logo_base64) {
        const mime = data.logo_mime || 'image/png';
        setLogoPreview(`data:${mime};base64,${data.logo_base64}`);
      } else {
        setLogoPreview(null);
      }
      setLogoBase64(null);
      setClearLogo(false);
      setPrinters(printersRes?.data?.printers || []);
      setDefaultPrinter(printersRes?.data?.default || '');
    } catch (err) {
      showMessage(err.message || 'No se pudo cargar la configuración', false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleHourChange = (day, field, value) => {
    setForm((prev) => ({
      ...prev,
      hours: prev.hours.map((h) => (h.day === day ? { ...h, [field]: value } : h)),
    }));
  };

  const handleLogo = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      showMessage('El logo debe ser una imagen (PNG o JPEG)', false);
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || '');
      setLogoPreview(result);
      setLogoBase64(result);
      setLogoMime(file.type);
      setClearLogo(false);
      setHasLogo(true);
    };
    reader.readAsDataURL(file);
  };

  const handleClearLogo = () => {
    setLogoPreview(null);
    setLogoBase64(null);
    setLogoMime(null);
    setClearLogo(true);
    setHasLogo(false);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setBusy(true);
      const payload = {
        store_name: form.store_name.trim(),
        address: form.address.trim(),
        wifi_ssid: form.wifi_ssid.trim(),
        wifi_password: form.wifi_password.trim(),
        promo_mes: form.promo_mes.trim(),
        footer_thanks: form.footer_thanks.trim() || 'Gracias por tu compra',
        printer_name: form.printer_name.trim(),
        hours: form.hours,
        clear_logo: clearLogo,
      };
      if (logoBase64 && !clearLogo) {
        payload.logo_base64 = logoBase64;
        payload.logo_mime = logoMime || 'image/png';
      }
      await saveTicketSettings(payload);
      showMessage('Configuración de ticket guardada');
      await load();
    } catch (err) {
      showMessage(err.message || 'No se pudo guardar', false);
    } finally {
      setBusy(false);
    }
  };

  const handleTestPrint = async () => {
    try {
      setBusy(true);
      const result = await testTicketPrint();
      showMessage(result.message || 'Ticket de prueba enviado');
    } catch (err) {
      showMessage(err.message || 'No se pudo imprimir. Revisa la impresora.', false);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="ticket-layout">
      <Header />
      <div className="ticket-content">
        <h1>Configuración de ticket</h1>
        <p className="ticket-help">
          Todo lo de esta página aparece en el ticket al cobrar. Logo en PNG o JPEG (mejor
          contraste). Impresora vacía = predeterminada de Windows
          {defaultPrinter ? ` (${defaultPrinter})` : ''}.
        </p>

        {message && (
          <div className={`ticket-message ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>
        )}

        {loading ? (
          <p>Cargando…</p>
        ) : (
          <form className="ticket-form" onSubmit={handleSave}>
            <label>
              Nombre de la tienda
              <input
                name="store_name"
                value={form.store_name}
                onChange={handleChange}
                placeholder="Lavandería Purimatic"
              />
            </label>

            <label>
              Dirección
              <textarea
                name="address"
                value={form.address}
                onChange={handleChange}
                rows={2}
                placeholder="Calle, número, colonia, ciudad"
              />
            </label>

            <label>
              Nombre de la red WiFi (SSID)
              <input
                name="wifi_ssid"
                value={form.wifi_ssid}
                onChange={handleChange}
                placeholder="Purimatic_Clientes"
              />
            </label>

            <label>
              Contraseña WiFi
              <input
                name="wifi_password"
                value={form.wifi_password}
                onChange={handleChange}
                placeholder="Clave WiFi"
              />
            </label>

            <label>
              Promoción del mes
              <textarea
                name="promo_mes"
                value={form.promo_mes}
                onChange={handleChange}
                rows={3}
                placeholder="Texto de promoción"
              />
            </label>

            <label>
              Mensaje final del ticket
              <input
                name="footer_thanks"
                value={form.footer_thanks}
                onChange={handleChange}
                placeholder="Gracias por tu compra"
              />
            </label>

            <label>
              Impresora (opcional)
              <select name="printer_name" value={form.printer_name} onChange={handleChange}>
                <option value="">Predeterminada de Windows</option>
                {printers.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </label>

            <div className="ticket-hours-block">
              <span className="ticket-hours-title">Horario (Lunes a Domingo)</span>
              <div className="ticket-hours-grid">
                {DAY_ROWS.map(({ day, label }) => {
                  const row = form.hours.find((h) => h.day === day) || {
                    day,
                    open: '07:00',
                    close: '22:00',
                    closed: false,
                  };
                  return (
                    <div key={day} className="ticket-hours-row">
                      <span className="ticket-day-label">{label}</span>
                      <label className="ticket-closed-check">
                        <input
                          type="checkbox"
                          checked={!!row.closed}
                          onChange={(e) => handleHourChange(day, 'closed', e.target.checked)}
                        />
                        Cerrado
                      </label>
                      <input
                        type="time"
                        value={row.open}
                        disabled={row.closed}
                        onChange={(e) => handleHourChange(day, 'open', e.target.value)}
                      />
                      <span>a</span>
                      <input
                        type="time"
                        value={row.close}
                        disabled={row.closed}
                        onChange={(e) => handleHourChange(day, 'close', e.target.value)}
                      />
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="ticket-logo-block">
              <span>Logo de la tienda</span>
              <input type="file" accept="image/png,image/jpeg,image/webp" onChange={handleLogo} />
              {logoPreview && (
                <div className="ticket-logo-preview">
                  <img src={logoPreview} alt="Logo" />
                  <button type="button" className="ticket-clear-logo" onClick={handleClearLogo}>
                    Quitar logo
                  </button>
                </div>
              )}
              {!logoPreview && hasLogo && <p>Hay un logo guardado.</p>}
            </div>

            <div className="ticket-actions">
              <button type="submit" className="ticket-save-btn" disabled={busy}>
                Guardar
              </button>
              <button
                type="button"
                className="ticket-test-btn"
                disabled={busy}
                onClick={handleTestPrint}
              >
                Imprimir prueba
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default TicketSettingsPage;
