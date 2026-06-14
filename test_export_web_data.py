"""
Test the file export_web_data.py
"""

import pytest

import export_web_data as ewd
import long_time


@pytest.mark.parametrize('stem,expected', [
    ('US_presidents', 'Rulers & Dynasties'),
    ('Roman_emperors', 'Rulers & Dynasties'),
    ('Ottoman_Sultans', 'Rulers & Dynasties'),
    ('Egyptian_dynasties', 'Civilizations & Periods'),
    ('Persian_empires', 'Civilizations & Periods'),
    ('Japanese_periods', 'Civilizations & Periods'),
    ('Modern_wars', 'Wars & Battles'),
    ('Battles', 'Wars & Battles'),
    ('Crusades', 'Wars & Battles'),
    ('Physicist_lives', 'Science & Technology'),
    ('Mathematician_lives', 'Science & Technology'),
    ('Space_missions', 'Science & Technology'),
    ('Composers', 'Arts & Letters'),
    ('Painter_lives', 'Arts & Letters'),
    ('Philosopher_lives', 'Thought & Religion'),
    ('Religious_founders', 'Thought & Religion'),
    ('American_lives', 'People'),
    ('World_events', 'Events'),
])
def test_classify_theme(stem, expected):
    assert ewd.classify_theme(stem) == expected


def test_classify_theme_unmatched_is_other():
    assert ewd.classify_theme('Something_Unrelated') == 'Other'


def test_classify_theme_first_rule_wins():
    # 'Egyptian_pharaohs' matches 'pharaoh' (Rulers) before any periods rule.
    assert ewd.classify_theme('Egyptian_pharaohs') == 'Rulers & Dynasties'


def test_prettify():
    assert ewd.prettify('US_presidents') == 'US presidents'
    assert ewd.prettify('Composers') == 'Composers'


@pytest.mark.parametrize('keywords,expected', [
    (['USA', 'Event'], 'event'),
    (['Roman', 'Reign'], 'reign'),
    (['Physicist', 'Life'], 'life'),
    (['War', 'Global'], 'war'),
    (['Civilization'], 'period'),
    ([], 'period'),
])
def test_entry_type(keywords, expected):
    assert ewd.entry_type(keywords) == expected


def test_entry_type_event_takes_priority():
    # An entry tagged both Reign and Event is treated as a point event.
    assert ewd.entry_type(['Reign', 'Event']) == 'event'


# ---- colour resolution from template.svg ---------------------------------

SAMPLE_STYLE = '''
rect { stroke: none; }
rect.House_of_Tudor.even { fill : #2e8b57; }
rect.House_of_Tudor.odd { fill: #5cb585; }
rect.Party_Democratic { fill: #0044c9; }
rect.England.Life { fill : #3aa76a; }
text.Reign { fill: #ffffff; }
'''


@pytest.fixture
def rules(tmp_path):
    svg = tmp_path / 'template.svg'
    svg.write_text(SAMPLE_STYLE + '</style>')
    return ewd.parse_style_rules(svg)


def test_parse_style_rules_skips_non_fill_and_non_rect(rules):
    # The bare `rect {}` rule has no fill and the `text.Reign` rule is not a
    # rect, so neither should appear.
    selectors = [classes for classes, _fill, _spec in rules]
    assert {'House_of_Tudor', 'even'} in selectors
    assert {'Party_Democratic'} in selectors
    assert not any('Reign' in c for c in selectors)


def test_resolve_template_color_most_specific_wins(rules):
    # A Tudor 'even' entry should match the two-class rule, not be ambiguous.
    color = ewd.resolve_template_color({'House_of_Tudor', 'even'}, rules)
    assert color == '#2e8b57'


def test_resolve_template_color_requires_all_classes(rules):
    # Missing the even/odd class means the Tudor rules do not apply.
    assert ewd.resolve_template_color({'House_of_Tudor'}, rules) is None


def test_resolve_template_color_single_class(rules):
    assert ewd.resolve_template_color({'Party_Democratic'}, rules) == '#0044c9'


def test_resolve_template_color_no_match(rules):
    assert ewd.resolve_template_color({'Unknown'}, rules) is None


# ---- fallback colour ------------------------------------------------------

def test_category_fallback_color_is_valid_hex():
    color = ewd.category_fallback_color('Composers', '')
    assert len(color) == 7 and color[0] == '#'
    int(color[1:], 16)  # parses as hex


def test_category_fallback_color_is_deterministic():
    a = ewd.category_fallback_color('Mathematician lives', 'even')
    b = ewd.category_fallback_color('Mathematician lives', 'even')
    assert a == b


def test_category_fallback_color_even_odd_differ():
    even = ewd.category_fallback_color('Painter lives', 'even')
    odd = ewd.category_fallback_color('Painter lives', 'odd')
    assert even != odd


@pytest.mark.parametrize('h,s,light,expected', [
    (0.0, 0.0, 0.0, '#000000'),
    (0.0, 0.0, 1.0, '#ffffff'),
    (0.0, 1.0, 0.5, '#ff0000'),
    (1 / 3, 1.0, 0.5, '#00ff00'),
    (2 / 3, 1.0, 0.5, '#0000ff'),
])
def test_hsl_to_hex(h, s, light, expected):
    assert ewd._hsl_to_hex(h, s, light) == expected


# ---- date helpers ---------------------------------------------------------

def test_year_float_ce_start_of_year():
    d = long_time.date(1789, 1, 1, True)
    assert ewd.year_float(d) == pytest.approx(1789.0)


def test_year_float_bce_is_negative():
    # 27 BCE, mid-January -> just past -27.0 (matches Augustus' reign start).
    d = long_time.date(27, 1, 16, False)
    val = ewd.year_float(d)
    assert -27.0 < val < -26.9


def test_year_float_fraction_advances_through_year():
    jan = ewd.year_float(long_time.date(1500, 1, 1, True))
    jul = ewd.year_float(long_time.date(1500, 7, 1, True))
    dec = ewd.year_float(long_time.date(1500, 12, 31, True))
    assert jan < jul < dec
    assert jan == pytest.approx(1500.0)
    assert dec == pytest.approx(1501.0, abs=0.01)


def test_era_label_ce():
    assert ewd.era_label(long_time.date(1776, 7, 4, True)) == '1776-07-04 CE'


def test_era_label_bce():
    assert ewd.era_label(long_time.date(44, 3, 15, False)) == '-0044-03-15 BCE'
