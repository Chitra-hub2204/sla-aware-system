import React from "react";

function badgeColor(status) {
  if (status === "OK") return "green";
  if (status === "BREACHED") return "red";
  if (status === "DEGRADED") return "yellow";
  return "gray";
}

export default function OrdersList({ orders, onSelect, onRefresh }) {
  return (
    <div>
      <button className="small" onClick={onRefresh}>Refresh</button>
      <ul className="orders">
        {orders.length === 0 && <li>No orders yet</li>}
        {orders.map((o) => (
          <li key={o.id} onClick={() => onSelect(o)} className="order-row">
            <div><b>{o.service_type}</b> — {o.user_name}</div>
            <div className={`badge ${badgeColor(o.status)}`}>{o.status || "Pending"}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
