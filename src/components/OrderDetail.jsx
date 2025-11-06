import React, { useEffect, useState } from "react";
import { getOrder } from "../api";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement, Legend, Tooltip
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Legend, Tooltip);

export default function OrderDetail({ orderId }) {
  const [order, setOrder] = useState(null);

  async function load() {
    const res = await getOrder(orderId);
    setOrder(res);
  }

  useEffect(() => {
    load();
    const i = setInterval(load, 5000);
    return () => clearInterval(i);
  }, [orderId]);

  if (!order) return <p>Loading...</p>;

  const timestamps = order.metrics?.map(m => new Date(m.timestamp).toLocaleTimeString()) || [];
  const uptime = order.metrics?.map(m => m.uptime_pct) || [];
  const latency = order.metrics?.map(m => m.latency_ms) || [];

  const chartData = {
    labels: timestamps,
    datasets: [
      { label: "Uptime (%)", data: uptime, borderWidth: 2, tension: 0.3 },
      { label: "Latency (ms)", data: latency, borderWidth: 2, tension: 0.3 }
    ]
  };

  return (
    <div>
      <h3>{order.service_type} — {order.user_name}</h3>
      <Line data={chartData} />
      <h4>Alerts</h4>
      {order.alerts?.length ? (
        <ul>{order.alerts.map(a => <li key={a.id}>{a.details}</li>)}</ul>
      ) : <p>No alerts yet</p>}
    </div>
  );
}
