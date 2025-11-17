import os
from typing import Any, Dict

from ncclient import manager


class NetconfClient:
    """Thin wrapper around ncclient for pushing SLA configurations."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        *,
        timeout: int = 30,
        hostkey_verify: bool = False,
        template_path: str | None = None,
        dry_run: bool = False,
        mode: str = "real",
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.hostkey_verify = hostkey_verify
        self.template_path = template_path or os.path.join(
            os.path.dirname(__file__), "rpc_templates", "sla_config.xml"
        )
        self.dry_run = dry_run
        self.mode = mode.lower()

    @classmethod
    def from_env(cls) -> "NetconfClient":
        return cls(
            host=os.getenv("NETCONF_HOST", "127.0.0.1"),
            port=int(os.getenv("NETCONF_PORT", "830")),
            username=os.getenv("NETCONF_USERNAME", "admin"),
            password=os.getenv("NETCONF_PASSWORD", "admin"),
            timeout=int(os.getenv("NETCONF_TIMEOUT", "30")),
            hostkey_verify=os.getenv("NETCONF_HOSTKEY_VERIFY", "false").lower() == "true",
            dry_run=os.getenv("NETCONF_DRY_RUN", "false").lower() == "true",
            mode=os.getenv("NETCONF_MODE", "real"),
        )

    def build_config(self, service_id: str, sla_params: Dict[str, Any]) -> str:
        with open(self.template_path, "r", encoding="utf-8") as template_file:
            template = template_file.read()

        replacements = {
            "{{service_id}}": str(service_id),
            "{{latency}}": str(sla_params.get("latency", "")),
            "{{throughput}}": str(sla_params.get("throughput", "")),
            "{{jitter}}": str(sla_params.get("jitter", "")),
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        return template

    def push_config(self, payload: str) -> str:
        if self.mode != "real":
            return "<rpc-reply><ok/></rpc-reply>"

        if self.dry_run:
            return "<rpc-reply><ok/></rpc-reply>"

        with manager.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
            hostkey_verify=self.hostkey_verify,
            allow_agent=False,
            look_for_keys=False,
        ) as m:
            response = m.edit_config(target="running", config=payload)
            return response.xml


