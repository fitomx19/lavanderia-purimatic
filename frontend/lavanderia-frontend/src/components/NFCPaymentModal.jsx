// CREAR NUEVO ARCHIVO: src/components/NFCPaymentModal.jsx

import React, { useState, useEffect } from 'react';
import { validateNFCPayment, processNFCPayment, getNFCStatusForSales } from '../services/salesService';
import './NFCPaymentModal.css';

const NFCPaymentModal = ({ 
  isOpen, 
  onClose, 
  amount, 
  onPaymentSuccess, 
  onPaymentError 
}) => {
  const [nfcStatus, setNfcStatus] = useState('checking'); // checking, available, unavailable
  const [paymentState, setPaymentState] = useState('idle'); // idle, waiting, validating, confirmed, processing, success, error
  const [cardData, setCardData] = useState(null);
  const [nfcUid, setNfcUid] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [logs, setLogs] = useState([]);
  const [validatedAmount, setValidatedAmount] = useState(0);

  // Verificar estado NFC al abrir modal
  useEffect(() => {
    if (isOpen) {
      checkNFCStatus();
      resetModalState();
    }
  }, [isOpen]);

  const resetModalState = () => {
    setPaymentState('idle');
    setCardData(null);
    setNfcUid(null);
    setErrorMessage('');
    setLogs([]);
    setValidatedAmount(amount);
  };

  const checkNFCStatus = async () => {
    try {
      setNfcStatus('checking');
      const response = await getNFCStatusForSales();
      if (response.success && response.data.connected) {
        setNfcStatus('available');
      } else {
        setNfcStatus('unavailable');
        setErrorMessage('Lector NFC no disponible');
      }
    } catch (error) {
      setNfcStatus('unavailable');
      setErrorMessage('Error al verificar lector NFC: ' + error.message);
    }
  };

  const handleStartPayment = async () => {
    console.log('🔍 [NFCPaymentModal] Iniciando handleStartPayment');
    console.log('🔍 [NFCPaymentModal] validatedAmount:', validatedAmount);
    
    try {
      console.log('🔍 [NFCPaymentModal] Cambiando estado a waiting');
      setPaymentState('waiting');
      setErrorMessage('');
      setLogs(['Esperando tarjeta NFC...']);

      console.log('🔍 [NFCPaymentModal] Llamando a validateNFCPayment con:', { validatedAmount, timeout: 30 });
      const response = await validateNFCPayment(validatedAmount, 30);
      
      console.log('🔍 [NFCPaymentModal] Respuesta de validateNFCPayment:', response);
      
      if (response.success) {
        console.log('✅ [NFCPaymentModal] Validación exitosa, configurando datos de tarjeta');
        setPaymentState('confirmed');
        console.log('🔍 [NFCPaymentModal] response.data:', response);
        setCardData(response.data.card_data);
        setNfcUid(response.data.nfc_uid);

/*         {
            "data": {
                "card_data": {
                    "card_id": "6866df6054802d62f0032d31",
                    "card_number": "412174099687",
                    "client_id": "6866d4e614f19bf5e0dd6c3c",
                    "client_name": "Pedro González",
                    "current_balance": 139,
                    "nfc_uid": "91AC001E",
                    "remaining_balance": 129
                },
                "logs": [
                    "[2025-07-20T19:20:42.834875] INFO - ⏳ Esperando tarjeta NFC por 30 segundos...",
                    "[2025-07-20T19:20:42.834875] INFO - 📖 Intentando leer UID de tarjeta NFC...",
                    "[2025-07-20T19:20:42.847534] INFO - 🔗 Conexión establecida con el lector",
                    "[2025-07-20T19:20:42.848535] INFO - ✅ UID leído exitosamente: 91AC001E",
                    "[2025-07-20T19:20:42.872329] INFO - 🎯 Tarjeta detectada en 0.04s: 91AC001E"
                ],
                "nfc_uid": "91AC001E"
            },
            "message": "Tarjeta válida para pago de $10.00",
            "success": true
        } */
        console.log('🔍 [NFCPaymentModal] nfcUid configurado:', response.data.nfc_uid);
        setLogs(prev => [...prev, ...response.data.logs || [], 'Tarjeta detectada y validada exitosamente']);
      } else {
        console.error('❌ [NFCPaymentModal] Error en validación:', response.message);
        setPaymentState('error');
        setErrorMessage(response.message);
        setCardData(response.errors?.card_data || null);
        setLogs(prev => [...prev, ...response.errors?.logs || [], `Error: ${response.message}`]);
      }
    } catch (error) {
      console.error('❌ [NFCPaymentModal] Error en handleStartPayment:', error);
      setPaymentState('error');
      setErrorMessage('Error al validar pago: ' + error.message);
      setLogs(prev => [...prev, `Error de conexión: ${error.message}`]);
    }
  };

  const handleConfirmPayment = async () => {
    console.log('🔍 [NFCPaymentModal] Iniciando handleConfirmPayment');
    console.log('🔍 [NFCPaymentModal] nfcUid:', nfcUid);
    console.log('🔍 [NFCPaymentModal] validatedAmount:', validatedAmount);
    console.log('🔍 [NFCPaymentModal] cardData:', cardData);
    
    if (!nfcUid) {
      console.error('❌ [NFCPaymentModal] UID NFC no disponible');
      setErrorMessage('UID NFC no disponible');
      return;
    }

    try {
      console.log('🔍 [NFCPaymentModal] Cambiando estado a processing');
      setPaymentState('processing');
      setLogs(prev => [...prev, 'Procesando pago...']);

      console.log('🔍 [NFCPaymentModal] Llamando a processNFCPayment con:', { nfcUid, validatedAmount });
      const response = await processNFCPayment(nfcUid, validatedAmount);
      
      console.log('🔍 [NFCPaymentModal] Respuesta de processNFCPayment:', response);
      
      if (response.success) {
        console.log('✅ [NFCPaymentModal] Pago procesado exitosamente');
        setPaymentState('success');
        setLogs(prev => [...prev, 'Pago procesado exitosamente']);
        
        // Llamar callback de éxito con datos del pago
        const paymentData = {
          payment_type: 'tarjeta_recargable',
          amount: validatedAmount,
          nfc_uid: nfcUid,
          card_id: cardData?.card_id,
          card_data: response.data
        };
        console.log('🔍 [NFCPaymentModal] Llamando onPaymentSuccess con:', paymentData);
        onPaymentSuccess(paymentData);
        
        // Cerrar modal después de 2 segundos
        setTimeout(() => {
          console.log('🔍 [NFCPaymentModal] Cerrando modal automáticamente');
          onClose();
        }, 2000);
      } else {
        console.error('❌ [NFCPaymentModal] Error en la respuesta:', response.message);
        setPaymentState('error');
        setErrorMessage(response.message);
        setLogs(prev => [...prev, `Error al procesar: ${response.message}`]);
      }
    } catch (error) {
      console.error('❌ [NFCPaymentModal] Error en handleConfirmPayment:', error);
      setPaymentState('error');
      setErrorMessage('Error al procesar pago: ' + error.message);
      setLogs(prev => [...prev, `Error de procesamiento: ${error.message}`]);
    }
  };

  const handleCancel = () => {
    onClose();
  };

  const handleRetry = () => {
    resetModalState();
    setNfcStatus('available');
  };

  if (!isOpen) return null;

  return (
    <div className="nfc-payment-modal-overlay">
      <div className="nfc-payment-modal">
        <div className="modal-header">
          <h2>💳 Pago con Tarjeta NFC</h2>
          <button onClick={handleCancel} className="close-button">×</button>
        </div>

        <div className="modal-body">
          {/* Información del pago */}
          <div className="payment-info">
            <div className="amount-display">
              <span className="amount-label">Monto a cobrar:</span>
              <span className="amount-value">${validatedAmount.toFixed(2)}</span>
            </div>
          </div>

          {/* Estado del lector NFC */}
          <div className={`nfc-status ${nfcStatus}`}>
            <div className="status-indicator">
              {nfcStatus === 'checking' && <span className="spinner">🔄</span>}
              {nfcStatus === 'available' && <span className="icon">🟢</span>}
              {nfcStatus === 'unavailable' && <span className="icon">🔴</span>}
            </div>
            <div className="status-text">
              {nfcStatus === 'checking' && 'Verificando lector NFC...'}
              {nfcStatus === 'available' && 'Lector NFC conectado y listo'}
              {nfcStatus === 'unavailable' && 'Lector NFC no disponible'}
            </div>
          </div>

          {/* Área principal según el estado */}
          <div className="payment-area">
            {/* Estado inicial */}
            {paymentState === 'idle' && nfcStatus === 'available' && (
              <div className="idle-state">
                <div className="nfc-icon">📱</div>
                <p>Presiona el botón para iniciar la lectura de la tarjeta</p>
                <button onClick={handleStartPayment} className="start-payment-btn">
                  🚀 Acercar Tarjeta para Pago
                </button>
              </div>
            )}

            {/* Esperando tarjeta */}
            {paymentState === 'waiting' && (
              <div className="waiting-state">
                <div className="nfc-animation">
                  <div className="nfc-waves">
                    <div className="wave"></div>
                    <div className="wave"></div>
                    <div className="wave"></div>
                  </div>
                  <div className="nfc-icon-center">📡</div>
                </div>
                <p className="waiting-text">Acerque la tarjeta al lector NFC...</p>
                <div className="progress-bar">
                  <div className="progress-fill"></div>
                </div>
              </div>
            )}

            {/* Tarjeta confirmada */}
            {paymentState === 'confirmed' && cardData && (
              <div className="confirmed-state">
                <div className="success-icon">✅</div>
                <h3>Tarjeta Detectada</h3>
                <div className="card-info">
                  <div className="info-row">
                    <span className="label">Cliente:</span>
                    <span className="value">{cardData.client_name}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Tarjeta:</span>
                    <span className="value">{cardData.card_number}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Saldo actual:</span>
                    <span className="value balance">${cardData.current_balance?.toFixed(2)}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Saldo después:</span>
                    <span className="value remaining">${cardData.remaining_balance?.toFixed(2)}</span>
                  </div>
                </div>
                <div className="confirm-buttons">
                  <button onClick={handleConfirmPayment} className="confirm-btn">
                    ✓ Confirmar Pago ${validatedAmount.toFixed(2)}
                  </button>
                  <button onClick={handleRetry} className="retry-btn">
                    🔄 Leer Otra Tarjeta
                  </button>
                </div>
              </div>
            )}

            {/* Procesando */}
            {paymentState === 'processing' && (
              <div className="processing-state">
                <div className="processing-spinner">
                  <div className="spinner"></div>
                </div>
                <p>Procesando pago...</p>
              </div>
            )}

            {/* Éxito */}
            {paymentState === 'success' && (
              <div className="success-state">
                <div className="success-icon">🎉</div>
                <h3>¡Pago Exitoso!</h3>
                <p>La venta se creará automáticamente</p>
                <div className="auto-close">Cerrando en 2 segundos...</div>
              </div>
            )}

            {/* Error */}
            {paymentState === 'error' && (
              <div className="error-state">
                <div className="error-icon">❌</div>
                <h3>Error en el Pago</h3>
                <p className="error-message">{errorMessage}</p>
                
                {/* Mostrar datos de tarjeta si están disponibles */}
                {cardData && (
                  <div className="error-card-info">
                    <h4>Información de la Tarjeta:</h4>
                    <div className="info-row">
                      <span className="label">Cliente:</span>
                      <span className="value">{cardData.client_name}</span>
                    </div>
                    <div className="info-row">
                      <span className="label">Saldo actual:</span>
                      <span className="value">${cardData.current_balance?.toFixed(2)}</span>
                    </div>
                  </div>
                )}
                
                <div className="error-buttons">
                  <button onClick={handleRetry} className="retry-btn">
                    🔄 Intentar Nuevamente
                  </button>
                  <button onClick={handleCancel} className="cancel-btn">
                    ❌ Cancelar
                  </button>
                </div>
              </div>
            )}

            {/* NFC no disponible */}
            {nfcStatus === 'unavailable' && (
              <div className="unavailable-state">
                <div className="error-icon">🔴</div>
                <h3>Lector NFC No Disponible</h3>
                <p className="error-message">{errorMessage}</p>
                <div className="unavailable-buttons">
                  <button onClick={checkNFCStatus} className="retry-btn">
                    🔄 Verificar Nuevamente
                  </button>
                  <button onClick={handleCancel} className="cancel-btn">
                    ❌ Cerrar
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Logs en tiempo real */}
          {logs.length > 0 && (
            <div className="logs-section">
              <details>
                <summary>Ver logs del proceso ({logs.length})</summary>
                <div className="logs-container">
                  {logs.map((log, index) => (
                    <div key={index} className="log-entry">
                      <span className="log-time">{new Date().toLocaleTimeString()}</span>
                      <span className="log-message">{log}</span>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button onClick={handleCancel} className="footer-cancel-btn">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
};

export default NFCPaymentModal;