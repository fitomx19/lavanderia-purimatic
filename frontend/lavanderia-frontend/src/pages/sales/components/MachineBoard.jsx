import React, { useState, useMemo } from 'react';
import MoreActions from './MoreActions';
import './MachineBoard.css';

const getMinutesLeft = (estimatedEndAt) => {
  if (!estimatedEndAt) return null;
  const end = new Date(estimatedEndAt);
  const diff = end.getTime() - Date.now();
  if (diff <= 0) return 0;
  return Math.ceil(diff / 60000);
};

const getMachineVisual = (machine) => {
  const estado = machine.estado;
  if (estado === 'fuera_de_servicio') {
    return { className: 'broken', label: 'No funciona', detail: null };
  }
  if (estado === 'disponible') {
    return { className: 'free', label: 'Libre', detail: null };
  }

  const minutesLeft = getMinutesLeft(machine.current_service?.estimated_end_at);
  const nearing = minutesLeft !== null && minutesLeft > 0 && minutesLeft <= 5;

  if (minutesLeft === 0) {
    return { className: 'busy nearing', label: 'Por terminar', detail: 'Ya acabó' };
  }
  if (nearing) {
    return {
      className: 'busy nearing',
      label: 'Por terminar',
      detail: `faltan ${minutesLeft} min`
    };
  }
  return {
    className: 'busy',
    label: 'En marcha',
    detail: minutesLeft != null ? `faltan ${minutesLeft} min` : null
  };
};

const MachineTile = ({ machine }) => {
  const visual = getMachineVisual(machine);
  const isWasher = machine.tipo === 'lavadora';

  return (
    <div className={`machine-tile ${visual.className}`}>
      <div className="machine-tile-icon">{isWasher ? '🧺' : '💨'}</div>
      <div className="machine-tile-number">#{machine.numero}</div>
      <div className="machine-tile-label">{visual.label}</div>
      {visual.detail && <div className="machine-tile-detail">{visual.detail}</div>}
    </div>
  );
};

const MachineBoard = ({
  machines,
  onLiberateMachines,
  onRefresh,
  onFinalizeAllReady,
  readyToCloseCount = 0,
  liberateAnimating,
  finalizingAll
}) => {
  const [onlyFree, setOnlyFree] = useState(false);

  const freeCount = machines.filter(m => m.estado === 'disponible').length;
  const busyCount = machines.length - freeCount;

  const washers = useMemo(() => {
    let list = machines.filter(m => m.tipo === 'lavadora');
    if (onlyFree) list = list.filter(m => m.estado === 'disponible');
    return list.sort((a, b) => (a.numero || 0) - (b.numero || 0));
  }, [machines, onlyFree]);

  const dryers = useMemo(() => {
    let list = machines.filter(m => m.tipo === 'secadora');
    if (onlyFree) list = list.filter(m => m.estado === 'disponible');
    return list.sort((a, b) => (a.numero || 0) - (b.numero || 0));
  }, [machines, onlyFree]);

  return (
    <section className="machine-board">
      <div className="machine-board-header">
        <h2>Máquinas</h2>
        <MoreActions
          onLiberateMachines={onLiberateMachines}
          onRefresh={onRefresh}
          onFinalizeAllReady={onFinalizeAllReady}
          readyToCloseCount={readyToCloseCount}
          liberateAnimating={liberateAnimating}
          finalizingAll={finalizingAll}
        />
      </div>

      <div className="machine-board-filters">
        <span className="machine-board-count">
          {freeCount} libres · {busyCount} ocupadas
        </span>
        <div className="machine-filter-toggle">
          <button
            type="button"
            className={!onlyFree ? 'on' : ''}
            onClick={() => setOnlyFree(false)}
          >
            Todas
          </button>
          <button
            type="button"
            className={onlyFree ? 'on' : ''}
            onClick={() => setOnlyFree(true)}
          >
            Solo libres
          </button>
        </div>
      </div>

      <div className="machine-board-scroll">
        <div className="machine-board-section">
          <h3>Lavadoras</h3>
          <div className="machine-tiles">
            {washers.length === 0 ? (
              <p className="machine-board-empty">
                {onlyFree ? 'No hay lavadoras libres' : 'No hay lavadoras'}
              </p>
            ) : (
              washers.map(m => <MachineTile key={m._id} machine={m} />)
            )}
          </div>
        </div>

        <div className="machine-board-section">
          <h3>Secadoras</h3>
          <div className="machine-tiles">
            {dryers.length === 0 ? (
              <p className="machine-board-empty">
                {onlyFree ? 'No hay secadoras libres' : 'No hay secadoras'}
              </p>
            ) : (
              dryers.map(m => <MachineTile key={m._id} machine={m} />)
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default MachineBoard;
