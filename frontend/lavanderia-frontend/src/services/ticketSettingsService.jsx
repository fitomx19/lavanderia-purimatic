import axios from 'axios';
import { API_BASE_URL } from './apiConfig';

const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
});

const unwrapError = (error, fallback) => {
  throw error.response ? error.response.data : new Error(fallback);
};

export const getTicketSettings = async (includeLogo = true) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/ticket-settings`, {
      headers: authHeaders(),
      params: { include_logo: includeLogo ? 'true' : 'false' },
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al cargar configuración de ticket');
  }
};

export const saveTicketSettings = async (payload) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/api/ticket-settings`, payload, {
      headers: authHeaders(),
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al guardar configuración de ticket');
  }
};

export const listTicketPrinters = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/ticket-settings/printers`, {
      headers: authHeaders(),
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al listar impresoras');
  }
};

export const testTicketPrint = async () => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/ticket-settings/test-print`,
      {},
      { headers: authHeaders() }
    );
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al imprimir ticket de prueba');
  }
};
