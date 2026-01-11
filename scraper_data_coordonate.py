import atexit
import os
import random
import re
import time
import warnings
import datetime
from urllib.parse import quote_plus

import cv2
import pandas as pd
import undetected_chromedriver as uc
from paddleocr import PaddleOCR
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

warnings.filterwarnings("ignore", category=UserWarning)

# === INPUT ===
LOCATIONS = ["Galati"]

try:
    NUM_HOTELS = int(input("\U0001F522 Introdu numărul de căzări de procesat pentru fiecare locație: "))
except:
    NUM_HOTELS = 3

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
]

SCRAPER_API_KEY = ""

def build_booking_url(location: str) -> str:
    checkin = datetime.date.today() + datetime.timedelta(days=30)
    checkout = checkin + datetime.timedelta(days=1)
    base = "https://www.booking.com/searchresults.ro.html"
    location_encoded = quote_plus(location)
    return (
        f"{base}?ss={location_encoded}&ssne={location_encoded}&ssne_untouched={location_encoded}"
        f"&checkin={checkin}&checkout={checkout}"
        f"&group_adults=2&no_rooms=1&group_children=0&lang=en"
    )

def with_scraperapi(url):
    return f"http://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&country_code=us&url={quote_plus(url)}"

CATEGORY_ALIASES = {
    "staff": "Staff",
    "facilities": "Facilities",
    "cleanliness": "Cleanliness",
    "comfort": "Comfort",
    "value for money": "Value for money",
    "location": "Location",
    "wifi": "Free Wifi",
    "wi-fi": "Free Wifi",
    "free wifi": "Free Wifi",
    "free wi-fi": "Free Wifi"
}

def human_delay(a=2, b=4):
    time.sleep(random.uniform(a, b))

output_folder = "booking_scraper_output"
screenshots_folder = os.path.join(output_folder, "screenshots")
os.makedirs(screenshots_folder, exist_ok=True)

# === CHROME DRIVER ===
options = uc.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
options.add_argument("--disable-blink-features=AutomationControlled")
options.page_load_strategy = 'eager'
driver = uc.Chrome(options=options)
atexit.register(lambda: driver.quit())

# === PaddleOCR ===
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)

def close_cookies_popup():
    popup_selectors = [
        'button[aria-label="Respinge toate"]',
        '//button[contains(text(), "Refuz")]',
        '//button[contains(text(), "Decline")]',
        '//button[contains(text(), "Nu, mulțumesc")]'
    ]
    for sel in popup_selectors:
        try:
            btn = driver.find_element(By.XPATH, sel) if sel.startswith("//") else driver.find_element(By.CSS_SELECTOR, sel)
            btn.click()
            human_delay(1, 2)
            break
        except:
            continue

def process_rating_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    result = ocr.ocr(gray, cls=True)
    ratings = {}
    for line in result[0]:
        text = line[1][0]
        box = line[0]
        if any(char.isdigit() for char in text):
            try:
                score = float(text)
                category = find_category_for_score(result[0], box)
                if category:
                    norm = category.lower().strip()
                    for alias, canonical in CATEGORY_ALIASES.items():
                        if alias in norm:
                            ratings[canonical] = score
                            break
            except ValueError:
                pass
    return ratings

def find_category_for_score(all_boxes, score_box):
    score_x = min([pt[0] for pt in score_box])
    score_y = sum([score_box[0][1], score_box[3][1]]) / 2
    best_category = None
    min_distance = float('inf')
    for line in all_boxes:
        text = line[1][0]
        box = line[0]
        if not any(char.isdigit() for char in text):
            category_x = max([pt[0] for pt in box])
            category_y = sum([box[0][1], box[3][1]]) / 2
            if category_x < score_x:
                y_distance = abs(category_y - score_y)
                x_distance = score_x - category_x
                distance = y_distance * 3 + x_distance
                if distance < min_distance:
                    min_distance = distance
                    best_category = text
    return best_category

