import os
import json
from time import sleep
from collections.abc import Iterable

import dotenv
import yagmail

import sssb
from sssb import Listing


dotenv.load_dotenv()
SENDER = os.getenv("SENDER")
APP_PASSWORD = os.getenv("APP_PASSWORD")
RECIPIENT = os.getenv("RECIPIENT")

TRACKING_FILE = "listings.json"
SLEEP_TIME_AFTER_EMAIL = 5


def is_relevant(listing: Listing) -> bool:
    if "korridor" in listing.apartment_type.lower():
        return False
    if listing.square_meters <= 25:
        return False
    if not "1 rum" in listing.apartment_type.lower():
        return False
    return True


def notify(subject: str, contents: str) -> None:    
    with yagmail.SMTP(user=SENDER, password=APP_PASSWORD) as yag:
        yag.send(to=RECIPIENT, subject=subject, contents=contents)
    sleep(SLEEP_TIME_AFTER_EMAIL)


def load_previous_listings() -> list[Listing]:
    try:
        with open(TRACKING_FILE) as file:
            serializable_listings = json.load(file)
            listings = [Listing(**listing)
                        for listing in serializable_listings]
    except Exception:
        listings = []
    return listings


def save_listings(listings: Iterable[Listing]) -> None:
    serializable_listings = [listing.asdict()
                             for listing in listings]
    with open(TRACKING_FILE, "w") as file:
        json.dump(serializable_listings, file, indent=4)


def send_notification(listing: Listing) -> None:
    subject = f"[{listing.apartment_number}] {listing.apartment_type} @ {listing.adress}"
    contents = f"""
        Typ: {listing.apartment_type}
        Adress: {listing.adress}
        Lägenhets nr: {listing.apartment_number}
        Område: {listing.region}
        Våning: {listing.floor}
        Yta: {listing.square_meters} m²
        Hyra: {listing.rent} kr
        Inflytt: {listing.move_in_date}
        URL: {listing.url}
        """.replace("   ", "").strip()
    notify(subject, contents)

        
def main() -> None:
    try:
        current_listings = sssb.current_listings()
        previous_listings = load_previous_listings()

        all_listings = set(current_listings) | set(previous_listings)
        
        new_listings = set(current_listings) - set(previous_listings)
        relevant_listings = [listing
                        for listing in new_listings
                        if is_relevant(listing)]
        print(f"Found {len(relevant_listings)} new relevant listings")

        for listing in relevant_listings:
            send_notification(listing)
            print(f" - {listing.apartment_type} @ {listing.adress}")

        save_listings(all_listings)
    
    except Exception as e:
        subject = "SSSB Notification ran into an error"
        contents = f"{type(e).__name__}: {e}"
        notify(subject, contents)


if __name__ == "__main__":
    main()
    