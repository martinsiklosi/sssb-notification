from time import sleep
from contextlib import contextmanager
from dataclasses import dataclass, asdict

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


URL = "https://sssb.se/soka-bostad/sok-ledigt/lediga-bostader/?pagination=0&paginationantal=0"


@contextmanager
def chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=chrome_options)
    try:
        yield driver
    finally:
        driver.quit()


def get_html(url: str, load_time_seconds: int = 5) -> str:
    with chrome_driver() as driver:
        driver.get(url)
        sleep(load_time_seconds)
        return driver.page_source
    

@dataclass(frozen=True)
class Listing:
    url: str
    apartment_type: str
    adress: str
    apartment_number: str
    region: str
    floor: int
    square_meters: int
    rent: int
    move_in_date: str
    
    def asdict(self) -> dict:
        return asdict(self)
    

def extract_int(text: str) -> int:
    digits = "".join(character 
                for character in text
                if character.isdigit())
    digits = "0" + digits # 0 if text does not contain any digits
    return int(digits)

def parse_raw_listing(raw_listing: BeautifulSoup) -> Listing:
    # URL and apartment type
    title_element = raw_listing.find(attrs={"class": "ObjektTyp"})
    url = title_element.find(href=True).get("href", "")
    apartment_type = title_element.text.strip()
    
    # Adress
    adress, apartment_number = raw_listing.find(attrs={"class": "ObjektAdress"}).text.split("/")
    adress = adress.strip()
    apartment_number = apartment_number.strip()
    
    # Region
    region = raw_listing.find("dd", attrs={"class": "ObjektOmrade"}).text.strip()
    
    # Floor
    floor_text = raw_listing.find("dd", attrs={"class": "ObjektVaning hidden-phone"}).text.strip()
    floor = extract_int(floor_text)
    
    # Square meters
    square_meters_text = raw_listing.find("dd", attrs={"class": "ObjektYta"}).text.strip()
    square_meters_text = square_meters_text.replace("²", "") # Fucks up the int extraction
    square_meters = extract_int(square_meters_text)
    
    # Rent
    rent_text = raw_listing.find("dd", attrs={"class": "ObjektHyra"}).text.replace(u"\xa0", u" ").strip()
    rent = extract_int(rent_text)
    
    # Move in date
    move_in_date = raw_listing.find("dd", attrs={"class": "ObjektInflytt hidden-phone"}).text.strip()
    
    return Listing(
        url=url,
        apartment_type=apartment_type,
        adress=adress,
        apartment_number=apartment_number,
        region=region,
        floor=floor,
        square_meters=square_meters,
        rent=rent,
        move_in_date=move_in_date,
    )


def current_listings() -> list[Listing]:
    html = get_html(URL)
    soup = BeautifulSoup(html, features="lxml")
    raw_listings = soup.find_all(attrs={"class": "Box ObjektListItem"})
    return [parse_raw_listing(raw_listing)
            for raw_listing in raw_listings]