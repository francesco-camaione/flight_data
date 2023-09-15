import multiprocessing
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from typing import List
from selenium.webdriver.remote.webelement import WebElement
from model.flight import Flight
from lib import utils


class WebScraper:

    def __init__(self, departure_station, arrival_station, when, budget, stops):
        self.departure_station = departure_station
        self.arrival_station = arrival_station
        self.when = when
        self.budget = budget
        self.stops = stops

    failed_urls = []
    retry_count = 0

    @staticmethod
    def get_departure_and_arrival_time(div_elements) -> tuple[str | int, str | int]:
        departure_time = 0
        arrival_time = 0
        if div_elements:
            spans = div_elements.find_all("span")
            if len(spans) == 3:
                departure_time = spans[0].get_text()
                arrival_time = spans[2].get_text()
        return departure_time, arrival_time

    @staticmethod
    def get_departure_and_arrival_stations(div_elements) -> tuple[str, str]:

        def get_station_name(div):
            spans = div.find_all("span")
            departure_span_1 = spans[1].get_text()
            departure_span_2 = spans[2].get_text()
            return f"{departure_span_1} {departure_span_2}"

        departure, arrival = [get_station_name(div) for div in div_elements]
        return departure, arrival

    @staticmethod
    def get_duration_time(div_element: BeautifulSoup | None):
        div = div_element.find_all("div")
        return div[0].get_text()

    @staticmethod
    def delete_pound_sign(price_str: str) -> int:
        price = price_str.replace("£", "").strip()
        return int(price)

    def is_flight_directed(self) -> bool:
        return True if self.stops == 0 else False

    def list_of_days(self) -> List[str]:
        input_data = datetime.strptime(self.when, '%Y-%m-%d')
        # Print the next 7 days including the choosen day
        days = [input_data.strftime('%Y-%m-%d')]
        for i in range(7):
            input_data += timedelta(days=1)
            days.append(input_data.strftime('%Y-%m-%d'))
        return days

    def compute_urls(self, days, is_return=False) -> List[str]:
        urls = []
        if is_return:
            return_start_date = datetime.strptime(days[0], '%Y-%m-%d')
            return_days = [(return_start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(3, 11)]
            for day in return_days:
                url = (f"https://www.kayak.co.uk/flights/{self.arrival_station}-{self.departure_station}"
                       f"/when={day}?fs=price=-{self.budget};stops={self.stops}&sort=bestflight_a")
                urls.append(url)
        else:
            for day in days:
                url = (f"https://www.kayak.co.uk/flights/{self.departure_station}-{self.arrival_station}"
                       f"/when={day}?fs=price=-{self.budget};stops={self.stops}&sort=bestflight_a")
                urls.append(url)
        return urls

    def parse_flight_web_elements(self, elements: list[WebElement], date: str):
        stations_pattern = re.compile(r'.*-mod-variant-full-airport-wide')
        duration_pattern = re.compile(r'.*-mod-full-airport')
        time_pattern = re.compile(r'.*-mod-variant-large')
        price_text_pattern = re.compile(r'.*-price-text$')
        res = []

        for element in elements:
            elementHTML = element.get_attribute('outerHTML')
            elementSoup = BeautifulSoup(elementHTML, "html.parser")

            stations = elementSoup.find_all("div", {"class": stations_pattern})
            time_div = elementSoup.find("div", {"class": time_pattern})
            duration_div = elementSoup.find("div", {"class": duration_pattern})
            price_div = elementSoup.find("div", {"class": price_text_pattern})

            departure, arrival = self.get_departure_and_arrival_stations(stations)
            departure_time, arrival_time = self.get_departure_and_arrival_time(time_div)
            duration = self.get_duration_time(duration_div)
            price = self.delete_pound_sign(price_div.text)
            is_direct = self.is_flight_directed()
            flight_id = utils.remove_spaces_and_digits(
                f"{departure}{arrival}{date}{departure_time}{arrival_time}{duration}{price}")
            res.append(
                {
                    "flight_id": flight_id,
                    "departure": departure,
                    "arrival": arrival,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "duration": duration,
                    "price": utils.pounds_to_euros(price),
                    "is_direct": is_direct,
                    "when": date
                }
            )
            return res

    def scrape_data(self, url, max_retries=2):
        if self.retry_count <= max_retries:
            try:
                popup_window_button = "//button[contains(@class, 'Py0r')]"

                driver = webdriver.Chrome()
                driver.get(url)
                sleep(5)
                driver.find_element("xpath", popup_window_button).click()

                # scrape data by finding elements using XPath
                element = driver.find_elements("xpath", '//div[@data-resultid]')
                if element is not None:
                    el = self.parse_flight_web_elements(element, utils.extract_date_from_url(url))
                    driver.quit()
                    return el

            except WebDriverException as err:
                print(f"Failed to scrape data from {url}: {str(err)}")
                self.retry_count += 1
                self.failed_urls.append(url)
                return

        else:
            print("Number of attempts exceeded")

    def requests_data(self, urls: List[str]):
        # Create a pool of worker processes
        num_processes = multiprocessing.cpu_count()  # Use CPU cores - 1
        pool = multiprocessing.Pool(processes=num_processes - 1)

        # Use multiprocessing to scrape data from multiple URLs concurrently
        results = pool.map(self.scrape_data, urls)

        # results = [self.scrape_data(url) for url in self.compute_urls()]

        # After the initial scraping retry failed URLs (max 2 times)
        if self.failed_urls and self.retry_count <= 2:
            print("Retrying failed URLs...")
            sleep(3)
            results.append([self.scrape_data(url) for url in self.failed_urls])

        # Close the pool of worker processes
        pool.close()
        pool.join()
        print("res: ", results)
        return results

    @staticmethod
    def flight_objects(results):
        if results is not None:
            flights = []
            for day_elements in results:
                if day_elements is not None:
                    for flight_dict in day_elements:
                        flights.append(Flight(*flight_dict.values()))
            return flights
            # return [Flight(*flight_dict.values()) for day_elements in results
            #         for flight_dict in day_elements]

    def one_way_flights(self):
        days = self.list_of_days()
        results = self.requests_data(self.compute_urls(days))
        # testing_data
        # results = [None, None, None, None, None, None, None, None]
        flight_objects = self.flight_objects(results)
        return flight_objects

    def round_trip(self):
        days = self.list_of_days()
        outbound_flights_results: List = self.requests_data(self.compute_urls(days))
        return_flights_results: List = self.requests_data(self.compute_urls(days, is_return=True))

        # testing_data
        # outbound_flights_results = [None, None, None, None, None, None, None, None]

        outbound_flights_results.extend(return_flights_results)
        flight_objects = self.flight_objects(outbound_flights_results)
        return flight_objects

# if __name__ == "__main__":
#     flights = WebScraper(
#         "ROM",
#         "LIS",
#         "2024-02-03",
#         200,
#         0
#     ).round_trip()
#     print(flights)
