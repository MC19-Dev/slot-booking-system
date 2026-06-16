import random
import time
from typing import Any
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import config
from driver import save_and_upload_screenshot


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


def accept_cookies_if_present(driver):
    safe_click_if_present(driver, By.ID, "rcc-confirm-button", timeout=3)


def click_login_if_present(driver):
    safe_click_if_present(driver, By.CSS_SELECTOR, 'a[href="/login"]', timeout=5)


def login(driver, account: config.Account):
    wait_type(driver, By.ID, "email-input", account.email, timeout=10)
    password_input = wait_type(
        driver, By.NAME, "password", account.password, timeout=10
    )
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
        wait_click(
            driver, By.XPATH, f'//li[normalize-space()="{option_text}"]', timeout=10
        )
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Complex selection failed: {e}")


def select_sport_field(driver, field_name: str):
    print(f"[INFO] Selecting field: {field_name}...")
    try:
        wait_click(driver, By.ID, "mui-component-select-courtId", timeout=10)
        wait_click(
            driver, By.XPATH, f'//li[normalize-space()="{field_name}"]', timeout=10
        )
        time.sleep(1)
    except Exception as e:
        print(f"[WARN] Field selection failed: {e}")
        save_and_upload_screenshot(driver, "field_selection_debug.png")
        raise e


def click_arrow_forward(driver, times=1, timeout=10):
    wait = WebDriverWait(driver, timeout)
    for _ in range(times):
        btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    '(//button[.//*[name()="svg" and @data-testid="ArrowForwardIcon"]])[last()]',
                )
            )
        )
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.4)


def select_day(driver, day: int):
    target_xpath = f"//button[not(@disabled) and not(@aria-disabled='true')]//h6[normalize-space()='{day}']"
    try:
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, target_xpath))
        )
        time.sleep(random.uniform(0.2, 0.4))
        driver.execute_script("arguments[0].click();", btn)
        print(f"[DEBUG] Successfully clicked day {day}")
    except TimeoutException:
        save_and_upload_screenshot(driver, "calendar_not_found.png")
        raise TimeoutException(f"Could not find or click day {day}.")


def is_target_slot_available(driver, time_text: str) -> Any:
    """
    Checks the exact chip for the requested time.
    Returns the element if it's available (clickable), or None if it's disabled/missing.
    """
    try:
        chip_xpath = f'//div[contains(@class, "MuiChip-root")][.//span[contains(., "{time_text}")]]'
        chip = driver.find_element(By.XPATH, chip_xpath)
        
        classes = chip.get_attribute("class")
        
        if "Mui-disabled" in classes:
            return None
            
        return chip
    except Exception:
        # Element hasn't rendered on the page layout yet
        return None


def click_reserve_button(driver):
    print("[INFO] Clicking the 'Rezervă' button...")
    btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                '//button[@type="submit" and (normalize-space()="Rezervă" or contains(., "Rezervă"))]',
            )
        )
    )
    driver.execute_script("arguments[0].click();", btn)


def click_confirm_reservation(driver):
    print("[INFO] Clicking the 'Confirmă rezervarea' button...")
    btn = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//button[normalize-space()="Confirmă rezervarea"]')
        )
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
        EC.presence_of_element_located(
            (By.XPATH, '//a[contains(@href,"/reservations/confirm")]')
        )
    )
    return element.get_attribute("href")


def open_reservation_page_and_prepare(driver, week_clicks: int):
    driver.get(config.TARGET_URL)
    accept_cookies_if_present(driver)
    click_reserve_now_if_present(driver)
    select_sport(driver, config.SPORT_NAME)
    select_sports_complex(driver, config.SPORTS_COMPLEX)
    select_sport_field(driver, config.FIELD_NAME)
    driver.execute_script("window.scrollBy(0, 400);")
    click_arrow_forward(driver, times=week_clicks)
    time.sleep(1)
