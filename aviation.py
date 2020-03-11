#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from math import radians, degrees, sin, cos, asin, acos, sqrt
"""
Created on Sun Dec  8 09:16:59 2019

@author: turki
"""
# riyadh id: 7113
import requests
import json
import numpy as np
# In[1] API calls


def get_indices_by_id(city_id):
    return json.loads(requests.get('http://www.numbeo.com:8008/api/indices?api_key=KEY&city_id='+city_id).text)


def get_close_cities(city_id, distance):
    return json.loads(requests.get('http://www.numbeo.com:8008/api/close_cities_with_prices?api_key=KEY&max_distance='+distance+'&query=riyadh').text)


# In[2] Calculate distance


def distance(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    return 6371 * (
        acos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2))
    )


# In[3] get list of dict that represent cities (country, city, lat, long, city_id)
r = requests.get(
    'http://www.numbeo.com:8008/api/cities?api_key=KEY')
cities = json.loads(r.text)
with open('cities.json', 'w') as file:
    json.dump(json.loads(r.text), file, ensure_ascii=False, indent=2)

# In[4] read from written file, instead of making api call
cities = json.loads(open('cities.json', 'r').read())['cities']

# In[5] test city indices on Riyadh(7113)

#x = get_indices_by_id('7113')
near_cities = get_close_cities('7113', '10000')['cities']

# In[6] search dict via generator, test distance function
riyadh = next(city for city in cities if city['city_id'] == 7113)
di = distance(riyadh['longitude'], riyadh['latitude'],  -0.2907496, 27.8756137)

# In[7] add "distance from riyadh" attribute to all cities
for city in cities:
    keys = city.keys()
    if 'latitude' in keys and 'longitude' in keys:
        city['distance_from_riyadh'] = distance(
            riyadh['longitude'], riyadh['latitude'], city['longitude'], city['latitude'],)

# In[8] group cities that are within a particular distance from Riyadh
near_cities = []
treshold = 4000
for city in cities:
    if 'distance_from_riyadh' in city.keys() and city['distance_from_riyadh'] <= treshold:
        near_cities.append(city)
# In[9] get the indices for citites within the threshold
near_cities_indiceses = []
for city in near_cities:
    temp = get_indices_by_id(str(city['city_id']))
    near_cities_indiceses.append(temp)

# In[10] apply the formula
scored_cities = []
#near_cities_indiceses = json.loads(open('scrored_citites_4000_with_qol_30c_min.json', 'r').read())

# values we will use in the formula
keys_list = ['cpi_index', 'groceries_index', 'rent_index', 'restaurant_price_index',
             'safety_index', 'traffic_index', 'quality_of_life_index']
for city in near_cities_indiceses:
    keys = city.keys()
    # check if all the values are in the cities' keys list
    if all(k in keys for k in keys_list):
        # sum the contributors
        contr = city['contributors_cost_of_living'] + \
            city['contributors_healthcare']+city['contributors_traffic']
        + city['contributors_pollution'] + \
            city['contributors_crime']+city['contributors_property']
        if contr > 30:
            # apply the formula
            city['score'] = (city['safety_index']*1.8 + city['quality_of_life_index'])/(city['cpi_index']*1.5 + city['groceries_index']*0.5 +
                                                                                        city['rent_index']*1.1 + city['traffic_index'] + city['restaurant_price_index']*0.8)
            scored_cities.append(city)
# In[11] sort by score and write to file
c = sorted(scored_cities, key=lambda x: x['score'], reverse=True)
with open('scrored_citites_4000_with_qol_30c_min_w1.json', 'w') as file:
    json.dump(c, file, ensure_ascii=False, indent=2)

# In[12] write a shoreted version of scored citites to file
short_scrored_citites = []
for city in c:
    short_scrored_citites.append(
        {'name': city['name'], 'score': city['score'], 'distance': city['distance_from_riyadh']})
with open('short_scrored_citites_4000_with_qol_30c_min_w1.json', 'w') as file:
    json.dump(short_scrored_citites, file, ensure_ascii=False, indent=2)

# In[13] add dinstance
for entry in near_cities_indiceses:
    # some entiries have more than one comma, the last is always the country, everything else is the city
    temp = entry['name'].split(',')
    if len(temp) > 2:
        city, country = ''.join(temp[0:-1]), temp[-1]
    else:
        city, country = temp[0], temp[1]
#    print(city, country)
    for c in near_cities:
        if c['city'] == city:
            #            print(c['distance_from_riyadh'])
            entry['distance_from_riyadh'] = round(c['distance_from_riyadh'], 2)

