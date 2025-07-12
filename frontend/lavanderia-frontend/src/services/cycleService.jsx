import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const getToken = () => {
  return localStorage.getItem('token');
};

// Funciones para Ciclos de Servicio
export const getServiceCycles = async (page = 1, per_page = 10, service_type = null) => {
  try {
    const token = getToken();
    const params = { page, per_page };
    if (service_type) {
      params.service_type = service_type;
    }
    const response = await axios.get(`${API_BASE_URL}/api/service-cycles`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      params,
    });
    // Agregamos un console.log para mostrar la salida de la respuesta
    console.log('Respuesta de getServiceCycles:', response.data);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener ciclos de servicio');
  }
};

export const getServiceCycleById = async (id) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/api/service-cycles/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    // Agregamos un console.log para mostrar la salida de la respuesta
    console.log('Respuesta de getServiceCycleById:', response.data);
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener ciclo de servicio por ID');
  }
};

export const createServiceCycle = async (cycleData) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/api/service-cycles`, cycleData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear ciclo de servicio');
  }
};

export const deleteServiceCycle = async (id) => {
  try {
    const token = getToken();
    const response = await axios.delete(`${API_BASE_URL}/api/service-cycles/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al eliminar ciclo de servicio');
  }
};