import React, { useEffect, useMemo, useState } from 'react';
import Header from '../../components/layout/Header';
import { searchClients, getClientCards, queryBalanceViaNFC } from '../../services/clientsService';
import {
  getCardBenefitsSettings,
  computeReloadCredit,
} from '../../services/cardBenefitsService';
import { createReloadSale } from '../../services/salesService';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import '../ticket/TicketSettingsPage.css';

const STORE_ID = '65239f60a92d4f5f5f5f5f5f';

const RecargasPage = () => {
  const [benefits, setBenefits] = useState(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [client, setClient] = useState(null);
  const [cards, setCards] = useState([]);
  const [cardId, setCardId] = useState('');
  const [packageIndex, setPackageIndex] = useState(null);
  const [payAmount, setPayAmount] = useState('');
  const [paymentType, setPaymentType] = useState('efectivo');
  const [busy, setBusy] = useState(false);
  const [nfcBusy, setNfcBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const res = await getCardBenefitsSettings();
        setBenefits(res.data || {});
      } catch (err) {
        toast.error(err.message || 'No se pudo cargar configuración de beneficios');
      }
    })();
  }, []);

  const mode = benefits?.reload_promo_mode || 'paquetes_y_libre';
  const bonusOn = !!benefits?.reload_bonus_enabled;
  const packages = benefits?.reload_packages || [];
  const allowLibre =
    !bonusOn || mode === 'paquetes_y_libre' || mode === 'porcentaje_y_libre';
  const allowPackages = !bonusOn || mode === 'paquetes' || mode === 'paquetes_y_libre';

  const creditInfo = useMemo(() => {
    const pay = Number(payAmount) || 0;
    if (pay <= 0) return { credit: 0, bonus: 0 };
    return computeReloadCredit(benefits, pay, packageIndex);
  }, [benefits, payAmount, packageIndex]);

  const search = async () => {
    if (!query.trim()) return;
    try {
      const res = await searchClients(query.trim(), 1, 15);
      const list = res.data?.clients || res.data || [];
      setResults(Array.isArray(list) ? list : []);
    } catch (err) {
      toast.error(err.message || 'Error al buscar clientes');
    }
  };

  const selectClient = async (c) => {
    setClient(c);
    setResults([]);
    setQuery(c.nombre || c.name || '');
    try {
      const res = await getClientCards(c._id);
      const list = res.data || [];
      setCards(list);
      const first = list.find((x) => x.is_active !== false) || list[0];
      setCardId(first?._id || '');
    } catch (err) {
      toast.error(err.message || 'No se pudieron cargar tarjetas');
      setCards([]);
      setCardId('');
    }
  };

  const selectPackage = (idx) => {
    const pkg = packages[idx];
    if (!pkg) return;
    setPackageIndex(idx);
    setPayAmount(String(pkg.pay_amount));
  };

  const readNfc = async () => {
    try {
      setNfcBusy(true);
      toast.info('Acerque la tarjeta al lector…');
      const res = await queryBalanceViaNFC();
      const data = res.data || res;
      const foundCard = data.card || data.data || data;
      if (!foundCard?._id && !foundCard?.card_id) {
        toast.error(res.message || 'No se leyó ninguna tarjeta');
        return;
      }
      const cid = foundCard._id || foundCard.card_id;
      setCardId(cid);
      setCards([foundCard]);
      if (foundCard.client_id || data.client) {
        const c = data.client || { _id: foundCard.client_id, nombre: foundCard.client_name };
        setClient(c);
        setQuery(c.nombre || c.name || 'Cliente NFC');
      }
      toast.success(`Tarjeta leída. Saldo: $${Number(foundCard.balance || 0).toFixed(2)}`);
    } catch (err) {
      toast.error(err.message || 'Error leyendo NFC');
    } finally {
      setNfcBusy(false);
    }
  };

  const handleConfirm = async () => {
    const pay = Number(payAmount);
    if (!cardId) {
      toast.error('Selecciona o lee una tarjeta');
      return;
    }
    if (!pay || pay <= 0) {
      toast.error('Indica el monto a cobrar');
      return;
    }
    if (bonusOn && mode === 'paquetes' && packageIndex == null) {
      toast.error('Selecciona un paquete de recarga');
      return;
    }

    try {
      setBusy(true);
      const payload = {
        store_id: STORE_ID,
        card_id: cardId,
        client_id: client?._id || undefined,
        pay_amount: pay,
        credit_amount: creditInfo.credit,
        package_index: packageIndex,
        payment_methods: [{ payment_type: paymentType, amount: pay }],
      };
      const res = await createReloadSale(payload);
      toast.success(
        `Recarga OK. Pagó $${pay.toFixed(2)} · Acreditó $${Number(creditInfo.credit).toFixed(2)}` +
          (res.data?.ticket_printed === false ? ' (ticket no impreso)' : '')
      );
      setPayAmount('');
      setPackageIndex(null);
      // refrescar saldo
      if (client?._id) {
        const cardsRes = await getClientCards(client._id);
        setCards(cardsRes.data || []);
      }
    } catch (err) {
      toast.error(err.message || 'Error al cobrar la recarga');
    } finally {
      setBusy(false);
    }
  };

  const selectedCard = cards.find((c) => c._id === cardId);

  return (
    <div className="ticket-layout">
      <Header />
      <ToastContainer position="top-right" autoClose={3500} />
      <main className="ticket-content">
        <h1>Recarga rápida</h1>
        <p className="ticket-help">
          Busca al cliente o lee la tarjeta NFC, elige el monto, cobra en efectivo o tarjeta bancaria
          y el saldo se acredita al instante (queda registrado en ventas).
        </p>

        <div className="ticket-form">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input
              style={{ flex: 1, minWidth: 200 }}
              placeholder="Buscar cliente (nombre / tel)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && search()}
            />
            <button type="button" className="ticket-secondary" onClick={search}>
              Buscar
            </button>
            <button type="button" className="ticket-primary" disabled={nfcBusy} onClick={readNfc}>
              {nfcBusy ? 'Leyendo…' : 'Leer NFC'}
            </button>
          </div>

          {results.length > 0 && (
            <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 8 }}>
              {results.map((c) => (
                <button
                  key={c._id}
                  type="button"
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: '0.5rem',
                    border: 'none',
                    background: 'transparent',
                    cursor: 'pointer',
                  }}
                  onClick={() => selectClient(c)}
                >
                  <strong>{c.nombre || c.name}</strong>
                  {c.telefono ? ` · ${c.telefono}` : ''}
                  {c.saldo_tarjeta_recargable != null
                    ? ` · saldo $${Number(c.saldo_tarjeta_recargable).toFixed(2)}`
                    : ''}
                </button>
              ))}
            </div>
          )}

          {client && (
            <div className="ticket-help">
              Cliente: <strong>{client.nombre || client.name}</strong>
              {selectedCard && (
                <>
                  {' '}
                  · Tarjeta <strong>{selectedCard.card_number}</strong> · Saldo $
                  {Number(selectedCard.balance || 0).toFixed(2)}
                </>
              )}
            </div>
          )}

          {cards.length > 1 && (
            <label>
              Tarjeta
              <select value={cardId} onChange={(e) => setCardId(e.target.value)}>
                {cards.map((c) => (
                  <option key={c._id} value={c._id}>
                    {c.card_number} — ${Number(c.balance || 0).toFixed(2)}
                  </option>
                ))}
              </select>
            </label>
          )}

          {allowPackages && bonusOn && packages.length > 0 && (
            <div>
              <strong>Paquetes</strong>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                {packages.map((pkg, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={
                      packageIndex === idx ? 'ticket-primary' : 'ticket-secondary'
                    }
                    onClick={() => selectPackage(idx)}
                  >
                    {pkg.label || `Paga $${pkg.pay_amount}`}
                    <br />
                    <small>Acredita ${pkg.credit_amount}</small>
                  </button>
                ))}
              </div>
            </div>
          )}

          {allowLibre && (
            <label>
              Monto a cobrar ($)
              <input
                type="number"
                min="1"
                step="1"
                value={payAmount}
                onChange={(e) => {
                  setPackageIndex(null);
                  setPayAmount(e.target.value);
                }}
                disabled={bonusOn && mode === 'paquetes'}
              />
            </label>
          )}

          <div
            style={{
              background: '#f0f7ff',
              borderRadius: 12,
              padding: '1rem',
              display: 'grid',
              gap: 6,
            }}
          >
            <div>
              Cobra al cliente: <strong>${Number(payAmount || 0).toFixed(2)}</strong>
            </div>
            <div>
              Acredita a la tarjeta: <strong>${Number(creditInfo.credit || 0).toFixed(2)}</strong>
            </div>
            {creditInfo.bonus > 0 && (
              <div style={{ color: '#0f5132' }}>
                Bono: <strong>+${Number(creditInfo.bonus).toFixed(2)}</strong>
              </div>
            )}
          </div>

          <label>
            Método de cobro
            <select value={paymentType} onChange={(e) => setPaymentType(e.target.value)}>
              <option value="efectivo">Efectivo</option>
              <option value="tarjeta_credito">Tarjeta bancaria</option>
            </select>
          </label>

          <div className="ticket-actions">
            <button
              type="button"
              className="ticket-primary"
              disabled={busy || !cardId || !(Number(payAmount) > 0)}
              onClick={handleConfirm}
            >
              {busy ? 'Procesando…' : 'Cobrar y recargar'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default RecargasPage;
