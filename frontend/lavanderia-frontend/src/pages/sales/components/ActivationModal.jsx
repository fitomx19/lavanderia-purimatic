import React from 'react';
import './ActivationModal.css';

const ActivationModal = ({
  isOpen,
  saleSummary,
  onConfirm,
  onLater,
  loading
}) => {
  if (!isOpen) return null;

  const services = saleSummary?.services || [];

  return (
    <div className="activation-modal-overlay">
      <div className="activation-modal" role="dialog" aria-modal="true">
        <h2>Venta lista</h2>
        <p className="activation-modal-lead">
          ¿Encender las máquinas ahora?
        </p>

        {services.length > 0 ? (
          <ul className="activation-service-list">
            {services.map((svc, idx) => (
              <li key={idx}>
                <span className="activation-service-main">
                  {svc.machineLabel} · {svc.serviceName}
                </span>
                {svc.durationLabel && (
                  <span className="activation-service-meta">{svc.durationLabel}</span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="activation-modal-note">
            Esta venta solo tiene productos. No hay máquinas que encender.
          </p>
        )}

        <div className="activation-modal-actions">
          {services.length > 0 ? (
            <>
              <button
                type="button"
                className="activation-btn-yes"
                onClick={onConfirm}
                disabled={loading}
              >
                {loading ? 'Encendiendo…' : 'Sí, encender máquinas'}
              </button>
              <button
                type="button"
                className="activation-btn-later"
                onClick={onLater}
                disabled={loading}
              >
                Después
              </button>
            </>
          ) : (
            <button
              type="button"
              className="activation-btn-yes"
              onClick={onLater}
            >
              Continuar
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ActivationModal;
