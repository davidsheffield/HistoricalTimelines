"""
Export timeline data to a JavaScript file for the interactive web viewer.

Unlike ``timeline.py`` (which renders fixed printable SVG sheets), the web
viewer in ``web/index.html`` lays everything out dynamically in the browser.
This script reuses ``timeline.py``'s data pipeline to load every YAML file in
``dates/``, then writes a single ``web/timeline_data.js`` that assigns the data
to ``window.TIMELINE_DATA``.

A plain ``.js`` file (rather than JSON loaded with ``fetch``) is used so the
viewer also works when opened directly from disk with a ``file://`` URL, where
``fetch`` is blocked but ``<script src>`` is not.

Usage:
    python export_web_data.py
"""

import json
import pathlib
import re

import pandas as pd

import timeline

# ---------------------------------------------------------------------------
# Theme classification
# ---------------------------------------------------------------------------
#
# Categories (one per YAML file) are grouped into a handful of top-level themes
# so the viewer can offer a tidy hierarchical selector. Matching is by keyword
# substrings against the file stem, in order; the first match wins.

THEME_RULES = [
    ('Rulers & Dynasties', (
        'monarch', 'emperor', 'sultan', 'president', 'rulers', 'kings',
        'caliphate', 'leaders', 'tsars', 'shogun', 'pharaoh',
    )),
    ('Civilizations & Periods', (
        'dynast', 'empire', 'civilization', 'kingdom', 'period', 'state',
        'culture', 'settlement', 'nomad', 'mediterranean',
    )),
    ('Wars & Battles', (
        'war', 'battle', 'crusade', 'napoleonic',
    )),
    ('Science & Technology', (
        'physic', 'discover', 'technology', 'milestone', 'space',
        'mathematician', 'inventor',
    )),
    ('Arts & Letters', (
        'composer', 'painter', 'writer',
    )),
    ('Thought & Religion', (
        'philosopher', 'religious', 'theolog', 'reformer',
    )),
    ('People', (
        'lives', 'life',
    )),
    ('Events', (
        'event',
    )),
]


def classify_theme(stem: str) -> str:
    """Map a YAML file stem to a top-level theme name."""
    low = stem.lower()
    for theme, needles in THEME_RULES:
        if any(n in low for n in needles):
            return theme
    return 'Other'


def prettify(stem: str) -> str:
    """Turn a file stem like 'US_presidents' into 'US presidents'."""
    return stem.replace('_', ' ')


# ---------------------------------------------------------------------------
# Colour resolution from template.svg
# ---------------------------------------------------------------------------
#
# The print stylesheet keys fill colours off combinations of CSS classes
# (keywords + an even/odd alternating class). We parse those rules once and,
# for each entry, pick the most specific rule whose classes are all present on
# that entry. Entries with no matching rule fall back to a per-category hue so
# every bar still gets a sensible colour in the viewer.

_RULE_RE = re.compile(r'(rect[^\{]+)\{([^}]*)\}')
_FILL_RE = re.compile(r'fill\s*:\s*(#[0-9a-fA-F]+)')


def parse_style_rules(template_path: pathlib.Path):
    """Return a list of (class_set, fill, specificity) from template.svg.

    Only single-selector ``rect`` rules carrying a ``fill`` are kept. A rule
    like ``rect.House_of_Tudor.even`` becomes
    ({'House_of_Tudor', 'even'}, '#2e8b57', 2).
    """
    text = template_path.read_text()
    # Drop the substitution placeholders and everything after the <style> block.
    style = text.split('</style>', 1)[0]
    rules = []
    for selector_blob, body in _RULE_RE.findall(style):
        fill_match = _FILL_RE.search(body)
        if not fill_match:
            continue
        fill = fill_match.group(1)
        # A rule may list several comma-separated selectors sharing one body.
        for selector in selector_blob.split(','):
            selector = selector.strip()
            if not selector.startswith('rect'):
                continue
            classes = set(selector.split('.')[1:])
            if not classes:
                continue
            rules.append((classes, fill, len(classes)))
    return rules


def resolve_template_color(class_set, rules):
    """Best-matching template fill for a set of classes, or None."""
    best = None
    best_spec = -1
    for classes, fill, spec in rules:
        if classes <= class_set and spec > best_spec:
            best = fill
            best_spec = spec
    return best


