import React, { useEffect, useRef, useState } from 'react';
import { getTransactions } from '../../services/transactionsService';
import { getAllSales } from '../../services/salesService';
import { getAllEmployeesForLookup } from '../../services/employeeService';
import { getAllProductsForLookup } from '../../services/productoService';
import { getAllServiceCyclesForLookup } from '../../services/cycleService';
import { searchClients } from '../../services/clientsService';
import Header from '../../components/layout/Header';
import './TransactionsPage.css';

const TransactionsPage = () => {
  // Ventas por defecto
  const [activeTab, setActiveTab] = useState('sales'); // 'sales' | 'transactions'

  // Estado para transacciones
  const [transactions, setTransactions] = useState([]);
  const [loadingTransactions, setLoadingTransactions] = useState(true);
  const [errorTransactions, setErrorTransactions] = useState(null);
  const [currentPageTransactions, setCurrentPageTransactions] = useState(1);
  const [totalPagesTransactions, setTotalPagesTransactions] = useState(1);
  const [totalTransactions, setTotalTransactions] = useState(0);

  // Estado para ventas
  const [sales, setSales] = useState([]);
  const [loadingSales, setLoadingSales] = useState(true);
  const [errorSales, setErrorSales] = useState(null);
  const [currentPageSales, setCurrentPageSales] = useState(1);
  const [totalPagesSales, setTotalPagesSales] = useState(1);
  const [totalSales, setTotalSales] = useState(0);

  const [perPage, setPerPage] = useState(50);

  // Filtros para transacciones
  const [filterType, setFilterType] = useState('');
  const [filterCardId, setFilterCardId] = useState('');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');
  const [clientQuery, setClientQuery] = useState('');
  const [clientHits, setClientHits] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null); // { _id, nombre, ... }
  const clientSearchTimer = useRef(null);

  // Filtros para ventas
  const [filterStatus, setFilterStatus] = useState('');
  const [filterPaymentType, setFilterPaymentType] = useState('');
  const [filterStartDateSales, setFilterStartDateSales] = useState('');
  const [filterEndDateSales, setFilterEndDateSales] = useState('');
  const [filterFolio, setFilterFolio] = useState('');

  // Estado para empleados (lookup)
  const [employeesMap, setEmployeesMap] = useState({});
  const [employeesLoading, setEmployeesLoading] = useState(true);

  // Estado para productos (lookup)
  const [productsMap, setProductsMap] = useState({});
  const [productsLoading, setProductsLoading] = useState(true);

  // Estado para ciclos de servicio (lookup)
  const [cyclesMap, setCyclesMap] = useState({});
  const [cyclesLoading, setCyclesLoading] = useState(true);

  const fetchTransactions = async () => {
    try {
      setLoadingTransactions(true);
      const filters = {};

      if (filterType) filters.transaction_type = filterType;
      if (filterCardId) filters.card_id = filterCardId;
      if (selectedClient?._id) filters.client_id = selectedClient._id;
      if (filterStartDate) filters.start_date = filterStartDate;
      if (filterEndDate) filters.end_date = filterEndDate;

      const data = await getTransactions(currentPageTransactions, perPage, filters);

      setTransactions(data.data.transactions);
      setTotalPagesTransactions(data.data.pagination.total_pages);
      setTotalTransactions(data.data.pagination.total);
      setErrorTransactions(null);
    } catch (err) {
      setErrorTransactions(err.message);
    } finally {
      setLoadingTransactions(false);
    }
  };

  const fetchSales = async () => {
    try {
      setLoadingSales(true);
      const filters = {};

      if (filterStatus) filters.status = filterStatus;
      if (filterPaymentType) filters.payment_type = filterPaymentType;
      if (filterStartDateSales) filters.start_date = filterStartDateSales;
      if (filterEndDateSales) filters.end_date = filterEndDateSales;
      if (filterFolio.trim()) filters.folio = filterFolio.trim();

      const data = await getAllSales(currentPageSales, perPage, filters);

      setSales(data.data.sales);
      setTotalPagesSales(data.data.pagination.total_pages);
      setTotalSales(data.data.pagination.total);
      setErrorSales(null);
    } catch (err) {
      setErrorSales(err.message);
    } finally {
      setLoadingSales(false);
    }
  };

  const fetchEmployees = async () => {
    try {
      setEmployeesLoading(true);
      const result = await getAllEmployeesForLookup();
      if (result.success) {
        setEmployeesMap(result.employeeMap);
      }
    } catch (err) {
      console.error('Error cargando empleados:', err);
    } finally {
      setEmployeesLoading(false);
    }
  };

  const fetchProducts = async () => {
    try {
      setProductsLoading(true);
      const result = await getAllProductsForLookup();
      if (result.success) {
        setProductsMap(result.productMap);
      }
    } catch (err) {
      console.error('Error cargando productos:', err);
    } finally {
      setProductsLoading(false);
    }
  };

  const fetchCycles = async () => {
    try {
      setCyclesLoading(true);
      const result = await getAllServiceCyclesForLookup();
      if (result.success) {
        setCyclesMap(result.cycleMap);
      }
    } catch (err) {
      console.error('Error cargando ciclos de servicio:', err);
    } finally {
      setCyclesLoading(false);
    }
  };

  const getEmployeeName = (employeeId) => {
    if (!employeeId) return 'Desconocido';
    return employeesMap[employeeId] || `ID: ${employeeId.substring(0, 8)}...`;
  };

  const getProductName = (productId, quantity = 1) => {
    if (!productId) return 'Producto desconocido';
    const name = productsMap[productId] || `ID: ${productId.substring(0, 8)}...`;
    return quantity > 1 ? `${name} (${quantity})` : name;
  };

  const getCycleName = (cycleId) => {
    if (!cycleId) return 'Servicio desconocido';
    return cyclesMap[cycleId] || `ID: ${cycleId.substring(0, 8)}...`;
  };

  const formatSaleItems = (sale) => {
    if (sale.sale_type === 'recarga' || sale.items?.reload) {
      const reload = sale.items?.reload || {};
      const pay = Number(reload.pay_amount ?? sale.pay_amount ?? sale.total_amount ?? 0);
      const credit = Number(reload.credit_amount ?? sale.credit_amount ?? pay);
      const bonus = Number(reload.bonus_amount ?? sale.bonus_amount ?? Math.max(0, credit - pay));
      return {
        products: [],
        services: [
          `Recarga · pagó $${pay.toFixed(2)} · acreditó $${credit.toFixed(2)}` +
            (bonus > 0 ? ` · bono $${bonus.toFixed(2)}` : ''),
        ],
      };
    }

    const products = sale.items?.products || [];
    const services = sale.items?.services || [];

    const productDetails = products.map((product) =>
      getProductName(product.product_id, product.quantity)
    );

    const serviceDetails = services.map((service) =>
      getCycleName(service.service_cycle_id)
    );

    return {
      products: productDetails,
      services: serviceDetails,
    };
  };

  useEffect(() => {
    // Cargar datos de lookup al montar el componente
    fetchEmployees();
    fetchProducts();
    fetchCycles();
  }, []);

  useEffect(() => {
    if (activeTab === 'transactions') {
      fetchTransactions();
    } else {
      fetchSales();
    }
  }, [currentPageTransactions, currentPageSales, perPage, activeTab]);

  // Búsqueda de clientes (debounce) en pestaña de transacciones
  useEffect(() => {
    if (activeTab !== 'transactions') return;
    if (clientSearchTimer.current) clearTimeout(clientSearchTimer.current);
    const q = clientQuery.trim();
    if (q.length < 2 || selectedClient) {
      setClientHits([]);
      return;
    }
    clientSearchTimer.current = setTimeout(async () => {
      try {
        const res = await searchClients(q, 1, 8);
        const list = res.data?.clients || res.data || [];
        setClientHits(Array.isArray(list) ? list : []);
      } catch {
        setClientHits([]);
      }
    }, 300);
    return () => {
      if (clientSearchTimer.current) clearTimeout(clientSearchTimer.current);
    };
  }, [clientQuery, activeTab, selectedClient]);

  const pickClient = (c) => {
    setSelectedClient(c);
    setClientQuery(c.nombre || c.name || '');
    setClientHits([]);
    setFilterCardId('');
    setCurrentPageTransactions(1);
    setTimeout(() => {
      // fetch con el cliente ya seleccionado
      const filters = {};
      if (filterType) filters.transaction_type = filterType;
      if (filterStartDate) filters.start_date = filterStartDate;
      if (filterEndDate) filters.end_date = filterEndDate;
      filters.client_id = c._id;
      setLoadingTransactions(true);
      getTransactions(1, perPage, filters)
        .then((data) => {
          setTransactions(data.data.transactions);
          setTotalPagesTransactions(data.data.pagination.total_pages);
          setTotalTransactions(data.data.pagination.total);
          setErrorTransactions(null);
        })
        .catch((err) => setErrorTransactions(err.message))
        .finally(() => setLoadingTransactions(false));
    }, 0);
  };

  const clearSelectedClient = () => {
    setSelectedClient(null);
    setClientQuery('');
    setClientHits([]);
  };

  const handleApplyFilters = () => {
    if (activeTab === 'transactions') {
      setCurrentPageTransactions(1);
      fetchTransactions();
    } else {
      setCurrentPageSales(1);
      fetchSales();
    }
  };

  const handleClearFilters = () => {
    if (activeTab === 'transactions') {
      setFilterType('');
      setFilterCardId('');
      setFilterStartDate('');
      setFilterEndDate('');
      setSelectedClient(null);
      setClientQuery('');
      setClientHits([]);
      setCurrentPageTransactions(1);
      setLoadingTransactions(true);
      getTransactions(1, perPage, {})
        .then((data) => {
          setTransactions(data.data.transactions);
          setTotalPagesTransactions(data.data.pagination.total_pages);
          setTotalTransactions(data.data.pagination.total);
          setErrorTransactions(null);
        })
        .catch((err) => setErrorTransactions(err.message))
        .finally(() => setLoadingTransactions(false));
    } else {
      setFilterStatus('');
      setFilterPaymentType('');
      setFilterStartDateSales('');
      setFilterEndDateSales('');
      setFilterFolio('');
      setCurrentPageSales(1);
      setLoadingSales(true);
      getAllSales(1, perPage, {})
        .then((data) => {
          setSales(data.data.sales);
          setTotalPagesSales(data.data.pagination.total_pages);
          setTotalSales(data.data.pagination.total);
          setErrorSales(null);
        })
        .catch((err) => setErrorSales(err.message))
        .finally(() => setLoadingSales(false));
    }
  };

  const handleNextPage = () => {
    if (activeTab === 'transactions') {
      if (currentPageTransactions < totalPagesTransactions) {
        setCurrentPageTransactions(currentPageTransactions + 1);
      }
    } else {
      if (currentPageSales < totalPagesSales) {
        setCurrentPageSales(currentPageSales + 1);
      }
    }
  };

  const handlePrevPage = () => {
    if (activeTab === 'transactions') {
      if (currentPageTransactions > 1) {
        setCurrentPageTransactions(currentPageTransactions - 1);
      }
    } else {
      if (currentPageSales > 1) {
        setCurrentPageSales(currentPageSales - 1);
      }
    }
  };

  const getTransactionTypeLabel = (type) => {
    const types = {
      'saldo_inicial': '💰 Saldo Inicial',
      'recarga_manual': '➕ Recarga Manual',
      'recarga_nfc': '📱 Recarga NFC',
      'recarga_venta': '🧾 Recarga (venta)',
      'pago_venta': '💳 Pago en Venta',
      'transferencia_out': '↗️ Transferencia Salida',
      'transferencia_in': '↘️ Transferencia Entrada',
      'ajuste_manual': '🔧 Ajuste Manual'
    };
    return types[type] || type;
  };

  const getTransactionColor = (type) => {
    if (type.includes('recarga') || type === 'saldo_inicial' || type === 'transferencia_in') {
      return 'transaction-positive';
    }
    return 'transaction-negative';
  };

  const getStatusLabel = (status) => {
    const statuses = {
      'pending': '⏳ Pendiente',
      'completed': '✅ Completada',
      'cancelled': '❌ Cancelada',
      'finalized': '🏁 Finalizada'
    };
    return statuses[status] || status;
  };

  const getPaymentTypeLabel = (type) => {
    const types = {
      'efectivo': '💵 Efectivo',
      'tarjeta_credito': '💳 Tarjeta Crédito',
      'tarjeta_recargable': '🎫 Tarjeta Recargable'
    };
    return types[type] || type;
  };

  const loading = activeTab === 'transactions' ? loadingTransactions : loadingSales;
  const error = activeTab === 'transactions' ? errorTransactions : errorSales;
  const isLoadingInitialData = (employeesLoading || productsLoading || cyclesLoading) && (loadingTransactions || loadingSales);

  return (
    <div className="transactions-page-container">
      <Header />
      <h1>Registro de transacciones y ventas</h1>

      {/* Pestañas — Ventas primero / predeterminada */}
      <div className="tabs-container">
        <button
          className={`tab-button ${activeTab === 'sales' ? 'active' : ''}`}
          onClick={() => setActiveTab('sales')}
        >
          Ventas
        </button>
        <button
          className={`tab-button ${activeTab === 'transactions' ? 'active' : ''}`}
          onClick={() => setActiveTab('transactions')}
        >
          Transacciones de tarjetas
        </button>
      </div>

      {/* Contenido de Transacciones */}
      {activeTab === 'transactions' && (
        <>
          {/* Filtros de Transacciones */}
          <div className="filters-section">
            <h3>Filtros</h3>
            <div className="client-search-bar">
              <label htmlFor="client-search-tx">Buscar cliente</label>
              <div className="client-search-row">
                <input
                  id="client-search-tx"
                  type="text"
                  placeholder="Nombre o teléfono — ver todas sus transacciones"
                  value={clientQuery}
                  onChange={(e) => {
                    setClientQuery(e.target.value);
                    if (selectedClient) setSelectedClient(null);
                  }}
                />
                {selectedClient && (
                  <button type="button" className="clear-filters-btn" onClick={clearSelectedClient}>
                    Quitar cliente
                  </button>
                )}
              </div>
              {clientHits.length > 0 && (
                <div className="client-hits">
                  {clientHits.map((c) => (
                    <button
                      key={c._id}
                      type="button"
                      className="client-hit"
                      onClick={() => pickClient(c)}
                    >
                      <strong>{c.nombre || c.name}</strong>
                      {c.telefono ? ` · ${c.telefono}` : ''}
                      {c.saldo_tarjeta_recargable != null
                        ? ` · saldo $${Number(c.saldo_tarjeta_recargable).toFixed(2)}`
                        : ''}
                    </button>
                  ))}
                </div>
              )}
              {selectedClient && (
                <p className="client-selected-hint">
                  Mostrando movimientos de <strong>{selectedClient.nombre || selectedClient.name}</strong>
                </p>
              )}
            </div>
            <div className="filters-grid">
              <div className="filter-item">
                <label>Tipo de Transacción:</label>
                <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                  <option value="">Todos</option>
                  <option value="saldo_inicial">Saldo Inicial</option>
                  <option value="recarga_manual">Recarga Manual</option>
                  <option value="recarga_nfc">Recarga NFC</option>
                  <option value="recarga_venta">Recarga (venta)</option>
                  <option value="pago_venta">Pago en Venta</option>
                  <option value="transferencia_out">Transferencia Salida</option>
                  <option value="transferencia_in">Transferencia Entrada</option>
                  <option value="ajuste_manual">Ajuste Manual</option>
                </select>
              </div>

              <div className="filter-item">
                <label>ID de Tarjeta:</label>
                <input
                  type="text"
                  placeholder="ID de tarjeta..."
                  value={filterCardId}
                  onChange={(e) => setFilterCardId(e.target.value)}
                  disabled={!!selectedClient}
                />
              </div>

              <div className="filter-item">
                <label>Fecha Inicio:</label>
                <input
                  type="date"
                  value={filterStartDate}
                  onChange={(e) => setFilterStartDate(e.target.value)}
                />
              </div>

              <div className="filter-item">
                <label>Fecha Fin:</label>
                <input
                  type="date"
                  value={filterEndDate}
                  onChange={(e) => setFilterEndDate(e.target.value)}
                />
              </div>
            </div>

            <div className="filter-buttons">
              <button onClick={handleApplyFilters} className="apply-filters-btn">
                Aplicar Filtros
              </button>
              <button onClick={handleClearFilters} className="clear-filters-btn">
                Limpiar Filtros
              </button>
            </div>
          </div>

          {isLoadingInitialData ? (
            <div className="loading-message">Cargando datos iniciales...</div>
          ) : loading ? (
            <div className="loading-message">Cargando transacciones...</div>
          ) : error ? (
            <div className="error-message">Error: {error}</div>
          ) : (
            <>
              {/* Resumen de Transacciones */}
              <div className="transactions-summary">
                <p>Total de transacciones: <strong>{totalTransactions}</strong></p>
              </div>

              {/* Tabla de Transacciones */}
              <table className="transactions-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Tipo</th>
                    <th>Tarjeta ID</th>
                    <th>Monto</th>
                    <th>Saldo Antes</th>
                    <th>Saldo Después</th>
                    <th>Empleado</th>
                    <th>Notas</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((transaction) => (
                    <tr key={transaction._id}>
                      <td>{new Date(transaction.created_at).toLocaleString('es-MX')}</td>
                      <td>
                        <span className={`transaction-type ${getTransactionColor(transaction.transaction_type)}`}>
                          {getTransactionTypeLabel(transaction.transaction_type)}
                        </span>
                      </td>
                      <td className="mono-text">{transaction.card_id.substring(0, 8)}...</td>
                      <td className={`amount ${getTransactionColor(transaction.transaction_type)}`}>
                        ${transaction.amount.toFixed(2)}
                      </td>
                      <td>${transaction.balance_before.toFixed(2)}</td>
                      <td>${transaction.balance_after.toFixed(2)}</td>
                      <td>{getEmployeeName(transaction.employee_id)}</td>
                      <td className="notes-cell">{transaction.notes || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Paginación */}
              <div className="pagination-controls">
                <button onClick={handlePrevPage} disabled={currentPageTransactions === 1}>
                  Anterior
                </button>
                <span>
                  Página {currentPageTransactions} de {totalPagesTransactions} ({totalTransactions} transacciones)
                </span>
                <button onClick={handleNextPage} disabled={currentPageTransactions === totalPagesTransactions}>
                  Siguiente
                </button>
              </div>
            </>
          )}
        </>
      )}

      {/* Contenido de Ventas */}
      {activeTab === 'sales' && (
        <>
          {/* Filtros de Ventas */}
          <div className="filters-section">
            <h3>Filtros</h3>
            <div className="folio-search-bar">
              <label htmlFor="folio-scan">Buscar folio / escanear código</label>
              <input
                id="folio-scan"
                type="text"
                placeholder="Ej. 202609-0001 — escanea o escribe y Enter"
                value={filterFolio}
                onChange={(e) => setFilterFolio(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    setCurrentPageSales(1);
                    fetchSales();
                  }
                }}
                autoComplete="off"
              />
            </div>
            <div className="filters-grid">
              <div className="filter-item">
                <label>Estado:</label>
                <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                  <option value="">Todos</option>
                  <option value="pending">Pendiente</option>
                  <option value="completed">Completada</option>
                  <option value="cancelled">Cancelada</option>
                  <option value="finalized">Finalizada</option>
                </select>
              </div>

              <div className="filter-item">
                <label>Tipo de Pago:</label>
                <select value={filterPaymentType} onChange={(e) => setFilterPaymentType(e.target.value)}>
                  <option value="">Todos</option>
                  <option value="efectivo">Efectivo</option>
                  <option value="tarjeta_credito">Tarjeta Crédito</option>
                  <option value="tarjeta_recargable">Tarjeta Recargable</option>
                </select>
              </div>

              <div className="filter-item">
                <label>Fecha Inicio:</label>
                <input
                  type="date"
                  value={filterStartDateSales}
                  onChange={(e) => setFilterStartDateSales(e.target.value)}
                />
              </div>

              <div className="filter-item">
                <label>Fecha Fin:</label>
                <input
                  type="date"
                  value={filterEndDateSales}
                  onChange={(e) => setFilterEndDateSales(e.target.value)}
                />
              </div>
            </div>

            <div className="filter-buttons">
              <button onClick={handleApplyFilters} className="apply-filters-btn">
                Aplicar Filtros
              </button>
              <button onClick={handleClearFilters} className="clear-filters-btn">
                Limpiar Filtros
              </button>
            </div>
          </div>

          {isLoadingInitialData ? (
            <div className="loading-message">Cargando datos iniciales...</div>
          ) : loading ? (
            <div className="loading-message">Cargando ventas...</div>
          ) : error ? (
            <div className="error-message">Error: {error}</div>
          ) : (
            <>
              {/* Resumen de Ventas */}
              <div className="transactions-summary">
                <p>Total de ventas: <strong>{totalSales}</strong></p>
              </div>

              {/* Tabla de Ventas */}
              <table className="sales-table">
                <thead>
                  <tr>
                    <th>Folio</th>
                    <th>Tipo</th>
                    <th>Fecha</th>
                    <th>Cliente</th>
                    <th>Estado</th>
                    <th>Total</th>
                    <th>Métodos de Pago</th>
                    <th>Detalle</th>
                    <th>Empleado</th>
                  </tr>
                </thead>
                <tbody>
                  {sales.map((sale) => {
                    const itemsDetails = formatSaleItems(sale);
                    const isReload = sale.sale_type === 'recarga' || sale.items?.reload;
                    const detailLines = [
                      ...itemsDetails.products,
                      ...itemsDetails.services,
                    ];
                    return (
                      <tr key={sale._id}>
                        <td><strong>{sale.folio || '—'}</strong></td>
                        <td>
                          <span className={`sale-type-badge ${isReload ? 'reload' : 'normal'}`}>
                            {isReload ? 'Recarga' : 'Venta'}
                          </span>
                        </td>
                        <td>{new Date(sale.created_at).toLocaleString('es-MX')}</td>
                        <td>{sale.client_name || '—'}</td>
                        <td>
                          <span className={`sale-status status-${sale.status}`}>
                            {getStatusLabel(sale.status)}
                          </span>
                        </td>
                        <td className="amount-cell">${Number(sale.total_amount || 0).toFixed(2)}</td>
                        <td className="payment-methods-cell">
                          {(sale.payment_methods || []).map((pm, idx) => (
                            <div key={idx} className="payment-method-item">
                              {getPaymentTypeLabel(pm.payment_type)}: ${Number(pm.amount || 0).toFixed(2)}
                            </div>
                          ))}
                        </td>
                        <td className="items-details-cell">
                          {detailLines.length > 0 ? (
                            <div className="items-list">
                              {detailLines.map((line, idx) => (
                                <div key={idx} className="item-detail">
                                  • {line}
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="no-items">—</span>
                          )}
                          {Number(sale.discount_amount || 0) > 0 && (
                            <div className="item-detail savings-line">
                              Ahorro: ${Number(sale.discount_amount).toFixed(2)}
                            </div>
                          )}
                        </td>
                        <td>{getEmployeeName(sale.employee_id)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Paginación */}
              <div className="pagination-controls">
                <button onClick={handlePrevPage} disabled={currentPageSales === 1}>
                  Anterior
                </button>
                <span>
                  Página {currentPageSales} de {totalPagesSales} ({totalSales} ventas)
                </span>
                <button onClick={handleNextPage} disabled={currentPageSales === totalPagesSales}>
                  Siguiente
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default TransactionsPage;
