import os
from selenium import webdriver
from google.cloud import storage
import config


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

    gcs_enabled = os.environ.get("GOOGLE_STORAGE_ENABLED", "false").lower() == "true"
    if gcs_enabled:
        try:
            print(f"[INFO] GCS Upload enabled. Sending {filename} to the cloud...")
            storage_client = storage.Client()
            safe_bucket_name = (
                f"{config.SPORT_SLUGS.get(config.SPORT_NAME)}-bot-screenshots"
            )
            bucket = storage_client.bucket(safe_bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_filename(filename)
            print(f"[SUCCESS] Uploaded {filename} to Google Cloud Storage bucket!")
        except Exception as e:
            print(f"[WARN] Failed to upload screenshot to GCP Storage: {e}")
