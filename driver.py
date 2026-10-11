import os

from selenium import webdriver


def build_driver() -> webdriver.Chrome | webdriver.Firefox:

    is_github = os.environ.get("GITHUB_ACTIONS") == "true"

    if is_github:

        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.set_preference("dom.webdriver.enabled", False)
        return webdriver.Firefox(options=options)

    else:

        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--window-size=1920,1080")

        return webdriver.Chrome(options=options)


def save_and_upload_screenshot(driver, filename: str):
    driver.save_screenshot(filename)
    print(f"[INFO] Saved local screenshot: {filename}")
