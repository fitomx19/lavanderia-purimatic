import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header'; // Importar Header
import { createSale, getSales, completeSale, deactivateMachines } from '../../services/salesService';
import { getProducts } from '../../services/productoService';
import { getAllActiveWashers, getAllActiveDryers } from '../../services/machineService';
import { getServiceCycles } from '../../services/cycleService';
import './SalesPages.css';

const SalesPage = () => {
  const [sales, setSales] = useState([]);
  const [products, setProducts] = useState([]);
  const [machines, setMachines] = useState([]);
  const [serviceCycles, setServiceCycles] = useState([]);
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

  useEffect(() => {
    const fetchData = async () => {
      try {
        const salesData = await getSales();
        setSales(salesData.data);

        const productsData = await getProducts();
        console.log('Products Data:', productsData);
        setProducts(productsData.data.products || []);

        const washersData = await getAllActiveWashers();
        const dryersData = await getAllActiveDryers();



        console.log('Washers Data:', washersData);
        console.log('Dryers Data:', dryersData);

        const allMachines = [
          ...(washersData.data?.map(w => ({ ...w, tipo: 'lavadora' })) || []),
          ...(dryersData.data?.map(d => ({ ...d, tipo: 'secadora' })) || []),
        ];
        setMachines(allMachines);
        console.log('All Machines State:', allMachines); // Debugging line

        const serviceCyclesData = await getServiceCycles();
        setServiceCycles(serviceCyclesData.data || []);
        console.log('Service Cycles State:', serviceCyclesData.data || []); // Debugging line

      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

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
      alert(response.message);
      const updatedSales = await getSales();
      setSales(updatedSales.data);
      setNewSale({
        store_id: '65239f60a92d4f5f5f5f5f5f',
        items: {
          products: [],
          services: [] // Mantener la estructura para el frontend
        },
        payment_methods: []
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeactivateMachines = async () => {
    try {
      const response = await deactivateMachines();
      alert(response.message);
    } catch (err) {
      setError(err.message);
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

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="sales-layout">
      
      <div className="main-content">
        <Header />
        <div className="sales-content">
          <h1>Gestión de Ventas</h1>

          <button onClick={handleDeactivateMachines} className="deactivate-button">
            Reactivar Máquinas Manualmente
          </button>

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
            </form>
            <div className="total-amount">
              <h3>Total: ${totalAmount.toFixed(2)}</h3>
            </div>
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
                      <td>
                        {sale.status === 'pending' && (
                          <button onClick={() => completeSale(sale._id)} className="complete-sale-button">Completar Venta</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
      </div>
    </div>
  );
};

export default SalesPage;
