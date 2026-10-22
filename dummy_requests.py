import os
import random
import time
import threading

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

URL = "http://localhost:8501"
FIREFOX_BINARY = "/snap/firefox/current/usr/lib/firefox/firefox"
GECKODRIVER = "/snap/firefox/current/usr/lib/firefox/geckodriver"
NUM_WINDOWS = 3

file_lock = threading.Lock()
stop_event = threading.Event()

def create_driver():
    """Create an independent Firefox WebDriver instance."""
    options = Options()
    options.binary_location = FIREFOX_BINARY
    service = Service(executable_path=GECKODRIVER)
    driver = webdriver.Firefox(service=service, options=options)
    driver.get(URL)
    time.sleep(3)
    return driver

def worker(worker_id):
    """Run the automation loop in an independent Firefox window."""
    driver = None
    try:
        driver = create_driver()
        print(f"[Worker {worker_id}] Firefox started")
        while not stop_event.is_set():
            try:
                is_zip = random.random() > 0.7
                filename = ("image.zip" if is_zip else f"image{random.randint(0, 9)}.jpeg")
                file_path = os.path.abspath(os.path.join("images", filename))

                if not os.path.exists(file_path):
                    print(f"[Worker {worker_id}] File not found: {filename}")
                    stop_event.wait(3)
                    continue

                mode = "Bulk" if is_zip else "Single"
                driver.find_element(By.XPATH, f"//label[contains(., '{mode}')]").click()
                time.sleep(1)

                file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                file_input.send_keys(file_path)
                time.sleep(2)

                btn_text = ("Process Batch" if is_zip else "Generate Caption")
                driver.find_element(By.XPATH, f"//button[contains(., '{btn_text}')]").click()
                print(f"[Worker {worker_id}] Processed: {filename}")

                delay = (random.uniform(10, 12) if is_zip else random.uniform(3, 7))
                stop_event.wait(delay)

            except Exception as e:
                print(f"[Worker {worker_id}] Error: {e}")
                stop_event.wait(1)

    except Exception as e:
        print(f"[Worker {worker_id}] Stopping: {e}")

    finally:
        if driver:
            driver.quit()
        print(f"[Worker {worker_id}] Firefox closed")


if __name__ == "__main__":
    threads = []
    try:
        for i in range(NUM_WINDOWS):
            thread = threading.Thread(target=worker, args=(i + 1,), daemon=False)
            thread.start()
            threads.append(thread)
            time.sleep(2)
        print(f"Started {NUM_WINDOWS} Firefox windows.")
        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        print("\nStopping automation...")
        stop_event.set()
        for thread in threads:
            thread.join()
        print("Automation stopped.")
