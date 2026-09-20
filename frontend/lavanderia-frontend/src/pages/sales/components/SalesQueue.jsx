import React, { useState } from 'react';
import './SalesQueue.css';

export const isSaleReadyToClose = (sale) => {
  if (sale.status !== 'completed') return false;
  if ((sale.items?.services?.length || 0) === 0) return true;
  return !!sale.allServicesCompleted;
};

const getSaleStatusLabel = (sale) => {
  if (sale.status === 'pending') return { text: 'Falta encender', className: 'waiting' };
  if (sale.status === 'finalized') return { text: 'Cerrada', className: 'closed' };

  if (sale.status === 'completed') {
    if (isSaleReadyToClose(sale)) {
      return { text: 'Ya terminó — cerrar', className: 'ready' };
    }
    return { text: 'En marcha', className: 'running' };
  }

  return { text: sale.status, className: 'unknown' };
};

const describeServices = (sale, machines, serviceCycles) => {
  return (sale.items?.services || []).map(svc => {
    const machine = machines.find(m => m._id === svc.machine_id);
    const cycle = serviceCycles.find(s => s._id === svc.service_cycle_id);
    const typeLabel = machine?.tipo === 'secadora' ? 'Secadora' : 'Lavadora';
    const parts = [
      machine ? `${typeLabel} ${machine.numero}` : null,
      cycle?.name || null
    ].filter(Boolean);
    return parts.join(' · ') || 'Servicio';
  });
};

const paymentLabel = (type) => {
  switch (type) {
    case 'efectivo': return 'Efectivo';
    case 'tarjeta_credito': return 'Tarjeta';
    case 'tarjeta_recargable': return 'Tarjeta del cliente';
    default: return type;
  }
};

