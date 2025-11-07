import axios from "axios";

// ✅ Automatically uses environment variable from Vercel or defaults to Railway
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://sla-aware-system-production.up.railway.app";

console.log("🌍 Backend in use:", API_BASE_URL);

// ✅ Create a new SLA order
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

// ✅ Fetch all SLA orders
export const getOrders = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/orders`);
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching orders:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Fetch a specific SLA order by ID (used in OrderDetail.jsx)
export const getOrder = async (orderId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/orders/${orderId}`);
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching order details:", error.response?.data || error.message);
    throw error;
  }
};

// ✅ Simulate SLA metrics for an order
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

// ✅ Health check (optional utility)
export const checkHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  } catch (error) {
    console.error("⚠️ Backend health check failed:", error.message);
    throw error;
  }
};

// ✅ Compatibility alias (for old code using listOrders)
export { getOrders as listOrders };
