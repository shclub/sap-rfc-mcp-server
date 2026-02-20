"""
Config-driven custom RFC tools.

Define RFC function + import/export/table parameter mapping in a JSON file;
the server exposes each definition as an MCP tool.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp.types import Tool

logger = logging.getLogger(__name__)

# Default config path (optional); set RFC_TOOLS_CONFIG to override
DEFAULT_CONFIG_PATH = "rfc_tools.json"


def _find_config_path() -> Optional[Path]:
    path = os.environ.get("RFC_TOOLS_CONFIG")
    if path:
        p = Path(path)
        return p if p.is_file() else None
    for base in (Path.cwd(), Path(__file__).resolve().parent.parent):
        p = base / DEFAULT_CONFIG_PATH
        if p.is_file():
            return p
    return None


def _get_writable_config_path() -> Path:
    """Return path for reading/writing config; create parent dirs if needed."""
    path = os.environ.get("RFC_TOOLS_CONFIG")
    if path:
        p = Path(path)
    else:
        p = Path.cwd() / DEFAULT_CONFIG_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_rfc_tools_config() -> List[Dict[str, Any]]:
    """
    Load custom tool definitions from JSON file.
    Returns a list of tool definitions; empty if file not found or invalid.
    """
    path = _find_config_path()
    if not path:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tools = data.get("tools", data) if isinstance(data, dict) else data
        if not isinstance(tools, list):
            logger.warning("rfc_tools config: 'tools' must be a list")
            return []
        return tools
    except Exception as e:
        logger.warning("Failed to load rfc_tools config from %s: %s", path, e)
        return []


def build_tool_from_definition(defn: Dict[str, Any]) -> Optional[Tool]:
    """
    Build an MCP Tool from a single tool definition.

    Definition format:
      - name: tool name (required)
      - description: short description (required)
      - function_name: SAP RFC function name (required)
      - import_parameters: dict of param_name -> { "description", "default", "type" } (optional)
        If omitted, no fixed import params (caller passes parameters freely).
      - export_parameters: list of export param names to return, or null = all (optional)
      - table_parameters: list of table param names to return, or null = all (optional)
    """
    name = defn.get("name")
    description = defn.get("description")
    function_name = defn.get("function_name")
    if not name or not description or not function_name:
        logger.warning("Tool definition missing name, description, or function_name: %s", defn)
        return None

    import_params = defn.get("import_parameters", {})
    if not isinstance(import_params, dict):
        import_params = {}

    properties = {}
    required = []

    for param_name, param_def in import_params.items():
        if isinstance(param_def, dict):
            desc = param_def.get("description", param_name)
            param_type = param_def.get("type", "string")
            default = param_def.get("default")
        else:
            desc = str(param_def)
            param_type = "string"
            default = None
        prop = {"type": param_type, "description": desc}
        if default is not None:
            prop["default"] = default
        properties[param_name] = prop
        if default is None and param_def.get("required", True):
            required.append(param_name)

    # Always allow extra parameters to pass through to RFC
    properties["_extra_parameters"] = {
        "type": "object",
        "description": "Optional additional RFC parameters (key-value)",
    }

    input_schema = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    return Tool(
        name=name,
        description=description,
        inputSchema=input_schema,
    )


def get_custom_tools() -> List[Tool]:
    """Load config and return list of MCP Tools for custom RFC tools."""
    definitions = load_rfc_tools_config()
    tools = []
    for defn in definitions:
        t = build_tool_from_definition(defn)
        if t:
            tools.append(t)
    return tools


def get_custom_tool_definition(tool_name: str) -> Optional[Dict[str, Any]]:
    """Return the definition for a custom tool by name, or None."""
    definitions = load_rfc_tools_config()
    for defn in definitions:
        if defn.get("name") == tool_name:
            return defn
    return None


def _sap_type_to_tool_type(sap_type: str) -> str:
    """Map SAP parameter type to tool inputSchema type."""
    if not sap_type:
        return "string"
    t = str(sap_type).upper()
    if t in ("INT", "INT1", "INT2", "INT4", "INT8"):
        return "integer"
    if t in ("DEC", "QUAN", "FLTP"):
        return "number"
    if t in ("BOOL", "CHAR1"):
        return "boolean"
    return "string"


def generate_tool_definition_from_rfc_metadata(
    function_name: str,
    metadata: Dict[str, Any],
    tool_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a tool definition from RFC function metadata (import/export/table).

    metadata: result of metadata_manager.get_function_metadata(function_name),
              with keys "inputs", "outputs", "tables", "_metadata".
    tool_name: optional custom tool name; default is function_name lowercased.
    """
    info = metadata.get("_metadata", {})
    desc = info.get("description", "") or f"RFC function {function_name}"
    default_name = function_name.lower().replace(" ", "_")
    name = (tool_name or default_name).strip() or default_name

    import_params: Dict[str, Any] = {}
    for param_name, param_meta in metadata.get("inputs", {}).items():
        if not isinstance(param_meta, dict):
            param_meta = {}
        p = {
            "description": param_meta.get("description", param_name),
            "type": _sap_type_to_tool_type(param_meta.get("sap_type", param_meta.get("type", ""))),
        }
        if "default" in param_meta and param_meta["default"] != "":
            p["default"] = param_meta["default"]
        import_params[param_name] = p

    export_names = list(metadata.get("outputs", {}).keys())
    table_names = list(metadata.get("tables", {}).keys())

    return {
        "name": name,
        "description": desc,
        "function_name": function_name,
        "import_parameters": import_params,
        "export_parameters": export_names if export_names else None,
        "table_parameters": table_names if table_names else None,
    }


