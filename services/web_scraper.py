import multiprocessing
from time import sleep
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup, NavigableString
import re
from datetime import datetime, timedelta
from typing import List
from selenium.webdriver.remote.webelement import WebElement
from model.flight import Flight


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

    def compute_urls(self) -> List[str]:
        urls = []
        for day in self.list_of_days():
            url = (f"https://www.kayak.co.uk/flights/{self.departure_station}-{self.arrival_station}"
                   f"/{day}?fs=price=-{self.budget};stops={self.stops}&sort=bestflight_a")
            urls.append(url)
        return urls

    def parse_flight_web_elements(self, elements: list[WebElement], url: str):
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
            res.append(
                {
                    "url": url,
                    "departure": departure,
                    "arrival": arrival,
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "duration": duration,
                    "price": price,
                    "is_direct": is_direct,
                }
            )
        return res

    def scrape_data(self, url, max_retries=2):
        if self.retry_count <= max_retries:
            try:
                popup_window_button = "//button[contains(@class, 'Py0r')]"

                driver = webdriver.Chrome()
                driver.get(url)
                sleep(4)
                driver.find_element("xpath", popup_window_button).click()

                # scrape data by finding elements using XPath
                element = driver.find_elements("xpath", '//div[@data-resultid]')
                if element is not None:
                    el = self.parse_flight_web_elements(element, url)
                    driver.quit()
                    return el

            except WebDriverException as err:
                print(f"Failed to scrape data from {url}: {str(err)}")
                self.retry_count += 1
                self.failed_urls.append(url)
                return

        else:
            print("Number of attempts exceeded")

    def requests_data(self):
        # Create a pool of worker processes
        num_processes = multiprocessing.cpu_count()  # Use CPU cores - 1
        pool = multiprocessing.Pool(processes=num_processes - 1)

        # Use multiprocessing to scrape data from multiple URLs concurrently
        results = pool.map(self.scrape_data, self.compute_urls())

        # results = [self.scrape_data(url) for url in self.compute_urls()]

        # After the initial scraping retry failed URLs (max 2 times)
        if self.failed_urls and self.retry_count <= 2:
            print("Retrying failed URLs...")
            sleep(3)
            results.append([self.scrape_data(url) for url in self.failed_urls])

        # Close the pool of worker processes
        pool.close()
        pool.join()

        return results

    @staticmethod
    def flight_objects(results):
        return [Flight(*flight_dict.values()) for day_elements in results
                for flight_dict in day_elements if day_elements is not None]

    def list_of_flights(self):
        # results = self.requests_data()

        # testing_data
        results = [
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-03?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-03?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-03?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-03?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-03?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-04?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=87, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-04?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=87, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-04?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=87, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-04?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='21:00',
                   arrival_time='23:25', duration_time='2h 25m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-04?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-04?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=222, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-04?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=289, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-05?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=84, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-05?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=84, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-05?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=84, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-05?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='21:00',
                   arrival_time='23:25', duration_time='2h 25m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-05?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=160, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-05?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=188, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-05?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=261, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-06?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-06?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-06?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='21:00',
                   arrival_time='23:25', duration_time='2h 25m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-06?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-06?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-06?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-07?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=87, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-07?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=78, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-07?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=78, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-07?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='21:00',
                   arrival_time='23:25', duration_time='2h 25m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-07?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-07?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-07?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-08?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-08?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-08?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='21:00',
                   arrival_time='23:25', duration_time='2h 25m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-08?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-08?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-08?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-09?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-09?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=90, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-09?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='21:00',
                   arrival_time='23:25', duration_time='2h 25m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-09?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-09?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-09?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-10?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=84, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-10?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='14:30',
                   arrival_time='17:05', duration_time='2h 35m', price=84, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-10?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='08:30',
                   arrival_time='11:05', duration_time='2h 35m', price=84, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-10?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='06:10',
                   arrival_time='08:45', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-10?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='17:15',
                   arrival_time='19:50', duration_time='2h 35m', price=135, direct_flight=True),
            Flight(url='https://www.kayak.co.uk/flights/ROM-AMS/2024-02-10?fs=price=-450;stops=0&sort=bestflight_a',
                   departure_station='FCO Fiumicino', arrival_station='AMS Schiphol', departure_time='12:45',
                   arrival_time='15:20', duration_time='2h 35m', price=135, direct_flight=True)]

        flight_objects = self.flight_objects(results)

        return flight_objects


if __name__ == "__main__":
    print(WebScraper(
        "ROM",
        "AMS",
        "2024-02-03",
        200,
        0
    ).list_of_flights())
