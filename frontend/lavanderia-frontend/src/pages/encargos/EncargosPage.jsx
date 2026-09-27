import React, { useEffect, useMemo, useRef, useState } from 'react';
import Header from '../../components/layout/Header';
import {
  getEncargoSettings,
  listEncargos,
  createEncargo,
  updateEncargoStatus,
  reprintEncargo,
} from '../../services/encargoService';
import { searchClients, createClient } from '../../services/clientsService';
import { validateNFCPayment } from '../../services/salesService';
import { getServiceCycles } from '../../services/cycleService';
import { getAllActiveWashers } from '../../services/machineService';
import {
  getCardBenefitsSettings,
  resolvePayDiscountStyle,
} from '../../services/cardBenefitsService';
import './EncargosPage.css';

const STATUS_LABEL = {
  recibida: 'Recibida',
  en_lavado: 'En lavado',
  terminada: 'Terminada',
  entregada: 'Entregada',
};

const STATUS_TABS = [
  { value: '', label: 'Todas' },
  { value: 'recibida', label: 'Recibida' },
  { value: 'en_lavado', label: 'En lavado' },
  { value: 'terminada', label: 'Terminada' },
  { value: 'entregada', label: 'Entregada' },
];

const NEXT_STATUS = {
  recibida: 'en_lavado',
  en_lavado: 'terminada',
  terminada: 'entregada',
};

const PAY_LABEL = {
  efectivo: 'Efectivo',
  tarjeta_credito: 'Tarjeta',
  tarjeta_recargable: 'NFC / recargable',
};

const emptyLine = () => ({
  catalogId: '',
  name: '',
  size: '',
  price: '',
  qty: 1,
  custom: false,
});

