from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import bs4
import json
import mysql.connector

db = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = '',
    database = 'skraped'
)

query = db.cursor()

#query.execute("CREATE DATABASE scappedweather")
#query.execute("CREATE TABLE customers (name VARCHAR(255))")


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
forcast_label = target.find_all('div', class_='forecast-label')
# Create a list of forcast label
for l in forcast_label:
    #print(l.get_text())
    text_forcast_label.append(l.get_text())
    
text_forcast_text = []
forcast_text = target.find_all('div', class_='forecast-text')
# Create a list of forcast text
for t in forcast_text:
    #print(t.get_text())
    text_forcast_text.append(t.get_text())


#detailed_forcast = {}
detailed_forcast = []

for fl in text_forcast_label:
    for ft in text_forcast_text:
        if text_forcast_label.index(fl) == text_forcast_text.index(ft):
            #detailed_forcast[fl] = ft
            detailed_forcast.append([fl, ft])

#print(detailed_forcast)


current_conditions_html = html.find(id='current-conditions')
#print(current_conditions_html)


panel_heading = current_conditions_html.find('div', class_='panel-heading')
#print(panel_heading)

# Get panel header text
panel_header = panel_heading.find('b')
panel_header = panel_header.get_text()
#print(panel_header)


# Get panel title text
panel_header_title = panel_heading.find(class_='panel-title')
panel_header_title = panel_header_title.get_text()
#print(panel_header_title)


# This section gets the coordinates
coordinates = {}
panel_header_title_small_text = panel_heading.find(class_='smallTxt')
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


current_conditions_summary = {}
current_conditions_summary_html = html.find(id='current_conditions-summary')

#print(current_conditions_summary_html)

image = current_conditions_summary_html.find('img')
image_src = 'https://forecast.weather.gov/' + image['src']

current_conditions_summary['image_src'] = image_src

paragraphs = current_conditions_summary_html.findAll('p')
for p in paragraphs:
    #print(p.get_text())
    #current_conditions_summary[p] = p.get_text()
    item = p.get_text()
    if item == 'Overcast':
        current_conditions_summary['mini_title'] = item
        #print(item)
    else:
        #print(item[-1:])
        if item[-1:] == 'F':
            current_conditions_summary['Fahrenheit'] = item
        elif item[-1:] == 'C':
            current_conditions_summary['Celsius'] = item
        
    

current_conditions_detail = {}
current_conditions_detail_html = html.find(id='current_conditions_detail')
table_rows = current_conditions_detail_html.findAll('tr')

#print(table_rows)
title = []
body = []
for tr in table_rows:
    tit = tr.find('b')
    title.append(tit.get_text())
    
    bod = tr.findAll('td')
    for b in bod:
        if(b.has_attr('class')):
            print()
        else:
            for td in b:
                body.append(td.replace('\n','').strip())
    
#print(title)

for t in title:
    for b in body:
        if title.index(t) == body.index(b):
            current_conditions_detail[t] = b


#print(current_conditions_detail)

full_report = {}
full_report['panel_header'] = panel_header
full_report['panel_header_title'] = panel_header_title
full_report['coordinates'] = coordinates
full_report['current_conditions_summary'] = current_conditions_summary
full_report['current_conditions_detail'] = current_conditions_detail
full_report['detailed_forcast'] = detailed_forcast

# convert the report to json. This is pointless for now, I only used it to make sure my dictionary is well formed
# full_report_json = json.dumps(full_report)
# print(full_report_json)

#print(full_report)

query.execute("SELECT COUNT(panel_header_title) FROM weathers WHERE panel_header_title = panel_header_title")
rowcount = query.fetchone()[0]

if rowcount == 0:
    sql = "INSERT INTO weathers (panel_header, panel_header_title, coordinates, current_conditions_summary, current_conditions_detail, detailed_forcast) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (panel_header, panel_header_title, str(coordinates), str(current_conditions_summary), str(current_conditions_detail), str(detailed_forcast))
    query.execute(sql, val)

    
    db.commit()
    print('Data saved to db!')
else:
    #update
    query.execute("SELECT * FROM weathers WHERE panel_header_title = panel_header_title")
    
    myresult = query.fetchone()[0]
    #print(myresult[2])
    sql = "UPDATE weathers SET panel_header = %s, panel_header_title = %s, coordinates = %s, current_conditions_summary = %s, current_conditions_detail = %s, detailed_forcast = %s WHERE panel_header_title = %s"
    val = (panel_header, panel_header_title, str(coordinates), str(current_conditions_summary), str(current_conditions_detail), str(detailed_forcast), panel_header_title)
    
    query.execute(sql, val)
    
    db.commit()
    print('Data updated!')
    