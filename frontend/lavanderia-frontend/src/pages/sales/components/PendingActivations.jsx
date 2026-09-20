import React, { useState, useEffect } from 'react';
import './PendingActivations.css';

const describeSale = (sale, machines, serviceCycles) => {
  return (sale.items?.services || []).map(svc => {
    const machine = machines.find(m => m._id === svc.machine_id);
    const cycle = serviceCycles.find(s => s._id === svc.service_cycle_id);
    const typeLabel = machine?.tipo === 'secadora' ? 'Secadora' : 'Lavadora';
    const num = machine?.numero ?? '?';
    const name = cycle?.name || 'Servicio';
    return `${typeLabel} ${num} · ${name}`;
  });
};

const PendingActivations = ({
  pendingSales,
  machines,
  serviceCycles,
  onActivate,
  activatingId,
  forceOpen = false,
  onForceOpenHandled
}) => {
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    if (forceOpen && pendingSales?.length > 0) {
      setModalOpen(true);
      if (typeof onForceOpenHandled === 'function') {
        onForceOpenHandled();
      }
    }
  }, [forceOpen, pendingSales, onForceOpenHandled]);

  if (!pendingSales || pendingSales.length === 0) return null;

  const count = pendingSales.length;

  return (
    <>
      <button
        type="button"
        className="pending-notify-bar"
        onClick={() => setModalOpen(true)}
        aria-haspopup="dialog"
        aria-expanded={modalOpen}
      >
        <span className="pending-notify-pulse" aria-hidden="true" />
        <span className="pending-notify-text">
          {count === 1
            ? 'Hay 1 venta que falta encender'
            : `Hay ${count} ventas que faltan encender`}
        </span>
        <span className="pending-notify-action">Toca para encender</span>
      </button>

      {modalOpen && (
        <div
          className="pending-modal-overlay"
          onClick={() => setModalOpen(false)}
          role="presentation"
        >
          <div
            className="pending-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="pending-modal-title"
            onClick={e => e.stopPropagation()}
          >
            <div className="pending-modal-header">
              <h2 id="pending-modal-title">Encender máquinas</h2>
              <button
                type="button"
                className="pending-modal-close"
                onClick={() => setModalOpen(false)}
              >
                Cerrar
              </button>
            </div>

            <p className="pending-modal-lead">
              Elige cuál quieres encender ahora
            </p>

            <div className="pending-modal-list">
              {pendingSales.map(sale => {
                const lines = describeSale(sale, machines, serviceCycles);
                const isActivating = activatingId === sale._id;
                const canActivate = lines.length > 0;

                return (
                  <div key={sale._id} className="pending-modal-card">
                    <div className="pending-modal-card-body">
                      <div className="pending-modal-total">
                        ${Number(sale.total_amount || 0).toFixed(2)}
                      </div>
                      <div className="pending-modal-lines">
                        {canActivate ? (
                          lines.map((line, i) => <span key={i}>{line}</span>)
                        ) : (
                          <span>Solo productos — no hay máquinas</span>
                        )}
                      </div>
                    </div>
                    <button
                      type="button"
                      className="pending-activate-btn"
                      onClick={async () => {
                        if (!canActivate) return;
                        await onActivate(sale._id);
                      }}
                      disabled={isActivating || !canActivate}
                    >
                      {isActivating ? 'Encendiendo…' : 'Encender máquinas'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default PendingActivations;
