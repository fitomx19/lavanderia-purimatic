import React, { useEffect, useState } from 'react';
import { getClients, deleteClient, createClient, updateClient, createClientCard, getClientCards, addSubtractCardBalance, transferCardBalance, getCardBalance, deleteCard } from '../../services/clientsService';
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

  const handleDeleteClient = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este cliente?')) {
      try {
        await deleteClient(id);
        setClients(clients.filter(client => client._id !== id));
        alert('Cliente eliminado exitosamente.');
        fetchClients();
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
      fetchClients();
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
      fetchClients();
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
    } catch (err) {
      setError(err.message);
    }
  };


  if (loading) {
    return <div>Cargando clientes...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="clients-page-container">
      <Header />
      <h1>Gestión de Clientes</h1>
      <div className="controls-section">
        <button onClick={() => setShowCreateForm(!showCreateForm)} className="create-client-button">
          {showCreateForm ? 'Cancelar' : 'Agregar Nuevo Cliente'}
        </button>
      </div>

      {showCreateForm && (
        <form onSubmit={handleCreateClient} className="create-client-form">
          <h2>Crear Nuevo Cliente</h2>
          <input
            type="text"
            name="nombre"
            placeholder="Nombre"
            value={newClient.nombre}
            onChange={handleInputChange}
            required
          />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={newClient.email}
            onChange={handleInputChange}
            required
          />
          <input
            type="text"
            name="telefono"
            placeholder="Teléfono"
            value={newClient.telefono}
            onChange={handleInputChange}
            required
          />
          <input
            type="text"
            name="direccion"
            placeholder="Dirección"
            value={newClient.direccion}
            onChange={handleInputChange}
            required
          />
          <button type="submit">Guardar Cliente</button>
        </form>
      )}

      {editingClient && (
        <div className="edit-client-modal">
          <form onSubmit={handleUpdateClient} className="edit-client-form">
            <h2>Editar Cliente</h2>
            <label>Nombre:</label>
            <input
              type="text"
              name="nombre"
              value={editFormData.nombre}
              onChange={handleEditFormChange}
              required
            />
            <label>Teléfono:</label>
            <input
              type="text"
              name="telefono"
              value={editFormData.telefono}
              onChange={handleEditFormChange}
              required
            />
            <label>Dirección:</label>
            <input
              type="text"
              name="direccion"
              value={editFormData.direccion}
              onChange={handleEditFormChange}
              required
            />
            <label>Email:</label>
            <input
              type="email"
              name="email"
              value={editFormData.email}
              onChange={handleEditFormChange}
              required
            />
            <button type="submit">Actualizar Cliente</button>
            <button type="button" onClick={() => setEditingClient(null)}>Cancelar</button>
          </form>
        </div>
      )}

      {showCardModal && selectedClientForCard && (
        <div className="card-modal">
          <div className="card-modal-content">
            <div className="modal-header">
              <h2>Tarjetas de {selectedClientForCard.nombre}</h2>
              <button onClick={() => setShowCardModal(false)} className="close-button">X</button>
            </div>
            <form onSubmit={handleCreateCard} className="create-card-form">
              <h3>Crear Nueva Tarjeta</h3>
              <input
                type="number"
                step="0.01"
                placeholder="Saldo Inicial"
                value={newCardBalance}
                onChange={(e) => setNewCardBalance(e.target.value)}
                required
              />
              <button type="submit">Crear Tarjeta</button>
            </form>
            <h3>Tarjetas Existentes</h3>
            {currentClientCards.length > 0 ? (
              <table className="cards-table">
                <thead>
                  <tr>
                    <th>Número de Tarjeta</th>
                    <th>Saldo</th>
                    <th>Activa</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {currentClientCards.map((card) => (
                    <tr key={card._id}>
                      <td>{card.card_number}</td>
                      <td>{card.balance}</td>
                      <td>{card.is_active ? 'Sí' : 'No'}</td>
                      <td>
                        <button onClick={() => handleAddSubtractBalanceClick(card)}>Añadir/Restar Saldo</button>
                        <button onClick={() => handleDeleteCard(card._id)}>Eliminar</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>Este cliente no tiene tarjetas.</p>
            )}

            {currentClientCards.length > 1 && (
              <div className="transfer-section">
                <h3 onClick={() => setShowTransferForm(!showTransferForm)} style={{ cursor: 'pointer' }}>
                  Transferir Saldo entre Tarjetas {showTransferForm ? '▲' : '▼'}
                </h3>
                {showTransferForm && (
                  <form onSubmit={handleTransferBalance}>
                    <select
                      value={fromCardId}
                      onChange={(e) => setFromCardId(e.target.value)}
                      required
                    >
                      <option value="">Seleccionar Tarjeta Origen</option>
                      {currentClientCards.map((card) => (
                        <option key={card._id} value={card._id}>
                          {card.card_number} (Saldo: {card.balance})
                        </option>
                      ))}
                    </select>
                    <select
                      value={toCardId}
                      onChange={(e) => setToCardId(e.target.value)}
                      required
                    >
                      <option value="">Seleccionar Tarjeta Destino</option>
                      {currentClientCards.map((card) => (
                        <option key={card._id} value={card._id}>
                          {card.card_number} (Saldo: {card.balance})
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="Cantidad a Transferir"
                      value={transferAmount}
                      onChange={(e) => setTransferAmount(e.target.value)}
                      required
                    />
                    <button type="submit">Transferir</button>
                  </form>
                )}
              </div>
            )}

            <button onClick={() => setShowCardModal(false)} className="close-button">Cerrar</button>
          </div>
        </div>
      )}

      {showAddSubtractBalanceModal && selectedCardForBalance && (
        <div className="add-subtract-balance-modal">
          <div className="modal-content">
            <h2>{operationForBalance === 'add' ? 'Añadir' : 'Restar'} Saldo a Tarjeta {selectedCardForBalance.card_number}</h2>
            <form onSubmit={handleAddSubtractBalance}>
              <input
                type="number"
                step="0.01"
                placeholder="Cantidad"
                value={amountForBalance}
                onChange={(e) => setAmountForBalance(e.target.value)}
                required
              />
              <select value={operationForBalance} onChange={(e) => setOperationForBalance(e.target.value)}>
                <option value="add">Añadir</option>
                <option value="subtract">Restar</option>
              </select>
              <button type="submit">Confirmar</button>
              <button type="button" onClick={() => setShowAddSubtractBalanceModal(false)}>Cancelar</button>
            </form>
          </div>
        </div>
      )}

      <table className="clients-table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Email</th>
            <th>Teléfono</th>
            <th>Dirección</th>
            <th>Saldo Tarjeta Recargable</th>
            <th>Activo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {clients.map((client) => (
            <tr key={client._id}>
              <td>{client.nombre}</td>
              <td>{client.email}</td>
              <td>{client.telefono}</td>
              <td>{client.direccion}</td>
              <td>{client.saldo_tarjeta_recargable}</td>
              <td>{client.is_active ? 'Sí' : 'No'}</td>
              <td>
                <button onClick={() => handleEditClick(client)}>Editar</button>
                <button onClick={() => handleDeleteClient(client._id)}>Eliminar</button>
                <button onClick={() => handleManageCardsClick(client)}>Gestionar Tarjetas</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination-controls">
        <button onClick={handlePrevPage} disabled={currentPage === 1}>Anterior</button>
        <span>Página {currentPage} de {totalPages} ({totalClients} clientes)</span>
        <button onClick={handleNextPage} disabled={currentPage === totalPages}>Siguiente</button>
      </div>
    </div>
  );
};

export default ClientsPage;
