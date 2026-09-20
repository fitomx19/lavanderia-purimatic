import React, { useMemo, useState, useEffect } from 'react';
import './NewSaleWizard.css';

const PAYMENT_TYPES = [
  { id: 'efectivo', label: 'Efectivo', icon: '💵' },
  { id: 'tarjeta_credito', label: 'Tarjeta', icon: '💳' },
  { id: 'tarjeta_recargable', label: 'Tarjeta del cliente', icon: '🎫' }
];

const getServiceDisplayName = (cycle) => {
  if (cycle.service_type === 'encargo_lavado') {
    return cycle.name || 'Lavado por kilo';
  }
  return cycle.name;
};

const getServicePriceLabel = (cycle) => {
  if (cycle.service_type === 'encargo_lavado') {
    return `$${Number(cycle.price_per_kg || 0).toFixed(2)}/kg`;
  }
  return `$${Number(cycle.price || 0).toFixed(2)}`;
};

const STEP_LABELS = [
  { n: 1, text: 'Elegir' },
  { n: 2, text: 'Máquina' },
  { n: 3, text: 'Pagar' }
];

const normalizeText = (value) =>
  String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const NewSaleWizard = ({
  products,
  serviceCycles,
  machines,
  onSubmit,
  onOpenNFC,
  onTicketChange,
  submitting
}) => {
  const [step, setStep] = useState(1);
  const [catalogTab, setCatalogTab] = useState('services');
  const [catalogSearch, setCatalogSearch] = useState('');
  const [onlyFreeMachines, setOnlyFreeMachines] = useState(true);
  const [productQty, setProductQty] = useState({});
  const [serviceSelections, setServiceSelections] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [cashReceived, setCashReceived] = useState({});
  const [showSplitPayment, setShowSplitPayment] = useState(false);

  const hasItems =
    Object.values(productQty).some(q => q > 0) || serviceSelections.length > 0;
  const hasServices = serviceSelections.length > 0;

  const paidTotal = useMemo(
    () => paymentMethods.reduce((sum, pm) => sum + (Number(pm.amount) || 0), 0),
    [paymentMethods]
  );

  const addService = (cycle) => {
    setServiceSelections(prev => [
      ...prev,
      {
        localId: `${cycle._id}-${Date.now()}-${Math.random()}`,
        service_cycle_id: cycle._id,
        service_type: cycle.service_type,
        machine_id: '',
        weight_kg: cycle.service_type === 'encargo_lavado' ? 1 : '',
        name: getServiceDisplayName(cycle),
        duration_minutes: cycle.duration_minutes,
        price: cycle.price,
        price_per_kg: cycle.price_per_kg,
        allowed_machines: (cycle.allowed_machines || []).map(am => am._id || am)
      }
    ]);
  };

  const removeService = (localId) => {
    setServiceSelections(prev => prev.filter(s => s.localId !== localId));
  };

  const updateService = (localId, field, value) => {
    setServiceSelections(prev =>
      prev.map(s => (s.localId === localId ? { ...s, [field]: value } : s))
    );
  };

  const bumpProduct = (productId, delta) => {
    setProductQty(prev => {
      const current = prev[productId] || 0;
      const product = products.find(p => p._id === productId);
      const maxStock = product?.stock ?? 999;
      const next = Math.max(0, Math.min(maxStock, current + delta));
      if (next === 0) {
        const { [productId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [productId]: next };
    });
  };

  const ticketLines = useMemo(() => {
    const lines = [];
    Object.entries(productQty).forEach(([id, qty]) => {
      const p = products.find(x => x._id === id);
      if (p && qty > 0) {
        lines.push({
          key: `p-${id}`,
          label: `${p.nombre} × ${qty}`,
          amount: Number(p.precio) * qty
        });
      }
    });
    serviceSelections.forEach(svc => {
      let amount = 0;
      if (svc.service_type === 'encargo_lavado') {
        amount = Number(svc.price_per_kg || 0) * Number(svc.weight_kg || 0);
      } else {
        amount = Number(svc.price || 0);
      }
      const machine = machines.find(m => m._id === svc.machine_id);
      const machinePart = machine ? ` · #${machine.numero}` : '';
      const kgPart =
        svc.service_type === 'encargo_lavado' && svc.weight_kg
          ? ` (${svc.weight_kg} kg)`
          : '';
      lines.push({
        key: svc.localId,
        label: `${svc.name}${kgPart}${machinePart}`,
        amount
      });
    });
    return lines;
  }, [productQty, products, serviceSelections, machines]);

  const computedTotal = useMemo(
    () => ticketLines.reduce((s, l) => s + l.amount, 0),
    [ticketLines]
  );

  useEffect(() => {
    if (typeof onTicketChange === 'function') {
      onTicketChange(computedTotal);
    }
  }, [computedTotal, onTicketChange]);

  const machinesReady = serviceSelections.every(svc => {
    if (!svc.machine_id) return false;
    if (svc.service_type === 'encargo_lavado' && !(Number(svc.weight_kg) > 0)) return false;
    return true;
  });

  const setPrimaryPayment = (type) => {
    setPaymentMethods([
      {
        localId: `pay-${Date.now()}`,
        payment_type: type,
        amount: Number(computedTotal.toFixed(2)),
        card_id: '',
        nfc_uid: '',
        validated: false
      }
    ]);
    setCashReceived({});
    setShowSplitPayment(false);
  };

  const addPayment = (type) => {
    const rem = Math.max(0, Number((computedTotal - paidTotal).toFixed(2)));
    const amount = rem > 0 ? rem : (computedTotal > 0 ? computedTotal : 0);
    setPaymentMethods(prev => [
      ...prev,
      {
        localId: `pay-${Date.now()}`,
        payment_type: type,
        amount,
        card_id: '',
        nfc_uid: '',
        validated: false
      }
    ]);
    setShowSplitPayment(false);
  };

  useEffect(() => {
    if (step === 3 && paymentMethods.length === 0 && computedTotal > 0) {
      setPrimaryPayment('efectivo');
    }
  }, [step]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (step !== 3) return;
    if (paymentMethods.length !== 1) return;
    const only = paymentMethods[0];
    if (only.validated) return;
    const nextAmount = Number(computedTotal.toFixed(2));
    if (Number(only.amount) === nextAmount) return;
    setPaymentMethods(prev =>
      prev.map(pm => (pm.localId === only.localId ? { ...pm, amount: nextAmount } : pm))
    );
  }, [computedTotal, step]); // eslint-disable-line react-hooks/exhaustive-deps

  const removePayment = (localId) => {
    setPaymentMethods(prev => prev.filter(pm => pm.localId !== localId));
    setCashReceived(prev => {
      const { [localId]: _, ...rest } = prev;
      return rest;
    });
  };

  const updatePaymentAmount = (localId, amount) => {
    setPaymentMethods(prev =>
      prev.map(pm => (pm.localId === localId ? { ...pm, amount } : pm))
    );
  };

  const resetWizard = () => {
    setStep(1);
    setCatalogTab('services');
    setCatalogSearch('');
    setOnlyFreeMachines(true);
    setProductQty({});
    setServiceSelections([]);
    setPaymentMethods([]);
    setCashReceived({});
    setShowSplitPayment(false);
  };

  const handleSubmit = async () => {
    const productsPayload = Object.entries(productQty)
      .filter(([, qty]) => qty > 0)
      .map(([product_id, quantity]) => ({ product_id, quantity }));

    const servicesPayload = serviceSelections.map(svc => ({
      service_cycle_id: svc.service_cycle_id,
      service_type: svc.service_type,
      machine_id: svc.machine_id,
      weight_kg: svc.service_type === 'encargo_lavado' ? Number(svc.weight_kg) : undefined
    }));

    const paymentsPayload = paymentMethods.map(pm => ({
      payment_type: pm.payment_type,
      amount: Number(pm.amount) || 0,
      card_id: pm.card_id || '',
      nfc_uid: pm.nfc_uid || '',
      validated: !!pm.validated
    }));

    const ok = await onSubmit({
      products: productsPayload,
      services: servicesPayload,
      payment_methods: paymentsPayload,
      ticketTotal: computedTotal,
      serviceSelections
    });

    if (ok) resetWizard();
  };

  const handleOpenNFCFor = (pm) => {
    onOpenNFC(pm.amount, (paymentData) => {
      setPaymentMethods(prev =>
        prev.map(p =>
          p.localId === pm.localId
            ? {
                ...p,
                nfc_uid: paymentData.nfc_uid,
                card_id: paymentData.card_id || '',
                validated: true
              }
            : p
        )
      );
    });
  };

  const goNext = () => {
    if (step === 1) {
      if (!hasItems) return;
      if (hasServices) setStep(2);
      else setStep(3);
      return;
    }
    if (step === 2) {
      if (!machinesReady) return;
      setStep(3);
    }
  };

  const goBack = () => {
    if (step === 3) {
      setStep(hasServices ? 2 : 1);
      return;
    }
    if (step === 2) setStep(1);
  };

  const primaryPayment = paymentMethods[0];
  const isSimplePay = paymentMethods.length <= 1;
  const selectedType = primaryPayment?.payment_type;

  const searchQuery = normalizeText(catalogSearch.trim());

  const filteredServices = useMemo(() => {
    const list = [...(serviceCycles || [])].sort((a, b) =>
      getServiceDisplayName(a).localeCompare(getServiceDisplayName(b), 'es')
    );
    if (!searchQuery) return list;
    return list.filter(cycle =>
      normalizeText(getServiceDisplayName(cycle)).includes(searchQuery)
    );
  }, [serviceCycles, searchQuery]);

  const filteredProducts = useMemo(() => {
    const list = [...(products || [])].sort((a, b) =>
      String(a.nombre || '').localeCompare(String(b.nombre || ''), 'es')
    );
    if (!searchQuery) return list;
    return list.filter(product =>
      normalizeText(product.nombre).includes(searchQuery)
    );
  }, [products, searchQuery]);

  const stepTitle =
    step === 1
      ? '¿Qué quiere el cliente?'
      : step === 2
        ? '¿Qué máquina usa?'
        : '¿Cómo paga?';

  return (
    <section className="new-sale-wizard">
      <div className="wizard-header">
        <div className="wizard-step-trail">
          {STEP_LABELS.map((s, i) => {
            const skipped = s.n === 2 && !hasServices && step === 3;
            const on = step === s.n || (step > s.n && !skipped);
            return (
              <React.Fragment key={s.n}>
                {i > 0 && <span className="wizard-trail-arrow">→</span>}
                <span className={`wizard-trail-step ${on ? 'on' : ''} ${skipped ? 'skip' : ''}`}>
                  {s.text}
                </span>
              </React.Fragment>
            );
          })}
        </div>
      </div>

      <h3 className="wizard-question">{stepTitle}</h3>

      {step === 1 && (
        <div className="wizard-body">
          <div className="catalog-tabs">
            <button
              type="button"
              className={`catalog-tab ${catalogTab === 'services' ? 'active' : ''}`}
              onClick={() => {
                setCatalogTab('services');
                setCatalogSearch('');
              }}
            >
              Servicios
            </button>
            <button
              type="button"
              className={`catalog-tab ${catalogTab === 'products' ? 'active' : ''}`}
              onClick={() => {
                setCatalogTab('products');
                setCatalogSearch('');
              }}
            >
              Productos
            </button>
          </div>

          <input
            type="search"
            className="catalog-search"
            placeholder="Buscar…"
            value={catalogSearch}
            onChange={e => setCatalogSearch(e.target.value)}
            aria-label="Buscar"
          />

          {catalogTab === 'services' && (
            <>
              <div className="catalog-scroll">
                {filteredServices.length === 0 ? (
                  <p className="catalog-empty">No hay nada con ese nombre</p>
                ) : (
                  <div className="catalog-grid">
                    {filteredServices.map(cycle => {
                      const count = serviceSelections.filter(s => s.service_cycle_id === cycle._id).length;
                      return (
                        <button
                          key={cycle._id}
                          type="button"
                          className={`catalog-card ${count > 0 ? 'selected' : ''}`}
                          onClick={() => addService(cycle)}
                        >
                          <span className="catalog-card-name">{getServiceDisplayName(cycle)}</span>
                          <span className="catalog-card-meta">
                            {cycle.duration_minutes ? `${cycle.duration_minutes} min` : ''}
                          </span>
                          <span className="catalog-card-price">{getServicePriceLabel(cycle)}</span>
                          {count > 0 && <span className="catalog-card-badge">×{count}</span>}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
              {serviceSelections.length > 0 && (
                <div className="selected-services-strip">
                  {serviceSelections.map(svc => (
                    <div key={svc.localId} className="selected-chip">
                      <span>{svc.name}</span>
                      <button type="button" onClick={() => removeService(svc.localId)} aria-label="Quitar">
                        −
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {catalogTab === 'products' && (
            <div className="catalog-scroll">
              {filteredProducts.length === 0 ? (
                <p className="catalog-empty">No hay nada con ese nombre</p>
              ) : (
                <div className="catalog-grid">
                  {filteredProducts.map(product => {
                    const qty = productQty[product._id] || 0;
                    return (
                      <div
                        key={product._id}
                        className={`catalog-card product-card ${qty > 0 ? 'selected' : ''}`}
                      >
                        <button
                          type="button"
                          className="catalog-card-tap"
                          onClick={() => bumpProduct(product._id, 1)}
                          disabled={product.stock <= 0}
                        >
                          <span className="catalog-card-name">{product.nombre}</span>
                          <span className="catalog-card-meta">Quedan {product.stock}</span>
                          <span className="catalog-card-price">
                            ${Number(product.precio).toFixed(2)}
                          </span>
                        </button>
                        {qty > 0 && (
                          <div className="qty-controls">
                            <button type="button" onClick={() => bumpProduct(product._id, -1)}>−</button>
                            <span>{qty}</span>
                            <button type="button" onClick={() => bumpProduct(product._id, 1)}>+</button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {step === 2 && (
        <div className="wizard-body">
          {(() => {
            const freeCount = machines.filter(m => m.estado === 'disponible').length;
            const busyCount = machines.length - freeCount;
            return (
              <div className="machine-pick-toolbar">
                <span className="machine-pick-count">
                  {freeCount} libres · {busyCount} ocupadas
                </span>
                <div className="machine-filter-toggle">
                  <button
                    type="button"
                    className={!onlyFreeMachines ? 'on' : ''}
                    onClick={() => setOnlyFreeMachines(false)}
                  >
                    Todas
                  </button>
                  <button
                    type="button"
                    className={onlyFreeMachines ? 'on' : ''}
                    onClick={() => setOnlyFreeMachines(true)}
                  >
                    Solo libres
                  </button>
                </div>
              </div>
            );
          })()}

          {serviceSelections.map(svc => {
            let allowed = machines.filter(m => {
              if (svc.allowed_machines?.length) {
                return svc.allowed_machines.includes(m._id);
              }
              return true;
            });

            const selectedMachine = allowed.find(m => m._id === svc.machine_id);
            if (onlyFreeMachines) {
              allowed = allowed.filter(
                m => m.estado === 'disponible' || m._id === svc.machine_id
              );
            }
            allowed = [...allowed].sort((a, b) => (a.numero || 0) - (b.numero || 0));

            return (
              <div key={svc.localId} className="machine-pick-block">
                <p className="machine-pick-label">
                  Para <strong>{svc.name}</strong>, toca una máquina
                </p>

                {svc.service_type === 'encargo_lavado' && (
                  <div className="weight-picker">
                    <span className="weight-label">¿Cuántos kilos?</span>
                    <div className="weight-controls">
                      <button
                        type="button"
                        onClick={() =>
                          updateService(
                            svc.localId,
                            'weight_kg',
                            Math.max(0.5, Number((Number(svc.weight_kg || 1) - 0.5).toFixed(1)))
                          )
                        }
                      >
                        − 0.5
                      </button>
                      <input
                        type="number"
                        min="0.5"
                        step="0.5"
                        value={svc.weight_kg}
                        onChange={e =>
                          updateService(svc.localId, 'weight_kg', parseFloat(e.target.value) || 0)
                        }
                      />
                      <button
                        type="button"
                        onClick={() =>
                          updateService(
                            svc.localId,
                            'weight_kg',
                            Number((Number(svc.weight_kg || 0) + 0.5).toFixed(1))
                          )
                        }
                      >
                        + 0.5
                      </button>
                    </div>
                  </div>
                )}

                <div className="machine-pick-scroll">
                  <div className="machine-pick-grid">
                    {allowed.length === 0 ? (
                      <p className="catalog-empty">
                        {onlyFreeMachines
                          ? 'No hay máquinas libres para este servicio'
                          : 'No hay máquinas disponibles'}
                      </p>
                    ) : (
                      allowed.map(machine => {
                        const available = machine.estado === 'disponible';
                        const selected = svc.machine_id === machine._id;
                        const takenByOther = serviceSelections.some(
                          s => s.localId !== svc.localId && s.machine_id === machine._id
                        );
                        const disabled = (!available && !selected) || takenByOther;

                        return (
                          <button
                            key={machine._id}
                            type="button"
                            className={`machine-pick-tile ${selected ? 'selected' : ''} ${disabled ? 'disabled' : ''} ${available ? 'free' : 'busy'}`}
                            disabled={disabled}
                            onClick={() => updateService(svc.localId, 'machine_id', machine._id)}
                          >
                            <span className="mp-num">#{machine.numero}</span>
                            <span className="mp-status">
                              {takenByOther
                                ? 'Ya elegida'
                                : available
                                  ? 'Libre'
                                  : 'Ocupada'}
                            </span>
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>
                {selectedMachine && onlyFreeMachines && selectedMachine.estado !== 'disponible' && (
                  <p className="machine-pick-note">Máquina elegida (ocupada)</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {step === 3 && (
        <div className="wizard-body">
          <div className="pay-total-huge">${computedTotal.toFixed(2)}</div>

          <div className="pay-type-row">
            {PAYMENT_TYPES.map(pt => (
              <button
                key={pt.id}
                type="button"
                className={`pay-type-btn ${selectedType === pt.id && isSimplePay ? 'selected' : ''}`}
                onClick={() => {
                  if (isSimplePay) {
                    setPrimaryPayment(pt.id);
                  } else {
                    addPayment(pt.id);
                  }
                }}
              >
                <span className="pay-type-icon">{pt.icon}</span>
                <span>{pt.label}</span>
              </button>
            ))}
          </div>

          {isSimplePay && primaryPayment?.payment_type === 'efectivo' && (
            <div className="cash-change simple">
              <label>
                ¿Cuánto te dio?
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={cashReceived[primaryPayment.localId] ?? ''}
                  onChange={e =>
                    setCashReceived(prev => ({
                      ...prev,
                      [primaryPayment.localId]: parseFloat(e.target.value) || 0
                    }))
                  }
                />
              </label>
              {Number(cashReceived[primaryPayment.localId] || 0) > 0 && (
                <div className="change-amount">
                  Cambio:{' '}
                  <strong>
                    $
                    {Math.max(
                      0,
                      Number(cashReceived[primaryPayment.localId] || 0) - Number(primaryPayment.amount || 0)
                    ).toFixed(2)}
                  </strong>
                </div>
              )}
            </div>
          )}

          {isSimplePay && primaryPayment?.payment_type === 'tarjeta_recargable' && (
            <div className="nfc-block">
              {!primaryPayment.validated ? (
                <button
                  type="button"
                  className="nfc-big-btn"
                  disabled={!primaryPayment.amount || primaryPayment.amount <= 0}
                  onClick={() => handleOpenNFCFor(primaryPayment)}
                >
                  Acerca la tarjeta
                </button>
              ) : (
                <div className="nfc-ok">
                  <span>Tarjeta lista ✓</span>
                  <button
                    type="button"
                    onClick={() => {
                      setPaymentMethods(prev =>
                        prev.map(p =>
                          p.localId === primaryPayment.localId
                            ? { ...p, nfc_uid: '', card_id: '', validated: false }
                            : p
                        )
                      );
                    }}
                  >
                    Cambiar tarjeta
                  </button>
                </div>
              )}
            </div>
          )}

          {!isSimplePay && (
            <div className="payments-list split">
              {paymentMethods.map(pm => (
                <div key={pm.localId} className="payment-block simple-split">
                  <div className="split-row">
                    <span className="split-type">
                      {PAYMENT_TYPES.find(t => t.id === pm.payment_type)?.label || pm.payment_type}
                    </span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={pm.amount}
                      onChange={e =>
                        updatePaymentAmount(pm.localId, parseFloat(e.target.value) || 0)
                      }
                      aria-label="Monto"
                    />
                    <button
                      type="button"
                      className="pay-remove"
                      onClick={() => removePayment(pm.localId)}
                    >
                      −
                    </button>
                  </div>
                  {pm.payment_type === 'tarjeta_recargable' && (
                    <div className="nfc-block">
                      {!pm.validated ? (
                        <button
                          type="button"
                          className="nfc-big-btn"
                          disabled={!pm.amount || pm.amount <= 0}
                          onClick={() => handleOpenNFCFor(pm)}
                        >
                          Acerca la tarjeta
                        </button>
                      ) : (
                        <div className="nfc-ok">
                          <span>Tarjeta lista ✓</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          <button
            type="button"
            className="add-payment-link"
            onClick={() => setShowSplitPayment(prev => !prev)}
          >
            {showSplitPayment ? 'Cancelar dividir' : 'Dividir pago'}
          </button>
          {showSplitPayment && (
            <div className="add-payment-choices">
              {PAYMENT_TYPES.map(pt => (
                <button key={pt.id} type="button" onClick={() => addPayment(pt.id)}>
                  {pt.icon} {pt.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="wizard-ticket">
        {ticketLines.length === 0 ? (
          <p className="ticket-empty">Aún no hay nada</p>
        ) : (
          <ul>
            {ticketLines.map(line => (
              <li key={line.key}>
                <span>{line.label}</span>
                <span>${line.amount.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        )}
        <div className="ticket-total">
          <span>Total</span>
          <strong>${computedTotal.toFixed(2)}</strong>
        </div>
      </div>

      <div className="wizard-footer">
        {step > 1 && (
          <button type="button" className="wizard-btn secondary" onClick={goBack}>
            Atrás
          </button>
        )}
        {step < 3 && (
          <button
            type="button"
            className="wizard-btn primary"
            onClick={goNext}
            disabled={
              (step === 1 && !hasItems) ||
              (step === 2 && !machinesReady)
            }
          >
            Siguiente
          </button>
        )}
        {step === 3 && (
          <button
            type="button"
            className="wizard-btn primary charge"
            onClick={handleSubmit}
            disabled={submitting || paymentMethods.length === 0 || computedTotal <= 0}
          >
            {submitting ? 'Cobrando…' : 'Cobrar'}
          </button>
        )}
      </div>
    </section>
  );
};

export default NewSaleWizard;
