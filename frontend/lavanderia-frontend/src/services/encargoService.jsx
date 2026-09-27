import axios from 'axios';
import { API_BASE_URL } from './apiConfig';

const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
});

const unwrap = (error, fallback) => {
  throw error.response ? error.response.data : new Error(fallback);
};

export const getEncargoSettings = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/encargos/settings`, {
      headers: authHeaders(),
    });
    return res.data;
  } catch (e) {
    unwrap(e, 'Error al cargar configuración de encargos');
  }
};

export const saveEncargoSettings = async (payload) => {
  try {
    const res = await axios.put(`${API_BASE_URL}/api/encargos/settings`, payload, {
      headers: authHeaders(),
    });
    return res.data;
  } catch (e) {
    unwrap(e, 'Error al guardar configuración');
  }
};

export const listEncargos = async (params = {}) => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/encargos`, {
      headers: authHeaders(),
      params,
    });
    return res.data;
  } catch (e) {
    unwrap(e, 'Error al listar encargos');
  }
};

export const createEncargo = async (payload) => {
  try {
    const res = await axios.post(`${API_BASE_URL}/api/encargos`, payload, {
      headers: authHeaders(),
    });
    return res.data;
  } catch (e) {
    unwrap(e, 'Error al crear encargo');
  }
};

export const updateEncargoStatus = async (id, payload) => {
  try {
    const body = typeof payload === 'string' ? { status: payload } : payload;
    const res = await axios.post(
      `${API_BASE_URL}/api/encargos/${id}/status`,
      body,
      { headers: authHeaders() }
    );
    return res.data;
  } catch (e) {
    unwrap(e, 'Error al actualizar estado');
  }
};

export const reprintEncargo = async (id) => {
  try {
    const res = await axios.post(
      `${API_BASE_URL}/api/encargos/${id}/reprint`,
      {},
      { headers: authHeaders() }
    );
    return res.data;
  } catch (e) {
    unwrap(e, 'Error al reimprimir');
  }
};
