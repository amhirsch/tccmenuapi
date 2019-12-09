import pprint
from typing import Any, Dict, List, Tuple, Union

from bs4 import BeautifulSoup
import requests

BREAKFAST = 'Breakfast'
LUNCH = 'Lunch'
DINNER = 'Dinner'

COLLINS = 'Collins'

HALL_URL = {
    COLLINS: 'https://collins-cmc.cafebonappetit.com/cafe/collins/',
}

def extract_meals(entire_page: BeautifulSoup) -> Dict[str, Tuple[str, Any]]:
    """Extracts all the meals for the day.

    Args:
        entire_page: A BeautifulSoupo representation of the dining hall index.html
    
    Returns:
        A dictionary whose keys are the meal names.
        Each entry contains a two element tuple with a string representation
        of the meal times and a BeautifulSoup tag for the daily specials.
    """
    meals = {}
    all_meals = entire_page.find_all('section', class_='site-panel--daypart')

    for meal in all_meals:
        name = meal.find('h2', class_='site-panel__daypart-panel-title').get_text(strip=True)
        time = meal.find('div', class_='site-panel__daypart-time').get_text(strip=True)
        # the specials will be listed first, so no need to check other tabs
        specials = meal.find('div', class_='site-panel__daypart-tab-content-inner')

        meals[name] = (time, specials)
    
    return meals


def extract_stations(daily_special) -> Dict[str, Any]:
    """Seperates a daily specials listing into the stations.

    Args:
        daily_special: A BeautifulSoup tag represenation of the daily specials.
    
    Returns:
        A dictionary whose keys are the serving stations for the dining hall.
        Note that any food item listed outside a station will be encapsulated into
            an 'other' station.
    """
    stations = {'other': []}
    current_div = daily_special.find('div')

    while current_div is not None:
        if current_div == '\n':
            pass
        else:
            if 'site-pannel__daypart-item' in current_div.attrs['class']:
                # a standalone item
                stations['other'] += [ current_div.find('button') ]
            elif 'station-title-inline-block' in current_div.attrs['class']:
                name = current_div.find('h3').get_text()
                stations[name] = current_div
        
        current_div = current_div.next_sibling

    # TODO make 'other' into an html tag to make it work in subsequent calls
    del stations['other']

    return stations


def extract_food_containers(anc_tag) -> List[Any]:
    """Extracts the tag with all the data for a given food.

    Args:
        anc_tag: A BeautifulSoup tag containing all desired foods.
            This can be an entire menu or just a station.
    
    Returns:
        A list of BeautifulSoup tags of food items.
    """
    all_buttons = anc_tag.find_all('div', {'class': 'site-panel__daypart-item-container'})
    return list(map( (lambda x: x), all_buttons ))


def extract_food_header(food_tag) -> Any:
    """Isolates the food header tag. This contains information such as food
        title and dietary notes.
    """
    return food_tag.find('button', {'class': 'h4 site-panel__daypart-item-title'})


def extract_food_title(food_tag) -> str:
    """Extracts the food's name"""
    food_header = extract_food_header(food_tag)
    return food_header.get_text(strip=True)


def extract_food_notes(food_tag) -> List[str]:
    """Extracts the notes for a given food item"""
    notes = []
    # notes are found as images
    current_img = food_tag.find('img')
    
    while current_img is not None:
        notes += [ current_img.attrs['title'].strip() ]
        current_img = current_img.next_sibling
    
    return notes


def extract_food_description(raw_html) -> str:
    """Isolates the description for a given food"""
    desc_div = raw_html.find('div', {'class': 'site-panel__daypart-item-description'})
    #TODO decide how to deal with multi line arguments

    if desc_div is None:
        return ''
    else:
        return desc_div.get_text(strip=True)
    

def generate_food_data(food_tag, note_map) -> Dict[str, Union[str, List[str]]]:
    """Organizes food data in an easy to view dictionary
    
    Args:
        food_tag: A BeautifulSoup tag containing the food item.
        note_map: A dictionary whose keys are the note descriptions (found in)
            the food_tag content and values are the quick reference for the note.
            See extract_note_mapping()
    
    Returns:
        A dictionary with the following keys:
            title: The food title
            notes: A list of notes provided by Cafe Bon Appetit
            details: Additonal information for the food. On the website this
                appears as a subtitle
    """

    title = extract_food_title(food_tag)
    notes_raw = extract_food_notes(food_tag)
    details = extract_food_description(food_tag)

    notes_key = []
    for note in notes_raw:
        if note in note_map:
            notes_key += [ note_map[note] ]
        else:
            notes_key += note

    return {'title': title, 'notes': notes_key, 'details': details}


def extract_note_mapping(entire_page):
    """Generates a mapping between the food note and the note key.
    
    The Cafe Bon Appetit menu html has food tags whose notes are represented as
        images. The text is the longer description, which is cumbersome to read.
        This function creates a mapping between the longer description, provided
        in a food item and a quick name.

    Args:
        entire_page: A BeautifulSoup representation of the menu html page.

    Returns:
        A dictionary whose keys are note descriptions and values are note titles. 
    """
    note_map = {}
    note_tag = entire_page.find_all('div', class_='site-panel__diet-pref-row')

    for tag in note_tag:
        title = tag.find('span', class_='site-panel__diet-pref-header-inner').get_text(strip=True)
        description = tag.find('div', class_='site-panel__diet-pref-acc-content').get_text(strip=True)
        note_map[description] = title
    
    return note_map


def parse_station_menu(station_tag, notes_map):
    """Parses a station into a Python data format
    
    Args:
        station_tag: A BeautifulSoup tag with the station information.
        notes_map: A dictionary mapping between note descriptions and
            note titles.
    
    Returns:
        A list whose elements are the food data station's offerings.
        See generate_food_data().
    """
    return [generate_food_data(x, notes_map) for x in extract_food_containers(station_tag)]


def parse_menu(entire_page):
    """Parses the entire menu into a Python data structure.
    
    Args:
        entire_page: A BeautifulSoup representaion of the menu html
    
    Returns:
        A dictionary whose keys are meals, with subsequent dictonaries are 
        stations, then a list of food offerings.
    """    
    menu = {}
    all_meals = extract_meals(entire_page)
    notes_map = extract_note_mapping(entire_page)

    for meal in all_meals:
        meal_stations = extract_stations(all_meals[meal][1])
        station_sub_menu = {}

        for station in meal_stations:
            station_sub_menu[station] = parse_station_menu(meal_stations[station], notes_map)
        
        menu[meal] = station_sub_menu

    return menu            


if __name__ == "__main__":
    soup = None

    # r = requests.get(HALL_URL[COLLINS] + '2019-12-09/')
    # if r.status_code == 200:
    #     soup = BeautifulSoup(r.text, 'html.parser')
    #     meals = extract_meals(soup)
    #     dinner = meals[DINNER]
    # else:
    #     "connection did not work"

    with open('collins-2019-12-09.html') as f:
        soup = BeautifulSoup(f, 'html.parser')

    parsed = parse_menu(soup)