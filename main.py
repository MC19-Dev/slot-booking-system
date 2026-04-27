import os
import random
import time
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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

COMPLEX_SLUGS = {
    "Baza Sportivă Gheorgheni": "gheorgheni-base",
    "Baza Sportivă „La Terenuri“": "la-terenuri-base",
}

ALLOWED_SPORT_NAMES = set(SPORT_SLUGS.keys())
ALLOWED_SPORTS_COMPLEXES = set(COMPLEX_SLUGS.keys())

SPORT_NAME = os.environ.get("SPORT_NAME", "Fotbal")
FIELD_NAME = os.environ.get("FIELD_NAME", f"{SPORT_NAME} 2")
SPORTS_COMPLEX = os.environ.get("SPORTS_COMPLEX", "Baza Sportivă „La Terenuri“")

TARGET_URL = f"{BASE_DOMAIN}/reservations/{SPORT_SLUGS.get(SPORT_NAME, 'football')}?preferredSportComplex={COMPLEX_SLUGS.get(SPORTS_COMPLEX, 'la-terenuri-base')}"

@dataclass
class Account:
    email: str
    password: str

def get_accounts() -> tuple[Account, List[Account]]:
    main_email = os.environ.get("MAIN_ACCOUNT_EMAIL")
    main_pass = os.environ.get("MAIN_ACCOUNT_PASSWORD")
    
    if not main_email or not main_pass:
        raise ValueError("CRITICAL: MAIN_ACCOUNT_EMAIL or PASSWORD not set in environment.")
    
    main_acc = Account(email=main_email, password=main_pass)
    
    others = []
    for i in range(1, 4):
        email = os.environ.get(f"OTHER_ACCOUNT_{i}_EMAIL")
        pw = os.environ.get(f"OTHER_ACCOUNT_{i}_PASSWORD")
        if email and pw:
            others.append(Account(email=email, password=pw))
            
    return main_acc, others

MAIN_ACCOUNT, OTHER_ACCOUNTS = get_accounts()


def build_driver() -> webdriver.Firefox:

    is_github = os.environ.get("GITHUB_ACTIONS") == "true"

    if is_github:
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        options = FirefoxOptions()
        options.add_argument("--headless")
        options.set_preference("dom.webdriver.enabled", False)
        return webdriver.Firefox(options=options)
    
    else:
        from selenium.webdriver.chrome.options import Options
        options = webdriver.ChromeOptions()
    
        options.add_argument("--headless=new") 
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")

        options.add_argument("--window-size=1920,1080")

        return webdriver.Chrome(options=options)


def wait_for_release_time(target_hour: int):
    """
    Pauses the script until 1 second before the target_hour.
    If we want a 16:00 slot, we wait until 15:59:59.
    """
    print(f"[TIMER] Target release: {target_hour}:00:00. Waiting...")
    
    while True:
        now = datetime.now(TIMEZONE)
        
        if now.hour == (target_hour - 1) and now.minute == 59 and now.second >= 59:
            print(f"[FIRE] {now.strftime('%H:%M:%S')} reached. Pouncing!")
            break
            
        if now.hour >= target_hour:
            print("[INFO] Slot should already be released. Proceeding immediately.")
            break

        if now.minute == 59 and now.second > 50:
            time.sleep(0.3)
        else:
            time.sleep(2)


def get_now():
    """Mockable current datetime for testing purposes."""
    return datetime(2026, 4, 27, 14, 55, tzinfo=TIMEZONE)


def get_target_reservation_datetime(now=None):
    if now is None:
        now = datetime.now(TIMEZONE)

    if now.minute < 10:
        base_hour = now.replace(minute=0, second=0, microsecond=0)
    else:
        base_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
    return base_hour + timedelta(days=14)


def get_week_clicks_needed(now=None):
    if now is None:
        now = datetime.now(TIMEZONE)

    target_dt = get_target_reservation_datetime(now)
    delta_days = (target_dt.date() - now.date()).days
    return delta_days // 7


def wait_click(driver, by, value, timeout=10):
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    element.click()
    return element


def wait_js_click(driver, by, value, timeout=10):
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )
    driver.execute_script("arguments[0].click();", element)
    return element


def wait_type(driver, by, value, text, timeout=10, clear=True):
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    if clear:
        element.clear()
    element.send_keys(text)
    return element


def safe_click_if_present(driver, by, value, timeout=3) -> bool:
    try:
        wait_click(driver, by, value, timeout)
        return True
    except TimeoutException:
        return False


def validate_config():
    if SPORT_NAME not in ALLOWED_SPORT_NAMES:
        raise ValueError(f"Invalid SPORT_NAME: '{SPORT_NAME}'.")

    if SPORTS_COMPLEX not in ALLOWED_SPORTS_COMPLEXES:
        raise ValueError(f"Invalid SPORTS_COMPLEX: '{SPORTS_COMPLEX}'.")


