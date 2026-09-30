from app.ui.themes import DEFAULT_THEME_ID, MODERN_LABELS, get_theme, list_themes


def test_all_themes_have_full_labels() -> None:
    keys = set(MODERN_LABELS.keys())
    for theme in list_themes():
        assert set(theme.labels.keys()) == keys


def test_get_theme_fallback() -> None:
    assert get_theme('unknown').id == DEFAULT_THEME_ID


def test_theme_ids() -> None:
    ids = {theme.id for theme in list_themes()}
    assert ids == {
        'warm', 'cold', 'autumn', 'spring', 'pink',
        'modern', 'wood', 'leather', 'glass', 'metal',
    }
