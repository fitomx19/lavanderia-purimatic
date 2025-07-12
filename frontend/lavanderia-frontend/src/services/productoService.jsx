import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const getToken = () => {
  return localStorage.getItem('token');
};

// Funciones para Productos
export const getProducts = async (page = 1, per_page = 10) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/products`, {
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
    throw error.response ? error.response.data : new Error('Error de conexión al obtener productos');
  }
};

export const getProductById = async (id) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/products/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener producto');
  }
};

export const createProduct = async (productData) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/products`, productData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear producto');
  }
};

export const updateProduct = async (id, productData) => {
  try {
    const token = getToken();
    const response = await axios.put(`${API_BASE_URL}/products/${id}`, productData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al actualizar producto');
  }
};

export const deleteProduct = async (id) => {
  try {
    const token = getToken();
    const response = await axios.delete(`${API_BASE_URL}/products/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al eliminar producto');
  }
};