import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const getToken = () => {
  return localStorage.getItem('token');
};

export const getClients = async (page = 1, per_page = 10) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/clients`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        page,
        per_page,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener clientes');
  }
};

export const getClientById = async (id) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/clients/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener cliente');
  }
};

export const updateClient = async (id, clientData) => {
  try {
    const token = getToken();
    const response = await axios.put(`${API_BASE_URL}/clients/${id}`, clientData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al actualizar cliente');
  }
};

export const createClient = async (clientData) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/clients`, clientData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear cliente');
  }
};

export const deleteClient = async (id) => {
  try {
    const token = getToken();
    const response = await axios.delete(`${API_BASE_URL}/clients/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al eliminar cliente');
  }
};

export const createClientCard = async (clientId, balance) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/clients/${clientId}/cards`, { balance }, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear tarjeta para cliente');
  }
};

export const getClientCards = async (clientId) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/api/clients/${clientId}/cards`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener tarjetas del cliente');
  }
};

export const addSubtractCardBalance = async (cardId, amount, operation) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/cards/${cardId}/add-balance`, { amount, operation }, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al actualizar saldo de tarjeta');
  }
};

export const transferCardBalance = async (fromCardId, toCardId, amount) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/cards/transfer-balance`, { from_card_id: fromCardId, to_card_id: toCardId, amount }, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al transferir saldo entre tarjetas');
  }
};

export const getCardBalance = async (cardId) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/api/cards/${cardId}/balance`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al consultar saldo de tarjeta');
  }
};

export const deleteCard = async (cardId) => {
  try {
    const token = getToken();
    const response = await axios.delete(`${API_BASE_URL}/api/cards/${cardId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al eliminar tarjeta');
  }
};
export const getNFCStatus = async () => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/api/nfc/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error al consultar estado NFC');
  }
};

export const linkCardToNFC = async (cardId) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/cards/${cardId}/link-nfc`, {}, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error al vincular tarjeta NFC');
  }
};

export const reloadCardViaNFC = async (amount) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/cards/reload-nfc`, { amount }, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error al recargar tarjeta NFC');
  }
};

export const queryBalanceViaNFC = async () => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/cards/query-balance-nfc`, {}, {
      headers: { 
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error al consultar saldo NFC');
  }
};
/* import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export const loginUser = async (username, password) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, {
      username,
      password,
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión');
  }
};
 */