import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const getToken = () => {
  return localStorage.getItem('token');
};

// Función para crear una nueva venta
export const createSale = async (saleData) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/sales`, saleData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear la venta');
  }
};

// Función para obtener la lista de ventas
export const getSales = async (params = {}) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/api/sales`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: params,
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener las ventas');
  }
};

// Función para obtener una venta por ID
export const getSaleById = async (saleId) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/api/sales/${saleId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener la venta');
  }
};

// Función para completar una venta y activar servicios
export const completeSale = async (saleId) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/sales/${saleId}/complete`, {}, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al completar la venta');
  }
};

// Función para finalizar una venta
export const finalizeSale = async (saleId) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/sales/${saleId}/finalize`, {}, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al finalizar la venta');
  }
};

// Función para reactivar máquinas (administrativo)
export const deactivateMachines = async () => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/sales/deactivate-machines`, {}, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al reactivar máquinas');
  }
};