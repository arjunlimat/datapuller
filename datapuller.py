# -*- coding: utf-8 -*-
"""
Created on Fri Sep 9 12:18:43 2022

@author: Tamilselvan Arjunan
"""
import requests
from bs4 import BeautifulSoup
import json
import re
import csv
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import locationtagger
from tldextract import extract
#https://landscapedevelopment.com/contact/
#https://www.marianilandscape.com/where-we-are/
#https://www.junipercares.com/
#https://www.yellowstonelandscape.com/locations
#https://gothiclandscape.com/
urls = ['https://www.ruppertlandscape.com/branches/']



#Generate output file 
def csvwriter(to_csv):
    filename = "output.csv"
    fields =  ["Parent Company", "Sub-Brand (if relevant)", 
     "Branch Type (If relevant)", "Street", "City", "State", "Zip Code", "Other Comments", "Link"]
    with open(filename, 'w', newline = '') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(to_csv)
#get the preprocessed names
def get_options(scrambled, flag, totals, last):
    dictionary = [i.strip('\n') for i in open('the_file.txt')]
    if flag:
        return totals
    else:
        new_list = [i for i in dictionary if scrambled.startswith(i)]
        if new_list:
            possible_word = new_list[-1]
            new_totals = totals
            new_totals.append(possible_word)
            new_scrambled = scrambled[len(possible_word):]
            return get_options(new_scrambled, False, new_totals, possible_word)
        else:
            return get_options("", True, totals, '')

#create treee structure to process the input urls
#https://www.marianilandscape.com/where-we-are/
def child_tree1(url, soup):
    to_csv = []
    pattern = re.compile(':(\[.*?\}\])')
    try:
        for script in soup.find_all('script',  {"type": "text/javascript"}):
            if len(script.contents) > 0:
                if 'address' in script.contents[0]:
                    match = pattern.search(script.string)
                    if match is not None:
                        result = json.loads(match.groups()[0])
        for d in result:
            sample_text = d['address']
            us_zip = r'(\d{5}\-?\d{0,4})'
            zip_code = re.search(us_zip, sample_text)
            zip_code = zip_code.group(1)
            place_entity = locationtagger.find_locations(text = sample_text)
            sample_text = sample_text.replace(zip_code, "")
            sample_text = sample_text.replace(", ,", ",")
            if sample_text[-2].endswith(','):
                sample_text = sample_text[0:len(sample_text)-2]
            # extracting entities.
            csv_list = [td, d['title'], branches, sample_text, place_entity.cities[0],
                             list(place_entity.country_regions.values())[0][0], zip_code, d['email'],  url]
            to_csv.append(csv_list)
        return to_csv
    except:
         return -1
    
 #https://landscapedevelopment.com/contact/ 
def child_tree2(url, soup):
    to_csv = []
    try:
        for script in soup.find_all('script',  {"type": "application/ld+json"}):
            try:
                address = json.loads(script.text)
                result = address['address']
            except:
                pass
        for d in result:
            csv_list = [td.capitalize(), d['name'].capitalize(), branches, d['streetAddress'], d['addressLocality'],
                                    d['addressRegion'], d['postalCode'] , d['telephone'],  d["hasMap"]]
            to_csv.append(csv_list)
        return to_csv
    except:
        return -1
#https://www.yellowstonelandscape.com/locations
def child_tree3(url, soup):
    to_csv = []
    pattern = re.compile('(\[\{.*?\}\])')  
    try:     
        for script in soup.find_all("script", {"src":False}):
            if script:
                m = pattern.search(script.string)
                if m is not None:
                    result = json.loads(m.groups()[0])
           
        for d in result:
            csv_list = [td, "NA", branches, d['address'], d['city'],d['state'], d['zip'], d['phone'],  d['link']]
            to_csv.append(csv_list)
        return to_csv
    except:
        return -1

