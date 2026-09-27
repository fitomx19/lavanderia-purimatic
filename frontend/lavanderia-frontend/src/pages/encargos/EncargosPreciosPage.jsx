import React, { useEffect, useState } from 'react';
import Header from '../../components/layout/Header';
import { getEncargoSettings, saveEncargoSettings } from '../../services/encargoService';
import './EncargosPage.css';

const newId = () => `svc-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

const EncargosPreciosPage = () => {
  const [pricePerKg, setPricePerKg] = useState(25);
  const [pricePerKgTarjeta, setPricePerKgTarjeta] = useState('');
  const [servicios, setServicios] = useState([]);
  const [printBagLabel, setPrintBagLabel] = useState(true);
  const [printNotes, setPrintNotes] = useState(true);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const showMessage = (text, ok = true) => setMessage({ text, ok });

  const load = async () => {
    const res = await getEncargoSettings();
    const data = res.data || {};
    setPricePerKg(Number(data.price_per_kg) || 25);
    setPricePerKgTarjeta(
      data.price_per_kg_tarjeta != null && data.price_per_kg_tarjeta !== ''
        ? Number(data.price_per_kg_tarjeta)
        : ''
    );
    setServicios(Array.isArray(data.servicios) ? data.servicios : []);
    setPrintBagLabel(data.print_bag_label !== false);
    setPrintNotes(data.print_notes !== false);
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await load();
      } catch (err) {
        showMessage(err.message || err.response?.data?.message || 'Error al cargar', false);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const updateRow = (idx, patch) => {
    setServicios((prev) => prev.map((row, i) => (i === idx ? { ...row, ...patch } : row)));
  };

  const addRow = () => {
    setServicios((prev) => [
      ...prev,
      { id: newId(), name: '', size: '', price: 0, price_tarjeta: '' },
    ]);
  };

  const removeRow = (idx) => {
    setServicios((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSave = async () => {
    try {
      setBusy(true);
      const payload = {
        price_per_kg: Number(pricePerKg) || 0,
        price_per_kg_tarjeta:
          pricePerKgTarjeta === '' || pricePerKgTarjeta == null
            ? null
            : Number(pricePerKgTarjeta),
        print_bag_label: Boolean(printBagLabel),
        print_notes: Boolean(printNotes),
        servicios: servicios
          .filter((s) => String(s.name || '').trim())
          .map((s) => ({
            id: s.id || newId(),
            name: String(s.name).trim(),
            size: String(s.size || '').trim(),
            price: Number(s.price) || 0,
            price_tarjeta:
              s.price_tarjeta === '' || s.price_tarjeta == null
                ? null
                : Number(s.price_tarjeta),
          })),
      };
      await saveEncargoSettings(payload);
      showMessage('Precios y servicios guardados');
      await load();
    } catch (err) {
      showMessage(err.message || 'Error al guardar', false);
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return (
      <div className="encargo-layout">
        <Header />
        <main className="encargo-content">
          <p>Cargando…</p>
        </main>
      </div>
    );
  }

  return (
    <div className="encargo-layout">
      <Header />
      <main className="encargo-content">
        <h1>Precios de encargos</h1>
        <p className="encargo-help">
          Configura el precio por kilo, precios con tarjeta recargable, el catálogo de servicios y
          las opciones de impresión.
        </p>

        {message && (
          <div className={`encargo-msg ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>
        )}

        <section className="encargo-card">
          <h2>Precio por kg</h2>
          <label>
            Precio normal ($ / kg)
            <input
              type="number"
              min="0"
              step="0.5"
              value={pricePerKg}
              onChange={(e) => setPricePerKg(e.target.value)}
            />
          </label>
          <label>
            Precio con tarjeta ($ / kg, opcional)
            <input
              type="number"
              min="0"
              step="0.5"
              value={pricePerKgTarjeta}
              onChange={(e) => setPricePerKgTarjeta(e.target.value)}
              placeholder="Vacío = mismo precio"
            />
          </label>
        </section>

        <section className="encargo-card">
          <div className="encargo-card-head">
            <h2>Servicios</h2>
            <button type="button" className="encargo-secondary" onClick={addRow}>
              Agregar
            </button>
          </div>
          <div className="encargo-servicios-admin">
            {servicios.length === 0 && <p className="encargo-muted">Sin servicios. Agrega uno.</p>}
            {servicios.map((row, idx) => (
              <div key={row.id || idx} className="encargo-servicio-admin-row">
                <input
                  placeholder="Nombre"
                  value={row.name || ''}
                  onChange={(e) => updateRow(idx, { name: e.target.value })}
                />
                <input
                  placeholder="Tamaño (opc.)"
                  value={row.size || ''}
                  onChange={(e) => updateRow(idx, { size: e.target.value })}
                />
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  placeholder="Precio"
                  value={row.price}
                  onChange={(e) => updateRow(idx, { price: e.target.value })}
                />
                <input
                  type="number"
                  min="0"
                  step="0.5"
                  placeholder="Precio tarjeta"
                  value={row.price_tarjeta ?? ''}
                  onChange={(e) => updateRow(idx, { price_tarjeta: e.target.value })}
                />
                <button type="button" className="encargo-danger" onClick={() => removeRow(idx)}>
                  Quitar
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="encargo-card">
          <h2>Impresión</h2>
          <label className="encargo-check">
            <input
              type="checkbox"
              checked={printBagLabel}
              onChange={(e) => setPrintBagLabel(e.target.checked)}
            />
            Imprimir etiqueta interna de bolsa (copia tienda)
          </label>
          <label className="encargo-check">
            <input
              type="checkbox"
              checked={printNotes}
              onChange={(e) => setPrintNotes(e.target.checked)}
            />
            Imprimir notas en el ticket del cliente
          </label>
        </section>

        <button type="button" className="encargo-primary" disabled={busy} onClick={handleSave}>
          {busy ? 'Guardando…' : 'Guardar configuración'}
        </button>
      </main>
    </div>
  );
};

export default EncargosPreciosPage;
