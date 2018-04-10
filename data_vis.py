#!/usr/bin/env python

#This is the script you actually run. It will feed the preprocessed data into folium base map and plot the data onto an interactive map.
#The resulting map will be saved into a html page in the current directory.

import folium
import branca
import branca.colormap as cm
from data_preprocess import DataPreprocess

data_manip = DataPreprocess("./data/")
election = data_manip.preprocess_pres_elec()
soybeans = data_manip.preprocess_soybeans()
senate_parties = data_manip.preprocess_senate()
house_fips, cd113_json = data_manip.preprocess_house()
county_geo, county_geo_1, state_geo = data_manip.geo_files()

#Create a base map
m = folium.Map(location=[40, -102], zoom_start=4, tiles="cartodbpositron")

#Add a TopoJson layer to the map for 2016 presidential election
colorscale_election = branca.colormap.linear.RdBu.scale(0,1)
election_series = election.set_index("combined_fips")["per_dem"]
def style_function_election(feature):
    election_res = election_series.get(feature["id"][-5:], None)
    return {
        'fillOpacity': 1,
        'weight': 0.3,
        'color': 'black',
        'fillColor': 'white' if election_res is None else colorscale_election(election_res)
    }

folium.TopoJson(
    open(county_geo),
    "objects.us_counties_20m",
    name="2016 presidential election",
    style_function=style_function_election
).add_to(m)

#Add a GeoJson layer to the map for current US senate members
senate_series = senate_parties.set_index("state_code")["party"]
def senate_color_function(party):
    if party == -4:  #2 gop
        return 'red'
    elif party == 0: #1 gop 1 dem
        return '#712ccc'
    elif party == 4: #2 dem
        return 'blue'
    else:            #ind and gop/dem
        return '#d6b915'

def style_function_senate(feature):
    senate_par = senate_series.get(feature["id"], None)
    return {
        'fillOpacity': 1,
        'weight': 1,
        'color': 'white',
        'fillColor': '#black' if senate_par is None else senate_color_function(senate_par)
    }

folium.GeoJson(state_geo,
    name="2017 US senate",
    style_function=style_function_senate
).add_to(m)

#Add a TopoJson layer to the map for current US house members
house_series = house_fips.set_index(["state_district_fips"])["party"]

def house_color_function(party):
    if party == "republican":
        return "red"
    else:
        return "blue"

def style_function_house(feature):
    house_party  = house_series.get(feature["properties"]["CD113FP"], None)
    return {
        'fillOpacity': 1,
        'weight': 0.3,
        'color': 'black',
        'fillColor': 'black' if house_party is None else house_color_function(house_party)
    }

folium.TopoJson(
    cd113_json,
    "objects.cd113",
    name="2017 US house",
    style_function=style_function_house
).add_to(m)

#Add a TopoJson layer to the map for 2016 soybeans production
colorscale_soybeans = branca.colormap.linear.YlGn.scale(10000, 8000000)
soybean_series = soybeans.set_index("FIPS")["Value"]

step_colorscale_soybeans = colorscale_soybeans.to_step(n=7, data=[0, 10000, 250000, 750000, 2000000, 4000000, 8000000], round_method="int")

def style_function_soybeans(feature):
    soybean_prod = soybean_series.get(feature["id"][-5:], None)
    return {
        'fillOpacity': 0.6,
        'weight': 0.3,
        'color': 'black',
        'fillColor': 'white' if soybean_prod is None else step_colorscale_soybeans(soybean_prod)
    }

folium.TopoJson(
    open(county_geo),
    "objects.us_counties_20m",
    name="2016 soybean production",
    style_function=style_function_soybeans
).add_to(m)

folium.LayerControl().add_to(m)
m.save("map.html")
