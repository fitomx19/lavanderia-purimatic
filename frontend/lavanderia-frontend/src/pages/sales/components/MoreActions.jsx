import React, { useState } from 'react';
import './MoreActions.css';

const MoreActions = ({
  onLiberateMachines,
  onRefresh,
  onFinalizeAllReady,
  readyToCloseCount = 0,
  liberateAnimating,
  finalizingAll
}) => {
  const [open, setOpen] = useState(false);
  const [confirmLiberate, setConfirmLiberate] = useState(false);
  const [confirmCloseAll, setConfirmCloseAll] = useState(false);

  const handleConfirmLiberate = async () => {
    setConfirmLiberate(false);
    setOpen(false);
    await onLiberateMachines();
  };

  const handleConfirmCloseAll = async () => {
    setConfirmCloseAll(false);
    setOpen(false);
    if (typeof onFinalizeAllReady === 'function') {
      await onFinalizeAllReady();
    }
  };

  return (
    <div className="more-actions">
      <button
        type="button"
        className="more-actions-toggle"
        onClick={() => setOpen(prev => !prev)}
        aria-expanded={open}
      >
        Otras opciones
        <span className={`more-actions-chevron ${open ? 'open' : ''}`}>▼</span>
      </button>

      {open && (
        <div className="more-actions-menu">
          <button
            type="button"
            className={`more-actions-item ${liberateAnimating ? 'pulse' : ''}`}
            onClick={() => setConfirmLiberate(true)}
          >
            Marcar libres las que ya acabaron
          </button>
          {readyToCloseCount > 0 && (
            <button
              type="button"
              className="more-actions-item"
              onClick={() => setConfirmCloseAll(true)}
              disabled={finalizingAll}
            >
              {finalizingAll
                ? 'Cerrando ventas…'
                : `Cerrar todas las que ya terminaron (${readyToCloseCount})`}
            </button>
          )}
          <button
            type="button"
            className="more-actions-item"
            onClick={() => {
              setOpen(false);
              onRefresh();
            }}
          >
            Actualizar pantalla
          </button>
        </div>
      )}

      {confirmLiberate && (
        <div className="more-actions-confirm-overlay" onClick={() => setConfirmLiberate(false)}>
          <div className="more-actions-confirm" onClick={e => e.stopPropagation()}>
            <p>¿Marcar libres las máquinas que ya acabaron?</p>
            <div className="more-actions-confirm-btns">
              <button type="button" className="confirm-yes" onClick={handleConfirmLiberate}>
                Sí, marcar libres
              </button>
              <button type="button" className="confirm-no" onClick={() => setConfirmLiberate(false)}>
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmCloseAll && (
        <div className="more-actions-confirm-overlay" onClick={() => setConfirmCloseAll(false)}>
          <div className="more-actions-confirm" onClick={e => e.stopPropagation()}>
            <p>
              ¿Cerrar {readyToCloseCount} venta{readyToCloseCount === 1 ? '' : 's'} que ya
              acabaron?
            </p>
            <div className="more-actions-confirm-btns">
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
    </div>
  );
};

export default MoreActions;
