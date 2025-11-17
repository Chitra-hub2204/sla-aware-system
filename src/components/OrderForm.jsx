import React, { useState } from "react";
import { createOrder } from "../api";

export default function OrderForm({ onCreated }) {
  const [userName, setUserName] = useState("");
  const [serviceType, setServiceType] = useState("compute");
  const [slaUptime] = useState(99.0); // Locked to 99
  const [slaLatency] = useState(500); // Locked to 500

  async function handleSubmit(e) {
    e.preventDefault();
    const payload = {
      user_name: userName,
      service_type: serviceType,
      sla_uptime_pct: Number(slaUptime),
      sla_latency_ms: Number(slaLatency)
    };
    try {
      await createOrder(payload);
      alert("Order created!");
      setUserName("");
      if (onCreated) onCreated();
    } catch (err) {
      alert("Error creating order");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="form">
      <label>
        Your Name
        <input value={userName} onChange={(e) => setUserName(e.target.value)} required />
      </label>

      <label>
        Service Type
        <select value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
          <option value="compute">Compute VM</option>
          <option value="storage">Storage</option>
          <option value="api">API Hosting</option>
        </select>
      </label>

      <label>
        SLA Uptime (%)
        <input type="number" value={slaUptime} readOnly disabled />
      </label>

      <label>
        SLA Latency (ms)
        <input type="number" value={slaLatency} readOnly disabled />
      </label>

      <button type="submit">Create</button>
    </form>
  );
}