def accept_cookies_if_present(driver):
    safe_click_if_present(driver, By.ID, "rcc-confirm-button", timeout=3)


def click_login_if_present(driver):
    safe_click_if_present(driver, By.CSS_SELECTOR, 'a[href="/login"]', timeout=5)


def login(driver, account: Account):
    wait_type(driver, By.ID, "email-input", account.email, timeout=10)
    password_input = wait_type(driver, By.NAME, "password", account.password, timeout=10)
    password_input.send_keys(Keys.RETURN)
    safe_click_if_present(driver, By.XPATH, '//button[@type="submit"]', timeout=5)


def click_reserve_now_if_present(driver):
    safe_click_if_present(driver, By.CSS_SELECTOR, 'a[href="/reservations"]', timeout=3)


def select_sport(driver, sport_name: str):
    sport_link_xpath = f'//a[.//img[@alt="{sport_name}"]]'
    sport_img_xpath = f'//img[@alt="{sport_name}"]'

    try:
        wait_click(driver, By.XPATH, sport_link_xpath, timeout=5)
    except TimeoutException:
        img = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, sport_img_xpath))
        )
        parent = img.find_element(By.XPATH, "./ancestor::div")
        driver.execute_script("arguments[0].click();", parent)


def select_sports_complex(driver, option_text: str):
    print(f"[INFO] Selecting sports complex: {option_text}...")
    try:
        wait_click(driver, By.ID, "mui-component-select-sportsComplexSlug", timeout=10)
        wait_click(driver, By.XPATH, f'//li[normalize-space()="{option_text}"]', timeout=10)
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Complex selection failed: {e}")


def select_sport_field(driver, field_name: str):
    print(f"[INFO] Selecting field: {field_name}...")
    try:
        wait_click(driver, By.ID, "mui-component-select-courtId", timeout=10)
        wait_click(driver, By.XPATH, f'//li[normalize-space()="{field_name}"]', timeout=10)
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Field selection failed: {e}")
        driver.save_screenshot("field_selection_debug.png")
        raise e


def click_arrow_forward(driver, times=1, timeout=10):
    wait = WebDriverWait(driver, timeout)

    for _ in range(times):
        btn = wait.until(
            EC.element_to_be_clickable((
                By.XPATH,
                '(//button[.//*[name()="svg" and @data-testid="ArrowForwardIcon"]])[last()]'
            ))
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.4)


def select_day(driver, day: int):
    target_xpath = (
        f"//button[not(@disabled) and not(@aria-disabled='true')]"
        f"//h6[contains(text(), '{day}')]"
    )
    
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, target_xpath))
        )
        
        time.sleep(random.uniform(0.3, 0.6)) 
        
        driver.execute_script("arguments[0].click();", btn)
        print(f"[DEBUG] Successfully clicked day {day}")
    except TimeoutException:
        driver.save_screenshot("calendar_not_found.png")
        raise TimeoutException(f"Could not find or click day {day}. Check calendar_not_found.png")


def try_select_time(driver, time_text: str, timeout=1) -> bool:
    try:
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((
                By.XPATH,
                f'//div[@role="button"][.//span[normalize-space()="{time_text}"]]'
            ))
        )
        time.sleep(random.uniform(0.15, 0.35))
        driver.execute_script("arguments[0].click();", btn)
        return True
    except TimeoutException:
        return False


def click_reserve_button(driver):
    print("[INFO] Clicking the 'Rezervă' button...")
    btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH, 
            '//button[@type="submit" and (normalize-space()="Rezervă" or contains(., "Rezervă"))]'
        ))
    )
    driver.execute_script("arguments[0].click();", btn)

def click_confirm_reservation(driver):
    print("[INFO] Clicking the 'Confirmă rezervarea' button...")
    btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((
            By.XPATH, 
            '//button[normalize-space()="Confirmă rezervarea"]'
        ))
    )
    driver.execute_script("arguments[0].click();", btn)

def check_all_visible_checkboxes(driver, timeout=10):
    print("[INFO] Checking all policy checkboxes...")
    checkboxes = WebDriverWait(driver, timeout).until(
        EC.presence_of_all_elements_located(
            (By.XPATH, '//input[@type="checkbox" and not(@disabled)]')
        )
    )
    for checkbox in checkboxes:
        if not checkbox.is_selected():
            driver.execute_script("arguments[0].click();", checkbox)


def get_confirmation_link(driver, timeout=10) -> str:
    element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((
            By.XPATH,
            '//a[contains(@href,"/reservations/confirm")]'
        ))
    )
    return element.get_attribute("href")


