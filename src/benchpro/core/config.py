import os
import shutil
import re
import socket
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field
from benchpro.core.logger import get_logger
from benchpro.core.exceptions import ConfigError

logger = get_logger()


# Constants
CONFIG_FILENAME = "config.yaml"
PROJECT_DIR_NAME = ".benchpro"
DEFAULT_USER_CONFIG_HOME = Path.home() / ".config/benchpro"
# Standard site config location, can be overridden by env var
DEFAULT_SITE_CONFIG_PATH = Path("/etc/benchpro") / CONFIG_FILENAME
# Install root relative to this file: src/benchpro/core/config.py -> root
INSTALL_ROOT = Path(__file__).resolve().parents[3]

class SystemConfig(BaseModel):
    name: str = "default"
    host_patterns: List[str] = Field(default_factory=list)
    platform_patterns: List[str] = Field(default_factory=list)
    scheduler: str = "local"
    default_walltime: int = 3600
    max_walltime: int = 86400
    max_local_tasks: int = 8
    account: Optional[str] = None
    partition: Optional[str] = None
    results_server_url: Optional[str] = None
    api_token: Optional[str] = None
    workspace_dir: Optional[str] = None
    compiler: Optional[str] = None
    mpi: Optional[str] = None
    reservation: Optional[str] = None


class BenchProConfig(BaseModel):
    config_dir: Optional[str] = None

class AppsConfig(BaseModel):
    check_duplicates: bool = True

class JobConfig(BaseModel):
    nodes: Optional[int] = None
    ranks: Optional[int] = None
    threads: Optional[int] = None
    gpus: Optional[int] = None
    walltime: Optional[str] = None

    model_config = ConfigDict(extra="allow")

class DefaultsConfig(BaseModel):
    compiler: Optional[str] = None
    mpi: Optional[str] = None

    model_config = ConfigDict(extra="allow")

