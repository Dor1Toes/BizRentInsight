from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import time
import pandas as pd

class LoopNetScraper:

    def __init__(self):
        self.loopNet_url = 'https://www.loopnet.ca/'
        self.chrome_driver = os.getcwd() + '\scraper\management\commands\chromedriver.exe'
        self.search_filters = {
            'regions': ['East of England'],
            'markets': ['Birmingham', 'London', 'Manchester'],
            'space_uses': ['Retail','Restaurant'],
            'use_classes': ['Sui Generis','E (Commercial, Business and Service)'],

        }


    def init_google_driver(self, url):
        driver_path = 'chromedriver.exe'
        # Set up Chrome options
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment to run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1440,1080")

        print("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(service=Service(self.chrome_driver), options=chrome_options)
        print("Chrome WebDriver initialized successfully.")

        driver.get(url)
        # click the search button for accessing advanced filters
        search_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='quick-search-container search-location-container']//div[@class='search-button']")))
        search_button.click()

        return driver
    

    def select_filters(self, wait, region, market, is_selected):
        # click the "filter" button
        filter_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='search-filter']//button[@class='button primary punchout inverted advanced']")))
        filter_button.click()

        # if already selected filters, then press clear button
        if is_selected:
            clear_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="ribbon actions advanced-filters-actions"]//button[@class="button primary punchout clear"]')))
            clear_button.click()

        # click to choose 'United Kingdom'
        dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[1]/div/button')))
        dropdown_button.click()
        uk_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[1]/div/ul/li[4]/button')))
        uk_option.click()

        # click the chosen region, e.g. 'East of England'
        dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[2]/div/div/div/input')))
        dropdown_button.click()
        region_option =wait.until(EC.element_to_be_clickable((By.XPATH, f"//li[@class='ui-select-choices-group' and @id='ui-select-choices-15']//div[@id='ui-select-choices-row-15-' and @role='option']//a[normalize-space()='{region}']")))
        region_option.click()

        # click the target market, e.g. 'Manchester'
        dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[5]/div/div/div/input')))
        dropdown_button.click()
        mkt_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//li[@class='ui-select-choices-group' and @id='ui-select-choices-18']//div[@id='ui-select-choices-row-18-' and @role='option']//a[normalize-space()='{market}']")))
        mkt_option.click()

        # select space uses, e.g. retail
        for space_use in self.search_filters['space_uses']:
            retail_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, f"//ul[@class='input-select-multiple multi-select-box space-use']//label[contains(normalize-space(), '{space_use}')]/input[@type='checkbox' and @class='input-checkbox']")))
            if not retail_checkbox.is_selected():
                retail_checkbox.click()

        # select use classes, e.g. Sui Generis
        for use_class in self.search_filters['use_classes']:
            sui_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, f"//ul[@class='input-select-multiple multi-select-box use-class']//label[contains(normalize-space(), '{use_class}')]/input[@type='checkbox' and @class='input-checkbox']")))
            if not sui_checkbox.is_selected():
                sui_checkbox.click()

        # output all available submarkets within this market
        dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[6]/div/div/div/input')))
        dropdown_button.click()
        time.sleep(1)
        submarket_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//li[@class='ui-select-choices-group']//div[@id='ui-select-choices-row-19-']//a[@class='ui-select-choices-row-inner']")
        ))
        submarkets = [element.text for element in submarket_elements]
        return submarkets


    def collect_property_list(self):
        """Scrape property listings from multiple pages until no 'Next Page' button exists."""
        properties_list = []
        for region in self.search_filters["regions"]:
            for market in self.search_filters["markets"]:
                driver = self.init_google_driver(self.loopNet_url)
                wait = WebDriverWait(driver, 10)  # wait up to 10 seconds for loading
                submarkets = self.select_filters(wait, region, market,False)
                for submarket in submarkets:
                    # select the submarket
                    dropdown_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[6]/div/div/div/input')))
                    dropdown_button.click()
                    submkt_option =wait.until(EC.element_to_be_clickable((By.XPATH, f"//li[@class='ui-select-choices-group' and @id='ui-select-choices-19']//div[@id='ui-select-choices-row-19-' and @role='option']//a[normalize-space()='{submarket}']")))
                    submkt_option.click()
                    # click search button
                    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@class="ribbon actions advanced-filters-actions"]//button[@class="button primary submit"]')))
                    search_button.click()
                    # scrape pages' context
                    submkt_list = self.scrape_pages(driver)
                    properties_list.extend(submkt_list)
                    # initialize the filter 
                    self.select_filters(wait,region, market,True)
                    print(f'{market},{submarket} property list is collected successfully!')
                
        return properties_list
            
                    

    def scrape_pages(self, driver):
        """Scrape property listings from multiple pages until no 'Next Page' button exists."""
        submkt_property_list = []
        while True:
            time.sleep(2)  # Allow page to load
            # Extract property listings
            listings = driver.find_elements(By.TAG_NAME, "article")

            for listing in listings:
                try:
                    property_area = listing.find_element(By.XPATH, ".//div[@class='header-col header-left']").text
                    city_address = listing.find_element(By.XPATH, ".//a[@class='right-h6']").text
                    size = listing.find_element(By.XPATH, ".//a[@class='right-h4']").text

                    try:
                        price = listing.find_element(By.XPATH, ".//ul[@class='data-points-a']/li[@name='Price']").text
                    except:
                        price = "N/A"

                    try:
                        availability = listing.find_element(By.XPATH,
                                                            ".//ul[@class='data-points-a']/li[@name='SpaceAvailable']").text
                    except:
                        availability = "N/A"

                except:
                    try:
                        title = listing.find_element(By.XPATH, ".//h4/a").text
                    except:
                        title = "N/A"

                    try:
                        subtitle = listing.find_element(By.XPATH, ".//h6/a").text
                    except:
                        subtitle = ""

                    property_area = f"{title}\n{subtitle}".strip(", ")

                    try:
                        city_address = listing.find_element(By.XPATH, ".//a[@class='subtitle-beta']").text
                    except:
                        city_address = "N/A"

                    try:
                        size = listing.find_element(By.XPATH, ".//ul[@class='data-points-2c']/li[1]").text
                    except:
                        size = "N/A"

                    try:
                        price = listing.find_element(By.XPATH, ".//ul[@class='data-points-2c']/li[@name='Price']").text
                    except:
                        price = "N/A"

                    try:
                        availability = listing.find_element(By.XPATH,
                                                            ".//ul[@class='data-points-2c']/li[@name='SpaceAvailable']").text
                    except:
                        availability = "N/A"

                submkt_property_list.append({
                    "property_area": property_area,
                    "city_address": city_address,
                    "size": size,
                    "price": price,
                    "availability": availability
                })

            # Try to find the "Next Page" button
            try:
                next_page_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@data-automation-id='NextPage']"))
                )
                next_page_button.click()  # Click to go to the next page

            except:
                print("No more pages to scrape. Exiting loop.")
                break
        
        submkt_property_list.pop()
        return submkt_property_list


if __name__ == '__main__':
    loopnet_scrp = LoopNetScraper()
    properties_list = loopnet_scrp.collect_property_list()