def process_accommodation(driver, link , LOCATION):

    result = {}
    try:
        driver.get(with_scraperapi(link))
        human_delay(4, 6)
        close_cookies_popup()
        name = driver.find_element(By.CSS_SELECTOR, 'h2.d2fee87262.pp-header__title').text
        address = "N/A"
        try:
            address_container = driver.find_element(By.CSS_SELECTOR, 'div.a53cbfa6de.f17adf7576')
            address_raw = address_container.text
            try:
                unwanted = driver.find_element(By.CSS_SELECTOR, 'div.ac52cd96ed').text
                address = address_raw.replace(unwanted, '').strip()
            except:
                address = address_raw.strip()
        except:
            pass
        try:
            review_box = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="review-score-right-component"]')
            general_score = review_box.find_element(By.CSS_SELECTOR, 'div.ac4a7896c7').text
            general_score = re.search(r"[\d.,]+", general_score).group() if re.search(r"[\d.,]+", general_score) else "N/A"
            rating_label = review_box.find_element(By.CSS_SELECTOR, 'div.e6208ee469.cb2cbb3ccb').text
            rating_label = rating_label.split('\n')[-1].strip()
            review_count = review_box.find_element(By.CSS_SELECTOR, 'div.abf093bdfe').text
            review_count = re.search(r"\d+", review_count).group() if re.search(r"\d+", review_count) else "N/A"
        except:
            general_score = "N/A"
            rating_label = "N/A"
            review_count = "0"
        try:
            stars_container = driver.find_element(By.CSS_SELECTOR, 'span[data-testid="rating-stars"]')
            stars = stars_container.find_elements(By.CSS_SELECTOR, 'span.fcd9eec8fb')
            numar_stele = len(stars)
        except:
            numar_stele = "0"

        try:
            prices_elements = driver.find_elements(By.CSS_SELECTOR, 'span.prco-valign-middle-helper')
            prices = []
            currency = ""
            for el in prices_elements:
                text = el.text.replace('\xa0', '').strip()
                match = re.search(r"([\d.,]+)", text)
                if match:
                    number = float(match.group(1).replace(',', '.'))
                    prices.append(number)
                    if not currency:
                        # Eliminăm valoarea numerică, păstrăm doar moneda (simbol sau cuvânt)
                        currency = re.sub(r"[\d.,]+", "", text).strip()
            min_price = min(prices) if prices else None
            max_price = max(prices) if prices else None
            average_price = round(sum(prices) / len(prices), 2) if prices else None
        except:
            min_price = max_price = average_price = None
            currency = ""

        latitudine = "N/A"
        longitudine = "N/A"
        try:
            map_wrapper = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="MapEntryPointDesktop-wrapper"]')
            latlng = map_wrapper.get_attribute("data-atlas-latlng")
            if latlng:
                latitudine, longitudine = latlng.split(",")
        except Exception as e:
            print(f"[Eroare coordonate]: {e}")

        result = {
            "Nume cazare": name,
            "Locatie": LOCATION,
            "Numar stele": numar_stele,
            "Adresa": address,
            "Latitudine": latitudine,
            "Longitudine": longitudine,
            "Scor general": general_score,
            "Calificativ": rating_label,
            "Nr. evaluări": review_count,
            "Pret minim": min_price,
            "Pret maxim": max_price,
            "Medie preturi": average_price,
            "Moneda": currency
        }
        review_section = driver.find_element(By.CLASS_NAME, "bui-spacer--larger")
        safe_name = re.sub(r'[^\w\-]', '_', name)[:40]
        random_suffix = str(random.randint(1000, 9999))
        screenshot_name = f"{safe_name}_{random_suffix}.png"
        screenshot_path = os.path.join(screenshots_folder, screenshot_name)
        driver.execute_script("arguments[0].scrollIntoView(true);", review_section)
        human_delay(1, 2)
        review_section.screenshot(screenshot_path)
        ocr_scores = process_rating_image(screenshot_path)
        for key in ["Staff", "Facilities", "Cleanliness", "Comfort", "Value for money", "Location", "Free Wifi"]:
            result[key] = ocr_scores.get(key)
    except Exception as e:
        print(f"[Eroare la cazare]: {e}")
    return result

existing_data = pd.DataFrame()
csv_path = os.path.join(output_folder, "booking_rezultate.csv")
if os.path.exists(csv_path):
    existing_data = pd.read_csv(csv_path)

results = []
for LOCATION in LOCATIONS:
    print(f"\n🌍 Locație: {LOCATION}")
    try:
        url = build_booking_url(LOCATION)
        driver.get(url)
        human_delay(5, 7)
        close_cookies_popup()
        accommodations = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="title-link"]')[:NUM_HOTELS]
        accommodation_links = [a.get_attribute("href") for a in accommodations]
        for idx, link in enumerate(accommodation_links):
            print(f"[{idx + 1}/{NUM_HOTELS}] ➔ {link}")
            result = process_accommodation(driver, link, LOCATION)
            if result:
                existing_data = existing_data[existing_data["Nume cazare"] != result["Nume cazare"]]
                results.append(result)
    except TimeoutException:
        print(f"⏱️ Timeout pentru locația: {LOCATION}. Trecem mai departe.")
        continue

if results:
    df_new = pd.DataFrame(results)
    df_all = pd.concat([existing_data, df_new], ignore_index=True)
    df_all.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ Gata! Datele au fost salvate în: {csv_path}")
else:
    print("\nℹ️ Nu au fost cazări noi sau actualizate.")