#https://www.junipercares.com/
def child_tree4(url, soup):
    to_csv = []
    pattern = re.compile('(\'.*?\')')
    if len(soup.find_all('script',  {"type": "text/javascript"})) == 0:
        return -1
    try:
        for script in soup.find_all('script',  {"type": "text/javascript"}):
            if script.string is None:
                continue
            try:
                match = pattern.search(script.string)
                var = match.groups()[0]
                result = var.replace('\\u003Cstrong\\u003E','').replace('\\u0020', ' ').replace('\\u003C\\/strong\\u003E\\u003Cbr\\u003E', ",").replace('u003Cbr\\u003E',",").replace('\\nPh\\u003A \\u0028', '').replace('\\u0029', '-').replace('\\', '').replace("u002D3", '-').replace('u002D5',  '').replace('u002D7' , '').replace('u002D6',  '')      
            except:
                continue
            if len(result) > 20:
                result =  result.replace(', ,', ',')
                result = result.split(',')
                us_zip = r'(\d{5}\-?\d{0,4})'
                zip_code = re.search(us_zip, result[3].strip())
                region = result[3].replace(zip_code.group(1), '')
                sub_branch = url.split('/')
                csv_list = [td, sub_branch[-1].replace('-', ' ').capitalize(), branches, result[1], result[2],
                region.strip(), zip_code.group(1), result[-1].replace("'", ''),  url]
                to_csv.append(csv_list)
                if len(to_csv) != 0:
                    return to_csv
        
                break
            
    except:
        return -1
#https://gothiclandscape.com/
def child_tree5(url, soup):
    to_csv = []
    link_site = []
    r = requests.get(url, verify = False)
    soup = BeautifulSoup(r.content, 'html.parser')
    for link in soup.find_all('a'):
        link  = link.get('href')
        if link is None:
            continue
        if 'branch' in link or 'location/' in link:
            if 'https' not in link:
                link = url + link
            link_site.append(link)
    link_site = list(set(link_site))
    for url in link_site:
        r = requests.get(url, verify = False)
        soup = BeautifulSoup(r.content, 'html.parser')
        if 'california' in url:
             place = ['col-24 c-py-9 border-top border-grey', 'col-24 c-py-9']
        else:
            place = ["col-lg-12 c-py-9", "col-lg-12 c-py-9 border-top border-grey border-lg-none"]
        for i in place:
            all_div = soup.find_all("div", class_ = i)
            for div in all_div:
                data = div.text.split('\n')
            result = []
            datastore = {}
            for i in data:
                if 'Landscape' in i:
                    sub_branch = i
                    continue
                if len(i) > 0:
                    if '.com' not in str(i):
                        datastore[i] = i
                    else:
                        datastore[i] = i
                        result.append(datastore)
                        datastore = {}
            for d in result:
                if 'arizona' in url or 'nevada' in url:
                    address = list(d.keys())[2]
                    address= address.split(',')
                    us_zip = r'(\d{5}\-?\d{0,4})'
                    zip_code = re.search(us_zip, address[-1])
                    phone = list(d.keys())[3].replace('Phone: ', '')
                    state = address[-1].replace(zip_code.group(1), '').strip()
                    csv_list = [td.capitalize(), sub_branch.capitalize(), branches.capitalize(), address[0], list(d.keys())[1],
                                                    state, zip_code.group(1), phone.replace('Management Contact:', ''),  url]
                    to_csv.append(csv_list)
                else:
                    address=list(d.keys())[3]
                    address= address.split(',')
                    us_zip = r'(\d{5}\-?\d{0,4})'
                    zip_code = re.search(us_zip, address[-1])
                    phone = list(d.keys())[4].replace('Phone: ', '').strip()
                    phone_tt = phone.replace('-', '')
                    if not phone_tt.isdigit():
                        phone = 'NA'
                    state = address[-1].replace(zip_code.group(1), '').strip()
                    csv_list = [td.capitalize(), sub_branch.capitalize(), branches.capitalize(), address[0], list(d.keys())[2],
                                                    state, zip_code.group(1), phone.replace('Management Contact:', ''),  url]
                    to_csv.append(csv_list)
                if len(d) > 10:
                    if 'arizona' in url or 'nevada' in url:
                        address=list(d.keys())[5]
                        address= address.split(',')
                        us_zip = r'(\d{5}\-?\d{0,4})'
                        zip_code = re.search(us_zip, address[-1])
                        phone = list(d.keys())[6].replace('Phone: ', '')
                        state = address[-1].replace(zip_code.group(1), '').strip()
                        csv_list = [td.capitalize(), sub_branch.capitalize(), branches.capitalize(), address[0], list(d.keys())[4],
                                                    state, zip_code.group(1), phone,  url]
                        to_csv.append(csv_list)
                    else:
                        
                        address=list(d.keys())[6]
                        address= address.split(',')
                        us_zip = r'(\d{5}\-?\d{0,4})'
                        zip_code = re.search(us_zip, address[-1])
                        phone = list(d.keys())[8].replace('Phone: ', '').strip()
                        phone_tt = phone.replace('-', '')
                        if not phone_tt.isdigit():
                            phone = 'NA'
                        state = address[-1].replace(zip_code.group(1), '').strip()
                        csv_list = [td.capitalize(), sub_branch.capitalize(), branches.capitalize(), address[0], list(d.keys())[5],
                                                    state, zip_code.group(1), phone,  url]
    
                        to_csv.append(csv_list)
    return to_csv
