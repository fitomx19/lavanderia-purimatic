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


// AGREGAR AL FINAL DE src/services/salesService.js

// Obtener estado del lector NFC para ventas
export const getNFCStatusForSales = async () => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/api/nfc/status`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener estado NFC');
  }
};

// Validar pago con tarjeta NFC
export const validateNFCPayment = async (amount, timeout = 30) => {
  console.log('🔍 [salesService] Iniciando validateNFCPayment');
  console.log('🔍 [salesService] Parámetros recibidos:', { amount, timeout });
  
  try {
    const token = getToken();
    console.log('🔍 [salesService] Token obtenido:', token ? 'SÍ' : 'NO');
    console.log('🔍 [salesService] URL de la API:', `${API_BASE_URL}/api/nfc/validate-payment`);
    
    const requestData = {
      amount: amount,
      timeout: timeout
    };
    console.log('🔍 [salesService] Datos de la petición:', requestData);
    
    const response = await axios.post(`${API_BASE_URL}/api/nfc/validate-payment`, requestData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    console.log('🔍 [salesService] Respuesta del servidor:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [salesService] Error en validateNFCPayment:', error);
    console.error('❌ [salesService] Error response:', error.response?.data);
    console.error('❌ [salesService] Error status:', error.response?.status);
    throw error.response ? error.response.data : new Error('Error de conexión al validar pago NFC');
  }
};

// Procesar pago con tarjeta NFC
export const processNFCPayment = async (nfcUid, amount) => {
  console.log('🔍 [salesService] Iniciando processNFCPayment');
  console.log('🔍 [salesService] Parámetros recibidos:', { nfcUid, amount });
  
  try {
    const token = getToken();
    console.log('🔍 [salesService] Token obtenido:', token ? 'SÍ' : 'NO');
    console.log('🔍 [salesService] URL de la API:', `${API_BASE_URL}/api/nfc/process-payment`);
    
    const requestData = {
      nfc_uid: nfcUid,
      amount: amount
    };
    console.log('🔍 [salesService] Datos de la petición:', requestData);
    
    const response = await axios.post(`${API_BASE_URL}/api/nfc/process-payment`, requestData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    console.log('🔍 [salesService] Respuesta del servidor:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ [salesService] Error en processNFCPayment:', error);
    console.error('❌ [salesService] Error response:', error.response?.data);
    console.error('❌ [salesService] Error status:', error.response?.status);
    throw error.response ? error.response.data : new Error('Error de conexión al procesar pago NFC');
  }
};

// Función para obtener todas las ventas con filtros
export const getAllSales = async (page = 1, perPage = 50, filters = {}) => {
  try {
    const token = getToken();
    const params = {
      page,
      per_page: perPage,
      ...filters
    };

    const response = await axios.get(`${API_BASE_URL}/api/sales/all-sales`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener ventas');
  }
};