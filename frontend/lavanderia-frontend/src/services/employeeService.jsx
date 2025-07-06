import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const getToken = () => {
  return localStorage.getItem('token');
};

export const getEmployees = async (page = 1, per_page = 10) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/employees`, {
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
    throw error.response ? error.response.data : new Error('Error de conexión al obtener empleados');
  }
};

export const getEmployeeById = async (id) => {
  try {
    const token = getToken();
    const response = await axios.get(`${API_BASE_URL}/employees/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al obtener empleado');
  }
};

export const updateEmployee = async (id, employeeData) => {
  try {
    const token = getToken();
    const response = await axios.put(`${API_BASE_URL}/employees/${id}`, employeeData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al actualizar empleado');
  }
};

export const deleteEmployee = async (id) => {
  try {
    const token = getToken();
    const response = await axios.delete(`${API_BASE_URL}/employees/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al eliminar empleado');
  }
};

export const createEmployee = async (employeeData) => {
  try {
    const token = getToken();
    const response = await axios.post(`${API_BASE_URL}/employees`, employeeData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  } catch (error) {
    throw error.response ? error.response.data : new Error('Error de conexión al crear empleado');
  }
}; 