const newPayment = (type, amount) => ({
  localId: `pay-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
  payment_type: type,
  amount: Number(amount) || 0,
  nfc_uid: '',
  card_id: '',
  validated: false,
});

const EncargosPage = () => {
  const [activeTab, setActiveTab] = useState('nuevo');
  const [settings, setSettings] = useState({
    price_per_kg: 25,
    price_per_kg_tarjeta: null,
    servicios: [],
  });
  const [cardBenefits, setCardBenefits] = useState(null);
  const [encargos, setEncargos] = useState([]);
  const [filterStatus, setFilterStatus] = useState('');
  const [searchQ, setSearchQ] = useState('');
  const [searchHits, setSearchHits] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [message, setMessage] = useState(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const [clientMode, setClientMode] = useState('buscar');
  const [clientQuery, setClientQuery] = useState('');
  const [clientHits, setClientHits] = useState([]);
  const [clientId, setClientId] = useState(null);
  const [clientName, setClientName] = useState('');
  const [clientPhone, setClientPhone] = useState('');
  const [nfcBusy, setNfcBusy] = useState(false);

  const [weightKg, setWeightKg] = useState('5');
  const [serviceLines, setServiceLines] = useState([]);
  const [notes, setNotes] = useState('');
  const [paymentMethods, setPaymentMethods] = useState([]);

  const [washModal, setWashModal] = useState(null);
  const [washers, setWashers] = useState([]);
  const [cycles, setCycles] = useState([]);
  const [washMachineId, setWashMachineId] = useState('');
  const [washCycleId, setWashCycleId] = useState('');

  const searchTimer = useRef(null);
  const listSearchTimer = useRef(null);

  const showMessage = (text, ok = true) => setMessage({ text, ok });

  const catalog = useMemo(
    () => (Array.isArray(settings.servicios) ? settings.servicios : []),
    [settings]
  );
  const usesCardPay = paymentMethods.some(
    (pm) => pm.payment_type === 'tarjeta_recargable'
  );
  const payStyle = usesCardPay ? resolvePayDiscountStyle(cardBenefits) : null;
  const payPercent = Number(cardBenefits?.pay_discount_percent) || 0;

  const pricePerKgBase = Number(settings.price_per_kg) || 0;
  const pricePerKg =
    payStyle === 'precio_ciclo' && settings.price_per_kg_tarjeta != null
      ? Number(settings.price_per_kg_tarjeta)
      : payStyle === 'porcentaje' && payPercent > 0
        ? Math.round(pricePerKgBase * (1 - payPercent / 100) * 10000) / 10000
        : pricePerKgBase;

  const kgTotal = useMemo(() => {
    const w = Number(weightKg) || 0;
    return Math.round(w * pricePerKg * 100) / 100;
  }, [weightKg, pricePerKg]);

  const kgTotalOriginal = useMemo(() => {
    const w = Number(weightKg) || 0;
    return Math.round(w * pricePerKgBase * 100) / 100;
  }, [weightKg, pricePerKgBase]);

  const serviciosTotal = useMemo(() => {
    return serviceLines.reduce((acc, line) => {
      let price = Number(line.price) || 0;
      if (payStyle === 'porcentaje' && payPercent > 0) {
        price = Math.round(price * (1 - payPercent / 100) * 100) / 100;
      } else if (payStyle === 'precio_ciclo' && line.price_tarjeta != null && line.price_tarjeta !== '') {
        price = Number(line.price_tarjeta);
      }
      const qty = Math.max(1, parseInt(line.qty, 10) || 1);
      return acc + price * qty;
    }, 0);
  }, [serviceLines, payStyle, payPercent]);

  const serviciosTotalOriginal = useMemo(() => {
    return serviceLines.reduce((acc, line) => {
      const price = Number(line.price) || 0;
      const qty = Math.max(1, parseInt(line.qty, 10) || 1);
      return acc + price * qty;
    }, 0);
  }, [serviceLines]);

  const total = Math.round((kgTotal + serviciosTotal) * 100) / 100;
  const subtotalBefore = Math.round((kgTotalOriginal + serviciosTotalOriginal) * 100) / 100;
  const savingsTotal = Math.round(Math.max(0, subtotalBefore - total) * 100) / 100;

  const paidTotal = useMemo(
    () =>
      Math.round(
        paymentMethods.reduce((s, pm) => s + (Number(pm.amount) || 0), 0) * 100
      ) / 100,
    [paymentMethods]
  );
  const remaining = Math.round((total - paidTotal) * 100) / 100;

  const selected = useMemo(
    () => encargos.find((e) => e._id === selectedId) || null,
    [encargos, selectedId]
  );

  const loadSettings = async () => {
    const res = await getEncargoSettings();
    const data = res.data || { price_per_kg: 25, servicios: [] };
    setSettings({
      price_per_kg: data.price_per_kg,
      price_per_kg_tarjeta: data.price_per_kg_tarjeta,
      servicios: data.servicios || data.extras || [],
      print_bag_label: data.print_bag_label,
      print_notes: data.print_notes,
    });
  };

  const loadList = async (opts = {}) => {
    const status = opts.status !== undefined ? opts.status : filterStatus;
    const q = opts.q !== undefined ? opts.q : searchQ;
    const params = { per_page: 50 };
    if (status) params.status = status;
    if (String(q || '').trim()) params.q = String(q).trim();
    const res = await listEncargos(params);
    const list = res.data?.encargos || [];
    setEncargos(list);
    return list;
  };

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        await loadSettings();
        try {
          const br = await getCardBenefitsSettings();
          setCardBenefits(br.data || null);
        } catch {
          setCardBenefits(null);
        }
        await loadList();
      } catch (err) {
        showMessage(err.message || 'Error al cargar', false);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (paymentMethods.length === 0 && total > 0) {
      setPaymentMethods([newPayment('efectivo', total)]);
    }
  }, [total]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (paymentMethods.length !== 1) return;
    const only = paymentMethods[0];
    if (only.validated) return;
    const nextAmount = Number(total.toFixed(2));
    if (Number(only.amount) === nextAmount) return;
    setPaymentMethods((prev) =>
      prev.map((pm) => (pm.localId === only.localId ? { ...pm, amount: nextAmount } : pm))
    );
  }, [total]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (clientMode !== 'buscar') return;
    if (searchTimer.current) clearTimeout(searchTimer.current);
    const q = clientQuery.trim();
    if (q.length < 2) {
      setClientHits([]);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      try {
        const res = await searchClients(q, 1, 8);
        const list = res.data?.clients || res.data || [];
        setClientHits(Array.isArray(list) ? list : []);
      } catch {
        setClientHits([]);
      }
    }, 300);
    return () => {
      if (searchTimer.current) clearTimeout(searchTimer.current);
    };
  }, [clientQuery, clientMode]);

  useEffect(() => {
    if (activeTab !== 'gestionar') return;
    if (listSearchTimer.current) clearTimeout(listSearchTimer.current);
    const q = searchQ.trim();
    listSearchTimer.current = setTimeout(async () => {
      try {
        if (q.length >= 1) {
          const res = await listEncargos({ q, per_page: 12, status: filterStatus || undefined });
          setSearchHits(res.data?.encargos || []);
        } else {
          setSearchHits([]);
        }
        await loadList({ q });
      } catch {
        setSearchHits([]);
      }
    }, 300);
    return () => {
      if (listSearchTimer.current) clearTimeout(listSearchTimer.current);
    };
  }, [searchQ, activeTab]); // eslint-disable-line react-hooks/exhaustive-deps

  const pickClient = (c) => {
    setClientId(c._id || c.id || null);
    setClientName(c.nombre || c.name || '');
    setClientPhone(c.telefono || c.phone || '');
    setClientHits([]);
    setClientQuery(c.nombre || '');
  };

  const clearClient = () => {
    setClientId(null);
    setClientName('');
    setClientPhone('');
    setClientQuery('');
    setClientHits([]);
  };

  const handleCreateClient = async () => {
    if (!clientName.trim() || !clientPhone.trim()) {
      showMessage('Nombre y teléfono son requeridos', false);
      return;
    }
    try {
      setBusy(true);
      const res = await createClient({
        nombre: clientName.trim(),
        telefono: clientPhone.trim(),
      });
      const c = res.data || res;
      setClientId(c._id || c.id || null);
      showMessage('Cliente creado');
      setClientMode('buscar');
    } catch (err) {
      showMessage(err.message || 'No se pudo crear el cliente', false);
    } finally {
      setBusy(false);
    }
  };

  const handleReadNfcClient = async () => {
    try {
      setNfcBusy(true);
      showMessage('Acerca la tarjeta…');
      const res = await validateNFCPayment(0.01, 30);
      if (!res.success) {
        showMessage(res.message || 'Lectura NFC fallida', false);
        return;
      }
      const payload = res.data || res;
      const card = payload.card_data || {};
      if (card.client_name || card.client_id) {
        setClientName(card.client_name || '');
        setClientId(card.client_id || null);
        setClientPhone(card.client_phone || '');
        showMessage('Cliente cargado desde tarjeta');
      } else {
        showMessage('Tarjeta leída sin cliente asociado', false);
      }
    } catch (err) {
      showMessage(err.message || 'Error NFC', false);
    } finally {
      setNfcBusy(false);
    }
  };

  const addServiceLine = (fromCatalog) => {
    if (fromCatalog && catalog.length > 0) {
      const c = catalog[0];
      setServiceLines((prev) => [
        ...prev,
        {
          catalogId: c.id,
          name: c.name,
          size: c.size || '',
          price: c.price,
          price_tarjeta: c.price_tarjeta,
          qty: 1,
          custom: false,
        },
      ]);
    } else {
      setServiceLines((prev) => [...prev, { ...emptyLine(), custom: true }]);
    }
  };

  const updateLine = (idx, patch) => {
    setServiceLines((prev) =>
      prev.map((line, i) => {
        if (i !== idx) return line;
        const next = { ...line, ...patch };
        if (patch.catalogId !== undefined) {
          if (patch.catalogId === 'custom') {
            next.custom = true;
            next.catalogId = '';
          } else {
            const c = catalog.find((x) => x.id === patch.catalogId);
            if (c) {
              next.custom = false;
              next.name = c.name;
              next.size = c.size || '';
              next.price = c.price;
              next.price_tarjeta = c.price_tarjeta;
            }
          }
        }
        return next;
      })
    );
  };

  const removeLine = (idx) => {
    setServiceLines((prev) => prev.filter((_, i) => i !== idx));
  };

  const resetForm = () => {
    clearClient();
    setWeightKg('5');
    setServiceLines([]);
    setNotes('');
    setPaymentMethods([newPayment('efectivo', 0)]);
    setClientMode('buscar');
  };

  const addPaymentRow = (type) => {
    const rem = Math.max(0, remaining);
    setPaymentMethods((prev) => [...prev, newPayment(type, rem > 0 ? rem : 0)]);
  };

  const removePayment = (localId) => {
    setPaymentMethods((prev) => prev.filter((pm) => pm.localId !== localId));
  };

  const updatePaymentAmount = (localId, amount) => {
    setPaymentMethods((prev) =>
      prev.map((pm) => (pm.localId === localId ? { ...pm, amount: Number(amount) || 0 } : pm))
    );
  };

  const validateNfcForPayment = async (pm) => {
    const amount = Number(pm.amount) || 0;
    if (amount <= 0) {
      showMessage('Indica el monto NFC antes de validar', false);
      return;
    }
    try {
      setNfcBusy(true);
      showMessage(`Acerca la tarjeta para $${amount.toFixed(2)}…`);
      const res = await validateNFCPayment(amount, 30);
      if (!res.success) {
        showMessage(res.message || 'Validación NFC fallida', false);
        return;
      }
      const payload = res.data || res;
      const card = payload.card_data || {};
      setPaymentMethods((prev) =>
        prev.map((p) =>
          p.localId === pm.localId
            ? {
                ...p,
                nfc_uid: payload.nfc_uid || card.nfc_uid,
                card_id: card.card_id || '',
                validated: true,
              }
            : p
        )
      );
      if (!clientName && card.client_name) {
        setClientName(card.client_name);
        setClientId(card.client_id || null);
      }
      showMessage('Tarjeta validada');
    } catch (err) {
      showMessage(err.message || 'Error NFC', false);
    } finally {
      setNfcBusy(false);
    }
  };

  const handleSubmit = async () => {
    if (!clientName.trim()) {
      showMessage('Indica el cliente', false);
      return;
    }
    if (!(Number(weightKg) > 0)) {
      showMessage('Los kilos deben ser mayores a 0', false);
      return;
    }
    if (paymentMethods.length === 0) {
      showMessage('Agrega al menos un método de pago', false);
      return;
    }
    if (Math.abs(remaining) > 0.05) {
      showMessage(`Los pagos deben sumar el total (resta $${remaining.toFixed(2)})`, false);
      return;
    }
    const nfcPending = paymentMethods.find(
      (pm) => pm.payment_type === 'tarjeta_recargable' && !pm.nfc_uid
    );
    if (nfcPending) {
      showMessage('Valida la tarjeta NFC pendiente', false);
      return;
    }

    try {
      setBusy(true);
      const servicios = serviceLines
        .filter((l) => String(l.name || '').trim())
        .map((l) => ({
          name: String(l.name).trim(),
          size: String(l.size || '').trim(),
          price: Number(l.price) || 0,
          qty: Math.max(1, parseInt(l.qty, 10) || 1),
        }));

      const payments = paymentMethods.map((pm) => ({
        payment_type: pm.payment_type,
        amount: Number(pm.amount) || 0,
        ...(pm.nfc_uid ? { nfc_uid: pm.nfc_uid } : {}),
        ...(pm.card_id ? { card_id: pm.card_id } : {}),
      }));

      const res = await createEncargo({
        client_id: clientId || undefined,
        client_name: clientName.trim(),
        client_phone: clientPhone.trim(),
        weight_kg: Number(weightKg),
        price_per_kg: pricePerKgBase,
        servicios,
        notes: notes.trim(),
        payment_methods: payments,
      });

      const printed = res.data?.ticket_printed;
      const bag = res.data?.bag_printed;
      showMessage(
        `Encargo ${res.data?.folio || ''} cobrado` +
          (printed ? ' · ticket OK' : '') +
          (bag ? ' · etiqueta OK' : '')
      );
      resetForm();
      await loadList();
      if (res.data?._id) setSelectedId(res.data._id);
    } catch (err) {
      showMessage(err.message || 'Error al cobrar', false);
    } finally {
      setBusy(false);
    }
  };

  const openWashModal = async (item) => {
    try {
      setBusy(true);
      const [wRes, cRes] = await Promise.all([
        getAllActiveWashers(),
        getServiceCycles(1, 100),
      ]);
      const wRaw = wRes.data?.washers || wRes.data || [];
      const wList = Array.isArray(wRaw) ? wRaw : [];
      const cRaw = cRes.data?.service_cycles || cRes.data || [];
      const cList = Array.isArray(cRaw) ? cRaw : [];
      const available = wList.filter((w) => !w.estado || w.estado === 'disponible');
      setWashers(available);
      setCycles(cList);
      setWashMachineId(available[0]?._id || '');
      setWashCycleId(cList[0]?._id || '');
      setWashModal(item);
    } catch (err) {
      showMessage(err.message || 'No se pudieron cargar máquinas/ciclos', false);
    } finally {
      setBusy(false);
    }
  };

  const confirmWash = async () => {
    if (!washModal) return;
    if (!washMachineId || !washCycleId) {
      showMessage('Elige máquina y ciclo', false);
      return;
    }
    try {
      setBusy(true);
      await updateEncargoStatus(washModal._id, {
        status: 'en_lavado',
        machine_id: washMachineId,
        service_cycle_id: washCycleId,
      });
      showMessage('En lavado · máquina encendida');
      setWashModal(null);
      await loadList();
    } catch (err) {
      showMessage(err.message || 'Error al activar lavado', false);
    } finally {
      setBusy(false);
    }
  };

  const handleAdvance = async (item) => {
    const next = NEXT_STATUS[item.status];
    if (!next) return;
    if (next === 'en_lavado') {
      await openWashModal(item);
      return;
    }
    try {
      setBusy(true);
      await updateEncargoStatus(item._id, { status: next });
      showMessage(`Estado → ${STATUS_LABEL[next]}`);
      await loadList();
    } catch (err) {
      showMessage(err.message || 'Error al actualizar', false);
    } finally {
      setBusy(false);
    }
  };

  const handleReprint = async (item) => {
    try {
      setBusy(true);
      const res = await reprintEncargo(item._id);
      showMessage(
        `Reimpresión ${item.folio}` +
          (res.data?.ticket_printed ? ' · ticket' : '') +
          (res.data?.bag_printed ? ' · bolsa' : '')
      );
    } catch (err) {
      showMessage(err.message || 'Error al reimprimir', false);
    } finally {
      setBusy(false);
    }
  };

  const pickSearchHit = async (item) => {
    setSearchQ(item.folio || '');
    setSearchHits([]);
    setSelectedId(item._id);
    await loadList({ q: item.folio });
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
      <main className="encargo-content encargo-content--wide">
        <h1>Encargos</h1>
        <p className="encargo-help">
          Recibe ropa por kilos, cobra e imprime. Actualiza el estatus hasta la entrega.
        </p>

        <nav className="encargo-tabs" aria-label="Secciones de encargos">
          <button
            type="button"
            className={`encargo-tab ${activeTab === 'nuevo' ? 'is-active' : ''}`}
            onClick={() => setActiveTab('nuevo')}
          >
            Nuevo encargo
          </button>
          <button
            type="button"
            className={`encargo-tab ${activeTab === 'gestionar' ? 'is-active' : ''}`}
            onClick={() => setActiveTab('gestionar')}
          >
            Buscar / estatus
          </button>
        </nav>

        {message && (
          <div className={`encargo-msg ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>
        )}

        {activeTab === 'nuevo' && (
          <section className="encargo-card">
            <h2>Nuevo encargo</h2>

            <div className="encargo-mode-tabs">
              {[
                { id: 'buscar', label: 'Buscar cliente' },
                { id: 'crear', label: 'Crear rápido' },
                { id: 'nfc', label: 'Tarjeta NFC' },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className={`encargo-chip ${clientMode === t.id ? 'is-active' : ''}`}
                  onClick={() => setClientMode(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {clientMode === 'buscar' && (
              <div className="encargo-client-block">
                <label>
                  Nombre o teléfono
                  <input
                    value={clientQuery}
                    onChange={(e) => setClientQuery(e.target.value)}
                    placeholder="Escribe para buscar…"
                    autoComplete="off"
                  />
                </label>
                {clientHits.length > 0 && (
                  <ul className="encargo-client-hits">
                    {clientHits.map((c) => (
                      <li key={c._id || c.id}>
                        <button type="button" onClick={() => pickClient(c)}>
                          <strong>{c.nombre}</strong>
                          <span>{c.telefono}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {(clientName || clientPhone) && (
                  <div className="encargo-client-picked">
                    <div>
                      <strong>{clientName}</strong>
                      {clientPhone && <span> · {clientPhone}</span>}
                    </div>
                    <button type="button" className="encargo-link" onClick={clearClient}>
                      Cambiar
                    </button>
                  </div>
                )}
              </div>
            )}

            {clientMode === 'crear' && (
              <div className="encargo-grid-2">
                <label>
                  Nombre
                  <input value={clientName} onChange={(e) => setClientName(e.target.value)} />
                </label>
                <label>
                  Teléfono
                  <input value={clientPhone} onChange={(e) => setClientPhone(e.target.value)} />
                </label>
                <button
                  type="button"
                  className="encargo-secondary"
                  disabled={busy}
                  onClick={handleCreateClient}
                >
                  Guardar cliente
                </button>
              </div>
            )}

            {clientMode === 'nfc' && (
              <div className="encargo-client-block">
                <p className="encargo-muted">Lee la tarjeta recargable para cargar el cliente asociado.</p>
                <button
                  type="button"
                  className="encargo-secondary"
                  disabled={nfcBusy}
                  onClick={handleReadNfcClient}
                >
                  {nfcBusy ? 'Esperando tarjeta…' : 'Leer tarjeta'}
                </button>
                {clientName && (
                  <div className="encargo-client-picked">
                    <div>
                      <strong>{clientName}</strong>
                      {clientPhone && <span> · {clientPhone}</span>}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="encargo-grid-2" style={{ marginTop: '1rem' }}>
              <label>
                Kilos
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                />
              </label>
              <div className="encargo-total">
                <span>Precio / kg</span>
                <strong>${pricePerKg.toFixed(2)}</strong>
                <span className="encargo-muted">Subtotal kg: ${kgTotal.toFixed(2)}</span>
                {savingsTotal > 0.009 && (
                  <span className="encargo-muted" style={{ color: '#0f5132' }}>
                    Ahorro con tarjeta: ${savingsTotal.toFixed(2)}
                  </span>
                )}
              </div>
            </div>

            <div className="encargo-servicios-block">
              <div className="encargo-card-head">
                <h3>Servicios</h3>
                <div className="encargo-inline-actions">
                  <button type="button" className="encargo-secondary" onClick={() => addServiceLine(true)}>
                    + Del catálogo
                  </button>
                  <button type="button" className="encargo-secondary" onClick={() => addServiceLine(false)}>
                    + Personalizado
                  </button>
                </div>
              </div>
              {serviceLines.length === 0 && (
                <p className="encargo-muted">Sin servicios adicionales.</p>
              )}
              {serviceLines.map((line, idx) => (
                <div key={idx} className="encargo-servicio-line">
                  {!line.custom ? (
                    <select
                      value={line.catalogId}
                      onChange={(e) => updateLine(idx, { catalogId: e.target.value })}
                    >
                      {catalog.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.name}
                          {c.size ? ` (${c.size})` : ''} — ${Number(c.price).toFixed(2)}
                        </option>
                      ))}
                      <option value="custom">Personalizado…</option>
                    </select>
                  ) : (
                    <>
                      <input
                        placeholder="Nombre"
                        value={line.name}
                        onChange={(e) => updateLine(idx, { name: e.target.value })}
                      />
                      <input
                        placeholder="Tamaño"
                        value={line.size}
                        onChange={(e) => updateLine(idx, { size: e.target.value })}
                      />
                    </>
                  )}
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    title="Precio"
                    value={line.price}
                    onChange={(e) => updateLine(idx, { price: e.target.value })}
                  />
                  <input
                    type="number"
                    min="1"
                    title="Cantidad"
                    value={line.qty}
                    onChange={(e) => updateLine(idx, { qty: e.target.value })}
                  />
                  <button type="button" className="encargo-danger" onClick={() => removeLine(idx)}>
                    ×
                  </button>
                </div>
              ))}
            </div>

            <label>
              Notas
              <textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} />
            </label>

            <div className="encargo-payments">
              <div className="encargo-card-head">
                <h3>Formas de pago</h3>
                <div className="encargo-inline-actions">
                  {Object.keys(PAY_LABEL).map((type) => (
                    <button
                      key={type}
                      type="button"
                      className="encargo-secondary"
                      onClick={() => addPaymentRow(type)}
                    >
                      + {PAY_LABEL[type]}
                    </button>
                  ))}
                </div>
              </div>
              {paymentMethods.map((pm) => (
                <div key={pm.localId} className="encargo-pay-row">
                  <span className="encargo-pay-type">{PAY_LABEL[pm.payment_type] || pm.payment_type}</span>
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={pm.amount}
                    onChange={(e) => updatePaymentAmount(pm.localId, e.target.value)}
                  />
                  {pm.payment_type === 'tarjeta_recargable' && (
                    <button
                      type="button"
                      className="encargo-secondary"
                      disabled={nfcBusy}
                      onClick={() => validateNfcForPayment(pm)}
                    >
                      {pm.validated || pm.nfc_uid ? 'NFC OK' : 'Validar NFC'}
                    </button>
                  )}
                  <button
                    type="button"
                    className="encargo-danger"
                    onClick={() => removePayment(pm.localId)}
                    disabled={paymentMethods.length <= 1}
                  >
                    ×
                  </button>
                </div>
              ))}
              <div className="encargo-pay-summary">
                <span>Pagado: ${paidTotal.toFixed(2)}</span>
                <span className={Math.abs(remaining) > 0.05 ? 'encargo-pay-rest' : ''}>
                  Resta: ${remaining.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="encargo-checkout">
              <div className="encargo-total">
                <span>Total</span>
                <strong>${total.toFixed(2)}</strong>
              </div>
              <button
                type="button"
                className="encargo-primary"
                disabled={busy || total <= 0}
                onClick={handleSubmit}
              >
                {busy ? 'Procesando…' : 'Cobrar, recibir e imprimir'}
              </button>
            </div>
          </section>
        )}

        {activeTab === 'gestionar' && (
          <section className="encargo-card">
            <h2>Buscar / actualizar estatus</h2>

            <div className="encargo-search-wrap">
              <label>
                Folio o nombre del cliente
                <input
                  className="encargo-folio"
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                  placeholder="E-202609-0001 o nombre…"
                  autoComplete="off"
                />
              </label>
              {searchHits.length > 0 && searchQ.trim() && (
                <ul className="encargo-search-hits">
                  {searchHits.map((hit) => (
                    <li key={hit._id}>
                      <button type="button" onClick={() => pickSearchHit(hit)}>
                        <strong>{hit.folio}</strong>
                        <span>
                          {hit.client_name || 'Sin nombre'} · {STATUS_LABEL[hit.status]}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="encargo-mode-tabs">
              {STATUS_TABS.map((t) => (
                <button
                  key={t.value || 'all'}
                  type="button"
                  className={`encargo-chip ${filterStatus === t.value ? 'is-active' : ''}`}
                  onClick={async () => {
                    setFilterStatus(t.value);
                    await loadList({ status: t.value });
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>

            <div className="encargo-list">
              {encargos.length === 0 && <p className="encargo-muted">No hay encargos.</p>}
              {encargos.map((item) => (
                <article
                  key={item._id}
                  className={`encargo-item ${selectedId === item._id ? 'is-selected' : ''}`}
                  onClick={() => setSelectedId(item._id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && setSelectedId(item._id)}
                >
                  <div>
                    <div>
                      <strong>{item.folio}</strong>
                      <span className={`encargo-badge st-${item.status}`}>
                        {STATUS_LABEL[item.status] || item.status}
                      </span>
                    </div>
                    <div className="encargo-muted">
                      {item.client_name || 'Sin nombre'} · {item.weight_kg} kg · $
                      {Number(item.total_amount || 0).toFixed(2)}
                      {item.machine_name ? ` · ${item.machine_name}` : ''}
                    </div>
                  </div>
                  <div className="encargo-item-actions" onClick={(e) => e.stopPropagation()}>
                    {NEXT_STATUS[item.status] && (
                      <button
                        type="button"
                        className="encargo-advance"
                        disabled={busy}
                        onClick={() => handleAdvance(item)}
                      >
                        → {STATUS_LABEL[NEXT_STATUS[item.status]]}
                      </button>
                    )}
                    <button
                      type="button"
                      className="encargo-secondary"
                      disabled={busy}
                      onClick={() => handleReprint(item)}
                    >
                      Reimprimir
                    </button>
                  </div>
                </article>
              ))}
            </div>

            {selected && (
              <div className="encargo-detail">
                <h3>Detalle {selected.folio}</h3>
                <p>
                  <strong>{selected.client_name}</strong>
                  {selected.client_phone ? ` · ${selected.client_phone}` : ''}
                </p>
                <p>
                  {selected.weight_kg} kg × ${Number(selected.price_per_kg || 0).toFixed(2)} · Total $
                  {Number(selected.total_amount || 0).toFixed(2)}
                </p>
                {(selected.servicios || selected.extras || []).length > 0 && (
                  <ul>
                    {(selected.servicios || selected.extras).map((s, i) => (
                      <li key={i}>
                        {s.qty || 1}× {s.name}
                        {s.size ? ` (${s.size})` : ''} — ${Number(s.price || 0).toFixed(2)}
                      </li>
                    ))}
                  </ul>
                )}
                {selected.notes && <p className="encargo-muted">Notas: {selected.notes}</p>}
                {selected.machine_name && (
                  <p className="encargo-muted">Máquina: {selected.machine_name}</p>
                )}
                <button
                  type="button"
                  className="encargo-primary"
                  disabled={busy}
                  onClick={() => handleReprint(selected)}
                >
                  Reimprimir ticket
                  {settings.print_bag_label !== false ? ' + etiqueta' : ''}
                </button>
              </div>
            )}
          </section>
        )}
      </main>

      {washModal && (
        <div className="encargo-modal-overlay" onClick={() => setWashModal(null)}>
          <div className="encargo-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Poner en lavado</h3>
            <p className="encargo-muted">
              Folio {washModal.folio} · elige lavadora y ciclo para encenderla.
            </p>
            <label>
              Máquina
              <select value={washMachineId} onChange={(e) => setWashMachineId(e.target.value)}>
                {washers.length === 0 && <option value="">Sin lavadoras disponibles</option>}
                {washers.map((w) => (
                  <option key={w._id} value={w._id}>
                    #{w.numero} {w.marca || ''} {w.esp32_id ? `(${w.esp32_id})` : ''}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Ciclo de lavado
              <select value={washCycleId} onChange={(e) => setWashCycleId(e.target.value)}>
                {cycles.length === 0 && <option value="">Sin ciclos</option>}
                {cycles.map((c) => (
                  <option key={c._id} value={c._id}>
                    {c.name} {c.duration_minutes ? `· ${c.duration_minutes} min` : ''}
                  </option>
                ))}
              </select>
            </label>
            <div className="encargo-modal-actions">
              <button type="button" className="encargo-secondary" onClick={() => setWashModal(null)}>
                Cancelar
              </button>
              <button
                type="button"
                className="encargo-primary"
                disabled={busy || !washMachineId || !washCycleId}
                onClick={confirmWash}
              >
                {busy ? 'Activando…' : 'Encender y continuar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EncargosPage;
