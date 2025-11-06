import axios from "axios";

// ✅ Your live backend URL
const API_BASE_URL = "https://sla-aware-system-production.up.railway.app";

export const createOrder = async (data) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/orders`, data);
    return response.data;
  } catch (error) {
    console.error("Error creating order:", error);
    throw error;
  }
};

export const getOrders = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/orders`);
    return response.data;
  } catch (error) {
    console.error("Error fetching orders:", error);
    throw error;
  }
};
