# coding=utf-8
## 507_waiver.py
## Skeleton for the 507 Waiver Test, Summer 2019
## ~~~ modify this file, but don't rename it ~~~

from urllib.request import urlopen
import re
from bs4 import BeautifulSoup
from distutils.filelist import findall
# regular the IO
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import plotly.plotly as py
import plotly.graph_objs as go
from plotly.offline import plot

import pandas as pd

import plotly.plotly as py
import plotly.graph_objs as go

import json
import urllib

from secrets import google_places_key

mapbox_access_token = 'your token here'

google_api = 'your api here'



## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NationalSite():
    def __init__(self, type, name, desc, url=None):
        self.type = type
        self.name = name
        self.description = desc
        self.url = url

        # needs to be changed, obviously
        self.address_street = '123 Main St.'
        self.address_city = 'Smallville'
        self.address_state = 'KS'
        self.address_zip = '11111'

    def __str__(self):
        return self.name + ' (' + self.type + '): ' + self.address_street + ', ' + self.address_city + ', ' + self.address_state + ' ' + self.address_zip

## you can, and should add to and modify this class any way you see fit
## you can add attributes and modify the __init__ parameters,
##   as long as tests still pass
##
## the starter code is here just to make the tests run (and fail)
class NearbyPlace():
    def __init__(self, name, lat=None, lng=None, has_gps=False):
        self.name = name
        self.lat = lat
        self.lng = lng
        self.has_gps = has_gps
    def __str__(self):
        return self.name

## Helping functions
## accept string, return [lat, lng] in string
def get_location(placename):
    place_name = placename.replace(" ", "+")
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=' + place_name + '&inputtype=textquery&fields=formatted_address,name,geometry&key=' + google_api

    place_content = urllib.request.urlopen(url).read().decode('ascii','ignore')

    #if not found
    if "ZERO_RESULTS" in place_content:
        return []
    
    content = json.loads(place_content)
    candidates = content['candidates']
    geometry = candidates[0]['geometry']
    result = []

    #if no location, no lat, no lng
    if 'location' in geometry:
        location = geometry['location']
        if 'lat' in location:
            if 'lng' in location:
                result.append(str(location['lat']))
                result.append(str(location['lng']))
        
    return result


## Must return the list of NationalSites for the specified state
## param: the 2-letter state abbreviation, lowercase
##        (OK to make it work for uppercase too)
## returns: all of the NationalSites
##        (e.g., National Parks, National Heritage Sites, etc.) that are listed
##        for the state at nps.gov
def get_sites_for_state(state_abbr):
    national_sites=[]
    page = urlopen('https://www.nps.gov/state/'+ state_abbr+'/index.htm')
    contents = page.read().decode('ascii','ignore')
    # print(contents)
    soup = BeautifulSoup(contents, "lxml")
    for tag in soup.find_all('li', class_='clearfix'):
        if tag==None or tag.find('a')==None or tag.find('h2')==None or tag.find('p')==None :
            continue
        #print(tag)

        m_name = tag.find('a').get_text().replace("\n","").rstrip()
        m_type = tag.find('h2').get_text().replace("\n","").rstrip()
        m_description = tag.find('p').get_text().replace("\n","").rstrip()

        m_li = tag.find('a').get('href').rstrip()

        ns = NationalSite(m_type, m_name, m_description, m_li)
        #print(m_li)
        m_url = urlopen('https://www.nps.gov'+ m_li + 'index.htm')
        deep_page_content = m_url.read()
        deep_soup = BeautifulSoup(deep_page_content, "lxml")

        #deep_tag = deep_soup.find('p', class_='adr')
        ns.address_street = deep_soup.find('span', class_='street-address').get_text().replace("\n","").rstrip()
        ns.address_city = deep_soup.find('span', itemprop='addressLocality').get_text().replace("\n","").rstrip()
        ns.address_state = deep_soup.find('span', class_='region').get_text().replace("\n","").rstrip()
        ns.address_zip = deep_soup.find('span', class_='postal-code').get_text().replace("\n","").rstrip()

        national_sites.append(ns)
        #print(ns)
    return national_sites


## Must return the list of NearbyPlaces for the specifite NationalSite
## param: a NationalSite object
## returns: a list of NearbyPlaces within 10km of the given site
##          if the site is not found by a Google Places search, this should
##          return an empty list
def get_nearby_places_for_site(national_site):
    search_name = national_site.name + ' ' + national_site.type
    ns_location = get_location(search_name)
    #if empty
    if len(ns_location) == 0:
        return []
    
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=' + ns_location[0] + ',' + ns_location[1] + '&radius=10000&key=' + google_api

    place_content = urllib.request.urlopen(url).read().decode('ascii','ignore')

    #if not found
    if "ZERO_RESULTS" in place_content:
        return []   

    content = json.loads(place_content)
    nearby_results = content['results'] #a list

    nearby_places = []
    for i in nearby_results:
        name = i['name']
        nearbyplace = NearbyPlace(name)
        #check if have result
        if 'geometry' in i:
            geo = i['geometry']
            if 'location' in geo:
                location = geo['location']
                if 'lat' in location:
                    nearbyplace.lat = str(location['lat'])
                    if 'lng' in location:
                        nearbyplace.lng = str(location['lng'])
                        nearbyplace.has_gps = True
        
        nearby_places.append(nearbyplace)

    return nearby_places

