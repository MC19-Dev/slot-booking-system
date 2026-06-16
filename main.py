import time
import random
from datetime import datetime, timedelta
import config
import actions
from driver import build_driver, save_and_upload_screenshot
from selenium.webdriver.remote.webdriver import WebDriver


def get_now() -> datetime:
    """Mockable current datetime for testing purposes."""
    return datetime(2026, 6, 15, 20, 58, tzinfo=config.TIMEZONE)


def get_target_reservation_datetime(now: datetime | None = None) -> datetime:
    if now is None:
        now = datetime.now(config.TIMEZONE)
    if now.minute < 10:
        base_hour = now.replace(minute=0, second=0, microsecond=0)
    else:
        base_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return base_hour + timedelta(days=14)


def get_week_clicks_needed(now: datetime | None = None) -> int:
    if now is None:
        now = datetime.now(config.TIMEZONE)
    target_dt = get_target_reservation_datetime(now)
    delta_days = (target_dt.date() - now.date()).days
    return delta_days // 7


def wait_for_slot_and_select(
    driver: WebDriver,
    day: int,
    time_text: str,
    week_clicks: int,
    max_minutes: int = 15,
    retry_delay: int = 2,
) -> bool:
    start_time = time.time()
    deadline = start_time + max_minutes * 60
    attempt = 0

    while time.time() < deadline:
        attempt += 1
        seconds_running = time.time() - start_time
        print(f"[INFO] Attempt {attempt}: Scanning slot state for {time_text}...")

        try:
            actions.select_day(driver, day)
            time.sleep(0.3)  # Small redraw window for the DOM

            target_chip = actions.is_target_slot_available(driver, time_text)

            if target_chip is not None:
                print(
                    f"[ALERT] Slot {time_text} detected as AVAILABLE! Clicking instantly."
                )
                time.sleep(random.uniform(0.05, 0.10))
                driver.execute_script("arguments[0].click();", target_chip)

                filename = f"found_slot_{day}_{time_text.replace(':', '-')}.png"
                save_and_upload_screenshot(driver, filename)
                return True
            else:
                print(f"[INFO] Slot {time_text} is still locked or missing.")

            if seconds_running < 300:
                sleep_time = random.uniform(15, 30)
            elif seconds_running < 600:
                sleep_time = random.uniform(10, 15)
            elif seconds_running < 840:
                sleep_time = random.uniform(3, 5)
            else:
                sleep_time = random.uniform(0.8, 1.5)  # High-speed window pacing

            if attempt % 6 == 0 and seconds_running < 840:
                print(
                    "[INFO] Performing structural lifecycle refresh to preserve session..."
                )
                actions.open_reservation_page_and_prepare(driver, week_clicks)
                time.sleep(2)

            elif seconds_running < 840:
                base_slug = config.FIELD_SLUGS.get(config.SPORT_NAME)
                other_field = (
                    "Oricare"
                    if config.FIELD_NAME != "Oricare"
                    else f"{base_slug} 2"
                )
                actions.select_sport_field(driver, other_field)
                time.sleep(sleep_time)
                actions.select_sport_field(driver, config.FIELD_NAME)

            else:
                time.sleep(sleep_time)

        except Exception as e:
            print(f"[WARN] Attempt {attempt} encountered a handling error: {e}")
            actions.open_reservation_page_and_prepare(driver, week_clicks)
            time.sleep(retry_delay)

    return False


def create_reservation(driver: WebDriver) -> str:
    # testing purpose:
    # now = get_now()
    # target_dt = get_target_reservation_datetime(now=now)
    # target_day = target_dt.day
    # target_time = target_dt.strftime("%H:%M")
    # week_clicks = get_week_clicks_needed(now=now)

    target_dt = get_target_reservation_datetime()
    target_day = target_dt.day
    target_time = target_dt.strftime("%H:%M")
    week_clicks = get_week_clicks_needed()

    print(f"[INFO] Target reservation datetime: {target_dt}")
    driver.get(config.TARGET_URL)
    actions.accept_cookies_if_present(driver)
    actions.click_login_if_present(driver)
    actions.login(driver, config.MAIN_ACCOUNT)

    print("[INFO] Preparing calendar and navigating to the target week...")
    actions.open_reservation_page_and_prepare(driver, week_clicks)

    if not wait_for_slot_and_select(driver, target_day, target_time, week_clicks, config.MAX_MINUTES):
        raise RuntimeError(
            f"Could not find slot for day {target_day} at {target_time}."
        )

    actions.click_reserve_button(driver)
    actions.check_all_visible_checkboxes(driver)
    actions.click_confirm_reservation(driver)
    if config.SPORT_NAME != "Tenis cu peretele":
        return actions.get_confirmation_link(driver)
    
    return "No confirmation link available."


def login_and_return_to_url(
    driver: WebDriver, account: config.Account, target_url: str
) -> None:
    driver.get(target_url)
    actions.accept_cookies_if_present(driver)
    actions.click_login_if_present(driver)
    actions.login(driver, account)
    actions.open_reservation_page_and_prepare(driver, 0)
    driver.get(target_url)


def confirm_from_shared_link(account: config.Account, confirmation_link: str) -> None:
    driver = build_driver()
    try:
        login_and_return_to_url(driver, account, confirmation_link)
        actions.check_all_visible_checkboxes(driver)
        actions.click_confirm_reservation(driver)
        print(f"[SUCCESS] Account {account.email} confirmed.")
    except Exception as e:
        print(f"[WARNING] Account {account.email} failed: {e}")
        save_and_upload_screenshot(driver, f"error_{account.email}.png")
    finally:
        driver.quit()


def main() -> None:
    config.validate_config()
    driver = build_driver()
    confirmation_link: str | None = None

    try:
        confirmation_link = create_reservation(driver)
        print(f"[SUCCESS] Slot secured! Link: {confirmation_link}")
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to create reservation: {e}")
        save_and_upload_screenshot(driver, "main_error.png")
        return
    finally:
        driver.quit()

    if confirmation_link:
        print(
            f"Starting confirmations for {len(config.OTHER_ACCOUNTS)} secondary accounts..."
        )
        for i, account in enumerate(config.OTHER_ACCOUNTS):
            if i > 0:
                time.sleep(random.randint(30, 90))
            if "Tenis" in config.SPORT_NAME and i == 1:
                break
            confirm_from_shared_link(account, confirmation_link)

    print("Automation process finished.")


if __name__ == "__main__":
    main()
