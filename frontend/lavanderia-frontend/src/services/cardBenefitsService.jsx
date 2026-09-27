import axios from 'axios';
import { API_BASE_URL } from './apiConfig';

const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`,
  'Content-Type': 'application/json',
});

const unwrapError = (error, fallback) => {
  throw error.response ? error.response.data : new Error(fallback);
};

export const getCardBenefitsSettings = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/card-benefits-settings`, {
      headers: authHeaders(),
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al cargar beneficios de tarjeta');
  }
};

export const saveCardBenefitsSettings = async (payload) => {
  try {
    const response = await axios.put(`${API_BASE_URL}/api/card-benefits-settings`, payload, {
      headers: authHeaders(),
    });
    return response.data;
  } catch (error) {
    unwrapError(error, 'Error al guardar beneficios de tarjeta');
  }
};

/** Estilo efectivo de descuento al pagar según config. */
export const resolvePayDiscountStyle = (settings) => {
  if (!settings?.pay_discount_enabled) return null;
  const mode = settings.pay_discount_mode || 'elegir_pct_o_precio';
  if (mode === 'solo_porcentaje') return 'porcentaje';
  if (mode === 'solo_precio_ciclo') return 'precio_ciclo';
  return settings.pay_discount_style || 'porcentaje';
};

/** Calcula crédito de recarga en el cliente (espejo del backend). */
export const computeReloadCredit = (settings, payAmount, packageIndex = null) => {
  const pay = Number(payAmount) || 0;
  if (!settings?.reload_bonus_enabled) {
    return { credit: pay, bonus: 0, source: 'sin_bono' };
  }
  const mode = settings.reload_promo_mode || 'paquetes_y_libre';
  const packages = settings.reload_packages || [];

  if (packageIndex != null && packageIndex >= 0 && packageIndex < packages.length) {
    const pkg = packages[packageIndex];
    const credit = Number(pkg.credit_amount) || pay;
    return { credit, bonus: credit - pay, source: 'paquete' };
  }

  if (mode === 'paquetes' || mode === 'paquetes_y_libre') {
    const match = packages.find((p) => Math.abs(Number(p.pay_amount) - pay) < 0.01);
    if (match) {
      const credit = Number(match.credit_amount) || pay;
      return { credit, bonus: credit - pay, source: 'paquete' };
    }
  }

  if (mode === 'porcentaje_y_libre') {
    const pct = Number(settings.reload_bonus_percent) || 0;
    const credit = Math.round(pay * (1 + pct / 100) * 100) / 100;
    return { credit, bonus: credit - pay, source: 'porcentaje' };
  }

  return { credit: pay, bonus: 0, source: 'libre' };
};
