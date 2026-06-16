import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

TIMEZONE = ZoneInfo("Europe/Bucharest")
BASE_DOMAIN = "https://sportinclujnapoca.ro"

SPORT_SLUGS = {
    "Fotbal": "football",
    "Tenis de masa": "table-tennis",
    "Baschet": "basketball",
    "Tenis": "tennis",
    "Tenis cu peretele": "wall-tennis",
    "Squash": "squash",
    "Volei": "volleyball",
}

FIELD_SLUGS = {
    "Fotbal": "Fotbal",
    "Tenis de masa": "Tenis masa",
    "Baschet": "Baschet",
    "Tenis": "Tenis",
    "Tenis cu peretele": "Tenis perete",
    "Squash": "Squash",
    "Volei": "Volei",
    "Oricare": "Oricare",
}

COMPLEX_SLUGS = {
    "Baza Sportivă Gheorgheni": "gheorgheni-base",
    "Baza Sportivă „La Terenuri“": "la-terenuri-base",
}

ALLOWED_SPORT_NAMES = set(SPORT_SLUGS.keys())
ALLOWED_SPORTS_COMPLEXES = set(COMPLEX_SLUGS.keys())

MAX_MINUTES = int(os.environ.get("MAX_MINUTES", 15))
SPORT_NAME = os.environ.get("SPORT_NAME", "Fotbal")
FIELD_NAME = os.environ.get("FIELD_NAME", "Oricare")
SPORTS_COMPLEX = os.environ.get("SPORTS_COMPLEX", "Baza Sportivă „La Terenuri“")

TARGET_URL = f"{BASE_DOMAIN}/reservations/{SPORT_SLUGS.get(SPORT_NAME, 'football')}?preferredSportComplex={COMPLEX_SLUGS.get(SPORTS_COMPLEX, 'la-terenuri-base')}"


@dataclass
class Account:
    email: str
    password: str


def get_accounts() -> tuple[Account, list[Account]]:
    main_email = os.environ.get("MAIN_ACCOUNT_EMAIL")
    main_pass = os.environ.get("MAIN_ACCOUNT_PASSWORD")

    if not main_email or not main_pass:
        raise ValueError(
            "CRITICAL: MAIN_ACCOUNT_EMAIL or PASSWORD not set in environment."
        )

    main_acc = Account(email=main_email, password=main_pass)
    others = []
    for i in range(1, 4):
        email = os.environ.get(f"OTHER_ACCOUNT_{i}_EMAIL")
        pw = os.environ.get(f"OTHER_ACCOUNT_{i}_PASSWORD")
        if email and pw:
            others.append(Account(email=email, password=pw))

    return main_acc, others


def validate_config():
    if SPORT_NAME not in ALLOWED_SPORT_NAMES:
        raise ValueError(f"Invalid SPORT_NAME: '{SPORT_NAME}'.")
    if SPORTS_COMPLEX not in ALLOWED_SPORTS_COMPLEXES:
        raise ValueError(f"Invalid SPORTS_COMPLEX: '{SPORTS_COMPLEX}'.")
    if not any(FIELD_NAME.startswith(val) for val in FIELD_SLUGS.values()):
        raise ValueError(f"Invalid FIELD_NAME: '{FIELD_NAME}'.")


MAIN_ACCOUNT, OTHER_ACCOUNTS = get_accounts()
