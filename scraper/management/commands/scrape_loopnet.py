from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from django.core.management.base import BaseCommand
from multiprocessing import Pool
import os
import time
import re

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BizRent.settings')
django.setup()


from scraper.models import Property

class LoopNetScraper:

    def __init__(self):
        self.loopNet_url = 'https://www.loopnet.ca/'
        self.chrome_driver = os.getcwd() + '\chromedriver.exe'
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
        self.safe_click(driver,"//div[@class='quick-search-container search-location-container']//div[@class='search-button']")

        return driver
    
    def safe_click(self, driver, xpath, retries=3):
        """ A safe click method to retry clicking elements in case of StaleElementReferenceException. """
        for _ in range(retries):
            try:
                element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                element.click()
                return True
            except StaleElementReferenceException:
                time.sleep(1)  # Sleep for a short time before retrying
        return False
    

    def select_filters(self, driver, region, market, is_selected):
        
        wait = WebDriverWait(driver, 10)
        # click the "filter" button
        self.safe_click(driver,"//div[@class='search-filter']//button[@class='button primary punchout inverted advanced']")

        # if already selected filters, then press clear button
        if is_selected:
            self.safe_click(driver,'//div[@class="ribbon actions advanced-filters-actions"]//button[@class="button primary punchout clear"]')

        # click to choose 'United Kingdom'
        self.safe_click(driver,'//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[1]/div/button')
        self.safe_click(driver,'//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[1]/div/ul/li[4]/button')

        # click the chosen region, e.g. 'East of England'
        self.safe_click(driver,'//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[2]/div/div/div/input')
        self.safe_click(driver, f"//li[@class='ui-select-choices-group' and @id='ui-select-choices-15']//div[@id='ui-select-choices-row-15-' and @role='option']//a[normalize-space()='{region}']")

        # click the target market, e.g. 'Manchester'
        self.safe_click(driver, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[5]/div/div/div/input')
        self.safe_click(driver, f"//li[@class='ui-select-choices-group' and @id='ui-select-choices-18']//div[@id='ui-select-choices-row-18-' and @role='option']//a[normalize-space()='{market}']")

        # select space uses, e.g. retail
        for space_use in self.search_filters['space_uses']:
            retail_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, f"//ul[@class='input-select-multiple multi-select-box space-use']//label[contains(normalize-space(), '{space_use}')]/input[@type='checkbox' and @class='input-checkbox']")))
            if not retail_checkbox.is_selected():
                self.safe_click(driver,f"//ul[@class='input-select-multiple multi-select-box space-use']//label[contains(normalize-space(), '{space_use}')]/input[@type='checkbox' and @class='input-checkbox']")

        # select use classes, e.g. Sui Generis
        for use_class in self.search_filters['use_classes']:
            sui_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, f"//ul[@class='input-select-multiple multi-select-box use-class']//label[contains(normalize-space(), '{use_class}')]/input[@type='checkbox' and @class='input-checkbox']")))
            if not sui_checkbox.is_selected():
                self.safe_click(driver,f"//ul[@class='input-select-multiple multi-select-box use-class']//label[contains(normalize-space(), '{use_class}')]/input[@type='checkbox' and @class='input-checkbox']")

        # output all available submarkets within this market
        self.safe_click(driver, '//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[6]/div/div/div/input')
        time.sleep(1)
        submarket_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//li[@class='ui-select-choices-group']//div[@id='ui-select-choices-row-19-']//a[@class='ui-select-choices-row-inner']")
        ))
        submarkets = [element.text for element in submarket_elements]
        return submarkets


    def collect_market_list(self,*args):
        """ collect single market data, as multiprocessing tasks """
        region, market = args
        driver = self.init_google_driver(self.loopNet_url)
        properties_list = []
        try:
            submarkets = self.select_filters(driver, region, market,False)

            for submarket in submarkets:
                # select the submarket
                self.safe_click(driver,'//*[@id="top"]/section[1]/div[2]/div[2]/div/click-event-bridge/section/form/div[4]/section[2]/div[6]/div/div/div/input')
                self.safe_click(driver,f"//li[@class='ui-select-choices-group' and @id='ui-select-choices-19']//div[@id='ui-select-choices-row-19-' and @role='option']//a[normalize-space()='{submarket}']")
                # click search button
                self.safe_click(driver,'//div[@class="ribbon actions advanced-filters-actions"]//button[@class="button primary submit"]')
                # scrape pages' context
                submkt_list = self.scrape_pages(driver, market, submarket)
                properties_list.extend(submkt_list)
                # initialize the filter 
                self.select_filters(driver,region, market,True)

            print(f'Collected {len(properties_list)} properties from {market}')

        except Exception as e:
            print(f"Error scraping {market}: {e}")
        
        finally:
            driver.quit()
            return properties_list 


    def collect_property_list(self):
        """Using multiprocessing to scrape different markets"""
        properties_list = []
        tasks = []

        for region in self.search_filters["regions"]:
            for market in self.search_filters["markets"]:
                tasks.append((region, market))

        with Pool(processes=len(self.search_filters["markets"])) as pool:
            results = pool.starmap(self.collect_market_list, tasks)
        
        for result in results:
             properties_list.extend(result)
        
        return properties_list
                    

    def scrape_pages(self, driver, market_name, submarket_name):
        """Scrape property listings from multiple pages until no 'Next Page' button exists."""
        submkt_property_list = []
        while True:
            time.sleep(2)  # Allow page to load
            # Extract property listings
            listings = driver.find_elements(By.TAG_NAME, "article")

            for listing in listings:
                try:
                    property_address = listing.find_element(By.XPATH, ".//div[@class='header-col header-left']").text
                    city_address = listing.find_element(By.XPATH, ".//div[@class='header-col header-right text-right']//a[@class='right-h6']").text
                    space_for_lease = listing.find_element(By.XPATH, ".//div[@class='header-col header-right text-right']//a[@class='right-h4']").text

                    try:
                        loopnet_tag = listing.find_element(By.XPATH, ".//div[@class='placard-pseudo']/a")
                        loopnet_url = loopnet_tag.get_attribute("href")
                    except:
                        loopnet_url = ""

                    try:
                        image_tag = listing.find_element(By.XPATH,".//div[@class='media']//div[@class='carousel-theme-light xfade carousel  ng-scope']//div[@class='carousel-inner']/div[contains(@class, 'slide') and contains(@class, 'active')]//figure/img")
                        image_url = image_tag.get_attribute("src")
                    except:
                        image_url = ""

                    try:
                        price_for_lease = listing.find_element(By.XPATH, ".//div[normalize-space(@class)='placard-content']/div[normalize-space(@class)='placard-info   placard-info-mobile-skeleton']/div[normalize-space(@class)='data']/ul[@class='data-points-a']/li[@name='Price']").text
                    except:
                        price_for_lease = ""

                    try:
                        is_available = listing.find_element(By.XPATH,
                                                            ".//div[normalize-space(@class)='placard-content']/div[normalize-space(@class)='placard-info   placard-info-mobile-skeleton']/div[normalize-space(@class)='data']/ul[@class='data-points-a']/li[@name='SpaceAvailable']").text
                    except:
                        is_available = ""

                except:
                    try:
                        loopnet_tag = listing.find_element(By.XPATH, ".//div[@class='placard-pseudo']/a")
                        loopnet_url = loopnet_tag.get_attribute("href")
                    except:
                        loopnet_url = ""
                    
                    try:
                        image_tag = listing.find_element(By.XPATH,".//div[@class='media']//div[@class='carousel-view']//div[@class='carousel-inner']/div[contains(@class, 'slide') and contains(@class, 'active')]/figure/img")
                        image_url = image_tag.get_attribute("src")
                    except:
                        image_url = ""
                    
                    try:
                        title = listing.find_element(By.XPATH, ".//div[normalize-space(@class)='placard-content show-logos']//div[normalize-space(@class)='header-col']/h4/a").text
                    except:
                        title = ""

                    try:
                        subtitle = listing.find_element(By.XPATH, ".//div[normalize-space(@class)='placard-content show-logos']//div[normalize-space(@class)='header-col']/h6/a").text
                    except:
                        subtitle = ""

                    property_address = f"{title}\n{subtitle}".strip(", ")

                    try:
                        city_address = listing.find_element(By.XPATH, ".//div[normalize-space(@class)='placard-content show-logos']//div[normalize-space(@class)='header-col']/a[@class='subtitle-beta']").text
                    except:
                        city_address = ""

                    try:
                        space_for_lease = listing.find_element(By.XPATH, ".//div[normalize-space(@class)='placard-content show-logos']/div[normalize-space(@class)='placard-info show-logos']//ul[@class='data-points-2c']/li[not(@name)]").text
                    except:
                        space_for_lease = ""

                    try:
                        price_for_lease = listing.find_element(By.XPATH, ".//div[normalize-space(@class)='placard-content show-logos']/div[normalize-space(@class)='placard-info show-logos']//ul[@class='data-points-2c']/li[@name='Price']").text
                    except:
                        price_for_lease = ""

                    try:
                        is_available = listing.find_element(By.XPATH,
                                                            ".//div[normalize-space(@class)='placard-content show-logos']/div[normalize-space(@class)='placard-info show-logos']//ul[@class='data-points-2c']/li[@name='SpaceAvailable']").text
                    except:
                        is_available = ""
                
                try:
                    city_name,zip_code = city_address.rsplit(", ", 1)
                except:
                    city_name = city_address
                    zip_code = ""

                try:
                    match = re.search(r'(\d+)/$', loopnet_url)
                    property_id = match.group(1) if match else ""
                except:
                    property_id = ""

                submkt_property_list.append({
                    "id":property_id,
                    "address": property_address,
                    "market":market_name,
                    "submarket":submarket_name,
                    "postal_code":zip_code,
                    "city":city_name,
                    "space": space_for_lease,
                    "price": price_for_lease,
                    "availability": is_available,
                    "image":image_url,
                    "access_link":loopnet_url
                })

            # Try to find the "Next Page" button
            try:
                # Click to go to the next page
                self.safe_click(driver,"//a[@data-automation-id='NextPage']")
            except:
                print("No more pages to scrape. Exiting loop.")
                break
        
        submkt_property_list.pop()
        return submkt_property_list


class Command(BaseCommand):
    help = "Scrape LoopNet and store property data in the database"

    def handle(self, *args, **options):
        self.stdout.write("Starting LoopNet Scraper...")
        loopnet_scraper = LoopNetScraper()
        scraped_data = loopnet_scraper.collect_property_list()

        # saving scraped data to database
        for data in scraped_data:
            property_obj, created = Property.objects.update_or_create(
                property_id=data["id"],
                defaults=data
            )
            if created:
                self.stdout.write(f"Added: {property_obj.property_id}")
            else:
                self.stdout.write(f"Updated: {property_obj.property_id}")

        self.stdout.write(self.style.SUCCESS("Scraping completed successfully!"))

