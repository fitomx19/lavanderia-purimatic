import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header'; // Importar Header
import { createSale, getSales, completeSale, deactivateMachines, finalizeSale } from '../../services/salesService';
import { getProducts } from '../../services/productoService';
import { getAllActiveWashers, getAllActiveDryers } from '../../services/machineService';
import { getServiceCycles } from '../../services/cycleService';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './SalesPages.css';
import { io } from 'socket.io-client'; // Importar el cliente de Socket.IO

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const SalesPage = () => {
  const [sales, setSales] = useState([]); // Ventas no finalizadas por defecto
  const [finalizedSales, setFinalizedSales] = useState([]); // Nuevas ventas finalizadas
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

        setLoading(false); // Indicar que la carga inicial ha terminado
      } catch (err) {
        console.error('Error fetching initial data:', err);
        setError(err.message);
        toast.error('Error al cargar datos iniciales: ' + err.message);
        setLoading(false); // Asegurarse de quitar el loading incluso en error
      }
    };
    fetchInitialData();
  }, []); // Dependencias vacías para que se ejecute solo una vez al montar

  // useEffect para la actualización periódica de ventas y ciclos de máquinas activos
  useEffect(() => {
    const updateSalesAndMachineCycles = async () => {
      try {
        // Cargar ventas no finalizadas para la tabla principal
        const salesData = await getSales({ exclude_finalized: true });
        const salesWithServiceCompletion = salesData.data.map(sale => {
          const allServicesCompleted = sale.items.services.every(svc => svc.status === 'completed');
          return { ...sale, allServicesCompleted };
        });
        setSales(salesWithServiceCompletion);

        // Cargar ventas finalizadas para la nueva sección
        const finalizedSalesResponse = await getSales({ status: 'finalized', page: finalizedSalesPage, per_page: 10 });
        setFinalizedSales(finalizedSalesResponse.data);
        setFinalizedSalesTotalPages(finalizedSalesResponse.pagination.total_pages);
        setLoadingFinalizedSales(false);

        // Lógica para máquinas en servicio activo
        const allSalesForMachineStatusResponse = await getSales(); // Obtener todas las ventas sin filtro exclude_finalized
        // Filtrar solo las ventas que NO están finalizadas para el estado de las máquinas
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
        console.error('Error updating data in interval:', err);
        // No setear error globalmente para no bloquear la UI por errores de intervalo
        toast.error('Error al actualizar datos periódicamente: ' + err.message);
      }
    };

    // Este useEffect ahora solo se encargará de inicializar los datos y no de un polling constante
    if (!loading) {
      updateSalesAndMachineCycles(); // Ejecutar al montar este useEffect por primera vez para cargar datos iniciales
    }
  }, [loading, machines, serviceCycles, finalizedSalesPage]); // Dependencias para este useEffect

  // Nuevo useEffect para la conexión y manejo de WebSockets
  useEffect(() => {
    const socket = io(API_BASE_URL);

    // Evento de conexión
    socket.on('connect', () => {
      console.log('Conectado al servidor WebSocket');
    });

    // Evento para cuando se crea una nueva venta
    socket.on('new_sale', (data) => {
      console.log('Nueva venta recibida por WebSocket:', data);
      // Refetch de ventas no finalizadas para incluir la nueva venta
      getSales({ exclude_finalized: true }).then(updatedSales => {
        const salesWithServiceCompletion = updatedSales.data.map(sale => {
          const allServicesCompleted = sale.items.services.every(svc => svc.status === 'completed');
          return { ...sale, allServicesCompleted };
        });
        setSales(salesWithServiceCompletion);
      }).catch(err => toast.error('Error al actualizar ventas por WebSocket: ' + err.message));
    });

    // Evento para cuando una venta es actualizada (completada)
    socket.on('sale_updated', (data) => {
      console.log('Venta actualizada por WebSocket:', data);
      // Refetch de ventas no finalizadas y finalizadas
      getSales({ exclude_finalized: true }).then(updatedSales => {
        const salesWithServiceCompletion = updatedSales.data.map(sale => {
          const allServicesCompleted = sale.items.services.every(svc => svc.status === 'completed');
          return { ...sale, allServicesCompleted };
        });
        setSales(salesWithServiceCompletion);
      }).catch(err => toast.error('Error al actualizar ventas por WebSocket: ' + err.message));

      getSales({ status: 'finalized', page: finalizedSalesPage, per_page: 10 }).then(finalizedSalesResponse => {
        setFinalizedSales(finalizedSalesResponse.data);
        setFinalizedSalesTotalPages(finalizedSalesResponse.pagination.total_pages);
      }).catch(err => toast.error('Error al actualizar ventas finalizadas por WebSocket: ' + err.message));
    });

    // Evento para cuando una venta es finalizada
    socket.on('sale_finalized', (data) => {
      console.log('Venta finalizada por WebSocket:', data);
      // Refetch de ventas no finalizadas y finalizadas
      getSales({ exclude_finalized: true }).then(updatedSales => {
        const salesWithServiceCompletion = updatedSales.data.map(sale => {
          const allServicesCompleted = sale.items.services.every(svc => svc.status === 'completed');
          return { ...sale, allServicesCompleted };
        });
        setSales(salesWithServiceCompletion);
      }).catch(err => toast.error('Error al actualizar ventas por WebSocket: ' + err.message));

      getSales({ status: 'finalized', page: finalizedSalesPage, per_page: 10 }).then(finalizedSalesResponse => {
        setFinalizedSales(finalizedSalesResponse.data);
        setFinalizedSalesTotalPages(finalizedSalesResponse.pagination.total_pages);
      }).catch(err => toast.error('Error al actualizar ventas finalizadas por WebSocket: ' + err.message));
    });

    // Evento para cuando el estado de las máquinas es actualizado
    socket.on('machine_status_updated', () => {
      console.log('Estado de máquinas actualizado por WebSocket.');
      // Refetch de ventas para recalcular activeMachineCycles
      getSales().then(allSalesForMachineStatus => {
        const currentActiveCycles = [];
        allSalesForMachineStatus.data.forEach(sale => {
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
      }).catch(err => toast.error('Error al actualizar ciclos de máquinas por WebSocket: ' + err.message));
    });

    // Evento de desconexión
    socket.on('disconnect', () => {
      console.log('Desconectado del servidor WebSocket');
    });

    // Limpiar la conexión al desmontar el componente
    return () => {
      socket.disconnect();
    };
  }, [machines, serviceCycles, finalizedSalesPage]); // Dependencias para re-establecer conexión si cambian

  // Refactorización de funciones para actualizar ventas y máquinas de forma centralizada
  const fetchAndUpdateSalesAndMachines = async () => {
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
      toast.error('Error al actualizar ventas y máquinas: ' + err.message);
    }
  };

  const handleCreateSale = async (e) => {
    e.preventDefault();
    try {
      // Reestructurar los items de servicio para el backend
      const itemsToSend = [
        ...newSale.items.products,
        ...newSale.items.services.flatMap(svc => {
          if (svc.service_type === 'mixto') {
            // Si es mixto, crea dos entradas separadas para lavadora y secadora
            return [
              { service_cycle_id: svc.service_cycle_id, machine_id: svc.washer_id },
              { service_cycle_id: svc.service_cycle_id, machine_id: svc.dryer_id }
            ];
          } else {
            // Para otros tipos, un solo item de servicio
            return [{ service_cycle_id: svc.service_cycle_id, machine_id: svc.machine_id }];
          }
        })
      ];

      const saleDataToSend = {
        ...newSale,
        items: itemsToSend // Usar la lista reestructurada de items
      };

      const response = await createSale(saleDataToSend);
      toast.success(response.message);
      
      // Las actualizaciones de ventas y máquinas ahora se manejan por WebSockets
      // Se llama a fetchAndUpdateSalesAndMachines después de crear la venta
      fetchAndUpdateSalesAndMachines(); // Llamar a la función centralizada

      setNewSale({
        store_id: '65239f60a92d4f5f5f5f5f5f',
        items: {
          products: [],
          services: [] // Mantener la estructura para el frontend
        },
        payment_methods: []
      });
      setTotalAmount(0); // Resetear el total después de la venta

    } catch (err) {
      setError(err.message);
      toast.error('Error al crear la venta: ' + err.message);
    }
  };

  const handleDeactivateMachines = async () => {
    try {
      const response = await deactivateMachines();
      toast.success(response.message);
      // Las máquinas se actualizarán vía WebSocket
      fetchAndUpdateSalesAndMachines(); // Llamar a la función centralizada

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
    // Añadir un nuevo item de servicio con campos para lavadora y secadora para ciclos mixtos
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

      // Si se cambia el service_cycle_id, actualiza el service_type del item
      if (field === 'service_cycle_id') {
        const selectedCycle = serviceCycles.find(cycle => cycle._id === value);
        if (selectedCycle) {
          updatedServices[index].service_type = selectedCycle.service_type;
          // Limpiar los IDs de máquina si se cambia el tipo de servicio
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

  // Nueva función para finalizar una venta
  const handleFinalizeSale = async (saleId) => {
    try {
      const response = await finalizeSale(saleId);
      toast.success(response.message);
      // Las ventas se actualizarán vía WebSocket
      fetchAndUpdateSalesAndMachines(); // Llamar a la función centralizada
    } catch (err) {
      toast.error('Error al finalizar la venta: ' + (err.response ? err.response.data.message : err.message));
    }
  };

  // Funciones de paginación para ventas finalizadas
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

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="sales-layout">
      
      <div className="main-content">
        <Header />
        <div className="sales-content">
          <h1>Gestión de Ventas</h1>

          <div className="sales-actions-and-summary"> {/* Nuevo contenedor */}
            <button onClick={handleDeactivateMachines} className={`deactivate-button ${animateDeactivateButton ? 'animate' : ''}`}>
              Reactivar Máquinas Manualmente
            </button>

            <section className="active-machines-summary-section">
              <h2>Máquinas en Servicio Activo</h2>
              {activeMachineCycles.length > 0 ? (
                <div className="active-machine-table-container">
                  <table className="active-machine-table">
                    <thead>
                      <tr>
                        <th>ID Venta</th>
                        <th>Máquina</th>
                        <th>Tipo</th>
                        <th>Servicio</th>
                        <th>Finaliza Aproximadamente</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeMachineCycles.map((cycle, index) => (
                        <tr key={cycle.saleId + '-' + index} className={cycle.statusClass}> {/* Aplica la clase de estado */}
                          <td>{cycle.saleId}</td>
                          <td>{cycle.machineNumber}</td>
                          <td>{cycle.machineType}</td>
                          <td>{cycle.serviceName}</td>
                          <td>{cycle.estimatedEndTime}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p>No hay máquinas en servicio activo en este momento.</p>
              )}
            </section>
          </div> {/* Fin del nuevo contenedor */}

          <div className="sales-dashboard-layout">
            <section className="create-sale-section">
              <h2>Crear Nueva Venta</h2>
              <form onSubmit={handleCreateSale} className="sale-form">
                <div className="form-group">
                  <h3>Productos</h3>
                  {newSale.items.products.map((item, index) => (
                  <div key={index} className="item-input-group">
                    <select
                      value={item.product_id}
                      onChange={(e) => handleProductItemChange(index, 'product_id', e.target.value)}
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
                      min="1"
                      required
                    />
                  </div>
                ))}
                <button type="button" onClick={handleAddProductItem} className="add-item-button">Añadir Producto</button>
              </div>

              <div className="form-group">
                <h3>Servicios de Máquina</h3>
                {newSale.items.services.map((item, index) => (
                  <div key={index} className="item-input-group">
                    <select
                      value={item.service_cycle_id}
                      onChange={(e) => handleServiceItemChange(index, 'service_cycle_id', e.target.value)}
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
                      <>
                        <select
                          value={item.washer_id}
                          onChange={(e) => handleServiceItemChange(index, 'washer_id', e.target.value)}
                          required
                        >
                          <option value="">Selecciona una lavadora</option>
                          {machines
                            .filter(machine => machine.tipo === 'lavadora') // Cambiado para mostrar todas las lavadoras
                            .map(machine => (
                              <option
                                key={machine._id}
                                value={machine._id}
                                disabled={machine.estado !== 'disponible'} // Deshabilitar si no está disponible
                                style={machine.estado !== 'disponible' ? { backgroundColor: 'yellow' } : {}} // Fondo amarillo si no está disponible
                              >
                                Lavadora {machine.numero} (Estado: {machine.estado})
                              </option>
                            ))}
                        </select>
                        <select
                          value={item.dryer_id}
                          onChange={(e) => handleServiceItemChange(index, 'dryer_id', e.target.value)}
                          required
                        >
                          <option value="">Selecciona una secadora</option>
                          {machines
                            .filter(machine => machine.tipo === 'secadora') // Cambiado para mostrar todas las secadoras
                            .map(machine => (
                              <option
                                key={machine._id}
                                value={machine._id}
                                disabled={machine.estado !== 'disponible'} // Deshabilitar si no está disponible
                                style={machine.estado !== 'disponible' ? { backgroundColor: 'yellow' } : {}} // Fondo amarillo si no está disponible
                              >
                                Secadora {machine.numero} (Estado: {machine.estado})
                              </option>
                            ))}
                        </select>
                      </>
                    ) : (
                      <select
                        value={item.machine_id}
                        onChange={(e) => handleServiceItemChange(index, 'machine_id', e.target.value)}
                        required
                      >
                        <option value="">Selecciona una máquina disponible</option>
                        {machines
                          .map(machine => (
                            <option
                              key={machine._id}
                              value={machine._id}
                              disabled={machine.estado !== 'disponible'} // Deshabilitar si no está disponible
                              style={machine.estado !== 'disponible' ? { backgroundColor: 'yellow' } : {}} // Fondo amarillo si no está disponible
                            >
                              {machine.numero} ({machine.marca} - {machine.tipo}) (Estado: {machine.estado})
                            </option>
                          ))}
                      </select>
                    )}
                  </div>
                ))}
                <button type="button" onClick={handleAddServiceItem} className="add-item-button">Añadir Servicio</button>
              </div>

              <div className="form-group">
                <h3>Métodos de Pago</h3>
                {newSale.payment_methods.map((method, index) => (
                  <div key={index} className="item-input-group">
                    <select
                      value={method.payment_type}
                      onChange={(e) => handlePaymentMethodChange(index, 'payment_type', e.target.value)}
                      required
                    >
                      <option value="efectivo">Efectivo</option>
                      <option value="tarjeta_credito">Tarjeta de Crédito</option>
                      <option value="tarjeta_recargable">Tarjeta Recargable</option>
                    </select>
                    <input
                      type="number"
                      placeholder="Monto"
                      value={method.amount}
                      onChange={(e) => handlePaymentMethodChange(index, 'amount', parseFloat(e.target.value))}
                      step="0.01"
                      required
                    />
                    {method.payment_type === 'tarjeta_recargable' && (
                      <input
                        type="text"
                        placeholder="ID de Tarjeta Recargable"
                        value={method.card_id}
                        onChange={(e) => handlePaymentMethodChange(index, 'card_id', e.target.value)}
                        required
                      />
                    )}
                  </div>
                ))}
                <button type="button" onClick={handleAddPaymentMethod} className="add-item-button">Añadir Método de Pago</button>
              </div>

              <button type="submit" className="submit-sale-button">Crear Venta</button>
              <div className="total-amount">
                <h3>Total: ${totalAmount.toFixed(2)}</h3>
              </div>
            </form>
          </section>

          <section className="machine-list-section">
            <h2>Estado de Máquinas</h2>
            <div className="machine-table-container">
              <table className="machine-table">
                <thead>
                  <tr>
                    <th>Número</th>
                    <th>Tipo</th>
                    <th>Marca</th>
                    <th>Capacidad</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {machines.map(machine => (
                    <tr key={machine._id} style={machine.estado !== 'disponible' ? { backgroundColor: 'yellow' } : {}}>
                      <td>{machine.numero}</td>
                      <td>{machine.tipo === 'lavadora' ? 'Lavadora' : 'Secadora'}</td>
                      <td>{machine.marca}</td>
                      <td>{machine.capacidad}</td>
                      <td>{machine.estado}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

          <details className="sales-history-details">
            <summary><h2>Historial de Ventas</h2></summary>
            <div className="sales-table-container">
              <table className="sales-table">
                <thead>
                  <tr>
                    <th>ID Venta</th>
                    <th>Fecha</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th>Métodos de Pago</th>
                    <th>Servicios</th> {/* Cambiado a Servicios */}
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {sales.map(sale => (
                    <tr key={sale._id}>
                      <td>{sale._id}</td>
                      <td>{new Date(sale.created_at).toLocaleString()}</td>
                      <td>${sale.total_amount.toFixed(2)}</td>
                      <td>{sale.status}</td>
                      <td>
                        {sale.payment_methods.map(pm => (
                          <div key={pm.payment_type}>
                            {pm.payment_type}: ${pm.amount.toFixed(2)}
                            {pm.card_id && ` (Tarjeta: ${pm.card_id})`}
                          </div>
                        ))}
                      </td>
                      <td> {/* Columna de Servicios Activos */}
                        {sale.items.services.map(svc => {
                          const machine = machines.find(m => m._id === svc.machine_id);
                          const serviceCycle = serviceCycles.find(s => s._id === svc.service_cycle_id);
                          const estimatedEndDate = svc.estimated_end_at ? new Date(svc.estimated_end_at) : null;
                          const completedDate = svc.completed_at ? new Date(svc.completed_at) : null;
                          const now = new Date();

                          let serviceDisplay = `${serviceCycle?.name || 'N/A'} - $${svc.price?.toFixed(2) || 'N/A'}`;
                          let machineDisplay = '';
                          let rowClass = '';

                          if (machine) {
                            machineDisplay = `Máquina: ${machine.numero} (${machine.tipo === 'lavadora' ? 'Lavadora' : 'Secadora'})`;
                          }

                          if (svc.status === 'completed' || (estimatedEndDate && estimatedEndDate < now)) {
                            serviceDisplay += '<br />Finalizado';
                            rowClass = 'completed-cycle-text'; // Clase para texto finalizado
                          } else if (svc.status === 'active' && estimatedEndDate) {
                            const timeLeft = estimatedEndDate.getTime() - now.getTime();
                            const fiveMinutes = 5 * 60 * 1000; // 5 minutos en milisegundos
                            if (timeLeft <= fiveMinutes && timeLeft > 0) {
                              serviceDisplay += `<br />Finaliza: ${estimatedEndDate.toLocaleString()}`; // Muestra la hora de finalización
                              rowClass = 'nearing-completion-text'; // Clase para texto cerca de finalizar
                            } else {
                              serviceDisplay += `<br />Finaliza: ${estimatedEndDate.toLocaleString()}`;
                            }
                          }
                          
                          return (
                            <div key={svc.service_cycle_id} className={rowClass}>
                              <span dangerouslySetInnerHTML={{ __html: serviceDisplay }} />
                              {machineDisplay && <div>{machineDisplay}</div>}
                            </div>
                          );
                        })}
                      </td>
                      <td>
                        {sale.status === 'pending' && (
                          <button onClick={async () => {
                            try {
                              const response = await completeSale(sale._id);
                              toast.success(response.message);
                              // Las ventas y máquinas se actualizarán vía WebSocket
                              fetchAndUpdateSalesAndMachines(); // Llamar a la función centralizada

                              // Activar animación del botón
                              setAnimateDeactivateButton(true);
                              setTimeout(() => {
                                setAnimateDeactivateButton(false);
                              }, 2000); // Duración de la animación en ms

                            } catch (err) {
                              toast.error('Error al completar la venta: ' + (err.response ? err.response.data.message : err.message));
                            }
                          }} className="complete-sale-button">Completar Venta</button>
                        )}
                        {sale.status === 'completed' && sale.allServicesCompleted && sale.items.services.length > 0 && (
                          <button onClick={() => handleFinalizeSale(sale._id)} className="finalize-sale-button">Finalizar Venta</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>

          <details className="finalized-sales-details"> {/* Nueva sección para ventas finalizadas */}
            <summary><h2>Historial de Ventas Finalizadas</h2></summary>
            {loadingFinalizedSales ? (
              <div>Cargando ventas finalizadas...</div>
            ) : finalizedSales.length > 0 ? (
              <div className="sales-table-container">
                <table className="sales-table">
                  <thead>
                    <tr>
                      <th>ID Venta</th>
                      <th>Fecha</th>
                      <th>Total</th>
                      <th>Estado</th>
                      <th>Métodos de Pago</th>
                      <th>Servicios</th>
                      <th>Fecha Finalización</th> {/* Nueva columna */}
                    </tr>
                  </thead>
                  <tbody>
                    {finalizedSales.map(sale => (
                      <tr key={sale._id}>
                        <td>{sale._id}</td>
                        <td>{new Date(sale.created_at).toLocaleString()}</td>
                        <td>${sale.total_amount.toFixed(2)}</td>
                        <td>{sale.status}</td>
                        <td>
                          {sale.payment_methods.map(pm => (
                            <div key={pm.payment_type}>
                              {pm.payment_type}: ${pm.amount.toFixed(2)}
                              {pm.card_id && ` (Tarjeta: ${pm.card_id})`}
                            </div>
                          ))}
                        </td>
                        <td>
                          {sale.items.services.map(svc => {
                            const serviceCycle = serviceCycles.find(s => s._id === svc.service_cycle_id);
                            return (
                              <div key={svc.service_cycle_id}>
                                {serviceCycle?.name || 'N/A'} - ${svc.price?.toFixed(2) || 'N/A'}
                              </div>
                            );
                          })}
                        </td>
                        <td>{sale.finalized_at ? new Date(sale.finalized_at).toLocaleString() : 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="pagination-controls">
                  <button onClick={handlePrevFinalizedPage} disabled={finalizedSalesPage === 1}>Anterior</button>
                  <span>Página {finalizedSalesPage} de {finalizedSalesTotalPages}</span>
                  <button onClick={handleNextFinalizedPage} disabled={finalizedSalesPage === finalizedSalesTotalPages}>Siguiente</button>
                </div>
              </div>
            ) : (
              <p>No hay ventas finalizadas.</p>
            )}
          </details>

        </div>
      </div>
      <ToastContainer position="bottom-right" autoClose={5000} hideProgressBar={false} newestOnTop={false} closeOnClick rtl={false} pauseOnFocusLoss draggable pauseOnHover />
    </div>
  );
};

export default SalesPage;
