import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const getToken = () => {
  return localStorage.getItem('token');
};

export const getTransactions = async (page = 1, perPage = 50, filters = {}) => {
  try {
    const token = getToken();
    const params = {
      page,
      per_page: perPage,
      ...filters
    };

    const response = await axios.get(`${API_BASE_URL}/api/cards/transactions`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener transacciones');
  }
};
