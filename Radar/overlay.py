##### Import Modules #####
#### Import Builtins ####
import urllib.request
import os
#### Import Pillow Modules ####
from PIL import Image
import PIL.ImageOps

##### Function Definitions ####
#### Make Radar Overlay ####
def make_overlay(station):
    """ Generate an overlay for a given radar station.
    
    Usage: make_overlay(station_id) """
    ### Fetch overlay components ###
    urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/Cities/Short/" + station + "_City_Short.gif", "city.gif")
    urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/County/Short/" + station + "_County_Short.gif", "county.gif")
    urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/Highways/Short/" + station + "_Highways_Short.gif", "highways.gif")
    urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/RangeRings/Short/" + station + "_RangeRing_Short.gif", "ring.gif")
    ### Open images ###
    ## Make white text black ##
    city = Image.open("city.gif")
    city = city.convert("RGBA")
    cityr,cityg,cityb,citya = city.split()
    cityrgb = Image.merge("RGB",(cityr,cityg,cityb))
    cityrgb = PIL.ImageOps.invert(cityrgb)
    cityr,cityg,cityb = cityrgb.split()
    city = Image.merge("RGBA",(cityr,cityg,cityb,citya))
    county = Image.open("county.gif")
    county = county.convert("RGBA")
    highways = Image.open("highways.gif")
    highways = highways.convert("RGBA")
    ring = Image.open("ring.gif")
    ring = ring.convert("RGBA")
    ### Merge images and save ###
    highways.paste(county,(0,0),county)
    highways.paste(ring,(0,0),ring)
    highways.paste(city,(0,0),city)
    highways.save("static/Overlay_" + station + ".png")
    # I should probably close image files somewhere along here...
    ### Delete image components ###
    os.remove("city.gif")
    os.remove("county.gif")
    os.remove("highways.gif")
    os.remove("ring.gif")