# Deterministic fallback hues per category, evenly spread around the wheel.
def category_fallback_color(category: str, alternating: str) -> str:
    """A stable HSL-derived hex colour for a category, varied by even/odd."""
    h = 0
    for ch in category:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    hue = h % 360
    # Odd entries are rendered a touch lighter so adjacent reigns differ.
    light = 0.42 if alternating != 'odd' else 0.56
    return _hsl_to_hex(hue / 360.0, 0.45, light)


def _hsl_to_hex(h: float, s: float, light: float) -> str:
    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        r = g = b = light
    else:
        q = light * (1 + s) if light < 0.5 else light + s - light * s
        p = 2 * light - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)
    return f'#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}'


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def year_float(date) -> float:
    """Signed fractional year for a long_time.date (matches calculate_x)."""
    signed = date.year if date.era else -date.year
    span = date.days_in_year() - 1
    frac = (date.ordinal_day() - 1) / span if span else 0.0
    return signed + frac


def era_label(date) -> str:
    """Human-readable 'YYYY-MM-DD CE/BCE' for tooltips."""
    signed = date.year if date.era else -date.year
    iso = date.isoformat()
    suffix = 'CE' if signed > 0 else 'BCE'
    return f'{iso} {suffix}'


def entry_type(keywords) -> str:
    """Coarse type used for layout/styling: reign, life, war, event, period."""
    kw = set(keywords)
    if 'Event' in kw:
        return 'event'
    if 'Reign' in kw:
        return 'reign'
    if 'Life' in kw:
        return 'life'
    if 'War' in kw:
        return 'war'
    return 'period'


# ---------------------------------------------------------------------------
# Main export
# ---------------------------------------------------------------------------

def build_records():
    root = pathlib.Path(__file__).parent
    rules = parse_style_rules(root / 'template.svg')

    dates = timeline.load_data()

    # extract_dates may skip entries with missing dates, so extract one file at
    # a time and tag each surviving row with its source category. This keeps the
    # category attribution correct even if some entries are dropped.
    frames = []
    for stem, df in dates.items():
        file_boxes = timeline.extract_dates({stem: df})
        if file_boxes.empty:
            continue
        file_boxes = file_boxes.copy()
        file_boxes['category_stem'] = stem
        frames.append(file_boxes)

    boxes = pd.concat(frames, ignore_index=True)
    boxes = timeline.assign_alternating_classes(boxes)

    records = []
    for _idx, row in boxes.iterrows():
        stem = row['category_stem']
        keywords = row['Keywords'] if isinstance(row['Keywords'], list) else []
        alternating = row.get('alternating_class', '') or ''
        class_set = set(keywords)
        if alternating:
            class_set.add(alternating)

        color = resolve_template_color(class_set, rules)
        if color is None:
            color = category_fallback_color(stem, alternating)

        start = year_float(row['Start'])
        end = year_float(row['End'])
        typ = entry_type(keywords)
        is_point = typ == 'event' or row['Start'] == row['End']

        records.append({
            'label': row['Label'],
            'category': prettify(stem),
            'theme': classify_theme(stem),
            'type': typ,
            'start': round(start, 4),
            'end': round(end, 4),
            'point': is_point,
            'color': color,
            'keywords': keywords,
            'startLabel': era_label(row['Start']),
            'endLabel': era_label(row['End']),
        })

    return records


def main():
    records = build_records()

    # Stable ordering: theme, category, then chronological.
    records.sort(key=lambda r: (r['theme'], r['category'], r['start']))

    out_dir = pathlib.Path(__file__).parent / 'web'
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / 'timeline_data.js'

    payload = json.dumps(records, ensure_ascii=False, separators=(',', ':'))
    out_path.write_text(
        '// Auto-generated by export_web_data.py. Do not edit by hand.\n'
        f'window.TIMELINE_DATA = {payload};\n',
        encoding='utf-8',
    )

    themes = {}
    for r in records:
        themes.setdefault(r['theme'], set()).add(r['category'])
    print(f'Wrote {len(records)} entries to {out_path}')
    for theme in sorted(themes):
        cats = ', '.join(sorted(themes[theme]))
        print(f'  {theme}: {cats}')


if __name__ == '__main__':
    main()
