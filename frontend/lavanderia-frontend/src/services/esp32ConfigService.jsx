import axios from 'axios';
import { API_BASE_URL } from './apiConfig';

const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
});

const unwrapError = (error, fallback) => {
  throw error.response ? error.response.data : new Error(fallback);
};

export const listEsp32Configs = async (includeInactive = true) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/esp32-config`, {
      headers: authHeaders(),
      params: { include_inactive: includeInactive ? 'true' : 'false' },
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al listar placas ESP32');
  }
};

export const saveEsp32Config = async (payload) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/esp32-config`, payload, {
      headers: authHeaders(),
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al guardar la placa ESP32');
  }
};

export const updateEsp32Config = async (esp32Id, payload) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/api/esp32-config/${esp32Id}`, payload, {
      headers: authHeaders(),
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al actualizar la placa ESP32');
  }
};

export const deactivateEsp32Config = async (esp32Id) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/api/esp32-config/${esp32Id}`, {
      headers: authHeaders(),
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al desactivar la placa ESP32');
  }
};

export const testEsp32 = async (esp32Id, action) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/esp32-config/${esp32Id}/test`,
      { action },
      { headers: authHeaders() }
    );
    return response.data;
  } catch (error) {
    unwrapError(error, `Error al probar ${action} en la placa ${esp32Id}`);
  }
};
