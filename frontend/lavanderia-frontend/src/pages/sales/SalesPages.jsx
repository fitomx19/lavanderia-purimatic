import React, { useState, useEffect, useCallback, useRef } from 'react';
import Header from '../../components/layout/Header';
import { createSale, getSales, completeSale, deactivateMachines, finalizeSale } from '../../services/salesService';
import { getProducts } from '../../services/productoService';
import { getAllActiveWashers, getAllActiveDryers } from '../../services/machineService';
import { getServiceCycles } from '../../services/cycleService';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './SalesPages.css';
import { io } from 'socket.io-client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

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
  const [newSale, setNewSale] = useState({
    store_id: '65239f60a92d4f5f5f5f5f5f',
    items: {
      products: [],
      services: []
    },
    payment_methods: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalAmount, setTotalAmount] = useState(0);
  const [animateDeactivateButton, setAnimateDeactivateButton] = useState(false);

  // Ref para la conexión WebSocket
  const socketRef = useRef(null);

  // Función para calcular el total
  const calculateTotal = (currentProducts, currentServices) => {
    let total = 0;

    currentProducts.forEach(item => {
      const product = products.find(p => p._id === item.product_id);
      if (product) {
        total += parseFloat(product.precio) * item.quantity;
      }
    });

    currentServices.forEach(item => {
      const serviceCycle = serviceCycles.find(s => s._id === item.service_cycle_id);
      if (serviceCycle) {
        total += parseFloat(serviceCycle.price);
      }
    });
    return total;
  };

  // Nueva función para actualizar solo los ciclos activos de máquinas
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

  // Función para actualizar las ventas y máquinas (separada del WebSocket)
  const fetchAndUpdateSalesAndMachines = useCallback(async () => {
    try {
      const salesData = await getSales({ exclude_finalized: true });
      const salesWithServiceCompletion = salesData.data.map(sale => {
        const allServicesCompleted = sale.items.services.every(svc => svc.status === 'completed');
        return { ...sale, allServicesCompleted };
      });
      setSales(salesWithServiceCompletion);

      const finalizedSalesResponse = await getSales({ status: 'finalized', page: finalizedSalesPage, per_page: 10 });
      setFinalizedSales(finalizedSalesResponse.data);
      setFinalizedSalesTotalPages(finalizedSalesResponse.pagination.total_pages);
      setLoadingFinalizedSales(false);

      fetchAndUpdateActiveCycles();

    } catch (err) {
      console.error('Error updating data:', err);
      toast.error('Error al actualizar datos: ' + err.message);
    }
  }, [finalizedSalesPage, fetchAndUpdateActiveCycles]);

  // useEffect para la carga inicial de datos estáticos
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const productsData = await getProducts();
        setProducts(productsData.data.products || []);

        const washersData = await getAllActiveWashers();
        const dryersData = await getAllActiveDryers();
        const allMachines = [
          ...(washersData.data?.map(w => ({ ...w, tipo: 'lavadora' })) || []),
          ...(dryersData.data?.map(d => ({ ...d, tipo: 'secadora' })) || []),
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

  // useEffect para la actualización periódica de ventas (solo cuando no está cargando)
  useEffect(() => {
    if (!loading && machines.length > 0 && serviceCycles.length > 0) {
      fetchAndUpdateSalesAndMachines();
    }
  }, [loading, fetchAndUpdateSalesAndMachines]);

  // useEffect separado solo para WebSockets (sin dependencias cambiantes)
  useEffect(() => {
    // Solo crear la conexión si no existe
    if (!socketRef.current) {
      console.log('Creando conexión WebSocket...');
      socketRef.current = io(API_BASE_URL, {
        autoConnect: true,
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
        timeout: 20000
      });

      socketRef.current.on('connect', () => {
        console.log('Conectado al servidor WebSocket');
      });

      socketRef.current.on('new_sale', (data) => {
        console.log('Nueva venta recibida por WebSocket:', data);
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('sale_updated', (data) => {
        console.log('Venta actualizada por WebSocket:', data);
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('sale_finalized', (data) => {
        console.log('Venta finalizada por WebSocket:', data);
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('machine_status_updated', () => {
        console.log('Estado de máquinas actualizado por WebSocket.');
        // Eliminado: fetchAndUpdateSalesAndMachines(); // Ahora machine_updated lo maneja
      });

      // Nuevo listener para actualizaciones específicas de máquinas
      socketRef.current.on('machine_updated', (data) => {
        console.log('Máquina actualizada en tiempo real:', data);
        const { machine_id, machine_data, operation } = data;
        
        // Actualizar solo esta máquina específica en el estado
        setMachines(prevMachines => 
          prevMachines.map(machine => 
            machine._id === machine_id ? { ...machine, ...machine_data } : machine
          )
        );
        
        // Mostrar notificación según la operación
        if (operation === 'activated') {
          toast.success(`⚡ Máquina ${machine_data.numero} activada`);
        } else if (operation === 'available') {
          toast.success(`✅ Máquina ${machine_data.numero} disponible`);
        }
        
        // Actualizar ciclos activos (esto ahora depende del estado 'machines' actualizado)
        fetchAndUpdateActiveCycles();
      });

      socketRef.current.on('services_completed', (data) => {
        console.log('Servicios completados detectados por WebSocket:', data);
        toast.success(`🎉 ${data.count} servicio(s) completado(s) automáticamente!`, {
          autoClose: 8000,
          hideProgressBar: false,
        });
        fetchAndUpdateSalesAndMachines();
      });

      socketRef.current.on('disconnect', (reason) => {
        console.log('Desconectado del servidor WebSocket:', reason);
      });

      socketRef.current.on('connect_error', (error) => {
        console.error('Error de conexión WebSocket:', error);
      });
    }

    // Cleanup al desmontar el componente
    return () => {
      if (socketRef.current) {
        console.log('Limpiando conexión WebSocket...');
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, []); // Sin dependencias para evitar reconexiones

  const handleCreateSale = async (e) => {
    e.preventDefault();
    try {
      const itemsToSend = [
        ...newSale.items.products,
        ...newSale.items.services.flatMap(svc => {
          if (svc.service_type === 'mixto') {
            return [
              { service_cycle_id: svc.service_cycle_id, machine_id: svc.washer_id },
              { service_cycle_id: svc.service_cycle_id, machine_id: svc.dryer_id }
            ];
          } else {
            return [{ service_cycle_id: svc.service_cycle_id, machine_id: svc.machine_id }];
          }
        })
      ];

      const saleDataToSend = {
        ...newSale,
        items: itemsToSend
      };

      const response = await createSale(saleDataToSend);
      toast.success(response.message);
      
      fetchAndUpdateSalesAndMachines();

      setNewSale({
        store_id: '65239f60a92d4f5f5f5f5f5f',
        items: {
          products: [],
          services: []
        },
        payment_methods: []
      });
      setTotalAmount(0);

    } catch (err) {
      setError(err.message);
      toast.error('Error al crear la venta: ' + err.message);
    }
  };

  const handleDeactivateMachines = async () => {
    try {
      const response = await deactivateMachines();
      toast.success(response.message);
      fetchAndUpdateSalesAndMachines();

    } catch (err) {
      setError(err.message);
      toast.error('Error al reactivar máquinas: ' + err.message);
    }
  };

  const handleAddProductItem = () => {
    setNewSale(prev => ({
      ...prev,
      items: {
        ...prev.items,
        products: [...prev.items.products, { product_id: '', quantity: 1 }]
      }
    }));
  };

  const handleProductItemChange = (index, field, value) => {
    setNewSale(prev => {
      const updatedProducts = prev.items.products.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      );
      const newTotal = calculateTotal(updatedProducts, prev.items.services);
      setTotalAmount(newTotal);
      return {
        ...prev,
        items: {
          ...prev.items,
          products: updatedProducts
        }
      };
    });
  };

  const handleAddServiceItem = () => {
    setNewSale(prev => ({
      ...prev,
      items: {
        ...prev.items,
        services: [...prev.items.services, { service_cycle_id: '', machine_id: '', service_type: '', washer_id: '', dryer_id: '' }]
      }
    }));
  };

  const handleServiceItemChange = (index, field, value) => {
    setNewSale(prev => {
      const updatedServices = prev.items.services.map((item, i) =>
        i === index ? { ...item, [field]: value } : item
      );

      if (field === 'service_cycle_id') {
        const selectedCycle = serviceCycles.find(cycle => cycle._id === value);
        if (selectedCycle) {
          updatedServices[index].service_type = selectedCycle.service_type;
          updatedServices[index].machine_id = '';
          updatedServices[index].washer_id = '';
          updatedServices[index].dryer_id = '';
        }
      }

      const newTotal = calculateTotal(prev.items.products, updatedServices);
      setTotalAmount(newTotal);
      return {
        ...prev,
        items: {
          ...prev.items,
          services: updatedServices
        }
      };
    });
  };

  const handleAddPaymentMethod = () => {
    setNewSale(prev => ({
      ...prev,
      payment_methods: [...prev.payment_methods, { payment_type: 'efectivo', amount: 0, card_id: '' }]
    }));
  };

  const handlePaymentMethodChange = (index, field, value) => {
    const updatedPayments = newSale.payment_methods.map((method, i) =>
      i === index ? { ...method, [field]: value } : method
    );
    setNewSale(prev => ({
      ...prev,
      payment_methods: updatedPayments
    }));
  };

  const handleFinalizeSale = async (saleId) => {
    try {
      const response = await finalizeSale(saleId);
      toast.success(response.message);
      fetchAndUpdateSalesAndMachines();
    } catch (err) {
      toast.error('Error al finalizar la venta: ' + (err.response ? err.response.data.message : err.message));
    }
  };

  const handleNextFinalizedPage = async () => {
    if (finalizedSalesPage < finalizedSalesTotalPages) {
      setLoadingFinalizedSales(true);
      try {
        const data = await getSales({ status: 'finalized', page: finalizedSalesPage + 1, per_page: 10 });
        setFinalizedSales(data.data);
        setFinalizedSalesPage(prev => prev + 1);
      } catch (err) {
        toast.error('Error al cargar más ventas finalizadas: ' + (err.response ? err.response.data.message : err.message));
      } finally {
        setLoadingFinalizedSales(false);
      }
    }
  };

  const handlePrevFinalizedPage = async () => {
    if (finalizedSalesPage > 1) {
      setLoadingFinalizedSales(true);
      try {
        const data = await getSales({ status: 'finalized', page: finalizedSalesPage - 1, per_page: 10 });
        setFinalizedSales(data.data);
        setFinalizedSalesPage(prev => prev - 1);
      } catch (err) {
        toast.error('Error al cargar ventas finalizadas anteriores: ' + (err.response ? err.response.data.message : err.message));
      } finally {
        setLoadingFinalizedSales(false);
      }
    }
  };

  if (loading) return (
    <div className="loading-container">
      <div className="loading-spinner"></div>
      <span>Cargando datos...</span>
    </div>
  );
  
  if (error) return (
    <div className="error-container">
      <div className="error-icon">⚠️</div>
      <span>Error: {error}</span>
    </div>
  );

  return (
    <div className="sales-layout">
      <Header />
      
      <div className="main-content">
        <div className="page-header">
          <div className="page-title">
            <h1>🏪 Gestión de Ventas</h1>
            <p>Sistema integrado de control y monitoreo</p>
          </div>
          <div className="stats-bar">
            <div className="stat-card">
              <span className="stat-number">{activeMachineCycles.length}</span>
              <span className="stat-label">Máquinas Activas</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">{sales.length}</span>
              <span className="stat-label">Ventas Pendientes</span>
            </div>
            <div className="stat-card">
              <span className="stat-number">${totalAmount.toFixed(2)}</span>
              <span className="stat-label">Total Actual</span>
            </div>
          </div>
        </div>

        <div className="dashboard-grid">
          {/* Control Panel */}
          <div className="control-panel">
            <div className="control-header">
              <h2>🎛️ Panel de Control</h2>
              <div className="auto-monitor-indicator">
                <span className="monitor-dot"></span>
                <span className="monitor-text">Monitoreo Automático Activo</span>
              </div>
            </div>
            <button 
              onClick={handleDeactivateMachines} 
              className={`reactivate-btn ${animateDeactivateButton ? 'animate' : ''}`}
            >
              <span className="btn-icon">🔄</span>
              Reactivar Máquinas
            </button>
            <br></br>

            <button
              onClick={fetchAndUpdateSalesAndMachines}
              className="reactivate-btn"
            >
              <span className="btn-icon">🔄</span>
              Recargar Máquinas
            </button>
          </div>

          {/* Active Machines Monitor */}
          <div className="machines-monitor">
            <div className="monitor-header">
              <h2>⚡ Máquinas en Servicio</h2>
              <div className="monitor-badge">{activeMachineCycles.length} Activas</div>
            </div>
            
            {activeMachineCycles.length > 0 ? (
              <div className="machines-grid">
                {activeMachineCycles.map((cycle, index) => (
                  <div key={cycle.saleId + '-' + index} className={`machine-card ${cycle.statusClass}`}>
                    <div className="machine-header">
                      <span className="machine-type-icon">
                        {cycle.machineType === 'Lavadora' ? '🧺' : '💨'}
                      </span>
                      <div className="machine-info">
                        <h3>#{cycle.machineNumber}</h3>
                        <span className="machine-type">{cycle.machineType}</span>
                      </div>
                    </div>
                    <div className="service-info">
                      <p className="service-name">{cycle.serviceName}</p>
                      <p className="end-time">Finaliza: {cycle.estimatedEndTime}</p>
                      <span className="sale-id">Venta: {cycle.saleId.slice(-6)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">😴</div>
                <p>No hay máquinas en servicio activo</p>
              </div>
            )}
          </div>

          {/* Sales Form */}
          <div className="sales-form-container">
            <div className="form-header">
              <h2>💳 Nueva Venta</h2>
            </div>
            
            <form onSubmit={handleCreateSale} className="modern-form">
              {/* Products Section */}
              <div className="form-section">
                <div className="section-header">
                  <h3>🛍️ Productos</h3>
                  <button type="button" onClick={handleAddProductItem} className="add-btn">
                    <span>+</span> Añadir
                  </button>
                </div>
                
                <div className="items-container">
                  {newSale.items.products.map((item, index) => (
                    <div key={index} className="item-row">
                      <select
                        value={item.product_id}
                        onChange={(e) => handleProductItemChange(index, 'product_id', e.target.value)}
                        className="modern-select"
                        required
                      >
                        <option value="">Selecciona un producto</option>
                        {products.map(product => (
                          <option key={product._id} value={product._id}>
                            {product.nombre} (Stock: {product.stock}) - ${product.precio}
                          </option>
                        ))}
                      </select>
                      <input
                        type="number"
                        placeholder="Cantidad"
                        value={item.quantity}
                        onChange={(e) => handleProductItemChange(index, 'quantity', parseInt(e.target.value))}
                        className="modern-input quantity-input"
                        min="1"
                        required
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Services Section */}
              <div className="form-section">
                <div className="section-header">
                  <h3>⚙️ Servicios</h3>
                  <button type="button" onClick={handleAddServiceItem} className="add-btn">
                    <span>+</span> Añadir
                  </button>
                </div>
                
                <div className="items-container">
                  {newSale.items.services.map((item, index) => (
                    <div key={index} className="service-item">
                      <select
                        value={item.service_cycle_id}
                        onChange={(e) => handleServiceItemChange(index, 'service_cycle_id', e.target.value)}
                        className="modern-select"
                        required
                      >
                        <option value="">Selecciona un ciclo de servicio</option>
                        {serviceCycles.map(cycle => (
                          <option key={cycle._id} value={cycle._id}>
                            {cycle.name} ({cycle.duration_minutes} min) - ${cycle.price}
                          </option>
                        ))}
                      </select>

                      {item.service_type === 'mixto' ? (
                        <div className="machine-selection">
                          <select
                            value={item.washer_id}
                            onChange={(e) => handleServiceItemChange(index, 'washer_id', e.target.value)}
                            className="modern-select"
                            required
                          >
                            <option value="">Lavadora</option>
                            {machines
                              .filter(machine => machine.tipo === 'lavadora')
                              .map(machine => (
                                <option
                                  key={machine._id}
                                  value={machine._id}
                                  disabled={machine.estado !== 'disponible'}
                                  className={machine.estado !== 'disponible' ? 'unavailable' : ''}
                                >
                                  Lavadora {machine.numero} ({machine.estado})
                                </option>
                              ))}
                          </select>
                          <select
                            value={item.dryer_id}
                            onChange={(e) => handleServiceItemChange(index, 'dryer_id', e.target.value)}
                            className="modern-select"
                            required
                          >
                            <option value="">Secadora</option>
                            {machines
                              .filter(machine => machine.tipo === 'secadora')
                              .map(machine => (
                                <option
                                  key={machine._id}
                                  value={machine._id}
                                  disabled={machine.estado !== 'disponible'}
                                  className={machine.estado !== 'disponible' ? 'unavailable' : ''}
                                >
                                  Secadora {machine.numero} ({machine.estado})
                                </option>
                              ))}
                          </select>
                        </div>
                      ) : (
                        <select
                          value={item.machine_id}
                          onChange={(e) => handleServiceItemChange(index, 'machine_id', e.target.value)}
                          className="modern-select"
                          required
                        >
                          <option value="">Selecciona una máquina</option>
                          {machines.map(machine => (
                            <option
                              key={machine._id}
                              value={machine._id}
                              disabled={machine.estado !== 'disponible'}
                              className={machine.estado !== 'disponible' ? 'unavailable' : ''}
                            >
                              {machine.numero} ({machine.marca} - {machine.tipo}) ({machine.estado})
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Payment Methods Section */}
              <div className="form-section">
                <div className="section-header">
                  <h3>💰 Métodos de Pago</h3>
                  <button type="button" onClick={handleAddPaymentMethod} className="add-btn">
                    <span>+</span> Añadir
                  </button>
                </div>
                
                <div className="items-container">
                  {newSale.payment_methods.map((method, index) => (
                    <div key={index} className="payment-row">
                      <select
                        value={method.payment_type}
                        onChange={(e) => handlePaymentMethodChange(index, 'payment_type', e.target.value)}
                        className="modern-select"
                        required
                      >
                        <option value="efectivo">💵 Efectivo</option>
                        <option value="tarjeta_credito">💳 Tarjeta de Crédito</option>
                        <option value="tarjeta_recargable">🎫 Tarjeta Recargable</option>
                      </select>
                      <input
                        type="number"
                        placeholder="Monto"
                        value={method.amount}
                        onChange={(e) => handlePaymentMethodChange(index, 'amount', parseFloat(e.target.value))}
                        className="modern-input"
                        step="0.01"
                        required
                      />
                      {method.payment_type === 'tarjeta_recargable' && (
                        <input
                          type="text"
                          placeholder="ID de Tarjeta"
                          value={method.card_id}
                          onChange={(e) => handlePaymentMethodChange(index, 'card_id', e.target.value)}
                          className="modern-input"
                          required
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-footer">
                <div className="total-display">
                  <span className="total-label">Total:</span>
                  <span className="total-amount">${totalAmount.toFixed(2)}</span>
                </div>
                <button type="submit" className="submit-btn">
                  <span className="btn-icon">🚀</span>
                  Crear Venta
                </button>
              </div>
            </form>
          </div>

          {/* Machine Status */}
          <div className="machine-status-panel">
            <div className="panel-header">
              <h2>🏭 Estado de Máquinas</h2>
            </div>
            
            <div className="machines-list">
              {machines.map(machine => (
                <div key={machine._id} className={`machine-status-card ${machine.estado}`}>
                  <div className="machine-icon">
                    {machine.tipo === 'lavadora' ? '🧺' : '💨'}
                  </div>
                  <div className="machine-details">
                    <h4>#{machine.numero}</h4>
                    <p>{machine.tipo === 'lavadora' ? 'Lavadora' : 'Secadora'}</p>
                    <span className="brand">{machine.marca}</span>
                    <span className="capacity">{machine.capacidad}</span>
                  </div>
                  <div className={`status-indicator ${machine.estado}`}>
                    <span className="status-dot"></span>
                    {machine.estado}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sales History */}
        <div className="history-section">
          <details className="collapsible-section">
            <summary className="section-summary">
              <h2 style={{color: 'var(--text-inverse)'}}>📊 Historial de Ventas</h2>
              <span className="toggle-icon">▼</span>
            </summary>
            
            <div className="table-container">
              <table className="modern-table">
                <thead>
                  <tr>
                    <th>ID Venta</th>
                    <th>Fecha</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th>Métodos de Pago</th>
                    <th>Servicios</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {sales.map(sale => (
                    <tr key={sale._id} className="table-row">
                      <td className="sale-id">{sale._id.slice(-8)}</td>
                      <td>{new Date(sale.created_at).toLocaleDateString()}</td>
                      <td className="amount">${sale.total_amount.toFixed(2)}</td>
                      <td>
                        <span className={`status-badge ${sale.status}`}>
                          {sale.status}
                        </span>
                      </td>
                      <td>
                        <div className="payment-methods">
                          {sale.payment_methods.map(pm => (
                            <div key={pm.payment_type} className="payment-item">
                              {pm.payment_type}: ${pm.amount.toFixed(2)}
                              {pm.card_id && <span className="card-id">({pm.card_id})</span>}
                            </div>
                          ))}
                        </div>
                      </td>
                      <td>
                        <div className="services-list">
                          {sale.items.services.map(svc => {
                            const machine = machines.find(m => m._id === svc.machine_id);
                            const serviceCycle = serviceCycles.find(s => s._id === svc.service_cycle_id);
                            const estimatedEndDate = svc.estimated_end_at ? new Date(svc.estimated_end_at) : null;
                            const now = new Date();

                            let serviceDisplay = `${serviceCycle?.name || 'N/A'}`;
                            let statusClass = '';

                            if (svc.status === 'completed' || (estimatedEndDate && estimatedEndDate < now)) {
                              statusClass = 'completed';
                            } else if (svc.status === 'active' && estimatedEndDate) {
                              const timeLeft = estimatedEndDate.getTime() - now.getTime();
                              const fiveMinutes = 5 * 60 * 1000;
                              if (timeLeft <= fiveMinutes && timeLeft > 0) {
                                statusClass = 'nearing-completion';
                              } else {
                                statusClass = 'active';
                              }
                            }
                            
                            return (
                              <div key={svc.service_cycle_id} className={`service-item ${statusClass}`}>
                                <span className="service-name">{serviceDisplay}</span>
                                <span className="service-price">${svc.price?.toFixed(2) || 'N/A'}</span>
                                {machine && (
                                  <span className="machine-info">
                                    Máquina: {machine.numero}
                                  </span>
                                )}
                                {estimatedEndDate && (
                                  <span className="end-time">
                                    {estimatedEndDate.toLocaleString()}
                                  </span>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </td>
                      <td>
                        <div className="action-buttons">
                          {sale.status === 'pending' && (
                            <button 
                              onClick={async () => {
                                try {
                                  const response = await completeSale(sale._id);
                                  toast.success(response.message);
                                  fetchAndUpdateSalesAndMachines();
                                  setAnimateDeactivateButton(true);
                                  setTimeout(() => setAnimateDeactivateButton(false), 2000);
                                } catch (err) {
                                  toast.error('Error al completar la venta: ' + (err.response ? err.response.data.message : err.message));
                                }
                              }} 
                              className="action-btn complete"
                            >
                              ✅ Completar
                            </button>
                          )}
                          {sale.status === 'completed' && sale.allServicesCompleted && sale.items.services.length > 0 && (
                            <button 
                              onClick={() => handleFinalizeSale(sale._id)} 
                              className="action-btn finalize"
                            >
                              🏁 Finalizar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>

          {/* Finalized Sales */}
          <details className="collapsible-section">
            <summary className="section-summary">
              <h2 style={{color: 'var(--text-inverse)'}}>✅ Ventas Finalizadas</h2>
              <span className="toggle-icon">▼</span>
            </summary>
            
            {loadingFinalizedSales ? (
              <div className="loading-container">
                <div className="loading-spinner"></div>
                <span>Cargando ventas finalizadas...</span>
              </div>
            ) : finalizedSales.length > 0 ? (
              <div className="table-container">
                <table className="modern-table">
                  <thead>
                    <tr>
                      <th>ID Venta</th>
                      <th>Fecha</th>
                      <th>Total</th>
                      <th>Estado</th>
                      <th>Métodos de Pago</th>
                      <th>Servicios</th>
                      <th>Fecha Finalización</th>
                    </tr>
                  </thead>
                  <tbody>
                    {finalizedSales.map(sale => (
                      <tr key={sale._id} className="table-row finalized">
                        <td className="sale-id">{sale._id.slice(-8)}</td>
                        <td>{new Date(sale.created_at).toLocaleDateString()}</td>
                        <td className="amount">${sale.total_amount.toFixed(2)}</td>
                        <td>
                          <span className="status-badge finalized">
                            {sale.status}
                          </span>
                        </td>
                        <td>
                          <div className="payment-methods">
                            {sale.payment_methods.map(pm => (
                              <div key={pm.payment_type} className="payment-item">
                                {pm.payment_type}: ${pm.amount.toFixed(2)}
                                {pm.card_id && <span className="card-id">({pm.card_id})</span>}
                              </div>
                            ))}
                          </div>
                        </td>
                        <td>
                          <div className="services-list">
                            {sale.items.services.map(svc => {
                              const serviceCycle = serviceCycles.find(s => s._id === svc.service_cycle_id);
                              return (
                                <div key={svc.service_cycle_id} className="service-item completed">
                                  <span className="service-name">{serviceCycle?.name || 'N/A'}</span>
                                  <span className="service-price">${svc.price?.toFixed(2) || 'N/A'}</span>
                                </div>
                              );
                            })}
                          </div>
                        </td>
                        <td>{sale.finalized_at ? new Date(sale.finalized_at).toLocaleDateString() : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                <div className="pagination">
                  <button 
                    onClick={handlePrevFinalizedPage} 
                    disabled={finalizedSalesPage === 1}
                    className="pagination-btn"
                  >
                    ← Anterior
                  </button>
                  <span className="pagination-info">
                    Página {finalizedSalesPage} de {finalizedSalesTotalPages}
                  </span>
                  <button 
                    onClick={handleNextFinalizedPage} 
                    disabled={finalizedSalesPage === finalizedSalesTotalPages}
                    className="pagination-btn"
                  >
                    Siguiente →
                  </button>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <p>No hay ventas finalizadas</p>
              </div>
            )}
          </details>
        </div>
      </div>
      
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