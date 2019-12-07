import pprint

from bs4 import BeautifulSoup
import requests

BREAKFAST = 'Breakfast'
LUNCH = 'Lunch'
DINNER = 'Dinner'

COLLINS = 'Collins'

HALL_URL = {
    COLLINS: 'https://collins-cmc.cafebonappetit.com/cafe/collins/',
}

def extract_meals(raw_html):
    meals = {}
    meals[BREAKFAST] = raw_html.find('section', {'id': 'breakfast'})
    meals[LUNCH] = raw_html.find('section', {'id': 'lunch'})
    meals[DINNER] = raw_html.find('section', {'id': 'dinner'})
    return meals

def extract_stations(raw_html):
    stations = {}
    all_stations = raw_html.find_all('div', {'class': 'station-title-inline-block'})
    for station in all_stations:
        name = station.find('h3').get_text()
        stations[name] = station
    return stations

def extract_specials(raw_html):
    all_specials = raw_html.find_all('button', {'class': 'h4 site-panel__daypart-item-title'})
    return list(map((lambda x: x.get_text(strip=True)), all_specials))

if __name__ == "__main__":
    r = requests.get(HALL_URL[COLLINS])
    soup = None
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
    else:
        "connection did not work"