## Must plot all of the NationalSites listed for the state on nps.gov
## Note that some NationalSites might actually be located outside the state.
## If any NationalSites are not found by the Google Places API they should
##  be ignored.
## param: the 2-letter state abbreviation
## returns: nothing
## side effects: launches page with the map in the web browser
def plot_sites_for_state(state_abbr):
    state_sites = get_sites_for_state(state_abbr)
    m_lat = []
    m_lng = []
    m_text = []
    center_lat = 0
    center_lng = 0

    #prepare the data
    for i in state_sites:
        location = get_location(i.name)
        if len(location) != 0:
            center_lat = center_lat + float(location[0])
            center_lng = center_lng + float(location[1])
            m_lat.append(location[0])
            m_lng.append(location[1])
            m_text.append(i.name)
        
    data = [
        go.Scattermapbox(lat = m_lat, lon = m_lng, mode='markers',
        marker=go.scattermapbox.Marker(
            size=9,
            color = 'black'
        ),
        text = m_text,
        )
    ]

    #calculate the center
    center_lat = center_lat / len(m_lat)
    center_lng = center_lng / len(m_lng)

    layout = go.Layout(
    autosize=True,
    hovermode='closest',
    mapbox=go.layout.Mapbox(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=go.layout.mapbox.Center(
            lat=center_lat,
            lon=center_lng
        ),
        pitch=0,
        zoom=5  #need to adjust
    ),
    )

    fig = go.Figure(data=data, layout=layout)
    plot(fig, filename='National_Sites.html')
    pass


## Must plot up to 20 of the NearbyPlaces found using the Google Places API
## param: the NationalSite around which to search
## returns: nothing
## side effects: launches a page with the map in the web browser
def plot_nearby_for_site(site_object):
    site_location = get_location(site_object.name)
    #handle error
    if len(site_location) == 0:
        print('We can not find the GPS of the site')
    else:
        nearby_places = get_nearby_places_for_site(site_object)
        nearby_lat = []
        nearby_lng = []
        nearby_text = []
        for i in nearby_places:
            #suppose have given lat and lng
            if i.has_gps == True:
                nearby_lat.append(i.lat)
                nearby_lng.append(i.lng)
                nearby_text.append(i.name.encode('ascii','ignore').decode())
            
            #suppose has not given
            #i_l = get_location(i.name)
            #if len(i_l) != 0:
            #    nearby_lat.append(i_l[0])
            #    nearby_lng.append(i_l[1])
            #    nearby_text.append(i.name)
        
        data = [
            go.Scattermapbox(lat = nearby_lat, lon = nearby_lng, mode='markers',
                marker=go.scattermapbox.Marker(
                    size=9,
                    color = 'black'
                ),
                text = nearby_text,
            ),

            go.Scattermapbox(
                lat=[site_location[0]],
                lon=[site_location[1]],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=20,
                    color = 'red'
                ),
                text=[site_object.name.encode('ascii','ignore').decode()],
            )
            ]

        #calculate center
        center_lat = float(site_location[0])
        center_lng = float(site_location[1])
        for i in nearby_lat:
            center_lat = center_lat + float(i)
        for i in nearby_lng:
            center_lng = center_lng + float(i)
        center_lat = center_lat / (len(nearby_lat) + 1)
        center_lng = center_lng / (len(nearby_lng) + 1)

        layout = go.Layout(
            autosize=True,
            hovermode='closest',
            mapbox=go.layout.Mapbox(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat=center_lat,
                    lon=center_lng
                ),
                pitch=0,
                zoom=11  #need to adjust
            ),
        )

        
        fig = go.Figure(data=data, layout=layout)
        plot(fig, filename='Nearby_Places.html')

    pass




def main():
    national_sites = []
    nearby_places = []
    last = ''
    abbr = ''
    count = ''

    while True:
        u_input = input("Please input the command: ")
        split_input = u_input.split()

        if split_input[0] == 'list':
            national_sites = get_sites_for_state(split_input[1])
            for i in national_sites:
                print(i)
            last = 'list'
            abbr = split_input[1]
        
        if split_input[0] == 'nearby' and last == 'list':
            nearby_places = get_nearby_places_for_site( national_sites[int(split_input[1]) - 1])
            for i in nearby_places:
                print(i)
            last = 'nearby'
            count = split_input[1]
        
        if split_input[0] == 'map' and (last == 'list' or last == 'nearby'):
            if last == 'list':
                plot_sites_for_state(abbr)
            if last == 'nearby':
                plot_nearby_for_site(national_sites[int(count) - 1])

        if split_input[0] == 'exit':
            break
        
        if split_input[0] == 'help':
            print('list <stateabbr>')
            print('\tavailable anytime')
            print('\tlists all National Sites in a state')
            print('\tvalid inputs: a two-letter state abbreviation')
            print('nearby <result_number>')
            print('\tavailable only if there is an active result set')
            print('\tlists all Places nearby a given result')
            print('\tvalid inputs: an integer 1-len(result_set_size)')
            print('map')
            print('\tavailable only if there is an active result set')
            print('\tdisplays the current results on a map')
            print('exit')
            print('\texits the program')
            print('help')
            print('\tlists available commands (these instructions)')


if __name__ == '__main__':
    main()