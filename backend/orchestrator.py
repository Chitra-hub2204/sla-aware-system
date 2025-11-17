from typing import Any, Dict

from netconf_client import NetconfClient


class ServiceOrchestrator:
    """Coordinates ONAP-like service ordering workflows."""

    def __init__(self, netconf_client: NetconfClient | None = None):
        if netconf_client is not None:
            self.netconf_client = netconf_client
        else:
            self.netconf_client = NetconfClient.from_env()

    def order_service(self, service_id: str, sla_params: Dict[str, Any]) -> Dict[str, Any]:
        if not service_id:
            raise ValueError("service_id is required for orchestration")

        normalized_sla = self._normalize_sla(sla_params)
        payload = self.netconf_client.build_config(service_id, normalized_sla)
        rpc_reply = self.netconf_client.push_config(payload)

        return {
            "status": "ACTIVATED",
            "service_id": service_id,
            "sla": normalized_sla,
            "rpc_reply": rpc_reply,
        }

    @staticmethod
    def _normalize_sla(sla_params: Dict[str, Any]) -> Dict[str, float]:
        defaults = {"latency": 0.0, "throughput": 0.0, "jitter": 0.0}
        normalized = {}
        for key, default_value in defaults.items():
            try:
                normalized[key] = float(sla_params.get(key, default_value))
            except (TypeError, ValueError):
                normalized[key] = default_value

        return normalized

