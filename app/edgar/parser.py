"""
SEC 13F-HR infotable XML parser.

Handles all three namespace variants found across EDGAR filing years:
  - No namespace  (pre-2013)
  - xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable"  (most common)
  - EIS/ns1 prefixed variants
Uses {*} wildcard so a single code path covers all three.
"""

import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RawHolding:
    cusip: str
    company_name: str
    title_of_class: str
    value_thousands: int
    shares: int
    investment_discretion: str
    put_call: Optional[str] = None


def _text(elem: ET.Element, tag: str) -> str:
    child = elem.find(f"{{*}}{tag}")
    return child.text.strip() if child is not None and child.text else ""


def parse_infotable(xml_text: str) -> list[RawHolding]:
    """Parse a 13F-HR infotable XML and return a list of RawHolding objects."""
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError as exc:
        logger.error("XML parse failure: %s", exc)
        return []

    holdings: list[RawHolding] = []

    for info in root.iter():
        # Match <infoTable> regardless of namespace prefix
        if not info.tag.endswith("}infoTable") and info.tag != "infoTable":
            continue

        name = _text(info, "nameOfIssuer")
        cusip = _text(info, "cusip")
        title = _text(info, "titleOfClass")
        value_str = _text(info, "value")

        # Shares live inside <shrsOrPrnAmt><sshPrnamt>
        shrs_elem = info.find("{*}shrsOrPrnAmt") or info.find("shrsOrPrnAmt")
        shares = 0
        if shrs_elem is not None:
            raw = _text(shrs_elem, "sshPrnamt")
            shares = int(re.sub(r"[^\d]", "", raw)) if raw else 0

        discretion = _text(info, "investmentDiscretion")

        pc_elem = info.find("{*}putCall") or info.find("putCall")
        put_call = pc_elem.text.strip() if pc_elem is not None and pc_elem.text else None

        try:
            value = int(re.sub(r"[^\d]", "", value_str))
        except ValueError:
            value = 0

        if not cusip:
            continue

        holdings.append(RawHolding(
            cusip=cusip,
            company_name=name,
            title_of_class=title,
            value_thousands=value,
            shares=shares,
            investment_discretion=discretion,
            put_call=put_call,
        ))

    return sorted(holdings, key=lambda h: h.value_thousands, reverse=True)