def save_rfc_tools_config(definitions: List[Dict[str, Any]]) -> Path:
    """Save tool definitions to config file. Returns path written."""
    path = _get_writable_config_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"tools": definitions}, f, indent=2, ensure_ascii=False)
    return path


def add_rfc_tool_definition(defn: Dict[str, Any]) -> Dict[str, Any]:
    """Add a tool definition. Raises ValueError if name already exists."""
    definitions = load_rfc_tools_config()
    name = defn.get("name")
    if not name:
        raise ValueError("Tool definition must have 'name'")
    if any(d.get("name") == name for d in definitions):
        raise ValueError(f"Tool with name '{name}' already exists")
    definitions.append(defn)
    save_rfc_tools_config(definitions)
    return defn


def update_rfc_tool_definition(name: str, defn: Dict[str, Any]) -> Dict[str, Any]:
    """Update a tool definition by name. Raises ValueError if not found."""
    definitions = load_rfc_tools_config()
    for i, d in enumerate(definitions):
        if d.get("name") == name:
            defn["name"] = name  # keep name immutable
            definitions[i] = defn
            save_rfc_tools_config(definitions)
            return defn
    raise ValueError(f"Tool with name '{name}' not found")


def delete_rfc_tool_definition(name: str) -> bool:
    """Remove a tool definition by name. Returns True if removed."""
    definitions = load_rfc_tools_config()
    new_list = [d for d in definitions if d.get("name") != name]
    if len(new_list) == len(definitions):
        return False
    save_rfc_tools_config(new_list)
    return True


def execute_custom_tool(
    call_rfc_fn,  # (function_name: str, **parameters) -> dict
    tool_name: str,
    arguments: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute a custom tool: build RFC parameters from definition + arguments, call RFC, return selected export/table.

    call_rfc_fn: e.g. sap_client.call_rfc_function
    """
    defn = get_custom_tool_definition(tool_name)
    if not defn:
        raise ValueError(f"Unknown custom tool: {tool_name}")

    function_name = defn["function_name"]
    import_parameters = defn.get("import_parameters", {})
    export_filter = defn.get("export_parameters")  # list or None = all
    table_filter = defn.get("table_parameters")  # list or None = all

    # Build RFC parameters: defaults from definition, then override with arguments
    params: Dict[str, Any] = {}
    for param_name, param_def in import_parameters.items():
        if isinstance(param_def, dict) and "default" in param_def:
            params[param_name] = param_def["default"]
    for k, v in arguments.items():
        if k.startswith("_"):
            continue
        params[k] = v
    extra = arguments.get("_extra_parameters")
    if isinstance(extra, dict):
        params.update(extra)

    result = call_rfc_fn(function_name, **params)

    # Optionally filter to only requested export/table keys
    out = {}
    if export_filter is not None:
        for key in export_filter:
            if key in result:
                out[key] = result[key]
    else:
        # By convention, skip internal keys and optionally only include known export/table
        for k, v in result.items():
            if not k.startswith("_"):
                out[k] = v

    if table_filter is not None:
        for key in table_filter:
            if key in result and key not in out:
                out[key] = result[key]
    else:
        for k, v in result.items():
            if k not in out and isinstance(v, (list, dict)):
                out[k] = v

    return out if out else result
