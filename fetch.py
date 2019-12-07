import pprint
from typing import Any, Dict

from bs4 import BeautifulSoup
import requests

BREAKFAST = 'Breakfast'
LUNCH = 'Lunch'
DINNER = 'Dinner'

COLLINS = 'Collins'

HALL_URL = {
    COLLINS: 'https://collins-cmc.cafebonappetit.com/cafe/collins/',
}

def extract_meals(entire_page: BeautifulSoup) -> Dict[str, Any]:
    meals = {}
    breakfast_raw = entire_page.find('section', {'id': 'breakfast'})
    lunch_raw = entire_page.find('section', {'id': 'lunch'})
    dinner_raw = entire_page.find('section', {'id': 'dinner'})
    meals[BREAKFAST] = extract_specials(breakfast_raw)
    meals[LUNCH] = extract_specials(lunch_raw)
    meals[DINNER] = extract_specials(dinner_raw)
    return meals

def extract_specials(meal):
    # the specials will be listed first, so find() is acceptable
    special_section = meal.find('div', {'class': 'site-panel__daypart-tab-content'})
    # there is a single usable child, so extract this specifically
    return special_section.find('div', {'class': 'site-panel__daypart-tab-content-inner'})

def extract_stations(raw_html):
    stations = {}
    all_stations = raw_html.find_all('div', {'class': 'station-title-inline-block'})
    for station in all_stations:
        name = station.find('h3').get_text()
        stations[name] = station
    return stations

def extract_foods(raw_html):
    all_specials = raw_html.find_all('button', {'class': 'h4 site-panel__daypart-item-title'})
    return list(map((lambda x: x.get_text(strip=True)), all_specials))

if __name__ == "__main__":
    r = requests.get(HALL_URL[COLLINS])
    soup = None
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, 'html.parser')
        meals = extract_meals(soup)
        dinner = meals[DINNER]
    else:
        "connection did not work"