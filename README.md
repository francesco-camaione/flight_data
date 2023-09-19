# Flight-Data

Flight data are scraped using Selenium and multiprocessing. Data
are stored in a PostgreSQL database and then processed using PySpark. 
At this stage the minimum ticket price for the period considered is returned, together with the average price for that route.
Additionally, an Apache Airflow workflow is implemented to
efficiently orchestrate the entire process on a weekly basis, ensuring up‑to‑date data and automation.

Data scraping using Selenium:
![Data scraping using Selenium screen](readme_screenshot/s_1.png)

Data processing output using PySpark:
![Screenshot 2023-09-19 alle 20.22.13.png](readme_screenshot/s_3.png)

Data orchestration using Apache Airflow:
![Screenshot 2023-09-19 alle 20.08.42.png](readme_screenshot/s_2.png)

