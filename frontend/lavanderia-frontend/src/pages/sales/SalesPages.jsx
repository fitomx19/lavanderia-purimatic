import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from '../../components/layout/Header';
import { createSale, getSales, completeSale, deactivateMachines, finalizeSale, finalizeReadySales } from '../../services/salesService';
import { getProducts } from '../../services/productoService';
import { getAllActiveWashers, getAllActiveDryers } from '../../services/machineService';
import { getServiceCycles } from '../../services/cycleService';
import NFCPaymentModal from '../../components/NFCPaymentModal';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { io } from 'socket.io-client';
import { API_BASE_URL } from '../../services/apiConfig';
import NewSaleWizard from './components/NewSaleWizard';
import PendingActivations from './components/PendingActivations';
import MachineBoard from './components/MachineBoard';
import SalesQueue, { isSaleReadyToClose } from './components/SalesQueue';
import './SalesPages.css';

const STORE_ID = '65239f60a92d4f5f5f5f5f5f';

const SalesPage = () => {
  const [sales, setSales] = useState([]);
  const [finalizedSales, setFinalizedSales] = useState([]);
  const [finalizedSalesPage, setFinalizedSalesPage] = useState(1);
  const [finalizedSalesTotalPages, setFinalizedSalesTotalPages] = useState(1);
  const [loadingFinalizedSales, setLoadingFinalizedSales] = useState(true);

  const [products, setProducts] = useState([]);
  const [machines, setMachines] = useState([]);
  const [serviceCycles, setServiceCycles] = useState([]);
  const [activeMachineCycles, setActiveMachineCycles] = useState([]);
  const [wizardTotal, setWizardTotal] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [animateDeactivateButton, setAnimateDeactivateButton] = useState(false);
  const [submittingSale, setSubmittingSale] = useState(false);
  const [activatingId, setActivatingId] = useState(null);

  const [showNFCPaymentModal, setShowNFCPaymentModal] = useState(false);
  const [nfcPaymentAmount, setNfcPaymentAmount] = useState(0);
  const nfcSuccessCallbackRef = useRef(null);

  const [activationLoading, setActivationLoading] = useState(false);
  const [forceOpenPendingModal, setForceOpenPendingModal] = useState(false);
  const [showMachinesPanel, setShowMachinesPanel] = useState(false);
  const [showSalesPanel, setShowSalesPanel] = useState(false);
  const [finalizingAll, setFinalizingAll] = useState(false);

  const socketRef = useRef(null);

  const fetchAndUpdateActiveCycles = useCallback(async () => {
    try {
      const allSalesForMachineStatusResponse = await getSales();
      const relevantSalesForMachineStatus = allSalesForMachineStatusResponse.data.filter(
        sale => sale.status !== 'finalized'
      );

      const currentActiveCycles = [];

      relevantSalesForMachineStatus.forEach(sale => {
        sale.items.services.forEach(svc => {
          const machine = machines.find(m => m._id === svc.machine_id);
          const serviceCycle = serviceCycles.find(s => s._id === svc.service_cycle_id);

          if (machine && serviceCycle) {
            const estimatedEndDate = svc.estimated_end_at ? new Date(svc.estimated_end_at) : null;
            const now = new Date();

            let cycleStatusClass = '';
            if (svc.status === 'completed' || (estimatedEndDate && estimatedEndDate < now)) {
              cycleStatusClass = 'completed-cycle';
            } else if (svc.status === 'active' && estimatedEndDate) {
              const timeLeft = estimatedEndDate.getTime() - now.getTime();
              const fiveMinutes = 5 * 60 * 1000;
              if (timeLeft <= fiveMinutes && timeLeft > 0) {
                cycleStatusClass = 'nearing-completion';
              } else {
                cycleStatusClass = 'active-cycle';
              }
            }

            if (cycleStatusClass === 'active-cycle' || cycleStatusClass === 'nearing-completion') {
              currentActiveCycles.push({
                saleId: sale._id,
                machineNumber: machine.numero,
                machineType: machine.tipo === 'lavadora' ? 'Lavadora' : 'Secadora',
                serviceName: serviceCycle.name,
                estimatedEndTime: estimatedEndDate ? estimatedEndDate.toLocaleString() : 'N/A',
                statusClass: cycleStatusClass,
                isCompleted: svc.status === 'completed' || (estimatedEndDate && estimatedEndDate < now)
              });
            }
          }
        });
      });
      setActiveMachineCycles(currentActiveCycles);
    } catch (err) {
      console.error('Error fetching active cycles:', err);
    }
  }, [machines, serviceCycles]);

  const fetchAndUpdateSalesAndMachines = useCallback(async () => {
    try {
      const salesData = await getSales({ exclude_finalized: true });
      const salesWithServiceCompletion = salesData.data.map(sale => {
        const allServicesCompleted = sale.items.services.every(svc => svc.status === 'completed');
        return { ...sale, allServicesCompleted };
      });
      setSales(salesWithServiceCompletion);

      const finalizedSalesResponse = await getSales({
        status: 'finalized',
        page: finalizedSalesPage,
        per_page: 10
      });
      setFinalizedSales(finalizedSalesResponse.data);
      setFinalizedSalesTotalPages(finalizedSalesResponse.pagination.total_pages);
      setLoadingFinalizedSales(false);

      fetchAndUpdateActiveCycles();
    } catch (err) {
      console.error('Error updating data:', err);
      toast.error('Error al actualizar datos: ' + err.message);
    }
  }, [finalizedSalesPage, fetchAndUpdateActiveCycles]);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const productsData = await getProducts();
        setProducts(productsData.data.products || []);

        const washersData = await getAllActiveWashers();
        const dryersData = await getAllActiveDryers();
        const allMachines = [
          ...(washersData.data?.map(w => ({ ...w, tipo: 'lavadora' })) || []),
          ...(dryersData.data?.map(d => ({ ...d, tipo: 'secadora' })) || [])
        ];
        setMachines(allMachines);

        const serviceCyclesData = await getServiceCycles();
        setServiceCycles(serviceCyclesData.data || []);

        setLoading(false);
      } catch (err) {
        console.error('Error fetching initial data:', err);
        setError(err.message);
        toast.error('Error al cargar datos iniciales: ' + err.message);
        setLoading(false);
      }
    };
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (!loading && machines.length > 0 && serviceCycles.length > 0) {
      fetchAndUpdateSalesAndMachines();
    }
  }, [loading, fetchAndUpdateSalesAndMachines]);

  useEffect(() => {
    if (!socketRef.current) {
      socketRef.current = io(API_BASE_URL || undefined, {
        autoConnect: true,
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
        timeout: 20000
      });

      socketRef.current.on('connect', () => {
        console.log('Conectado al servidor WebSocket');
      });

      socketRef.current.on('new_sale', () => {
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('sale_updated', () => {
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('sale_finalized', () => {
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('machine_status_updated', () => {});

      socketRef.current.on('machine_updated', (data) => {
        const { machine_id, machine_data, operation } = data;

        setMachines(prevMachines =>
          prevMachines.map(machine =>
            machine._id === machine_id ? { ...machine, ...machine_data } : machine
          )
        );

        if (operation === 'activated') {
          toast.success(`Máquina ${machine_data.numero} encendida`);
        } else if (operation === 'available') {
          toast.success(`Máquina ${machine_data.numero} libre`);
        }

        fetchAndUpdateActiveCycles();
      });

      socketRef.current.on('services_completed', (data) => {
        toast.success(`${data.count} servicio(s) terminaron solos`, {
          autoClose: 8000,
          hideProgressBar: false
        });
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('disconnect', (reason) => {
        console.log('Desconectado del servidor WebSocket:', reason);
      });

      socketRef.current.on('connect_error', (err) => {
        console.error('Error de conexión WebSocket:', err);
      });
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleWizardSubmit = async ({
    products: productsPayload,
    services: servicesPayload,
    payment_methods,
    ticketTotal,
    serviceSelections
  }) => {
    try {
      if (productsPayload.length === 0 && servicesPayload.length === 0) {
        toast.error('Agrega al menos un producto o un servicio.');
        return false;
      }
      if (payment_methods.length === 0) {
        toast.error('Agrega al menos una forma de pago.');
        return false;
      }

      const totalPaymentsAmount = payment_methods.reduce((sum, pm) => sum + pm.amount, 0);
      if (totalPaymentsAmount <= 0) {
        toast.error('El monto a cobrar debe ser mayor a cero.');
        return false;
      }

      const nfcPayments = payment_methods.filter(
        pm => pm.payment_type === 'tarjeta_recargable' && pm.nfc_uid
      );
      for (const nfcPayment of nfcPayments) {
        if (!nfcPayment.validated) {
          toast.error('Acerca la tarjeta del cliente antes de cobrar.');
          return false;
        }
      }

      const unvalidatedNfc = payment_methods.filter(
        pm => pm.payment_type === 'tarjeta_recargable' && !pm.validated
      );
      if (unvalidatedNfc.length > 0) {
        toast.error('Acerca la tarjeta del cliente antes de cobrar.');
        return false;
      }

      setSubmittingSale(true);

      const itemsToSend = [
        ...productsPayload.map(product => ({
          product_id: product.product_id,
          quantity: product.quantity
        })),
        ...servicesPayload.map(svc => {
          const selectedCycle = serviceCycles.find(cycle => cycle._id === svc.service_cycle_id);
          const serviceData = { service_cycle_id: svc.service_cycle_id };

          if (svc.service_type === 'encargo_lavado') {
            serviceData.weight_kg = svc.weight_kg;
            serviceData.machine_id = svc.machine_id;
            serviceData.price =
              parseFloat(selectedCycle?.price_per_kg || 0) * (svc.weight_kg || 0);
          } else {
            serviceData.machine_id = svc.machine_id;
            serviceData.price = parseFloat(selectedCycle?.price || 0);
          }
          return serviceData;
        })
      ];

      const saleDataToSend = {
        store_id: STORE_ID,
        items: itemsToSend,
        payment_methods: payment_methods.map(pm => ({
          payment_type: pm.payment_type,
          amount: pm.amount,
          ...(pm.card_id && { card_id: pm.card_id }),
          ...(pm.nfc_uid && { nfc_uid: pm.nfc_uid })
        }))
      };

      const response = await createSale(saleDataToSend);
      toast.success(response.message || 'Venta cobrada');

      await fetchAndUpdateSalesAndMachines();

      if (servicesPayload.length > 0) {
        setForceOpenPendingModal(true);
      }

      setWizardTotal(0);
      return true;
    } catch (err) {
      const msg = err?.message || err?.error || 'Error al cobrar';
      toast.error('Error al cobrar: ' + msg);
      return false;
    } finally {
      setSubmittingSale(false);
    }
  };

  const handleActivateSale = async (saleId) => {
    if (!saleId) return;
    setActivatingId(saleId);
    setActivationLoading(true);
    try {
      const response = await completeSale(saleId);
      toast.success(response.message || 'Máquinas encendidas');
      toast.success('Máquinas activadas correctamente');
      await fetchAndUpdateSalesAndMachines();
      setAnimateDeactivateButton(true);
      setTimeout(() => setAnimateDeactivateButton(false), 2000);
    } catch (err) {
      const apiMsg = err?.message || err?.response?.data?.message;
      const errorType = err?.errors?.error_type || err?.response?.data?.errors?.error_type;
      if (errorType === 'esp32_activation_failed') {
        toast.error(`No se pudo encender la máquina: ${apiMsg || 'revisa el equipo'}`);
      } else {
        toast.error('Error al encender: ' + (apiMsg || 'inténtalo de nuevo'));
      }
    } finally {
      setActivatingId(null);
      setActivationLoading(false);
    }
  };

  const handleDeactivateMachines = async () => {
    try {
      const response = await deactivateMachines();
      toast.success(response.message || 'Máquinas liberadas');
      fetchAndUpdateSalesAndMachines();
    } catch (err) {
      toast.error('Error al liberar máquinas: ' + (err.message || err));
    }
  };

  const handleFinalizeSale = async (saleId) => {
    try {
      const response = await finalizeSale(saleId);
      toast.success(response.message || 'Venta cerrada');
      fetchAndUpdateSalesAndMachines();
    } catch (err) {
      toast.error(
        'Error al cerrar la venta: ' +
          (err.response ? err.response.data.message : err.message)
      );
    }
  };

  const handleFinalizeAllReady = async () => {
    setFinalizingAll(true);
    try {
      const response = await finalizeReadySales();
      const closedCount = response?.data?.closed_count ?? 0;
      toast.success(response.message || `Se cerraron ${closedCount} ventas`);
      await fetchAndUpdateSalesAndMachines();
    } catch (err) {
      toast.error('Error al cerrar ventas: ' + (err.message || err));
    } finally {
      setFinalizingAll(false);
    }
  };

  const handleOpenNFC = (amount, onSuccess) => {
    if (!amount || amount <= 0) {
      toast.error('Ingresa un monto válido antes de usar la tarjeta');
      return;
    }
    nfcSuccessCallbackRef.current = onSuccess;
    setNfcPaymentAmount(amount);
    setShowNFCPaymentModal(true);
  };

  const handleNFCPaymentSuccess = (paymentData) => {
    if (nfcSuccessCallbackRef.current) {
      nfcSuccessCallbackRef.current(paymentData);
      nfcSuccessCallbackRef.current = null;
    }
    toast.success(
      `Tarjeta lista: ${paymentData.card_data?.client_name || 'cliente'} — $${paymentData.amount.toFixed(2)}`
    );
    setShowNFCPaymentModal(false);
    setNfcPaymentAmount(0);
  };

  const handleNFCPaymentError = (errMsg) => {
    toast.error(`Error con la tarjeta: ${errMsg}`);
    setShowNFCPaymentModal(false);
    nfcSuccessCallbackRef.current = null;
    setNfcPaymentAmount(0);
  };

  const handleNextFinalizedPage = async () => {
    if (finalizedSalesPage < finalizedSalesTotalPages) {
      setLoadingFinalizedSales(true);
      try {
        const data = await getSales({
          status: 'finalized',
          page: finalizedSalesPage + 1,
          per_page: 10
        });
        setFinalizedSales(data.data);
        setFinalizedSalesPage(prev => prev + 1);
      } catch (err) {
        toast.error(
          'Error al cargar más ventas: ' +
            (err.response ? err.response.data.message : err.message)
        );
      } finally {
        setLoadingFinalizedSales(false);
      }
    }
  };

  const handlePrevFinalizedPage = async () => {
    if (finalizedSalesPage > 1) {
      setLoadingFinalizedSales(true);
      try {
        const data = await getSales({
          status: 'finalized',
          page: finalizedSalesPage - 1,
          per_page: 10
        });
        setFinalizedSales(data.data);
        setFinalizedSalesPage(prev => prev - 1);
      } catch (err) {
        toast.error(
          'Error al cargar ventas: ' +
            (err.response ? err.response.data.message : err.message)
        );
      } finally {
        setLoadingFinalizedSales(false);
      }
    }
  };

  const pendingSales = sales.filter(s => s.status === 'pending');

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <span>Cargando…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <div className="error-icon">⚠️</div>
        <span>Error: {error}</span>
      </div>
    );
  }

  return (
    <div className="sales-layout">
      <Header />

      <div className="main-content pos-layout">
        <PendingActivations
          pendingSales={pendingSales}
          machines={machines}
          serviceCycles={serviceCycles}
          onActivate={handleActivateSale}
          activatingId={activatingId}
          forceOpen={forceOpenPendingModal}
          onForceOpenHandled={() => setForceOpenPendingModal(false)}
        />

        <NewSaleWizard
          products={products}
          serviceCycles={serviceCycles}
          machines={machines}
          submitting={submittingSale}
          onSubmit={handleWizardSubmit}
          onOpenNFC={handleOpenNFC}
          onTicketChange={setWizardTotal}
        />

        <div className="pos-bottom-actions">
          <button
            type="button"
            className="pos-bottom-btn"
            onClick={() => setShowMachinesPanel(true)}
          >
            Ver máquinas
          </button>
          <button
            type="button"
            className="pos-bottom-btn"
            onClick={() => setShowSalesPanel(true)}
          >
            Ver ventas
            {sales.length > 0 && <span className="pos-bottom-badge">{sales.length}</span>}
          </button>
        </div>
      </div>

      {showMachinesPanel && (
        <div className="pos-panel-overlay" onClick={() => setShowMachinesPanel(false)}>
          <div className="pos-panel" onClick={e => e.stopPropagation()}>
            <div className="pos-panel-header">
              <h2>Máquinas</h2>
              <button type="button" className="pos-panel-close" onClick={() => setShowMachinesPanel(false)}>
                Cerrar
              </button>
            </div>
            <MachineBoard
              machines={machines}
              onLiberateMachines={handleDeactivateMachines}
              onRefresh={fetchAndUpdateSalesAndMachines}
              onFinalizeAllReady={handleFinalizeAllReady}
              readyToCloseCount={sales.filter(isSaleReadyToClose).length}
              liberateAnimating={animateDeactivateButton}
              finalizingAll={finalizingAll}
            />
          </div>
        </div>
      )}

      {showSalesPanel && (
        <div className="pos-panel-overlay" onClick={() => setShowSalesPanel(false)}>
          <div className="pos-panel pos-panel-wide" onClick={e => e.stopPropagation()}>
            <div className="pos-panel-header">
              <h2>Ventas</h2>
              <button type="button" className="pos-panel-close" onClick={() => setShowSalesPanel(false)}>
                Cerrar
              </button>
            </div>
            <SalesQueue
              activeSales={sales}
              finalizedSales={finalizedSales}
              machines={machines}
              serviceCycles={serviceCycles}
              onActivate={handleActivateSale}
              onFinalize={handleFinalizeSale}
              onFinalizeAllReady={handleFinalizeAllReady}
              finalizingAll={finalizingAll}
              activatingId={activatingId}
              finalizedPage={finalizedSalesPage}
              finalizedTotalPages={finalizedSalesTotalPages}
              onPrevFinalized={handlePrevFinalizedPage}
              onNextFinalized={handleNextFinalizedPage}
              loadingFinalized={loadingFinalizedSales}
            />
          </div>
        </div>
      )}

      <NFCPaymentModal
        isOpen={showNFCPaymentModal}
        onClose={() => {
          setShowNFCPaymentModal(false);
          nfcSuccessCallbackRef.current = null;
        }}
        amount={nfcPaymentAmount}
        onPaymentSuccess={handleNFCPaymentSuccess}
        onPaymentError={handleNFCPaymentError}
      />

      <ToastContainer
        position="bottom-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="colored"
      />
    </div>
  );
};

export default SalesPage;
