import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:5000",
  headers: { "Content-Type": "application/json" }
});

export async function createOrder(payload) {
  const res = await API.post("/orders", payload);
  return res.data;
}

export async function listOrders() {
  const res = await API.get("/orders");
  return res.data;
}

export async function getOrder(id) {
  const res = await API.get(`/orders/${id}`);
  return res.data;
}
