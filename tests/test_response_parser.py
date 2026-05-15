from backend.response_parser import parse_classification


def test_parse_full_response():
    raw = {
        "types": ["TYPE_A", "TYPE_B"],
        "themes": ["强国建设", "上海实践"],
        "reason": "some reason",
        "title": "some title",
        "main_person": "some person",
    }
    result = parse_classification(raw)
    assert result["types"] == ["TYPE_A", "TYPE_B"]
    assert result["themes"] == ["强国建设", "上海实践"]
    assert result["reason"] == "some reason"
    assert result["primary_type"] == "TYPE_A"
    assert result["title"] == "some title"
    assert result["main_person"] == "some person"


def test_parse_chinese_keys():
    raw = {
        "主类型": ["TYPE_C"],
        "主题范围": ["创新发展"],
        "判断理由": "reason in chinese",
        "素材标题": "title in chinese",
        "主要人物": "person in chinese",
    }
    result = parse_classification(raw)
    assert result["types"] == ["TYPE_C"]
    assert result["themes"] == ["创新发展"]
    assert result["reason"] == "reason in chinese"
    assert result["title"] == "title in chinese"
    assert result["main_person"] == "person in chinese"


def test_parse_string_types():
    raw = {
        "types": "TYPE_A,TYPE_B",
    }
    result = parse_classification(raw)
    assert result["types"] == ["TYPE_A", "TYPE_B"]


def test_parse_exact_theme_match():
    raw = {
        "themes": ["上海实践", "实践"],
    }
    result = parse_classification(raw)
    assert "上海实践" in result["themes"]
    assert "实践" not in result["themes"]


def test_parse_fallback_title():
    raw = {}
    result = parse_classification(raw, fallback_title="fallback")
    assert result["title"] == "fallback"


def test_parse_empty_response():
    raw = {}
    result = parse_classification(raw)
    assert result["types"] == []
    assert result["themes"] == []
    assert result["reason"] == ""
    assert result["primary_type"] == ""
    assert result["title"] == ""
    assert result["main_person"] == ""


def test_parse_non_string_type_ignored():
    raw = {
        "types": ["TYPE_A", {"nested": "dict"}, "TYPE_B"],
    }
    result = parse_classification(raw)
    assert result["types"] == ["TYPE_A", "TYPE_B"]
