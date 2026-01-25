import kagglehub
from kagglehub import KaggleDatasetAdapter
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pdfplumber
import time

# --- Extract CSV data ---
df_hotels = kagglehub.load_dataset(KaggleDatasetAdapter.PANDAS,
                                   'raj713335/tbo-hotels-dataset',
                                   'hotels.csv',
                                   pandas_kwargs={'encoding': 'latin1'})

# Run basic dataset operations
print(df_hotels.head())

print('Dataset size:', df_hotels.shape)
print('Missing values:\n', df_hotels.isnull().sum())

# --- Extract HTML data ---
options = Options()
options.add_argument('--start-maximized')

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

WEB_URL = 'https://www.avis.com/en/reservation/vehicle-availability?dropoff_suggestion_type_code=AIRPORT&pickup_hour=12&pickup_location_region=NAM&pickup_minute=00&pickup_am_pm=PM&pickup_day=03&pickup_month=02&pickup_suggestion_type_code=AIRPORT&pickup_year=2026&residency_value=US&return_hour=12&return_minute=00&return_am_pm=PM&return_day=05&return_month=02&return_year=2026&pickup_location_code=LAX&return_location_code=LAX&age=25&country=us&locale=en-US&brand=avis&awd_number=D486601&coupon_number=UUWA036'
driver.get(WEB_URL)

# Pause for JavaScript generated content
time.sleep(5)

# Save HTML data
html = driver.page_source
driver.quit

# Extract vehicle and price information
soup = BeautifulSoup(html, 'html.parser')
vehicle_cards = soup.select('article[data-testid^="vehicle-card"]')

vehicles = []

for card in vehicle_cards:
    # Vehicle name
    name_card = card.select_one('[data-testid="vehicle-card-title-text"]')
    vehicle_name = name_card.get_text(strip=True) if name_card else None

    # Price (dollars only)
    price_card = card.select_one('[data-testid="daily-price-value"]')
    price = price_card.get_text(strip=True) if price_card else None

    vehicles.append({
        'vehicle_name': vehicle_name,
        'daily_price': price
    })

# Create dataframe
df_vehicles = pd.DataFrame(vehicles)

print('Rental Car Data:')
print(df_vehicles.head())

# --- Extract PDF data ---
pdf_text = ''

with pdfplumber.open('Flight Confirmation.pdf') as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            pdf_text += text + '\n'


# Aggregate data into a single CSV
hotels_str = (df_hotels.iloc[0].dropna().astype(str).str.strip().tolist())
hotels_str = ' | '.join(hotels_str)

vehicle_rows = []

for _, row in df_vehicles.iterrows():
    row_str = ', '.join(row.dropna().astype(str).str.strip())
    vehicle_rows.append(row_str)

vehicles_str = ' | '.join(vehicle_rows)

df = pd.DataFrame({'source': ['hotels_csv', 'AVIS_html', 'confirmation_pdf'],
                   'content': [hotels_str, vehicles_str, pdf_text]})

