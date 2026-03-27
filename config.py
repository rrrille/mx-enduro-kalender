"""Konfiguration för MX/Enduro-kalendern."""

# Klubbar och deras datakällor
CLUBS = {
    "asatra_mk": {
        "name": "Åsätra MK",
        "source": "rcmc",
        "location": {"lat": 59.48, "lng": 17.85},
        "discipline": ["enduro"],
    },
    "arlanda_mc": {
        "name": "Arlanda MC",
        "source": "rcmc",
        "location": {"lat": 59.62, "lng": 17.92},
        "discipline": ["enduro"],
    },
    "malaro_mck": {
        "name": "Mälarö MCK",
        "source": "rcmc",
        "location": {"lat": 59.33, "lng": 17.65},
        "discipline": ["enduro", "mx"],
    },
    "botkyrka_mk": {
        "name": "Botkyrka MK",
        "source": "rcmc",
        "location": {"lat": 59.20, "lng": 17.84},
        "discipline": ["enduro", "mx"],
    },
    "haninge_mk": {
        "name": "Haninge MK",
        "source": "rcmc",
        "location": {"lat": 59.10, "lng": 18.15},
        "discipline": ["enduro", "mx"],
    },
    "nynashamns_mck": {
        "name": "Nynäshamns MCK",
        "source": "rcmc",
        "location": {"lat": 58.90, "lng": 17.95},
        "discipline": ["enduro"],
    },
    "amf_sodertalje": {
        "name": "AMF Södertälje",
        "source": "rcmc",
        "location": {"lat": 59.18, "lng": 17.62},
        "discipline": ["enduro"],
    },
    "fmck_stockholm": {
        "name": "FMCK Stockholm",
        "source": "fmck_api",
        "api_url": "https://www.fmckstockholm.se/wp-json/tribe/events/v1/events",
        "location": {"lat": 59.48, "lng": 17.77},
        "discipline": ["enduro"],
    },
    "balsta_ek": {
        "name": "Bålsta Enduroklubb",
        "source": "manual",
        "website": "https://balstaenduroklubb.se",
        "location": {"lat": 59.57, "lng": 17.53},
        "discipline": ["enduro"],
    },
    "taby_mk": {
        "name": "Täby MK",
        "source": "gobraap",
        "website": "https://www.tabymk.se",
        "location": {"lat": 59.47, "lng": 18.10},
        "discipline": ["mx", "enduro"],
    },
}

# SMHI API för väderprognos
SMHI_FORECAST_URL = "https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{lng}/lat/{lat}/data.json"

# Output
OUTPUT_DIR = "output"
DATA_FILE = "data/events.json"
