import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const getToken = () => {
  return localStorage.getItem('token');
};

// Funciones para Lavadoras
export const createWasher = async (washerData) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/washers`, washerData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear lavadora');
  }
};

export const getWashersByStoreId = async (storeId, page = 1, per_page = 10) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/washers/store/${storeId}`, {
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
    throw error.response ? error.response.data : new Error('Error de conexión al obtener lavadoras');
  }
};

export const updateWasher = async (id, washerData) => {
  try {
    const token = getToken();
    const response = await axios.put(`${API_BASE_URL}/washers/${id}`, washerData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al actualizar lavadora');
  }
};

export const deleteWasher = async (id) => {
  try {
    const token = getToken();
    const response = await axios.delete(`${API_BASE_URL}/washers/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al eliminar lavadora');
  }
};

// Funciones para Secadoras
export const createDryer = async (dryerData) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/dryers`, dryerData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear secadora');
  }
};

export const getDryersByStoreId = async (storeId, page = 1, per_page = 10) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/dryers`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params: {
        page,
        per_page,
        store_id: storeId,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener secadoras');
  }
};

export const getAllActiveWashers = async () => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/washers/all-active`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener todas las lavadoras activas');
  }
};

export const getAllActiveDryers = async () => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/dryers/all-active`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener todas las secadoras activas');
  }
};

export const updateDryer = async (id, dryerData) => {
  try {
    const token = getToken();
    const response = await axios.put(`${API_BASE_URL}/dryers/${id}`, dryerData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al actualizar secadora');
  }
};

export const deleteDryer = async (id) => {
  try {
    const token = getToken();
    const response = await axios.delete(`${API_BASE_URL}/dryers/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al eliminar secadora');
  }
};