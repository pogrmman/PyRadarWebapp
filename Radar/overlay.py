from PIL import Image
import PIL.ImageOps
import argparse
import urllib.request
import os

parser = argparse.ArgumentParser(description="Generate an overlay for a new radar station")
parser.add_argument("station", metavar="station", type=str, help="NOAA Code for the radar station")
args = parser.parse_args()
station = args.station
urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/Cities/Short/" + station + "_City_Short.gif", "city.gif")
urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/County/Short/" + station + "_County_Short.gif", "county.gif")
urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/Highways/Short/" + station + "_Highways_Short.gif", "highways.gif")
urllib.request.urlretrieve("http://radar.weather.gov/ridge/Overlays/RangeRings/Short/" + station + "_RangeRing_Short.gif", "ring.gif")
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
highways.paste(county,(0,0),county)
highways.paste(ring,(0,0),ring)
highways.paste(city,(0,0),city)
highways.save("static/Overlay_" + station + ".png")
os.remove("city.gif")
os.remove("county.gif")
os.remove("highways.gif")
os.remove("ring.gif")
