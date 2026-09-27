import React, { useEffect, useState } from 'react';
import Header from '../../components/layout/Header';
import {
  getCardBenefitsSettings,
  saveCardBenefitsSettings,
} from '../../services/cardBenefitsService';
import '../ticket/TicketSettingsPage.css';

const emptyForm = {
  reload_bonus_enabled: false,
  reload_promo_mode: 'paquetes_y_libre',
  reload_packages: [],
  reload_bonus_percent: 0,
  pay_discount_enabled: false,
  pay_discount_mode: 'elegir_pct_o_precio',
  pay_discount_style: 'porcentaje',
  pay_discount_percent: 0,
};

const CardBenefitsPage = () => {
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const showMessage = (text, ok = true) => setMessage({ text, ok });

  const load = async () => {
    const res = await getCardBenefitsSettings();
    const data = res.data || {};
    setForm({
      reload_bonus_enabled: !!data.reload_bonus_enabled,
      reload_promo_mode: data.reload_promo_mode || 'paquetes_y_libre',
      reload_packages: Array.isArray(data.reload_packages) ? data.reload_packages : [],
      reload_bonus_percent: Number(data.reload_bonus_percent) || 0,
      pay_discount_enabled: !!data.pay_discount_enabled,
      pay_discount_mode: data.pay_discount_mode || 'elegir_pct_o_precio',
      pay_discount_style: data.pay_discount_style || 'porcentaje',
      pay_discount_percent: Number(data.pay_discount_percent) || 0,
    });
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await load();
      } catch (err) {
        showMessage(err.message || 'Error al cargar', false);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const updatePkg = (idx, patch) => {
    setForm((prev) => ({
      ...prev,
      reload_packages: prev.reload_packages.map((p, i) => (i === idx ? { ...p, ...patch } : p)),
    }));
  };

  const addPkg = () => {
    setForm((prev) => ({
      ...prev,
      reload_packages: [
        ...prev.reload_packages,
        { pay_amount: 500, credit_amount: 700, label: '' },
      ],
    }));
  };

  const removePkg = (idx) => {
    setForm((prev) => ({
      ...prev,
      reload_packages: prev.reload_packages.filter((_, i) => i !== idx),
    }));
  };

  const handleSave = async () => {
    try {
      setBusy(true);
      const payload = {
        ...form,
        reload_bonus_percent: Number(form.reload_bonus_percent) || 0,
        pay_discount_percent: Number(form.pay_discount_percent) || 0,
        reload_packages: (form.reload_packages || []).map((p) => ({
          pay_amount: Number(p.pay_amount) || 0,
          credit_amount: Number(p.credit_amount) || 0,
          label: String(p.label || '').trim(),
        })),
      };
      await saveCardBenefitsSettings(payload);
      showMessage('Beneficios de tarjeta guardados');
      await load();
    } catch (err) {
      showMessage(err.message || err.errors || 'Error al guardar', false);
    } finally {
      setBusy(false);
    }
  };

  const showPackages =
    form.reload_bonus_enabled &&
    (form.reload_promo_mode === 'paquetes' || form.reload_promo_mode === 'paquetes_y_libre');
  const showPercentBonus =
    form.reload_bonus_enabled && form.reload_promo_mode === 'porcentaje_y_libre';
  const showStylePicker =
    form.pay_discount_enabled && form.pay_discount_mode === 'elegir_pct_o_precio';
  const effectiveStyle =
    form.pay_discount_mode === 'solo_porcentaje'
      ? 'porcentaje'
      : form.pay_discount_mode === 'solo_precio_ciclo'
        ? 'precio_ciclo'
        : form.pay_discount_style;
  const showPercentPay =
    form.pay_discount_enabled &&
    (form.pay_discount_mode === 'solo_porcentaje' ||
      (form.pay_discount_mode === 'elegir_pct_o_precio' && form.pay_discount_style === 'porcentaje'));

  if (loading) {
    return (
      <div className="ticket-layout">
        <Header />
        <main className="ticket-content">
          <p>Cargando…</p>
        </main>
      </div>
    );
  }

  return (
    <div className="ticket-layout">
      <Header />
      <main className="ticket-content">
        <h1>Beneficios de tarjeta</h1>
        <p className="ticket-help">
          Configura bono en recarga y/o descuento al pagar con tarjeta recargable. Se pueden
          combinar ambas modalidades.
        </p>

        {message && (
          <div className={`ticket-message ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>
        )}

        <div className="ticket-form">
          <h2>Descuento en recarga</h2>
          <label>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={form.reload_bonus_enabled}
                onChange={(e) =>
                  setForm({ ...form, reload_bonus_enabled: e.target.checked })
                }
              />
              Activar bono al recargar
            </span>
          </label>

          {form.reload_bonus_enabled && (
            <>
              <label>
                Modalidad de promo de recarga
                <select
                  value={form.reload_promo_mode}
                  onChange={(e) => setForm({ ...form, reload_promo_mode: e.target.value })}
                >
                  <option value="paquetes">Solo paquetes fijos</option>
                  <option value="paquetes_y_libre">Paquetes + monto libre</option>
                  <option value="porcentaje_y_libre">Porcentaje de bono + monto libre</option>
                </select>
              </label>

              {showPercentBonus && (
                <label>
                  Porcentaje de bono (%)
                  <input
                    type="number"
                    min="0"
                    max="500"
                    step="1"
                    value={form.reload_bonus_percent}
                    onChange={(e) =>
                      setForm({ ...form, reload_bonus_percent: e.target.value })
                    }
                  />
                </label>
              )}

              {showPackages && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <strong>Paquetes (paga → acredita)</strong>
                    <button type="button" className="ticket-secondary" onClick={addPkg}>
                      Agregar
                    </button>
                  </div>
                  {(form.reload_packages || []).map((pkg, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr 1fr auto',
                        gap: 8,
                        marginBottom: 8,
                      }}
                    >
                      <input
                        type="number"
                        placeholder="Paga"
                        value={pkg.pay_amount}
                        onChange={(e) => updatePkg(idx, { pay_amount: e.target.value })}
                      />
                      <input
                        type="number"
                        placeholder="Acredita"
                        value={pkg.credit_amount}
                        onChange={(e) => updatePkg(idx, { credit_amount: e.target.value })}
                      />
                      <input
                        placeholder="Etiqueta"
                        value={pkg.label || ''}
                        onChange={(e) => updatePkg(idx, { label: e.target.value })}
                      />
                      <button type="button" className="ticket-danger" onClick={() => removePkg(idx)}>
                        Quitar
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          <h2>Descuento al pagar</h2>
          <label>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={form.pay_discount_enabled}
                onChange={(e) =>
                  setForm({ ...form, pay_discount_enabled: e.target.checked })
                }
              />
              Activar descuento al pagar con tarjeta recargable
            </span>
          </label>

          {form.pay_discount_enabled && (
            <>
              <label>
                Modalidad de descuento al pagar
                <select
                  value={form.pay_discount_mode}
                  onChange={(e) => setForm({ ...form, pay_discount_mode: e.target.value })}
                >
                  <option value="elegir_pct_o_precio">
                    Elegir: % global o precio por ciclo
                  </option>
                  <option value="solo_precio_ciclo">Solo precio especial por ciclo</option>
                  <option value="solo_porcentaje">Solo porcentaje global</option>
                </select>
              </label>

              {showStylePicker && (
                <label>
                  Tipo activo
                  <select
                    value={form.pay_discount_style}
                    onChange={(e) => setForm({ ...form, pay_discount_style: e.target.value })}
                  >
                    <option value="porcentaje">Porcentaje global</option>
                    <option value="precio_ciclo">Precio especial por ciclo</option>
                  </select>
                </label>
              )}

              {showPercentPay && (
                <label>
                  Porcentaje de descuento (%)
                  <input
                    type="number"
                    min="0"
                    max="100"
                    step="0.5"
                    value={form.pay_discount_percent}
                    onChange={(e) =>
                      setForm({ ...form, pay_discount_percent: e.target.value })
                    }
                  />
                </label>
              )}

              {effectiveStyle === 'precio_ciclo' && (
                <p className="ticket-help">
                  Configura el precio con tarjeta en Ciclos de servicio y en Precios de encargos.
                </p>
              )}
            </>
          )}

          <div className="ticket-actions">
            <button type="button" className="ticket-primary" disabled={busy} onClick={handleSave}>
              {busy ? 'Guardando…' : 'Guardar'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default CardBenefitsPage;
