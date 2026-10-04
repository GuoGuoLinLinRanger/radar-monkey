"""Title classifier for sources that carry no category of their own (Intern Insider).

Deliberately software-only: pure IT, hardware, test, and general "technology"
titles are left out. Sources that already filter by a software category (Jobright,
Simplify's own lists) never need this.
"""
from __future__ import annotations

import re

INCLUDE = re.compile(
    r"\b(software|swe|sde|sdet|developer|programm(er|ing)|full[ -]?stack|front[ -]?end|back[ -]?end|"
    r"web (developer|dev|engineer)|(mobile|ios|android|game|gameplay|platform|infrastructure|cloud|"
    r"security|robotics|graphics|simulation|tools|compiler|kernel|systems software|application) (developer|dev|engineer)|"
    r"devops|site reliability|sre|embedded|firmware|machine learning|ml engineer|ml intern|ai engineer|ai intern|"
    r"artificial intelligence|deep learning|nlp|computer vision|data engineer(ing)?|"
    r"computer science|computer engineering|quantitative developer|quant developer)\b", re.I)
EXCLUDE = re.compile(
    r"\b(sales|marketing|recruit|hr|human resources|accountant|accounting|finance|financial|"
    r"mechanical|civil|structural|electrical(?! and computer)|chemical|environmental|manufacturing|"
    r"industrial engineer|process engineer|quality engineer|nurse|clinical|legal|paralegal|"
    r"buyer|merchandis|logistics|supply chain|construction|field engineer|hvac|plumb|"
    r"transportation|automotive|radiology|lab tech|lab assistant|hardware|asic|fpga|rf engineer|"
    r"graphic design|ux writer|copywriter|social media|communications|event|hospitality|"
    r"tax|audit|actuar|underwrit|real estate|property|retail|warehouse|driver)\b", re.I)


def is_swe(title: str) -> bool:
    t = (title or "").replace("-", " ")
    return bool(INCLUDE.search(t)) and not EXCLUDE.search(t)
