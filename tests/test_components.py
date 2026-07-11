from ui.components import _esc, _badge_html


def test_esc_neutralizes_html_tags():
    assert _esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_esc_neutralizes_attribute_breakout():
    payload = '"><img src=x onerror=alert(1)>'
    escaped = _esc(payload)
    assert "<img" not in escaped
    assert "&lt;img" in escaped


def test_esc_handles_non_string_values():
    assert _esc(34240) == "34240"
    assert _esc(None) == "None"


def test_badge_html_escapes_text():
    html_out = _badge_html("<b>Loi publiée</b>")
    assert "<b>" not in html_out
    assert "&lt;b&gt;" in html_out
    assert 'class="uimm-badge"' in html_out