def maintree(url, soup):
    output = child_tree1(url, soup)
    if output == -1 :
        output = child_tree2(url, soup)
        if output == -1 :
            output = child_tree3(url, soup)
            if output == -1 :
                output = child_tree4(url, soup)
                if output == -1:
                    output = child_tree5(url, soup)
                    if output == -1:
                        pass
                    else:
                        return output
                else:
                    return output
            else:
                return output
        else:
           return output
          
    else:
        return output
to_csv = []
link_site = []
for given_url in urls:
    url = given_url
    if not given_url.endswith('locations') and given_url.endswith('com/'):
        if given_url[-1] != '/':
            given_url = given_url + '/locations'
        else:
            given_url = given_url + 'locations'
    r = requests.get(given_url, verify = False)
    if r.status_code != 200 and not 'contact' in url :
        r = requests.get(url, verify = False)
        soup = BeautifulSoup(r.content, 'html.parser')
        for link in soup.find_all('a'):
            link  = link.get('href')
            if link is None:
                continue
            if 'branch' in link or 'locations' in link:
                link = url + link
                link_site.append(link)
    soup = BeautifulSoup(r.content, 'html.parser')
    tsd, td, tsu = extract(url)
    td  = ' '.join(get_options(td, False, [], '')).capitalize()
    branch_type = ["maintenance", "installation", "enhancements", "irrigation", "snow-ice", 
                   "design", "construct", "commercial", "maintain", "landscape-construction", "landscape-management"
              "environmental-restoration", "sustainable-environments"]
    branch_type_string = "".join(branch_type)
    branches = ""
    for link in soup.find_all('a'):
        link  = link.get('href')
        if link is None:
            continue
        each_href = link.split('/')
        for href in each_href:
            if any(ext in href for ext in branch_type):
                before, sep, after = href.partition('?')
                before  = re.sub('[^A-Za-z0-9]+', ' ', before)
               # before  = ' '.join(get_options(before, False, [], ''))
                before = before.capitalize()
                if 'jpg' in before:
                    continue
                if 'com' in before:
                    if 'comm' in before:
                        pass
                    else:
                        continue
                branches= branches + before + ","
    branches = ','.join(set(branches.split(',')))[1:]
    link_site =list(set(link_site))
    csv_t = []
    if len(link_site) > 1:
        for url in link_site:
            r = requests.get(url, verify = False)
            soup = BeautifulSoup(r.content, 'html.parser')
            data = maintree(url, soup)
            if data is None:
                pass
            else:
                csv_t.append(data[0]) 
        to_csv.append(csv_t)
    else:
        data = maintree(url, soup)
        if data is None:
            pass
        else:
            to_csv.append(data)
print(to_csv)
output = csvwriter(to_csv[0])
