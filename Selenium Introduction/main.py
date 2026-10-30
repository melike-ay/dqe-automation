import time
import os
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)

REPORT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "report.html"))
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
CSV_DIR = os.path.join(os.path.dirname(__file__), "csv")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

class SeleniumWebDriverContextManager:
    def __init__(self, headless: bool = False, window_size: tuple = (1920, 1080)):
        self.headless = headless
        self.window_size = window_size
        self.driver = None

    def __enter__(self) -> WebDriver:
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        options.add_argument(f"--window-size={self.window_size[0]},{self.window_size[1]}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(2)
        return self.driver

    def __exit__(self, exc_type, exc_value, traceback):
        if self.driver:
            self.driver.quit()
        return False

def extract_table(driver: WebDriver) -> pd.DataFrame:
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "table"))
        )
        table = driver.find_element(By.CLASS_NAME, "table")
        columns = table.find_elements(By.XPATH, ".//*[@class='y-column']")

        headers = []
        data_by_column = []

        for column in columns:
            header_text = column.find_element(By.ID, "header").text.strip()
            headers.append(header_text)

            cells = column.find_elements(By.CSS_SELECTOR, ".cell-text")
            values = [c.text.strip() for c in cells if c.text.strip() != header_text and c.text.strip() != ""]
            data_by_column.append(values)

        num_rows = max((len(col) for col in data_by_column), default=0)
        rows = []
        for i in range(num_rows):
            row = {h: (data_by_column[idx][i] if i < len(data_by_column[idx]) else "")
                   for idx, h in enumerate(headers)}
            rows.append(row)

        return pd.DataFrame(rows, columns=headers)

    except TimeoutException:
        print("ERROR: Table did not become visible in time.")
        return pd.DataFrame()
    except NoSuchElementException as e:
        print(f"ERROR: Table element not found: {e}")
        return pd.DataFrame()

def save_table_csv(df: pd.DataFrame, filename: str = "table.csv"):
    if df.empty:
        print("WARNING: table DataFrame is empty, nothing saved.")
        return
    path = os.path.join(CSV_DIR, filename)
    try:
        df.to_csv(path, index=False)
        print(f"Saved {path}")
    except OSError as e:
        print(f"ERROR writing {path}: {e}")

def wait_for_chart(driver: WebDriver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "pielayer"))
    )

def take_screenshot(driver: WebDriver, index: int):
    path = os.path.join(SCREENSHOT_DIR, f"screenshot{index}.png")
    driver.save_screenshot(path)
    print(f"Saved {path}")

def extract_doughnut_data(driver: WebDriver) -> pd.DataFrame:
    rows = []
    try:
        doughnut = driver.find_element(By.CLASS_NAME, "pielayer")
        labels = doughnut.find_elements(By.CSS_SELECTOR, "text.slicetext[data-notex='1']")
        for label in labels:
            tspans = label.find_elements(By.TAG_NAME, "tspan")
            if len(tspans) >= 2:
                category = tspans[0].text.strip()
                value = tspans[1].text.strip()
                rows.append({"Facility Type": category, "Min Average Time Spent": value})
    except NoSuchElementException:
        print("WARNING: pielayer or slice labels not found.")
    return pd.DataFrame(rows, columns=["Facility Type", "Min Average Time Spent"])

def save_doughnut_csv(df: pd.DataFrame, index: int):
    path = os.path.join(CSV_DIR, f"doughnut{index}.csv")
    try:
        df.to_csv(path, index=False)
        print(f"Saved {path}")
    except OSError as e:
        print(f"ERROR writing {path}: {e}")

def get_legend_items(driver: WebDriver):
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "scrollbox"))
    )
    scrollbox = driver.find_element(By.CLASS_NAME, "scrollbox")
    return scrollbox.find_elements(By.CLASS_NAME, "traces")

def click_legend_item(driver: WebDriver, item) -> bool:
    try:
        ActionChains(driver).move_to_element(item).click(item).perform()
        time.sleep(1)
        return True
    except ElementClickInterceptedException:
        print("WARNING: click intercepted, retrying with JS click.")
        try:
            driver.execute_script("arguments[0].click();", item)
            time.sleep(1)
            return True
        except Exception as e:
            print(f"ERROR: could not click legend item: {e}")
            return False
    except StaleElementReferenceException:
        print("WARNING: legend item became stale, skipping this click.")
        return False

def run_doughnut_filter_iteration(driver: WebDriver):
    screenshot_index = 1
    csv_index = 1

    legend_items = get_legend_items(driver)
    num_items = len(legend_items)
    print(f"Found {num_items} legend/filter items.")

    for i in range(num_items):
        try:
            legend_items = get_legend_items(driver)
            if i >= len(legend_items):
                print(f"WARNING: legend item index {i} no longer exists, skipping.")
                continue

            item = legend_items[i]
            if not click_legend_item(driver, item):
                continue

            take_screenshot(driver, screenshot_index)
            screenshot_index += 1

            data_df = extract_doughnut_data(driver)
            if data_df.empty:
                print(f"NOTE: filter step {i} left no visible slices "
                      f"(all filters unselected or no matching data).")
            save_doughnut_csv(data_df, csv_index)
            csv_index += 1

        except Exception as e:
            print(f"ERROR during filter iteration {i}: {e}")
            continue

if __name__ == "__main__":
    with SeleniumWebDriverContextManager() as driver:
        file_path = REPORT_PATH
        driver.get(f"file://{file_path}")

        table_df = extract_table(driver)
        save_table_csv(table_df)

        wait_for_chart(driver)
        take_screenshot(driver, 0)
        initial_data_df = extract_doughnut_data(driver)
        save_doughnut_csv(initial_data_df, 0)

        run_doughnut_filter_iteration(driver)