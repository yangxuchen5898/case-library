VALID_TYPES = {"TYPE_A", "TYPE_B", "TYPE_C"}
VALID_THEMES = {"强国建设", "上海实践", "创新发展", "校园文明"}


def parse_classification(raw: dict, fallback_title: str = "") -> dict:
    """Normalize raw LLM response into canonical classification dict."""
    types = _extract_types(raw)
    themes = _extract_themes(raw)
    reason = _pick_field(raw, ["reason", "判断理由"], default="")
    title = _pick_field(raw, ["title", "素材标题"], default=fallback_title)
    main_person = _pick_field(raw, ["main_person", "主要人物"], default="")
    primary_type = types[0] if types else ""
    return {
        "types": types,
        "themes": themes,
        "reason": str(reason),
        "primary_type": primary_type,
        "title": str(title),
        "main_person": str(main_person),
    }


def _extract_types(raw: dict) -> list[str]:
    """Extract types from response, handling multiple key aliases and string splitting."""
    for key in ("types", "主类型", "type"):
        if key in raw:
            value = raw[key]
            if isinstance(value, str):
                value = value.split(",")
            if isinstance(value, list):
                result = []
                for t in value:
                    if isinstance(t, str):
                        t = t.strip()
                        if t in VALID_TYPES:
                            result.append(t)
                return result
            break
    return []


def _extract_themes(raw: dict) -> list[str]:
    """Extract themes from response, using EXACT match against VALID_THEMES (no substring)."""
    for key in ("themes", "主题范围", "theme"):
        if key in raw:
            value = raw[key]
            if isinstance(value, str):
                value = value.split(",")
            if isinstance(value, list):
                result = []
                for t in value:
                    if isinstance(t, str):
                        t = t.strip()
                        if t in VALID_THEMES:
                            result.append(t)
                return result
            break
    return []


def _pick_field(raw: dict, aliases: list[str], default=""):
    """Pick first non-empty value from raw using aliases, coerced to str."""
    for alias in aliases:
        if alias in raw:
            value = raw[alias]
            if value is not None and value != "":
                return str(value)
    return default
