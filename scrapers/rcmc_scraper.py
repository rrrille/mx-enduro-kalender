"""Scraper för enduro.rcmc.se (Enduro für alle).

Sidan är en Azure-hostrad kalender (enduroforall.azurewebsites.net)
som aggregerar öppettider från 7 klubbar i Stockholmsområdet.

Sidan visar events i en HTML-lista. Varje event har:
- Klubb/arrangör
- Datum och tid
- Plats/bana
- Beskrivning (övningsledare, baninfo etc.)

Sidan uppdateras var 30:e minut.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseScraper, TrainingEvent

# Mappar RCMC-klubbnamn till våra club_id:n
RCMC_CLUB_MAP = {
    "åsätra": "asatra_mk",
    "arlanda": "arlanda_mc",
    "mälarö": "malaro_mck",
    "botkyrka": "botkyrka_mk",
    "haninge": "haninge_mk",
    "nynäshamn": "nynashamns_mck",
    "södertälje": "amf_sodertalje",
    "amf": "amf_sodertalje",
}

URLS = [
    "https://enduro.rcmc.se/",
    "https://enduroforall.azurewebsites.net/",
]


class RcmcScraper(BaseScraper):
    """Scraper för enduro.rcmc.se / enduroforall.azurewebsites.net."""

    def scrape(self) -> list[TrainingEvent]:
        html = self._fetch_page()
        if not html:
            self.logger.warning("Kunde inte hämta sidan, returnerar tom lista")
            return []
        return self._parse_events(html)

    def _fetch_page(self) -> str | None:
        """Försök hämta sidan från båda URL:erna."""
        for url in URLS:
            try:
                self.logger.info(f"Försöker hämta {url}")
                resp = requests.get(url, timeout=15, headers={
                    "User-Agent": "MX-Enduro-Kalender/1.0 (Stockholm training calendar)"
                })
                resp.raise_for_status()
                return resp.text
            except requests.RequestException as e:
                self.logger.warning(f"Misslyckades med {url}: {e}")
        return None

    def _parse_events(self, html: str) -> list[TrainingEvent]:
        """Parsa HTML och extrahera events."""
        soup = BeautifulSoup(html, "lxml")
        events = []

        # Strategi 1: Leta efter tabellrader (vanligt för kalenderdata)
        for table in soup.find_all("table"):
            events.extend(self._parse_table(table))

        # Strategi 2: Leta efter div-baserade eventlistor
        if not events:
            events.extend(self._parse_divs(soup))

        # Strategi 3: Leta efter listor (ul/ol)
        if not events:
            events.extend(self._parse_lists(soup))

        # Strategi 4: Generisk text-parsing som fallback
        if not events:
            events.extend(self._parse_text_blocks(soup))

        self.logger.info(f"Hittade {len(events)} events från RCMC")
        return events

    def _parse_table(self, table) -> list[TrainingEvent]:
        """Parsa en tabell med events."""
        events = []
        rows = table.find_all("tr")
        headers = []

        for row in rows:
            cells = row.find_all(["th", "td"])
            cell_texts = [c.get_text(strip=True) for c in cells]

            if row.find("th"):
                headers = [h.lower() for h in cell_texts]
                continue

            if len(cell_texts) < 2:
                continue

            event = self._row_to_event(cell_texts, headers)
            if event:
                events.append(event)

        return events

    def _row_to_event(self, cells: list[str], headers: list[str]) -> TrainingEvent | None:
        """Konvertera en tabellrad till ett TrainingEvent."""
        data = {}
        if headers:
            data = dict(zip(headers, cells))
        else:
            # Gissa kolumnordning: datum, tid, namn/beskrivning, plats
            if len(cells) >= 3:
                data = {"datum": cells[0], "tid": cells[1], "beskrivning": " ".join(cells[2:])}

        date_str = self._extract_date(data.get("datum", "") or data.get("date", "") or cells[0])
        if not date_str:
            return None

        title = data.get("beskrivning", "") or data.get("aktivitet", "") or data.get("event", "")
        club_id = self._match_club(title + " " + data.get("plats", ""))
        start_time, end_time = self._extract_times(data.get("tid", "") or data.get("time", ""))

        return TrainingEvent(
            club=self._get_club_name(club_id),
            club_id=club_id,
            title=title or "Träning",
            date=date_str,
            start_time=start_time,
            end_time=end_time,
            location=data.get("plats", None) or data.get("bana", None),
            description=data.get("info", None) or data.get("kommentar", None),
            discipline=self.classify_discipline(title),
            event_type=self.classify_event_type(title),
            url=URLS[0],
        )

    def _parse_divs(self, soup) -> list[TrainingEvent]:
        """Parsa div-baserade eventlistor."""
        events = []
        # Sök efter vanliga CSS-klasser för events
        for selector in [".event", ".calendar-event", ".activity", "[class*='event']",
                         "[class*='kalender']", "[class*='training']"]:
            for elem in soup.select(selector):
                event = self._element_to_event(elem)
                if event:
                    events.append(event)
        return events

    def _parse_lists(self, soup) -> list[TrainingEvent]:
        """Parsa ul/ol-listor med events."""
        events = []
        for li in soup.find_all("li"):
            text = li.get_text(strip=True)
            date_str = self._extract_date(text)
            if date_str and len(text) > 10:
                club_id = self._match_club(text)
                events.append(TrainingEvent(
                    club=self._get_club_name(club_id),
                    club_id=club_id,
                    title=self._clean_title(text),
                    date=date_str,
                    discipline=self.classify_discipline(text),
                    event_type=self.classify_event_type(text),
                    url=URLS[0],
                ))
        return events

    def _parse_text_blocks(self, soup) -> list[TrainingEvent]:
        """Sista utväg: parsa alla textblock som innehåller datum."""
        events = []
        for elem in soup.find_all(["p", "div", "span", "h2", "h3", "h4"]):
            text = elem.get_text(strip=True)
            if len(text) < 10 or len(text) > 500:
                continue
            date_str = self._extract_date(text)
            if date_str:
                club_id = self._match_club(text)
                events.append(TrainingEvent(
                    club=self._get_club_name(club_id),
                    club_id=club_id,
                    title=self._clean_title(text),
                    date=date_str,
                    discipline=self.classify_discipline(text),
                    event_type=self.classify_event_type(text),
                    url=URLS[0],
                ))
        return events

    def _element_to_event(self, elem) -> TrainingEvent | None:
        """Extrahera event från ett generiskt HTML-element."""
        text = elem.get_text(strip=True)
        date_str = self._extract_date(text)
        if not date_str:
            return None

        club_id = self._match_club(text)
        title_elem = elem.find(["h2", "h3", "h4", "strong", "b"])
        title = title_elem.get_text(strip=True) if title_elem else self._clean_title(text)

        time_text = text
        start_time, end_time = self._extract_times(time_text)

        return TrainingEvent(
            club=self._get_club_name(club_id),
            club_id=club_id,
            title=title,
            date=date_str,
            start_time=start_time,
            end_time=end_time,
            discipline=self.classify_discipline(text),
            event_type=self.classify_event_type(text),
            url=URLS[0],
        )

    def _extract_date(self, text: str) -> str | None:
        """Extrahera datum från text. Returnerar YYYY-MM-DD eller None."""
        # ISO-format: 2026-03-27
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if m:
            return m.group(0)

        # Svenskt format: 27 mars, 27/3, 27.3.2026
        months_sv = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "maj": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dec": 12,
        }

        # "27 mars 2026" eller "27 mars"
        m = re.search(r"(\d{1,2})\s+(jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)\w*\.?\s*(\d{4})?", text.lower())
        if m:
            day = int(m.group(1))
            month = months_sv[m.group(2)[:3]]
            year = int(m.group(3)) if m.group(3) else datetime.now().year
            try:
                return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                pass

        # "27/3-2026" eller "27/3"
        m = re.search(r"(\d{1,2})[/.](\d{1,2})(?:[-.](\d{2,4}))?", text)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3)) if m.group(3) else datetime.now().year
            if year < 100:
                year += 2000
            if 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except ValueError:
                    pass

        return None

    def _extract_times(self, text: str) -> tuple[str | None, str | None]:
        """Extrahera start- och sluttid från text."""
        # "09:00 - 15:00" eller "09:00-15:00" eller "kl 09-15"
        m = re.search(r"(\d{1,2})[:.:](\d{2})?\s*[-–]\s*(\d{1,2})[:.:](\d{2})?", text)
        if m:
            start_h = int(m.group(1))
            start_m = int(m.group(2) or 0)
            end_h = int(m.group(3))
            end_m = int(m.group(4) or 0)
            return f"{start_h:02d}:{start_m:02d}", f"{end_h:02d}:{end_m:02d}"
        return None, None

    def _match_club(self, text: str) -> str:
        """Matcha text mot en klubb. Returnerar club_id."""
        text_lower = text.lower()
        for keyword, club_id in RCMC_CLUB_MAP.items():
            if keyword in text_lower:
                return club_id
        return self.club_id  # Fallback till den klubb scrapern tillhör

    def _get_club_name(self, club_id: str) -> str:
        """Hämta klubbnamn från club_id."""
        from config import CLUBS
        if club_id in CLUBS:
            return CLUBS[club_id]["name"]
        return club_id

    def _clean_title(self, text: str) -> str:
        """Rensa titel från datum och onödig info."""
        # Ta bort datum-mönster
        cleaned = re.sub(r"\d{4}-\d{2}-\d{2}", "", text)
        cleaned = re.sub(r"\d{1,2}[/.]\d{1,2}(?:[-/.]\d{2,4})?", "", cleaned)
        cleaned = re.sub(r"\d{1,2}\s+(?:jan|feb|mar|apr|maj|jun|jul|aug|sep|okt|nov|dec)\w*", "", cleaned, flags=re.I)
        # Ta bort tider
        cleaned = re.sub(r"\d{1,2}:\d{2}\s*[-–]\s*\d{1,2}:\d{2}", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:100] if cleaned else "Träning"
