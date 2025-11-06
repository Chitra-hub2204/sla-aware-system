import React, { useState, useEffect } from "react";
import OrderForm from "./components/OrderForm";
import OrdersList from "./components/OrdersList";
import OrderDetail from "./components/OrderDetail";
import { listOrders } from "./api";
import "./styles.css";

export default function App() {
  const [orders, setOrders] = useState([]);
  const [selected, setSelected] = useState(null);

  async function loadOrders() {
    try {
      const data = await listOrders();
      setOrders(data);
    } catch (err) {
      console.error("loadOrders", err);
    }
  }

  useEffect(() => {
    loadOrders();
    const interval = setInterval(loadOrders, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="container">
      <h1>SLA Service Ordering & Dashboard</h1>
      <div className="grid">
        <div className="panel">
          <h2>Create Order</h2>
          <OrderForm onCreated={loadOrders} />
        </div>

        <div className="panel">
          <h2>Orders</h2>
          <OrdersList orders={orders} onSelect={setSelected} onRefresh={loadOrders} />
        </div>

        <div className="panel full">
          <h2>Order Details</h2>
          {selected ? (
            <OrderDetail orderId={selected.id} />
          ) : (
            <div>Select an order to view details</div>
          )}
        </div>
      </div>
    </div>
  );
}
