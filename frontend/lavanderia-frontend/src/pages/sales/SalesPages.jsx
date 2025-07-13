import React, { useState, useEffect } from 'react';
import Sidebar from '../../components/layout/Sidebar';
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
    store_id: '65239f60a92d4f5f5f5f5f5f', // TODO: Obtener dinámicamente o de configuración
    items: {
      products: [],
      services: []
    },
    payment_methods: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const salesData = await getSales();
        setSales(salesData.data);

        const productsData = await getProducts();
        setProducts(productsData.data.products || []); // Asegurar que products sea un array

        const washersData = await getAllActiveWashers();
        const dryersData = await getAllActiveDryers();
        setMachines([...washersData.data, ...dryersData.data]);

        const serviceCyclesData = await getServiceCycles();
        setServiceCycles(serviceCyclesData.data.data || []); // Asegurar que serviceCycles sea un array

      } catch (err) {
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
      const response = await createSale(newSale);
      alert(response.message);
      const updatedSales = await getSales();
      setSales(updatedSales.data);
      setNewSale({
        store_id: '65239f60a92d4f5f5f5f5f5f',
        items: {
          products: [],
          services: []
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
    const updatedProducts = newSale.items.products.map((item, i) =>
      i === index ? { ...item, [field]: value } : item
    );
    setNewSale(prev => ({
      ...prev,
      items: {
        ...prev.items,
        products: updatedProducts
      }
    }));
  };

  const handleAddServiceItem = () => {
    setNewSale(prev => ({
      ...prev,
      items: {
        ...prev.items,
        services: [...prev.items.services, { service_cycle_id: '', machine_id: '' }]
      }
    }));
  };

  const handleServiceItemChange = (index, field, value) => {
    const updatedServices = newSale.items.services.map((item, i) =>
      i === index ? { ...item, [field]: value } : item
    );
    setNewSale(prev => ({
      ...prev,
      items: {
        ...prev.items,
        services: updatedServices
      }
    }));
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
      <Sidebar /> {/* Re-agregado el componente Sidebar */}
      <div className="main-content">
        <Header /> {/* Agregado el componente Header */}
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
                          {product.nombre} (Stock: {product.stock})
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
                    <select
                      value={item.machine_id}
                      onChange={(e) => handleServiceItemChange(index, 'machine_id', e.target.value)}
                      required
                    >
                      <option value="">Selecciona una máquina disponible</option>
                      {machines
                        .filter(machine => machine.estado === 'disponible')
                        .map(machine => (
                          <option key={machine._id} value={machine._id}>
                            {machine.numero} ({machine.marca} - {machine.tipo})
                          </option>
                        ))}
                    </select>
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
          </section>

          <section className="sales-list-section">
            <h2>Historial de Ventas</h2>
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
          </section>
        </div>
      </div>
    </div>
  );
};

export default SalesPage;
