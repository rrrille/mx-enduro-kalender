"""Huvudscript: kör scrapers, hämtar väder, genererar statisk sida."""

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader
from icalendar import Calendar, Event as ICalEvent

from config import CLUBS, SMHI_FORECAST_URL, OUTPUT_DIR, DATA_FILE
from scrapers.base import TrainingEvent
from scrapers.rcmc_scraper import RcmcScraper
from scrapers.fmck_scraper import FmckScraper
from scrapers.botkyrka_scraper import BotkyrkaScraper
from scrapers.nynashamn_scraper import NynashamnScraper
from scrapers.haninge_scraper import HaningeScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("main")


def run_scrapers() -> list[dict]:
    """Kör alla scrapers och samla events."""
    all_events = []

    # RCMC-scraper (aggregerar 7 klubbar)
    # Använd en av RCMC-klubbarna som bas
    rcmc_config = CLUBS["asatra_mk"]
    rcmc = RcmcScraper("asatra_mk", rcmc_config)
    try:
        events = rcmc.scrape()
        all_events.extend(e.to_dict() for e in events)
        logger.info(f"RCMC: {len(events)} events")
    except Exception as e:
        logger.error(f"RCMC scraper misslyckades: {e}")

    # FMCK Stockholm
    fmck_config = CLUBS["fmck_stockholm"]
    fmck = FmckScraper("fmck_stockholm", fmck_config)
    try:
        events = fmck.scrape()
        all_events.extend(e.to_dict() for e in events)
        logger.info(f"FMCK: {len(events)} events")
    except Exception as e:
        logger.error(f"FMCK scraper misslyckades: {e}")

    # Botkyrka MK
    try:
        scraper = BotkyrkaScraper("botkyrka_mk", CLUBS["botkyrka_mk"])
        events = scraper.scrape()
        all_events.extend(e.to_dict() for e in events)
        logger.info(f"Botkyrka: {len(events)} events")
    except Exception as e:
        logger.error(f"Botkyrka scraper misslyckades: {e}")

    # Nynäshamns MCK
    try:
        scraper = NynashamnScraper("nynashamns_mck", CLUBS["nynashamns_mck"])
        events = scraper.scrape()
        all_events.extend(e.to_dict() for e in events)
        logger.info(f"Nynäshamn: {len(events)} events")
    except Exception as e:
        logger.error(f"Nynäshamn scraper misslyckades: {e}")

    # Haninge MK
    try:
        scraper = HaningeScraper("haninge_mk", CLUBS["haninge_mk"])
        events = scraper.scrape()
        all_events.extend(e.to_dict() for e in events)
        logger.info(f"Haninge: {len(events)} events")
    except Exception as e:
        logger.error(f"Haninge scraper misslyckades: {e}")

    return all_events


def fetch_weather(lat: float, lng: float) -> dict | None:
    """Hämta SMHI-prognos för en koordinat."""
    url = SMHI_FORECAST_URL.format(lat=lat, lng=lng)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        forecasts = {}
        for ts in data.get("timeSeries", []):
            dt = ts["validTime"][:10]
            hour = int(ts["validTime"][11:13])
            if hour != 12:  # Ta 12:00-prognosen per dag
                continue
            params = {p["name"]: p["values"][0] for p in ts["parameters"]}
            forecasts[dt] = {
                "temp": params.get("t"),
                "wind": params.get("ws"),
                "symbol": params.get("Wsymb2"),
                "precip": params.get("pmean"),
            }
        return forecasts
    except Exception as e:
        logger.warning(f"Kunde inte hämta väder: {e}")
        return None


def get_weather_icon(symbol: int | None) -> str:
    """Returnera emoji baserat på SMHI-symbolkod."""
    if symbol is None:
        return ""
    icons = {
        1: "\u2600\ufe0f", 2: "\u26c5", 3: "\u2601\ufe0f", 4: "\u2601\ufe0f",
        5: "\u2601\ufe0f", 6: "\u2601\ufe0f", 7: "\ud83c\udf2b\ufe0f",
        8: "\ud83c\udf27\ufe0f", 9: "\ud83c\udf27\ufe0f", 10: "\ud83c\udf27\ufe0f",
        11: "\u26c8\ufe0f", 12: "\ud83c\udf28\ufe0f", 13: "\ud83c\udf28\ufe0f",
        14: "\ud83c\udf28\ufe0f", 15: "\u2744\ufe0f", 16: "\u2744\ufe0f",
        17: "\u2744\ufe0f", 18: "\ud83c\udf27\ufe0f", 19: "\ud83c\udf27\ufe0f",
        20: "\ud83c\udf27\ufe0f", 21: "\u26c8\ufe0f", 22: "\ud83c\udf28\ufe0f",
        23: "\ud83c\udf28\ufe0f", 24: "\ud83c\udf28\ufe0f", 25: "\u2744\ufe0f",
        26: "\u2744\ufe0f", 27: "\u2744\ufe0f",
    }
    return icons.get(int(symbol), "\u2601\ufe0f")


