from datetime import datetime
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup, SoupStrainer

if __name__ == "__main__":
	patterns = "*"
	ignore_patterns = ""
	ignore_directories = False
	case_sensitive = True
	my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)


scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sheets = client.open("Vehicle_Info").sheet1
row1 = ['Date', ' ', 'Time', ' ', 'Name', ' ', 'Plate no.', ' ', 'Brand', ' ', 'Color']

if sheets.row_values(1) != row1:
	sheets.insert_row(row1, 1)

def on_modified(event):
	try:
		if event.src_path != '.':
			home_url = 'https://parivahan.gov.in/rcdlstatus/'
			post_url = 'https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml'
			
			r = requests.get(url=home_url)
			cookies = r.cookies
			soup = BeautifulSoup(r.text, 'html.parser')
			viewstate = soup.select('input[name="javax.faces.ViewState"]')[0]['value']
			button = soup.find("button", {"type" : "submit"})
			
			data2 = json.loads(open('vehicle_info.json').read())
			first = str(data2['results'][0]['plate'])[0:6]
			second = str(data2['results'][0]['plate'])[6:]
			
			data = {
				'javax.faces.partial.ajax':'true',
				'javax.faces.source': button['id'],
				'javax.faces.partial.execute':'@all',
				'javax.faces.partial.render': 'form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl',
				 button['id']:button['id'],
				'form_rcdl':'form_rcdl',
				'form_rcdl:tf_reg_no1': first,
				'form_rcdl:tf_reg_no2': second,
				'javax.faces.ViewState': viewstate,
			}

			r = requests.post(url=post_url, data=data, cookies=cookies)
			soup = BeautifulSoup(r.text, 'html.parser')
			table = SoupStrainer('tr')
			soup = BeautifulSoup(soup.get_text(), 'html.parser', parse_only=table)

			data1 = list(map(str, soup.get_text().split('\n')))			
			now = datetime.now()
			d = {'time' : str(now)}
			
			row2 = [d['time'][0:9], ' ', d['time'][10:16], ' ', data1[12], ' ', data2['results'][0]['plate'], ' ', data2['results'][0]['vehicle']['make_model'][0]['name'], ' ', data2['results'][0]['vehicle']['color'][0]['name']]
			sheets.insert_row(row2, 2)
			
		else:
			pass
		
	except IndexError or KeyError or TypeError:
		pass	

my_event_handler.on_modified = on_modified




path = "."
go_recursively = False
my_observer = Observer()
my_observer.schedule(my_event_handler, path, recursive=go_recursively)

my_observer.start()

try:
	while True:
		time.sleep(10)
except KeyboardInterrupt:
	my_observer.stop()
	my_observer.join()

