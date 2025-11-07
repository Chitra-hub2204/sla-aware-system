import axios from "axios";

// ✅ Automatically picks the Railway backend when deployed on Vercel
// or uses localhost when testing locally
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://sla-aware-system-production.up.railway.app";

console.log("🌍 Backend in use:", API_BASE_URL);

// Create a new SLA order
export const createOrder = async (data) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/orders`, data, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("❌ Error creating order:", error.response?.data || error.message);
    throw error;
  }
};

// Fetch all SLA orders
export const getOrders = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/orders`);
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching orders:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Fetch details of a single order by ID
export const getOrder = async (orderId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/orders/${orderId}`);
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching order details:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Simulate metrics for a given order
export const simulateMetrics = async (orderId, data = {}) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/simulate/${orderId}`, data, {
      headers: {
        "Content-Type": "application/json",
      },
    });
    return response.data;
  } catch (error) {
    console.error("❌ Error simulating metrics:", error.response?.data || error.message);
    throw error;
  }
};
