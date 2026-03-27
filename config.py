"""Konfiguration för MX/Enduro-kalendern."""

# Klubbar och deras datakällor
CLUBS = {
    "fmck_stockholm": {
        "name": "FMCK Stockholm",
        "source": "fmck_api",
        "api_url": "https://www.fmckstockholm.se/wp-json/tribe/events/v1/events",
        "location": {"lat": 59.48, "lng": 17.77},
        "location_name": "Kungsängen / Myttinge",
        "discipline": ["enduro"],
        "website": "https://www.fmckstockholm.se/endurogruppen/",
        "calendar_url": "https://www.fmckstockholm.se/aktiviteter/",
        "description": "Endurospår på Kungsängens övningsfält. Grönt/Blått/Orange spår. Myttinge på Värmdö ca 30 söndagar/år.",
        "booking_info": "Medlemskap krävs. Anmälan via kalendern.",
    },
    "botkyrka_mk": {
        "name": "Botkyrka MK",
        "source": "jevents",
        "location": {"lat": 59.20, "lng": 17.84},
        "location_name": "Tumba",
        "discipline": ["enduro", "mx"],
        "website": "https://www.botkyrkamk.se/",
        "calendar_url": "https://www.botkyrkamk.se/kalender",
        "description": "MX-bana + endurospår. Crossbanan: tis/tor 18-21, lör/sön 10-14. Enduro: se kalender.",
        "booking_info": "Inskrivning i klubbstugan. Medlem 100 kr, ej medlem 140 kr.",
    },
    "asatra_mk": {
        "name": "Åsätra MK",
        "source": "svenskalag",
        "svenskalag_slug": "asatramk",
        "location": {"lat": 59.52, "lng": 18.32},
        "location_name": "Åsätra, Åkersberga",
        "discipline": ["enduro"],
        "website": "https://www.svenskalag.se/asatramk",
        "calendar_url": "https://www.svenskalag.se/asatramk/kalender",
        "description": "Endurospår i Åkersberga. Tis/tor 17-20, lör 11-16 (säsong).",
        "booking_info": "Kolla kalendern för öppetdagar. Öppethållare krävs.",
    },
    "arlanda_mc": {
        "name": "Arlanda MC",
        "source": "bokamera",
        "location": {"lat": 59.62, "lng": 17.92},
        "location_name": "Märsta",
        "discipline": ["enduro"],
        "website": "https://www.arlandamc.se/",
        "calendar_url": "https://arlandamc.bokamera.se/",
        "description": "Endurospår nära Arlanda. Bokning via BokaMera.",
        "booking_info": "Boka träningstid via BokaMera-appen/hemsidan.",
    },
    "malaro_mck": {
        "name": "Mälarö MCK",
        "source": "klubbenonline",
        "location": {"lat": 59.33, "lng": 17.65},
        "location_name": "Ekerö",
        "discipline": ["enduro", "mx"],
        "website": "https://mmck.nu/",
        "calendar_url": "https://mmck.nu/kalender",
        "description": "MX-bana och endurospår på Ekerö. Lör-sön 11-15, sommar även tis/tor 18-21.",
        "booking_info": "Medlemskap krävs.",
    },
    "haninge_mk": {
        "name": "Haninge MK",
        "source": "website",
        "location": {"lat": 59.10, "lng": 18.15},
        "location_name": "Högsta, Österhaninge",
        "discipline": ["enduro", "mx"],
        "website": "https://www.haningemotorklubb.se/",
        "calendar_url": "https://www.haningemotorklubb.se/17/7/oppningsinfo/",
        "description": "MX-bana (1,7 km) + endurospår (orange/grönt). Ons 17:30-20:30, lör/sön 10-14 (apr-okt).",
        "booking_info": "Medlem 100 kr, ej medlem 140 kr. Kontantfri.",
    },
    "nynashamns_mck": {
        "name": "Nynäshamns MCK",
        "source": "mec",
        "location": {"lat": 58.90, "lng": 17.95},
        "location_name": "Eneby, Nynäshamn",
        "discipline": ["enduro", "mx"],
        "website": "https://nynashamnsmck.se/",
        "calendar_url": "https://nynashamnsmck.se/kalender/",
        "description": "Crossbana och endurospår i Eneby. Ons 17-20, lör/sön 10-14.",
        "booking_info": "Anmälan i klubbstugan. Miljömatta obligatorisk.",
    },
    "amf_sodertalje": {
        "name": "AMF Södertälje",
        "source": "wp_rss",
        "location": {"lat": 59.18, "lng": 17.62},
        "location_name": "Tuvägen, Södertälje",
        "discipline": ["enduro"],
        "website": "https://www.amf.nu/",
        "calendar_url": "https://www.amf.nu/oppettider/",
        "description": "Endurospår i Södertälje. Ungdomsträning tor 17:30-19.",
        "booking_info": "Se hemsidan för aktuella öppettider.",
    },
    "taby_mk": {
        "name": "Täby MK",
        "source": "gobraap",
        "location": {"lat": 59.47, "lng": 18.10},
        "location_name": "Arninge, Täby",
        "discipline": ["mx"],
        "website": "https://www.tabymk.se/",
        "calendar_url": "https://www.tabymk.se/",
        "description": "Sveriges äldsta MX-klubb (1937). Öppettider via GoBraap-appen.",
        "booking_info": "Ladda GoBraap-appen för aktuell status och bokning.",
        "gobraap_note": "Alla öppettider uppdateras i realtid via GoBraap.",
    },
    "balsta_ek": {
        "name": "Bålsta Enduroklubb",
        "source": "facebook",
        "location": {"lat": 59.57, "lng": 17.53},
        "location_name": "Bålsta",
        "discipline": ["enduro"],
        "website": "https://balstaenduroklubb.se/",
        "calendar_url": "https://www.facebook.com/groups/476644216326197/",
        "description": "Enduroklubb i Bålsta. Träningstider publiceras på Facebook.",
        "booking_info": "Kolla Facebook-gruppen för aktuella tider.",
    },
}

# Events som INTE ska inkluderas (folkrace, snöskoter, etc.)
EXCLUDED_KEYWORDS = [
    "folkrace", "folk race", "folkracing",
    "snöskoter", "skoter", "snowmobile",
    "bilsport", "rally", "gokart", "go-kart",
    "båt", "vattenskoter",
    "årsmöte", "arsmote",
    "styrelsemöte",
]

# Nyckelord som MÅSTE finnas (minst ett) för att ett event ska inkluderas
REQUIRED_KEYWORDS = [
    "enduro", "cross", "mx", "motocross",
    "träning", "training", "öppet", "oppet",
    "bana", "spår", "spar",
    "offroad", "off-road", "off road",
    "prova", "läger", "lager",
    "banläggning", "banlaggning",
    "arbetsdag",  # Arbetsdagar på MX/endurobanor är relevanta
]

# SMHI API för väderprognos
SMHI_FORECAST_URL = "https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{lng}/lat/{lat}/data.json"

# Output
OUTPUT_DIR = "output"
DATA_FILE = "data/events.json"