def open_reservation_page_and_prepare(driver, week_clicks: int):
    driver.get(TARGET_URL)
    accept_cookies_if_present(driver)
    click_reserve_now_if_present(driver)
    select_sport(driver, SPORT_NAME)
    select_sports_complex(driver, SPORTS_COMPLEX)
    select_sport_field(driver, FIELD_NAME)
    driver.execute_script("window.scrollBy(0, 400);")
    click_arrow_forward(driver, times=week_clicks)
    time.sleep(1)


def wait_for_slot_and_select(driver: webdriver.Firefox | webdriver.Chrome, day: int, time_text: str, week_clicks: int, max_minutes=10, retry_delay=2) -> bool:
    deadline = time.time() + max_minutes * 60
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        print(f"[INFO] Attempt {attempt}: checking day {day}, time {time_text}...")

        try:
            select_day(driver, day)

            if try_select_time(driver, time_text, timeout=0.8):
                print(f"[INFO] Slot found: day {day}, time {time_text}")
                driver.save_screenshot(f"found_slot_{day}_{time_text}.png")
                return True
            
            if attempt % 8 == 0:
                print("[INFO] Periodic hard refresh to keep session alive...")
                driver.refresh()
                open_reservation_page_and_prepare(driver, week_clicks)
            else:
                print("[INFO] Toggling Field to force update...")
                other_field = f"{SPORT_NAME} 1" if FIELD_NAME == f"{SPORT_NAME} 2" else f"{SPORT_NAME} 2"
                select_sport_field(driver, other_field)
                wait_time = random.uniform(1, 3)
                time.sleep(wait_time)

        except Exception as e:
            print(f"[WARN] Attempt {attempt} failed: {e}")
            open_reservation_page_and_prepare(driver, week_clicks)
            time.sleep(retry_delay)

    print(f"[ERROR] Slot was not found within {max_minutes} minutes.")
    return False


def create_reservation(driver) -> str:
    # now = get_now()
    target_dt = get_target_reservation_datetime()
    # target_dt = get_target_reservation_datetime(now=now)
    target_day = target_dt.day
    target_time = target_dt.strftime("%H:%M")
    week_clicks = get_week_clicks_needed()
    # week_clicks = get_week_clicks_needed(now=now)


    print(f"[INFO] Target reservation datetime: {target_dt}")
    print(f"[INFO] Target day: {target_day}")
    print(f"[INFO] Target time: {target_time}")
    print(f"[INFO] Calendar week clicks: {week_clicks}")

    driver.get(TARGET_URL)
    accept_cookies_if_present(driver)
    click_login_if_present(driver)
    login(driver, MAIN_ACCOUNT)

    print("[INFO] Preparing calendar and navigating to the target week...")
    open_reservation_page_and_prepare(driver, week_clicks)

    wait_for_release_time(target_dt.hour)

    slot_found = wait_for_slot_and_select(
        driver=driver,
        day=target_day,
        time_text=target_time,
        week_clicks=week_clicks,
        max_minutes=10,
        retry_delay=2
    )

    if not slot_found:
        raise RuntimeError(f"Could not find slot for day {target_day} at {target_time} within 10 minutes.")

    click_reserve_button(driver)
    check_all_visible_checkboxes(driver)
    click_confirm_reservation(driver)

    return get_confirmation_link(driver)


def login_and_return_to_url(driver, account: Account, target_url: str):
    driver.get(target_url)
    accept_cookies_if_present(driver)
    click_login_if_present(driver)
    login(driver, account)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    driver.get(target_url)


def confirm_from_shared_link(driver, account: Account, confirmation_link: str):
    login_and_return_to_url(driver, account, confirmation_link)
    check_all_visible_checkboxes(driver)
    click_confirm_reservation(driver)


def main():
    validate_config()

    driver = build_driver()
    confirmation_link: Optional[str] = None

    try:
        confirmation_link = create_reservation(driver)
        print(f"[SUCCESS] Slot secured! Link: {confirmation_link}")
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to create reservation: {e}")
        driver.save_screenshot("main_error.png")
        return
    finally:
        driver.quit()

    if not confirmation_link:
        print("[ERROR] No confirmation link found. Exiting.")
        return

    print(f"Starting confirmations for {len(OTHER_ACCOUNTS)} secondary accounts...")
    
    for i, account in enumerate(OTHER_ACCOUNTS):
        if i > 0:
            delay = random.randint(30, 90)
            print(f"Waiting {delay}s before next account...")
            time.sleep(delay)

        driver = build_driver()
        try:
            confirm_from_shared_link(driver, account, confirmation_link)
            print(f"[SUCCESS] Account {account.email} confirmed.")
        except Exception as e:
            print(f"[WARNING] Account {account.email} failed: {e}")
            driver.save_screenshot(f"error_{account.email}.png")
        finally:
            driver.quit()

    print("Automation process finished.")


if __name__ == "__main__":
    main()
