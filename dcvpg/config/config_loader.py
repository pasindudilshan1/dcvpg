import os
import re
import yaml
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ProjectConfig(BaseModel):
    name: str
    team: str
    environment: str

class ContractsConfig(BaseModel):
    directory: str
    auto_register: bool = True
    watch_mode: bool = False

class ConnectionConfig(BaseModel):
    name: str
    type: str
    # Other parsed parameters go here; keep it flexible for now
    model_config = {"extra": "allow"}

class ExtensionsConfig(BaseModel):
    custom_rules_dir: Optional[str] = None
    custom_connectors_dir: Optional[str] = None

class DatabaseConfig(BaseModel):
    host: str
    port: int
    name: str
    user: str
    password: str

class SlackConfig(BaseModel):
    enabled: bool = False
    webhook_env: Optional[str] = None   # name of the env var that holds the URL
    webhook_url: Optional[str] = None   # direct URL (fallback if webhook_env not set)
    channel: Optional[str] = None
    mention_owners: bool = False

class PagerDutyConfig(BaseModel):
    enabled: bool = False
    api_key_env: Optional[str] = None
    service_id: Optional[str] = None
    severity_threshold: Optional[str] = None

class TeamsConfig(BaseModel):
    enabled: bool = False
    webhook_env: Optional[str] = None

class CustomAlerterConfig(BaseModel):
    enabled: bool = False
    module: Optional[str] = None

class AlertingConfig(BaseModel):
    default_severity_threshold: str = "WARNING"
    slack: Optional[SlackConfig] = None
    pagerduty: Optional[PagerDutyConfig] = None
    teams: Optional[TeamsConfig] = None
    custom_alerter: Optional[CustomAlerterConfig] = None

class AutowatchConfig(BaseModel):
    enabled: bool = False
    interval_seconds: int = 60

class DCVPGConfig(BaseModel):
    project: ProjectConfig
    contracts: ContractsConfig
    connections: List[ConnectionConfig] = []
    extensions: Optional[ExtensionsConfig] = None
    database: DatabaseConfig
    alerting: AlertingConfig
    autowatch: AutowatchConfig = AutowatchConfig()
    ai: Optional[Dict[str, Any]] = None
    mcp: Optional[Dict[str, Any]] = None
    api: Optional[Dict[str, Any]] = None
    dashboard: Optional[Dict[str, Any]] = None

def resolve_env_vars(data: Any) -> Any:
    env_var_pattern = re.compile(r'\$\{([^}]+)\}')
    
    if isinstance(data, dict):
        return {k: resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_vars(item) for item in data]
    elif isinstance(data, str):
        match = env_var_pattern.search(data)
        if match:
            env_var = match.group(1)
            return data.replace(f"${{{env_var}}}", os.environ.get(env_var, ""))
        return data
    return data

def load_config(config_path: str) -> DCVPGConfig:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = yaml.safe_load(f)
        
    resolved_config = resolve_env_vars(raw_config)
    return DCVPGConfig(**resolved_config)