def enrich_with_weather(events: list[dict]) -> list[dict]:
    """Lägg till väderdata för varje event."""
    # Hämta väder för Stockholm-centralt
    weather = fetch_weather(59.33, 18.07)
    if not weather:
        return events

    for event in events:
        date = event.get("date", "")
        if date in weather:
            w = weather[date]
            event["weather"] = {
                "temp": w["temp"],
                "wind": w["wind"],
                "icon": get_weather_icon(w["symbol"]),
                "precip": w["precip"],
            }
    return events


def generate_ical(events: list[dict]) -> str:
    """Generera iCal-fil från events."""
    cal = Calendar()
    cal.add("prodid", "-//MX Enduro Kalender Stockholm//SE")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "MX/Enduro Träning Stockholm")

    for ev in events:
        ical_event = ICalEvent()
        ical_event.add("summary", f"{ev['club']}: {ev['title']}")
        try:
            dt = datetime.strptime(ev["date"], "%Y-%m-%d")
            if ev.get("start_time"):
                h, m = map(int, ev["start_time"].split(":"))
                dt = dt.replace(hour=h, minute=m)
            ical_event.add("dtstart", dt)

            if ev.get("end_time"):
                h, m = map(int, ev["end_time"].split(":"))
                end_dt = dt.replace(hour=h, minute=m)
                ical_event.add("dtend", end_dt)
        except (ValueError, TypeError):
            continue

        if ev.get("location"):
            ical_event.add("location", ev["location"])
        if ev.get("description"):
            ical_event.add("description", ev["description"])
        if ev.get("url"):
            ical_event.add("url", ev["url"])

        ical_event.add("uid", f"{ev['club_id']}-{ev['date']}-{hash(ev['title'])}@mx-enduro-kalender")
        cal.add_component(ical_event)

    return cal.to_ical().decode("utf-8")


def generate_html(events: list[dict]):
    """Generera statisk HTML-sida."""
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("index.html")

    # Sortera efter datum
    events.sort(key=lambda e: e.get("date", ""))

    # Gruppera per datum
    events_by_date = {}
    for ev in events:
        date = ev.get("date", "okänt")
        events_by_date.setdefault(date, []).append(ev)

    # Unika klubbar och discipliner för filter
    clubs = sorted(set(ev["club"] for ev in events))
    disciplines = sorted(set(ev.get("discipline", "enduro") for ev in events))

    html = template.render(
        events=events,
        events_by_date=events_by_date,
        clubs=clubs,
        club_configs=CLUBS,
        disciplines=disciplines,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        total_events=len(events),
    )

    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    logger.info(f"HTML genererad: {output_dir / 'index.html'}")


def save_data(events: list[dict]):
    """Spara event-data som JSON."""
    data_dir = Path(DATA_FILE).parent
    data_dir.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    logger.info(f"Data sparad: {DATA_FILE}")


def main():
    logger.info("=== MX/Enduro Kalender - Startar ===")

    # 1. Skrapa events
    events = run_scrapers()
    logger.info(f"Totalt {len(events)} events skrapade")

    # 1b. Dedup: ta bort dubbletter baserat på klubb+datum+titel
    seen = set()
    unique_events = []
    for ev in events:
        key = (ev["club_id"], ev["date"], ev["title"][:50])
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)
    logger.info(f"Efter dedup: {len(unique_events)} unika events (tog bort {len(events) - len(unique_events)} dubbletter)")
    events = unique_events

    # Filtrera bort gamla events (före idag)
    today = datetime.now().strftime("%Y-%m-%d")
    events = [e for e in events if e.get("date", "") >= today]
    logger.info(f"Efter datumfilter: {len(events)} kommande events")

    # 2. Berika med väder
    events = enrich_with_weather(events)

    # 3. Spara data
    save_data(events)

    # 4. Generera iCal
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)
    ical_content = generate_ical(events)
    (output_dir / "calendar.ics").write_text(ical_content, encoding="utf-8")
    logger.info("iCal genererad")

    # 5. Generera HTML
    generate_html(events)

    # 6. Kopiera statiska filer
    static_src = Path("static")
    if static_src.exists():
        import shutil
        static_dst = output_dir / "static"
        if static_dst.exists():
            shutil.rmtree(static_dst)
        shutil.copytree(static_src, static_dst)

    logger.info("=== Klar! ===")


if __name__ == "__main__":
    main()
