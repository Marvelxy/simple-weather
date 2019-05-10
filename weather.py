from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import bs4
import json

def simple_get(url):
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return(resp.status_code == 200 and content_type is not None and content_type.find('html') > -1)

def log_error(e):
    print(e)
    
    
raw_html = simple_get('https://forecast.weather.gov/MapClick.php?lat=42.3587&lon=-71.0567')

html = BeautifulSoup(raw_html, 'html.parser')
target = html.find(id='detailed-forecast-body')

#print(html)

text_forcast_label = []
forcast_label = target.find_all('div', class_='forecast-label');
# Create a list of forcast label
for l in forcast_label:
    #print(l.get_text())
    text_forcast_label.append(l.get_text())
    
text_forcast_text = []
forcast_text = target.find_all('div', class_='forecast-text');
# Create a list of forcast text
for t in forcast_text:
    #print(t.get_text())
    text_forcast_text.append(t.get_text())


detailed_forcast = {}

for fl in text_forcast_label:
    for ft in text_forcast_text:
        if text_forcast_label.index(fl) == text_forcast_text.index(ft):
            detailed_forcast[fl] = ft

#print(detailed_forcast)


current_conditions_html = html.find(id='current-conditions')
#print(current_conditions_html)


panel_heading = current_conditions_html.find('div', class_='panel-heading');
#print(panel_heading)

# Get panel header text
panel_header = panel_heading.find('b');
panel_header = panel_header.get_text()
#print(panel_header)


# Get panel title text
panel_header_title = panel_heading.find(class_='panel-title');
panel_header_title = panel_header_title.get_text()
#print(panel_header_title)


# This section gets the coordinates
coordinates = {}
panel_header_title_small_text = panel_heading.find(class_='smallTxt');
for st in panel_header_title_small_text:
    #current_key = ''
    if isinstance(st, bs4.element.Tag):
        loc = st.get_text()
        #print(loc)
        current_key = loc.replace(':\xa0','')
    else:
        #print(st)
        coordinates[current_key] = st

#print(coordinates)


full_report = {}
full_report['panel_header'] = panel_header
full_report['panel_header_title'] = panel_header_title
full_report['coordinates'] = coordinates
full_report['detailed_forcast'] = detailed_forcast

#full_report_json = json.dumps(full_report)
#print(full_report_json)

#print(full_report)