class Config(BaseModel):
    benchpro: BenchProConfig = Field(default_factory=BenchProConfig)
    apps: AppsConfig = Field(default_factory=AppsConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    systems: Dict[str, SystemConfig] = Field(default_factory=dict)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    runtime: JobConfig = Field(default_factory=JobConfig)
    env: Dict[str, str] = Field(default_factory=dict)
    
    @staticmethod
    def get_user_config_dir() -> Path:
        """Get the user configuration directory."""
        config_dir = os.environ.get("BENCHPRO_CONFIG_DIR")
        if config_dir:
            return Path(config_dir)
        return DEFAULT_USER_CONFIG_HOME
    
    @classmethod
    def resolve_user_config_dir(cls) -> Path:
        """Resolve the effective user config directory, checking for redirects in bootstrap layers."""
        # 1. Define base layers (Site, Install, Local) to check for redirects
        candidates = []
        
        # Env override for CONFIG FILE (not dir) - check it for redirects too?
        env_path = os.environ.get("BENCHPRO_CONFIG")
        if env_path: candidates.append(Path(env_path))
            
        # Site config
        site_config = os.environ.get("BENCHPRO_SITE_CONFIG")
        if site_config: candidates.append(Path(site_config))
        else: candidates.append(DEFAULT_SITE_CONFIG_PATH)
            
        candidates.append(INSTALL_ROOT / "config" / CONFIG_FILENAME)
        candidates.append(Path.cwd() / PROJECT_DIR_NAME / CONFIG_FILENAME)
        
        # 2. Scan for redirection
        for path in candidates:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        data = yaml.safe_load(f)
                        if data and "benchpro" in data and "config_dir" in data["benchpro"]:
                            path_str = data["benchpro"]["config_dir"]
                            # Handle expanding vars
                            return Path(os.path.expandvars(path_str)).expanduser()
                except Exception:
                    pass
                    
        # 3. Fallback to default/env
        return cls.get_user_config_dir()

    @classmethod
    def _build_load_list(cls) -> List[Path]:
        """Build the list of config paths to load, respecting precedence and redirection."""
        # 1. Resolve User Config Directory (handling redirects)
        user_config_dir = cls.resolve_user_config_dir()
        user_config_path = user_config_dir / CONFIG_FILENAME
        
        # Auto-init if missing and using default (and not overridden by env?)
        # If user_config_dir was redirected, we might assume user wants it there.
        # But auto-init typically only happens for the default location to avoid spamming dirs?
        # User said: "i expect if I change benchpro.config_dir... I will create a new user config directory regardless"
        # So we should auto-init IF it doesn't exist.
        if not user_config_path.exists():
             cls._init_user_config(user_config_dir)

        # 2. Construct Final Load List
        final_list = []
        
        # Env
        env_path = os.environ.get("BENCHPRO_CONFIG")
        if env_path: final_list.append(Path(env_path))
        
        # Site
        site_config = os.environ.get("BENCHPRO_SITE_CONFIG")
        if site_config: final_list.append(Path(site_config))
        else: final_list.append(DEFAULT_SITE_CONFIG_PATH)
        
        # Install
        final_list.append(INSTALL_ROOT / "config" / CONFIG_FILENAME)
        
        # User
        final_list.append(user_config_path)
        
        # Local
        final_list.append(Path.cwd() / PROJECT_DIR_NAME / CONFIG_FILENAME)
        
        return final_list

    @classmethod
    def _expand_layers(cls, data: Dict[str, Any], source_map: Dict[str, Any] = None) -> None:
        """Dynamically load layers based on defaults (compiler, mpi)."""
        defaults = data.get("defaults", {})
        
        # Triggers
        triggers = {
            "compiler": "compilers.yaml",
            "mpi": "mpi.yaml"
        }
        
        from benchpro.core.env_config import EnvConfigLoader
        config_dir = INSTALL_ROOT / "config"
        
        # Check if dir exists, otherwise skip
        if not config_dir.exists():
            return

        loader = EnvConfigLoader(config_dir)
        
        for category, filename in triggers.items():
            name = defaults.get(category)
            if name and str(name).lower() not in ["system", "none", "null"]:
                # Load env vars
                env_vars = loader.resolve_env(name, None, category)
                
                if env_vars:
                    if "env" not in data:
                        data["env"] = {}
                    
                    data["env"].update(env_vars)
                    
                    if source_map is not None:
                        source_label = f"$BP_SITE/config/{filename} ({name})"
                        if "env" not in source_map:
                            source_map["env"] = {}
                        
                        for k in env_vars:
                            source_map["env"][k] = source_label

    @classmethod
    def load(cls, config_paths: List[Path] = None) -> "Config":
        """
        Load configuration from multiple layers.
        Precedence: Defaults < Site < Install < User < Local
        """
        config_data = {}
        
        if config_paths is None:
            config_paths = cls._build_load_list()
            
        # 1. Load and merge
        for path in config_paths:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        layer = yaml.safe_load(f)
                        if layer:
                            config_data = cls._deep_merge(config_data, layer)
                except Exception as e:
                    raise ConfigError(f"Failed to load config from {path}: {e}")

        # 2. Detect & Merge Active System (Pre-Interpolation)
        # We need to detect based on Raw Data.
        active_system_name, active_system_data = cls._detect_active_system(config_data)
        if active_system_name and active_system_data:
             if 'system' not in config_data: config_data['system'] = {}
             # Merge active system into system block
             sys_base = config_data.get('system', {})
             if not isinstance(sys_base, dict):
                 # Handle corruption/mismatch where system is scalar
                 sys_base = {}
             config_data['system'] = cls._deep_merge(sys_base, active_system_data)

        # 3. Expand Dynamic Layers (Compiler/MPI)
        # Now checks config_data (which has system defaults merged)
        cls._expand_layers(config_data, None)

        # 4. Interpolate variables
        from benchpro.core.templating import TemplateEngine
        
        # Add env vars to context (including those we just loaded from layers!)
        env_context = {k: v for k, v in os.environ.items()}
        # Merge loaded envs (from layers) into env context so they can be used in interpolation
        if "env" in config_data:
            env_context.update(config_data["env"])
        
        # Create context
        context = {
            "env": env_context,
            **config_data,
        }
        
        engine = TemplateEngine(context)
        resolved_data = engine.render(config_data)
        
        # 5. Create instance
        config = cls(**resolved_data)
        return config

    @classmethod
    def inspect(cls, config_paths: List[Path] = None) -> tuple[Dict[str, Any], Dict[str, str]]:
        """
        Load configuration and track sources.
        Returns (resolved_data, source_map)
        """
        config_data = {}
        source_map = {}
        
        if config_paths is None:
            config_paths = cls._build_load_list()
            
        # 1. Load and merge
        for path in config_paths:
            if path.exists():
                try:
                    with open(path, "r") as f:
                        layer = yaml.safe_load(f)
                        if layer:
                            config_data = cls._deep_merge(config_data, layer)
                            cls._update_source_map(source_map, layer, str(path))
                except Exception:
                    pass

        # 2. Detect & Merge Active System (Pre-Interpolation)
        active_system_name, active_system_data = cls._detect_active_system(config_data)
        if active_system_name and active_system_data:
             if 'system' not in config_data: config_data['system'] = {}
             # Merge active system into system block
             sys_base = config_data.get('system', {})
             if not isinstance(sys_base, dict):
                 sys_base = {}
             config_data['system'] = cls._deep_merge(sys_base, active_system_data)

             # Merge source map for system
             # Check if system in source map is dict
             if "systems" in source_map and active_system_name in source_map["systems"]:
                 system_sources = source_map.get("system", {})
                 if not isinstance(system_sources, dict):
                     system_sources = {}
                 active_sources = source_map["systems"][active_system_name]
                 source_map["system"] = cls._deep_merge(system_sources, active_sources)

        # 3. Expand Dynamic Layers (Compiler/MPI)
        cls._expand_layers(config_data, source_map)
                    
        # 4. Interpolate variables
        from benchpro.core.templating import TemplateEngine
        
        env_context = {k: v for k, v in os.environ.items()}
        # Merge loaded envs
        if "env" in config_data:
            env_context.update(config_data["env"])

        context = { "env": env_context, **config_data }
        engine = TemplateEngine(context)
        resolved_data = engine.render(config_data)
        
        return resolved_data, source_map

    @staticmethod
    def _detect_active_system(data: Dict[str, Any]) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Detect active system based on environment, platform, and hostname."""
        systems = data.get("systems", {})
        if not systems:
            return None, None

        # 1. Check env var override
        env_system = os.environ.get("BENCHPRO_SYSTEM")
        if env_system and env_system in systems:
            return env_system, systems[env_system]
        
        # 2. Check platform/OS matching
        current_platform = platform.system().lower()
        for name, sys_cfg in systems.items():
            patterns = sys_cfg.get("platform_patterns", [])
            for pattern in patterns:
                if re.match(pattern, current_platform, re.IGNORECASE):
                    return name, sys_cfg

        # 3. Check hostname matching
        hostname = socket.getfqdn()
        for name, sys_cfg in systems.items():
            patterns = sys_cfg.get("host_patterns", [])
            for pattern in patterns:
                if re.match(pattern, hostname):
                    return name, sys_cfg
                    
        return None, None

    @staticmethod
    def _update_source_map(source_map: Dict[str, Any], layer: Dict[str, Any], source: str):
        """Recursively update source map."""
        for key, value in layer.items():
            if isinstance(value, dict):
                if key not in source_map or not isinstance(source_map[key], dict):
                    source_map[key] = {}
                Config._update_source_map(source_map[key], value, source)
            else:
                source_map[key] = source

    @staticmethod
    def _deep_merge(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        """
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @classmethod
    def update_user_config(cls, key: str, value: Any, reset: bool = False, config_path: Path = None):
        """
        Update a value in the user configuration file with smart key matching.
        """
        if config_path is None:
            user_config_dir = cls.get_user_config_dir()
            config_path = user_config_dir / "config.yaml"
                
        if not config_path.exists():
            return False, "Configuration file not found"

        try:
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            return False, f"Failed to load user config: {e}"

        # Detect active system by loading FULL config to resolve environment/site defs
        # We need to know what the CURRENTLY active system is, which might be defined in site config
        try:
             full_config = cls.load()
             active_sys = full_config.system.name if full_config.system.name != "default" else None
        except Exception:
             active_sys = None

        # Split key path
        parts = key.split(".")
        
        target_dict = data
        last_key = parts[-1]
        
        # Smart Matching Logic
        if len(parts) == 1:
            simple_key = parts[0]
            # Check for known fields
            if simple_key == "root_dir":
                # defaults.root_dir
                target_dict = data.setdefault("defaults", {})
                last_key = "root_dir"
            elif simple_key in AppsConfig.model_fields:
                # apps.<key>
                target_dict = data.setdefault("apps", {})
                last_key = simple_key
            elif simple_key in SystemConfig.model_fields:
                # System parameter -> systems.<active>.<key>
                if active_sys:
                    systems = data.setdefault("systems", {})
                    target_dict = systems.setdefault(active_sys, {})
                    last_key = simple_key
                else:
                    # Fallback to global system block
                    target_dict = data.setdefault("system", {})
                    last_key = simple_key
            else:
                # Unknown key, default to system (global)
                target_dict = data.setdefault("system", {})
                last_key = simple_key
        else:
            # Dot notation: navigate to parent
            for part in parts[:-1]:
                target_dict = target_dict.setdefault(part, {})
                if not isinstance(target_dict, dict):
                     return False, f"Configuration key conflict: '{part}' is a value, expected section."
        
        # Update or Reset
        if reset:
            if last_key in target_dict:
                del target_dict[last_key]
                action = "removed"
            else:
                action = "not found"
        else:
            # Type inference
            if isinstance(value, str):
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                
            target_dict[last_key] = value
            action = "updated"
            
        # Write back
        try:
            with open(config_path, "w") as f:
                yaml.dump(data, f)
            return True, f"Successfully {action} '{key}' in {config_path}"
        except Exception as e:
            return False, f"Failed to write config: {e}"

    @staticmethod
    def _init_user_config(config_dir: Path):
        """
        Initialize user configuration directory with minimal settings.
        System defaults are inherited from site/install configuration.
        """
        print(f"First run detected. Initializing configuration in {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
        (config_dir / "profiles").mkdir(exist_ok=True)
        (config_dir / "templates").mkdir(exist_ok=True)
        
        # Create default config
        config_path = config_dir / CONFIG_FILENAME
        
        # Write minimal config
        config_data = {
            "benchpro": {
                "config_dir": str(config_dir)
            }
        }
        
        try:
            with open(config_path, "w") as f:
                yaml.dump(config_data, f)
            print(f"Created configuration at {config_path}")
        except Exception as e:
             print(f"Failed to write config: {e}")
             raise
        # We already set root_dir above based on detection.
        
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