# In[14]
#temp_near_cities = json.loads(open('short_scrored_citites_4000_with_qol_30c_min.json', 'r').read())
temp_near_citites_indices = c
for city_ in temp_near_cities:
    if 'rating' in city_.keys():
        t = next(city for city in temp_near_citites_indices if city_[
                 'name'] == city['name'])
        t['rating'] = city_['rating']
        t['total_number_of_photos'] = city_['total_number_of_photos']
# In[15]
hamad = json.loads(
    open('short_scrored_citites_4000_with_qol_30c_min.json', 'r').read())
for key, i in zip(hamad, enumerate(hamad)):
    if 'rating' not in key.keys():
        last_entry = i[0]
        break
hamad = hamad[:last_entry]
# In[16]
avg_stars = []
avg_reviews = []
avg_photos = []
for key in hamad:
    avg_stars.append(key['rating']['stars'])
    avg_reviews.append(key['rating']['reviews'])
    avg_photos.append(key['total_number_of_photos'])
print(np.mean(avg_stars), np.mean(avg_reviews),  np.mean(avg_photos))
# In[17] remove outliers


def is_outlier(data, mean, std, m=2):
    return abs(data - mean < m * std)


temp_lists = [avg_stars, avg_reviews, avg_photos]
for list_ in temp_lists:
    temp_mean = np.mean(list_)
    temp_std = np.std(list_)
    for element in list_:
        if not is_outlier(element, temp_mean, temp_std):
            list_.remove(element)
    print(np.mean(list_))


# In[18] Remove Certificate of Excellence, unreliable metric
for key in hamad:
    if 'Certificate of Excellence' in key.keys():
        del key['Certificate of Excellence']
with open('top_45_4000km.json', 'w') as file:
    json.dump(hamad, file, ensure_ascii=False, indent=2)

# In[19] Prototype file
file = json.loads(
    open('scrored_citites_4000_with_qol_30c_min.json', 'r').read())
for city, i in zip(file, enumerate(range(45))):
    city['rating'] = hamad[i[0]]['rating']
    city['total_number_of_photos'] = hamad[i[0]]['total_number_of_photos']
    city['score'] = hamad[i[0]]['score']
with open('scrored_citites_4000_with_qol_30c_min_w3.json', 'w')as file_:
    json.dump(file[:45], file_, ensure_ascii=False, indent=2)

# In[20] percentiles: find min/max
keys_list = ['cpi_index', 'groceries_index', 'rent_index', 'restaurant_price_index',
             'safety_index', 'traffic_index', 'quality_of_life_index']
#data = json.loads(open('scrored_citites_4000_with_qol_30c_min_w3.json', 'r').read())
per_dict = dict()
for key in keys_list:
    per_dict[key] = {'max': data[0][key], 'min': data[0][key]}
for entry in data:
    #    for key in keys_list:
    #        per_dict[key]['max'] = data[0][key]
    #        per_dict[key]['min'] = data[0][key]
    for key in keys_list:
        if per_dict[key]['max'] < entry[key]:
            per_dict[key]['max'] = entry[key]
            print('max:', key, entry[key])
        elif per_dict[key]['min'] > entry[key]:
            per_dict[key]['min'] = entry[key]
            print('min:', key, entry[key])

# In[21] percentile: difference
for key in per_dict:
    per_dict[key]['dif'] = per_dict[key]['max'] - per_dict[key]['min']

# In[22] get the percentiles, write them in a file
file_name = "scrored_citites_4000_with_qol_30c_min_w3_percentile"

data = json.loads(
    open('scrored_citites_4000_with_qol_30c_min_w3.json', 'r').read())
new_data = list()
temp = dict()
for entry in data:
    temp['name'] = entry['name']

    for key in keys_list:
        temp[key] = round(
            (entry[key] - per_dict[key]['min'])/per_dict[key]['dif'], 2)
    new_data.append(temp)
    temp = dict()
with open(file_name+'.json', 'w')as file:
    json.dump(new_data, file, ensure_ascii=False, indent=2)
# In[23] CSV
headers = ",".join(list(new_data[0].keys())[1:])
with open('csv_data.csv', 'w') as file:
    file.write(headers + '\n')
    for entry in new_data:
        temp = list()
        for key in entry.keys():
            temp.append(entry[key])
    #    temp = ",".join(temp)
    #    print(str(temp)[1:-1])
        file.write(str(temp[1:])[1:-1] + '\n')
