import React, { useEffect, useState } from 'react';
import { getClients, deleteClient, createClient, updateClient, createClientCard, getClientCards, addSubtractCardBalance, transferCardBalance, getCardBalance, deleteCard, getNFCStatus, linkCardToNFC, reloadCardViaNFC, queryBalanceViaNFC } from '../../services/clientsService';
import Header from '../../components/layout/Header';
import './ClientsPage.css';

const ClientsPage = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newClient, setNewClient] = useState({
    nombre: '',
    email: '',
    telefono: '',
    direccion: '',
  });
  const [editingClient, setEditingClient] = useState(null);
  const [editFormData, setEditFormData] = useState({
    nombre: '',
    telefono: '',
    direccion: '',
    email: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalClients, setTotalClients] = useState(0);
  const [showCardModal, setShowCardModal] = useState(false);
  const [currentClientCards, setCurrentClientCards] = useState([]);
  const [selectedClientForCard, setSelectedClientForCard] = useState(null);
  const [newCardBalance, setNewCardBalance] = useState('');
  const [showAddSubtractBalanceModal, setShowAddSubtractBalanceModal] = useState(false);
  const [selectedCardForBalance, setSelectedCardForBalance] = useState(null);
  const [amountForBalance, setAmountForBalance] = useState('');
  const [operationForBalance, setOperationForBalance] = useState('add');
  const [showTransferForm, setShowTransferForm] = useState(false);
  const [fromCardId, setFromCardId] = useState('');
  const [toCardId, setToCardId] = useState('');
  const [transferAmount, setTransferAmount] = useState('');


  // ========== ESTADOS NFC ==========
  const [showNFCModal, setShowNFCModal] = useState(false);
  const [nfcOperation, setNfcOperation] = useState(null); // 'linking' | 'reloading' | 'querying'
  const [nfcStatus, setNfcStatus] = useState('idle'); // 'idle' | 'waiting' | 'reading' | 'success' | 'error'
  const [selectedCardForNFC, setSelectedCardForNFC] = useState(null);
  const [reloadAmount, setReloadAmount] = useState('');
  const [nfcReaderStatus, setNfcReaderStatus] = useState({ connected: false });
  const [nfcLogs, setNfcLogs] = useState([]);
  const [queryResult, setQueryResult] = useState(null);


  const fetchClients = async () => {
    try {
      const data = await getClients(currentPage, perPage);
      console.log("data Clientes", data.data.clients)
      setClients(data.data.clients);
      setTotalPages(data.data.pagination.total_pages);
      setTotalClients(data.data.pagination.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClients();
  }, [currentPage, perPage]);

  // ========== EFFECT NFC ==========
  useEffect(() => {
    checkNFCStatus();
    const interval = setInterval(checkNFCStatus, 30000); // Verifica cada 30 segundos el estado del lector NFC
    return () => clearInterval(interval);
  }, []);

  const handleDeleteClient = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este cliente?')) {
      try {
        await deleteClient(id);
        setClients(clients.filter(client => client._id !== id));
        alert('Cliente eliminado exitosamente.');
        fetchClients(); // Añadido para recargar clientes después de eliminar uno
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewClient({ ...newClient, [name]: value });
  };

  const handleCreateClient = async (e) => {
    e.preventDefault();
    try {
      await createClient(newClient);
      alert('Cliente creado exitosamente.');
      setNewClient({
        nombre: '',
        email: '',
        telefono: '',
        direccion: '',
      });
      setShowCreateForm(false);
      fetchClients(); // Añadido para recargar clientes después de crear uno
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEditClick = (client) => {
    setEditingClient(client);
    setEditFormData({ nombre: client.nombre, telefono: client.telefono, direccion: client.direccion, email: client.email });
  };

  const handleEditFormChange = (e) => {
    const { name, value } = e.target;
    setEditFormData({ ...editFormData, [name]: value });
  };

  const handleUpdateClient = async (e) => {
    e.preventDefault();
    try {
      await updateClient(editingClient._id, editFormData);
      alert('Cliente actualizado exitosamente.');
      setEditingClient(null);
      fetchClients(); // Añadido para recargar clientes después de actualizar uno
    } catch (err) {
      setError(err.message);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleManageCardsClick = async (client) => {
    setSelectedClientForCard(client);
    try {
      setCurrentClientCards(client.client_cards || []);
      setShowCardModal(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateCard = async (e) => {
    e.preventDefault();
    try {
      await createClientCard(selectedClientForCard._id, parseFloat(newCardBalance));
      alert('Tarjeta creada exitosamente.');
      setNewCardBalance('');
      handleManageCardsClick(selectedClientForCard); // Refresh cards
      fetchClients(); // Añadido para recargar clientes después de crear una tarjeta
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteCard = async (cardId) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar esta tarjeta?')) {
      try {
        await deleteCard(cardId);
        alert('Tarjeta eliminada exitosamente.');
        handleManageCardsClick(selectedClientForCard); // Refresh cards
        fetchClients(); // Añadido para recargar clientes después de eliminar una tarjeta
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleAddSubtractBalanceClick = (card) => {
    setSelectedCardForBalance(card);
    setAmountForBalance('');
    setOperationForBalance('add');
    setShowAddSubtractBalanceModal(true);
  };

  const handleAddSubtractBalance = async (e) => {
    e.preventDefault();
    try {
      await addSubtractCardBalance(selectedCardForBalance._id, parseFloat(amountForBalance), operationForBalance);
      alert('Saldo de tarjeta actualizado exitosamente.');
      setShowAddSubtractBalanceModal(false);
      handleManageCardsClick(selectedClientForCard); // Refresh cards
      fetchClients(); // Añadido para recargar clientes después de actualizar el saldo
    } catch (err) {
      setError(err.message);
    }
  };

  const handleTransferBalance = async (e) => {
    e.preventDefault();
    try {
      await transferCardBalance(fromCardId, toCardId, parseFloat(transferAmount));
      alert('Transferencia realizada exitosamente.');
      setFromCardId(''); // Clear form fields after successful transfer
      setToCardId('');
      setTransferAmount('');
      handleManageCardsClick(selectedClientForCard); // Refresh cards for the selected client
      fetchClients(); // Añadido para recargar clientes después de transferir saldo
    } catch (err) {
      setError(err.message);
    }
  };

  // ========== FUNCIONES NFC ==========
  const checkNFCStatus = async () => {
    try {
      const result = await getNFCStatus();
      setNfcReaderStatus(result.data);
    } catch (err) {
      console.error('Error checking NFC status:', err);
      setNfcReaderStatus({ connected: false, error: err.message });
    }
  };

  const handleLinkNFCClick = (card) => {
    setSelectedCardForNFC(card);
    setNfcOperation('linking');
    setNfcStatus('idle');
    setNfcLogs([]);
    setShowNFCModal(true);
  };

  const handleReloadNFCClick = (card) => {
    setSelectedCardForNFC(card);
    setNfcOperation('reloading');
    setNfcStatus('idle');
    setReloadAmount('');
    setNfcLogs([]);
    setShowNFCModal(true);
  };

  const handleQueryBalanceNFCClick = () => {
    setSelectedCardForNFC(null);
    setNfcOperation('querying');
    setNfcStatus('idle');
    setNfcLogs([]);
    setQueryResult(null);
    setShowNFCModal(true);
  };

  const handleNFCOperation = async () => {
    setNfcStatus('waiting');
    setNfcLogs(['🔄 Iniciando operación NFC...']);

    try {
      if (nfcOperation === 'linking') {
        setNfcStatus('reading');
        setNfcLogs(prev => [...prev, '📖 Acerque su tarjeta al lector...']);

        const result = await linkCardToNFC(selectedCardForNFC._id);

        setNfcLogs(prev => [...prev, ...(result.data?.logs || []), '✅ Vinculación exitosa']);
        setNfcStatus('success');
        alert(`Tarjeta vinculada exitosamente con UID: ${result.data?.nfc_uid}`);

        // Refresh cards
        const clientCards = await getClientCards(selectedClientForCard._id);
        setCurrentClientCards(clientCards.data || []);
        fetchClients(); // Añadido para recargar clientes después de vincular NFC

      } else if (nfcOperation === 'reloading') {
        if (!reloadAmount || parseFloat(reloadAmount) <= 0) {
          alert('Ingrese un monto válido para recargar');
          setNfcStatus('idle');
          return;
        }

        setNfcStatus('reading');
        setNfcLogs(prev => [...prev, `💳 Acerque tarjeta para recargar $${reloadAmount}...`]);

        const result = await reloadCardViaNFC(parseFloat(reloadAmount));

        setNfcLogs(prev => [...prev, ...(result.data?.logs || []), `✅ Recarga exitosa: $${result.data?.new_balance}`]);
        setNfcStatus('success');
        alert(`Recarga exitosa. Nuevo saldo: $${result.data?.new_balance}`);

        // Refresh cards
        const clientCards = await getClientCards(selectedClientForCard._id);
        setCurrentClientCards(clientCards.data || []);
        fetchClients(); // Añadido para recargar clientes después de recargar NFC
        
      } else if (nfcOperation === 'querying') {
        setNfcStatus('reading');
        setNfcLogs(prev => [...prev, '💳 Acerque tarjeta para consultar saldo...']);

        const result = await queryBalanceViaNFC();

        setNfcLogs(prev => [...prev, ...(result.data?.logs || []), '✅ Consulta exitosa']);
        setNfcStatus('success');
        setQueryResult(result.data);
      }

      setTimeout(() => {
        if (nfcOperation !== 'querying') {
          setShowNFCModal(false);
          setNfcStatus('idle');
        }
      }, 3000);

    } catch (err) {
      setNfcStatus('error');
      setError(err.message);
      setNfcLogs(prev => [...prev, `❌ Error: ${err.message}`]);
      setTimeout(() => setNfcStatus('idle'), 5000);
    }
  };

  if (loading) {
    return (
      <div className="clients-layout">
        <Header />
        <main className="clients-content">
          <p className="clients-muted">Cargando clientes…</p>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="clients-layout">
        <Header />
        <main className="clients-content">
          <div className="clients-msg err">Error: {error}</div>
        </main>
      </div>
    );
  }

  return (
    <div className="clients-layout">
      <Header />
      <main className="clients-content">
        <header className="clients-page-head">
          <div>
            <h1>Gestión de clientes</h1>
            <p className="clients-help">
              Alta de clientes, edición y administración de tarjetas recargables (incluye NFC).
            </p>
          </div>
          <div className="clients-toolbar">
            <button
              type="button"
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="clients-btn clients-btn--primary"
            >
              {showCreateForm ? 'Cancelar' : 'Nuevo cliente'}
            </button>
            <button
              type="button"
              onClick={handleQueryBalanceNFCClick}
              className="clients-btn clients-btn--secondary"
            >
              Consultar saldo NFC
            </button>
          </div>
        </header>

        {showCreateForm && (
          <section className="clients-card">
            <h2>Nuevo cliente</h2>
            <form onSubmit={handleCreateClient} className="clients-form">
              <label>
                Nombre
                <input
                  type="text"
                  name="nombre"
                  placeholder="Nombre completo"
                  value={newClient.nombre}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  name="email"
                  placeholder="correo@ejemplo.com"
                  value={newClient.email}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <label>
                Teléfono
                <input
                  type="text"
                  name="telefono"
                  placeholder="Teléfono"
                  value={newClient.telefono}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <label>
                Dirección
                <input
                  type="text"
                  name="direccion"
                  placeholder="Dirección"
                  value={newClient.direccion}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <div className="clients-form-actions">
                <button type="submit" className="clients-btn clients-btn--primary">
                  Guardar cliente
                </button>
                <button
                  type="button"
                  className="clients-btn clients-btn--ghost"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="clients-card clients-card--table">
          <div className="clients-card-head">
            <h2>Clientes</h2>
            <span className="clients-count">{totalClients} registrados</span>
          </div>

          <div className="clients-table-wrap">
            <table className="clients-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Contacto</th>
                  <th>Dirección</th>
                  <th>Saldo tarjetas</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {clients.map((client) => (
                  <tr key={client._id}>
                    <td>
                      <strong className="clients-name">{client.nombre}</strong>
                    </td>
                    <td>
                      <div className="clients-contact">
                        <span>{client.telefono || '—'}</span>
                        <span className="clients-muted">{client.email || '—'}</span>
                      </div>
                    </td>
                    <td className="clients-address">{client.direccion || '—'}</td>
                    <td>
                      <span className="clients-balance">
                        ${Number(client.saldo_tarjeta_recargable || 0).toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <span className={`clients-badge ${client.is_active ? 'is-active' : 'is-inactive'}`}>
                        {client.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td>
                      <div className="clients-row-actions">
                        <button
                          type="button"
                          className="clients-btn clients-btn--sm clients-btn--secondary"
                          onClick={() => handleEditClick(client)}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="clients-btn clients-btn--sm clients-btn--accent"
                          onClick={() => handleManageCardsClick(client)}
                        >
                          Tarjetas
                        </button>
                        <button
                          type="button"
                          className="clients-btn clients-btn--sm clients-btn--danger"
                          onClick={() => handleDeleteClient(client._id)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="clients-pagination">
            <button
              type="button"
              className="clients-btn clients-btn--ghost"
              onClick={handlePrevPage}
              disabled={currentPage === 1}
            >
              Anterior
            </button>
            <span>
              Página {currentPage} de {totalPages}
            </span>
            <button
              type="button"
              className="clients-btn clients-btn--ghost"
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
            >
              Siguiente
            </button>
          </div>
        </section>
      </main>

      {editingClient && (
        <div className="clients-modal-overlay" role="dialog" aria-modal="true">
          <div className="clients-modal">
            <div className="clients-modal-head">
              <h2>Editar cliente</h2>
              <button
                type="button"
                className="clients-modal-close"
                onClick={() => setEditingClient(null)}
                aria-label="Cerrar"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleUpdateClient} className="clients-form">
              <label>
                Nombre
                <input
                  type="text"
                  name="nombre"
                  value={editFormData.nombre}
                  onChange={handleEditFormChange}
                  required
                />
              </label>
              <label>
                Teléfono
                <input
                  type="text"
                  name="telefono"
                  value={editFormData.telefono}
                  onChange={handleEditFormChange}
                  required
                />
              </label>
              <label>
                Dirección
                <input
                  type="text"
                  name="direccion"
                  value={editFormData.direccion}
                  onChange={handleEditFormChange}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  name="email"
                  value={editFormData.email}
                  onChange={handleEditFormChange}
                  required
                />
              </label>
              <div className="clients-form-actions">
                <button type="submit" className="clients-btn clients-btn--primary">
                  Guardar cambios
                </button>
                <button
                  type="button"
                  className="clients-btn clients-btn--ghost"
                  onClick={() => setEditingClient(null)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showCardModal && selectedClientForCard && (
        <div className="clients-modal-overlay" role="dialog" aria-modal="true">
          <div className="clients-modal clients-modal--wide">
            <div className="clients-modal-head">
              <div>
                <h2>Tarjetas de {selectedClientForCard.nombre}</h2>
                <div
                  className={`clients-nfc-pill ${nfcReaderStatus.connected ? 'is-on' : 'is-off'}`}
                >
                  Lector NFC: {nfcReaderStatus.connected ? 'Conectado' : 'Desconectado'}
                </div>
              </div>
              <button
                type="button"
                className="clients-modal-close"
                onClick={() => setShowCardModal(false)}
                aria-label="Cerrar"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateCard} className="clients-form clients-form--inline">
              <h3>Nueva tarjeta</h3>
              <div className="clients-inline-row">
                <label>
                  Saldo inicial
                  <input
                    type="number"
                    step="0.01"
                    placeholder="0.00"
                    value={newCardBalance}
                    onChange={(e) => setNewCardBalance(e.target.value)}
                    required
                  />
                </label>
                <button type="submit" className="clients-btn clients-btn--primary">
                  Crear tarjeta
                </button>
              </div>
            </form>

            <h3 className="clients-section-title">Tarjetas existentes</h3>
            {currentClientCards.length > 0 ? (
              <div className="clients-table-wrap">
                <table className="clients-table clients-table--compact">
                  <thead>
                    <tr>
                      <th>Número</th>
                      <th>Saldo</th>
                      <th>UID NFC</th>
                      <th>NFC</th>
                      <th>Activa</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentClientCards.map((card) => (
                      <tr key={card._id}>
                        <td className="mono">{card.card_number}</td>
                        <td>${Number(card.balance || 0).toFixed(2)}</td>
                        <td className="mono">{card.nfc_uid || '—'}</td>
                        <td>
                          <span className={`clients-badge ${card.is_nfc_enabled ? 'is-active' : 'is-inactive'}`}>
                            {card.is_nfc_enabled ? 'Sí' : 'No'}
                          </span>
                        </td>
                        <td>{card.is_active ? 'Sí' : 'No'}</td>
                        <td>
                          <div className="clients-row-actions">
                            <button
                              type="button"
                              className="clients-btn clients-btn--sm clients-btn--secondary"
                              onClick={() => handleAddSubtractBalanceClick(card)}
                            >
                              Ajuste saldo
                            </button>
                            {!card.nfc_uid ? (
                              <button
                                type="button"
                                className="clients-btn clients-btn--sm clients-btn--accent"
                                onClick={() => handleLinkNFCClick(card)}
                              >
                                Vincular NFC
                              </button>
                            ) : (
                              <button
                                type="button"
                                className="clients-btn clients-btn--sm clients-btn--primary"
                                onClick={() => handleReloadNFCClick(card)}
                              >
                                Recargar NFC
                              </button>
                            )}
                            <button
                              type="button"
                              className="clients-btn clients-btn--sm clients-btn--danger"
                              onClick={() => handleDeleteCard(card._id)}
                            >
                              Eliminar
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="clients-muted">Este cliente no tiene tarjetas.</p>
            )}

            {currentClientCards.length > 1 && (
              <div className="clients-transfer">
                <button
                  type="button"
                  className="clients-transfer-toggle"
                  onClick={() => setShowTransferForm(!showTransferForm)}
                >
                  Transferir saldo entre tarjetas {showTransferForm ? '▴' : '▾'}
                </button>
                {showTransferForm && (
                  <form onSubmit={handleTransferBalance} className="clients-form">
                    <label>
                      Origen
                      <select
                        value={fromCardId}
                        onChange={(e) => setFromCardId(e.target.value)}
                        required
                      >
                        <option value="">Seleccionar tarjeta origen</option>
                        {currentClientCards.map((card) => (
                          <option key={card._id} value={card._id}>
                            {card.card_number} (Saldo: {card.balance})
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Destino
                      <select
                        value={toCardId}
                        onChange={(e) => setToCardId(e.target.value)}
                        required
                      >
                        <option value="">Seleccionar tarjeta destino</option>
                        {currentClientCards.map((card) => (
                          <option key={card._id} value={card._id}>
                            {card.card_number} (Saldo: {card.balance})
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Monto
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Cantidad a transferir"
                        value={transferAmount}
                        onChange={(e) => setTransferAmount(e.target.value)}
                        required
                      />
                    </label>
                    <button type="submit" className="clients-btn clients-btn--primary">
                      Transferir
                    </button>
                  </form>
                )}
              </div>
            )}

            <div className="clients-form-actions">
              <button
                type="button"
                className="clients-btn clients-btn--ghost"
                onClick={() => setShowCardModal(false)}
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {showAddSubtractBalanceModal && selectedCardForBalance && (
        <div className="clients-modal-overlay" role="dialog" aria-modal="true">
          <div className="clients-modal">
            <div className="clients-modal-head">
              <h2>
                {operationForBalance === 'add' ? 'Añadir' : 'Restar'} saldo ·{' '}
                {selectedCardForBalance.card_number}
              </h2>
              <button
                type="button"
                className="clients-modal-close"
                onClick={() => setShowAddSubtractBalanceModal(false)}
                aria-label="Cerrar"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleAddSubtractBalance} className="clients-form">
              <label>
                Cantidad
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={amountForBalance}
                  onChange={(e) => setAmountForBalance(e.target.value)}
                  required
                />
              </label>
              <label>
                Operación
                <select
                  value={operationForBalance}
                  onChange={(e) => setOperationForBalance(e.target.value)}
                >
                  <option value="add">Añadir</option>
                  <option value="subtract">Restar</option>
                </select>
              </label>
              <div className="clients-form-actions">
                <button type="submit" className="clients-btn clients-btn--primary">
                  Confirmar
                </button>
                <button
                  type="button"
                  className="clients-btn clients-btn--ghost"
                  onClick={() => setShowAddSubtractBalanceModal(false)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showNFCModal && (
        <div className="clients-modal-overlay" role="dialog" aria-modal="true">
          <div className="clients-modal">
            <div className="clients-modal-head">
              <h2>
                {nfcOperation === 'linking'
                  ? 'Vincular tarjeta NFC'
                  : nfcOperation === 'reloading'
                    ? 'Recargar tarjeta NFC'
                    : 'Consultar saldo NFC'}
              </h2>
              <button
                type="button"
                className="clients-modal-close"
                onClick={() => setShowNFCModal(false)}
                aria-label="Cerrar"
              >
                ×
              </button>
            </div>

            <div
              className={`clients-nfc-pill ${nfcReaderStatus.connected ? 'is-on' : 'is-off'}`}
            >
              Lector NFC: {nfcReaderStatus.connected ? 'Conectado' : 'Desconectado'}
            </div>

            {selectedCardForNFC && (
              <div className="clients-info-box">
                <p>
                  <strong>Tarjeta:</strong> {selectedCardForNFC.card_number}
                </p>
                <p>
                  <strong>Saldo actual:</strong> ${selectedCardForNFC.balance}
                </p>
                {selectedCardForNFC.nfc_uid && (
                  <p>
                    <strong>UID:</strong> {selectedCardForNFC.nfc_uid}
                  </p>
                )}
              </div>
            )}

            {nfcOperation === 'querying' && queryResult && (
              <div className="clients-info-box clients-info-box--ok">
                <h3>Resultado de consulta</h3>
                <p>
                  <strong>Número:</strong> {queryResult.card_number}
                </p>
                <p>
                  <strong>Saldo:</strong> ${queryResult.balance}
                </p>
                <p>
                  <strong>UID NFC:</strong> {queryResult.nfc_uid}
                </p>
                <p>
                  <strong>Propietario:</strong> {queryResult.client_info?.name}
                </p>
                <p>
                  <strong>Email:</strong> {queryResult.client_info?.email}
                </p>
                <p>
                  <strong>Teléfono:</strong> {queryResult.client_info?.telefono}
                </p>
              </div>
            )}

            {nfcOperation === 'reloading' && nfcStatus === 'idle' && (
              <label className="clients-form-label-block">
                Monto a recargar
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  max="10000"
                  placeholder="0.00"
                  value={reloadAmount}
                  onChange={(e) => setReloadAmount(e.target.value)}
                />
              </label>
            )}

            <div className={`clients-nfc-status ${nfcStatus}`}>
              {nfcStatus === 'idle' && (
                <button
                  type="button"
                  onClick={handleNFCOperation}
                  disabled={!nfcReaderStatus.connected}
                  className="clients-btn clients-btn--primary clients-btn--block"
                >
                  {nfcOperation === 'linking'
                    ? 'Acercar tarjeta para vincular'
                    : nfcOperation === 'reloading'
                      ? 'Acercar tarjeta para recargar'
                      : 'Acercar tarjeta para consultar'}
                </button>
              )}

              {nfcStatus === 'waiting' && (
                <div className="clients-nfc-wait">
                  <div className="clients-spinner" />
                  <p>Acerque la tarjeta al lector…</p>
                </div>
              )}

              {nfcStatus === 'reading' && (
                <div className="clients-nfc-wait">
                  <div className="clients-spinner" />
                  <p>Procesando tarjeta…</p>
                </div>
              )}

              {nfcStatus === 'success' && (
                <div className="clients-msg ok">
                  {nfcOperation === 'linking'
                    ? 'Tarjeta vinculada'
                    : nfcOperation === 'reloading'
                      ? 'Recarga'
                      : 'Consulta'}{' '}
                  exitosa
                </div>
              )}

              {nfcStatus === 'error' && (
                <div className="clients-msg err">
                  Error en operación NFC
                  <button
                    type="button"
                    className="clients-btn clients-btn--sm clients-btn--secondary"
                    onClick={() => setNfcStatus('idle')}
                  >
                    Reintentar
                  </button>
                </div>
              )}
            </div>

            {nfcLogs.length > 0 && (
              <div className="clients-nfc-logs">
                <h4>Registro</h4>
                <div className="clients-logs-scroll">
                  {nfcLogs.map((log, index) => (
                    <div key={index} className="clients-log-entry">
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              type="button"
              className="clients-btn clients-btn--ghost clients-btn--block"
              onClick={() => setShowNFCModal(false)}
            >
              Cerrar
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClientsPage;