const SalesQueue = ({
  activeSales,
  finalizedSales,
  machines,
  serviceCycles,
  onActivate,
  onFinalize,
  onFinalizeAllReady,
  finalizingAll,
  activatingId,
  finalizedPage,
  finalizedTotalPages,
  onPrevFinalized,
  onNextFinalized,
  loadingFinalized
}) => {
  const [tab, setTab] = useState('active');
  const [confirmCloseAll, setConfirmCloseAll] = useState(false);

  const readyCount = (activeSales || []).filter(isSaleReadyToClose).length;

  const handleConfirmCloseAll = async () => {
    setConfirmCloseAll(false);
    if (typeof onFinalizeAllReady === 'function') {
      await onFinalizeAllReady();
    }
  };

  return (
    <section className="sales-queue">
      <div className="sales-queue-tabs">
        <button
          type="button"
          className={`sales-queue-tab ${tab === 'active' ? 'active' : ''}`}
          onClick={() => setTab('active')}
        >
          Ventas de hoy
          {activeSales.length > 0 && (
            <span className="tab-badge">{activeSales.length}</span>
          )}
        </button>
        <button
          type="button"
          className={`sales-queue-tab ${tab === 'past' ? 'active' : ''}`}
          onClick={() => setTab('past')}
        >
          Ventas pasadas
        </button>
      </div>

      {tab === 'active' && (
        <div className="sales-queue-list">
          {readyCount > 0 && (
            <button
              type="button"
              className="close-all-ready-btn"
              onClick={() => setConfirmCloseAll(true)}
              disabled={finalizingAll}
            >
              {finalizingAll
                ? 'Cerrando…'
                : `Cerrar todas las que ya terminaron (${readyCount})`}
            </button>
          )}

          {activeSales.length === 0 ? (
            <div className="sales-queue-empty">
              <p>No hay ventas de hoy</p>
            </div>
          ) : (
            activeSales.map(sale => {
              const status = getSaleStatusLabel(sale);
              const lines = describeServices(sale, machines, serviceCycles);
              const canActivate = sale.status === 'pending' && (sale.items?.services?.length || 0) > 0;
              const canFinalize = isSaleReadyToClose(sale);

              return (
                <article key={sale._id} className={`sale-card ${status.className}`}>
                  <div className="sale-card-main">
                    <div className="sale-card-top">
                      <span className="sale-card-total">
                        ${Number(sale.total_amount || 0).toFixed(2)}
                      </span>
                      <span className={`sale-status-pill ${status.className}`}>
                        {status.text}
                      </span>
                    </div>
                    <div className="sale-card-date">
                      {new Date(sale.created_at).toLocaleString()}
                    </div>
                    <div className="sale-card-lines">
                      {lines.length > 0
                        ? lines.map((l, i) => <span key={i}>{l}</span>)
                        : <span>Solo productos</span>}
                    </div>
                    <div className="sale-card-payments">
                      {(sale.payment_methods || []).map((pm, i) => (
                        <span key={i}>
                          {paymentLabel(pm.payment_type)}: ${Number(pm.amount || 0).toFixed(2)}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="sale-card-actions">
                    {canActivate && (
                      <button
                        type="button"
                        className="sale-action activate"
                        onClick={() => onActivate(sale._id)}
                        disabled={activatingId === sale._id}
                      >
                        {activatingId === sale._id ? 'Encendiendo…' : 'Encender máquinas'}
                      </button>
                    )}
                    {canFinalize && (
                      <button
                        type="button"
                        className="sale-action finalize"
                        onClick={() => onFinalize(sale._id)}
                      >
                        Cerrar venta
                      </button>
                    )}
                  </div>
                </article>
              );
            })
          )}
        </div>
      )}

      {tab === 'past' && (
        <div className="sales-queue-list">
          {loadingFinalized ? (
            <div className="sales-queue-empty">
              <p>Cargando…</p>
            </div>
          ) : finalizedSales.length === 0 ? (
            <div className="sales-queue-empty">
              <p>No hay ventas pasadas</p>
            </div>
          ) : (
            <>
              {finalizedSales.map(sale => {
                const lines = describeServices(sale, machines, serviceCycles);
                return (
                  <article key={sale._id} className="sale-card closed">
                    <div className="sale-card-main">
                      <div className="sale-card-top">
                        <span className="sale-card-total">
                          ${Number(sale.total_amount || 0).toFixed(2)}
                        </span>
                        <span className="sale-status-pill closed">Cerrada</span>
                      </div>
                      <div className="sale-card-date">
                        {sale.finalized_at
                          ? `Cerrada: ${new Date(sale.finalized_at).toLocaleString()}`
                          : new Date(sale.created_at).toLocaleString()}
                      </div>
                      <div className="sale-card-lines">
                        {lines.length > 0
                          ? lines.map((l, i) => <span key={i}>{l}</span>)
                          : <span>Solo productos</span>}
                      </div>
                    </div>
                  </article>
                );
              })}

              <div className="sales-queue-pagination">
                <button
                  type="button"
                  onClick={onPrevFinalized}
                  disabled={finalizedPage <= 1}
                >
                  ← Anterior
                </button>
                <span>
                  Página {finalizedPage} de {finalizedTotalPages}
                </span>
                <button
                  type="button"
                  onClick={onNextFinalized}
                  disabled={finalizedPage >= finalizedTotalPages}
                >
                  Siguiente →
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {confirmCloseAll && (
        <div className="sales-queue-confirm-overlay" onClick={() => setConfirmCloseAll(false)}>
          <div className="sales-queue-confirm" onClick={e => e.stopPropagation()}>
            <p>¿Cerrar {readyCount} venta{readyCount === 1 ? '' : 's'} que ya acabaron?</p>
            <div className="sales-queue-confirm-btns">
              <button type="button" className="confirm-yes" onClick={handleConfirmCloseAll}>
                Sí, cerrar todas
              </button>
              <button type="button" className="confirm-no" onClick={() => setConfirmCloseAll(false)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default SalesQueue;
