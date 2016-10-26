##### Import Modules #####
#### Import Builtins ####
import urllib.request
import glob
import os
#### Import Third-Party Modules ####
from lxml import etree
from PIL import Image
from images2gif import writeGif
### Import Flask Modules ###
from flask import Flask
from flask import request
from flask import render_template
#### Import Application Modules ####
import overlay

##### Class Definitions #####
#### Class for Communicating with weather.gov ####
class GetImgs(object):
    """ This class handles communication with the weather.gov site.
    
    This class provides the following methods:
    get_imgs_srcs, get_imgs, and get_name. """
    def __init__(self,station):
        """ Set url path and save path.
        
        Usage: __init__(station) """
        self.station = station
        self.warnings_url = "http://radar.weather.gov/ridge/Warnings/Short/" + station + "/"
        self.radar_url = "http://radar.weather.gov/ridge/RadarImg/N0R/" + station + "/"
        self.warnings_path = "static/warning_"
        self.radar_path = "static/radar_"
    def get_imgs_srcs(self,type,num):
        """ Find most recent image addresses.
        
        Usage: get_imgs_srcs(image_type, number_of_images)
        
        The image type is either "radar" or "warning". """
        # Should probably rewrite so it is tolerant of invalid station
        # Maybe fetch both warning and radar images in single pass? --> not necessarily good, you don't NEED warning images
        num += 1
        if type == "radar":
            url = self.radar_url
        elif type == "warnings":
            url = self.warnings_url
            num = num * 2
        html = urllib.request.urlopen(url)
        tree = etree.parse(html, etree.HTMLParser())
        imgs_srcs = []
        for element in tree.findall(".//table"): # The list of image urls is stored in a table from oldest to newest on that webpage
            table = element
        for i in range(len(table),len(table) - num,-1): # This actually gets the most recent links from that table
            for img_src in table[i-1].findall(".//a"):
                imgs_srcs.append(img_src.get("href"))
        if type == "radar": # Let image urls be accessable by other methods
            self.radar_srcs = imgs_srcs
        elif type == "warnings":
            self.warnings_srcs = imgs_srcs[1:-1:2]
    def get_imgs(self):
        """ Download the most recent radar and warning images.
        
        Usage: get_imgs() """
        count = 0
        for src in self.radar_srcs:
            urllib.request.urlretrieve(self.radar_url + src, self.radar_path + ("%02d" % (count)) + ".gif")
            count += 1
        count = 0
        for src in self.warnings_srcs:
            urllib.request.urlretrieve(self.warnings_url + src, self.warnings_path + ("%02d" % (count)) + ".gif")
            count += 1
    def get_name(self):
        """ Find the name of the radar station.
        
        Usage: get_name() """
        # Should probably move station validity checking to __init__
        if len(self.station) != 3:
            return ("short","short")
        else:
            local, headers = urllib.request.urlretrieve("http://radar.weather.gov/ridge/radar_lite.php?rid=" + self.station)
            html = open(local)
            if html.read() == "Did not get any records from ridge table<br>\n": # If the station doesn't exist, there is no valid HTML, just this
                return (None,None)
            else:
                html = open(local)
                tree = etree.parse(html, etree.HTMLParser())
                title_element = tree.find(".//title") # This finds the official title for the radar station, like "Austin/San Antonio"
                title_element = title_element.text
                location = title_element[36:]
                name = location + " Weather Radar" # These two versions are for the title of the webpage returned, and the page header
                title = location + " Radar"
                return (title,name)

##### Initialize Flask #####
app = Flask(__name__)

##### Request Handlers #####
#### Root ####
@app.route('/')
def index():
    ### Delete old images ###
    images = glob.glob("static/*.gif")
    for image in images:
        os.remove(image)
    ### Get images and station info ###
    img_num = 15 # How many frames for animation?
    station = request.args.get("station") # Get the radar station requested
    if not station:
        return render_template("home.html") # Render a home page with form to enter a radar station id
    else:
        station = station.upper() # Make it uppercase
        fetch = GetImgs(station) # Initialize communication handler
        title, name = fetch.get_name() # Get station name
        if title == None:
            return render_template("nostation.html", station=station) # If the station requested doesn't exist
        elif title == "short":
            return render_template("tooshort.html") # If the station requested doesn't have 3 letters (they all have three letters)
        if not os.path.isfile("static/Overlay_" + station + ".png"): # Does an overlay already exist for this station?
            overlay.make_overlay(station)
    fetch.get_imgs_srcs("radar",img_num) # Get urls for radar images
    fetch.get_imgs_srcs("warnings",img_num) # Get urls for warning overlay
    fetch.get_imgs() # Download images
    ### Make frames ###
    imgoverlay = Image.open("static/Overlay_" + station + ".png")
    frames = []
    img_num += -1 # Renumber to prevent off-by-one error within loop (list indicies start at 0)
    for i in range(img_num,0,-1):
        background = Image.open("static/Background.png")
        img = ("%02d" % i) # Image names start with 0 for all of them
        radar = Image.open("static/radar_" + img + ".gif")
        os.remove("static/radar_" + img + ".gif")
        radar = radar.convert("RGBA") # To prevent weird errors
        warnings = Image.open("static/warning_" + img + ".gif")
        os.remove("static/warning_" + img + ".gif")
        warnings = warnings.convert("RGBA")
        background.paste(radar,(0,0),radar)
        background.paste(warnings,(0,0),warnings)
        background.paste(imgoverlay,(0,0),imgoverlay)
        background.convert("RGB").convert("P", palette=Image.ADAPTIVE) # So it can be saved as a gif
        frames.append(background)
    ### Write animation, save, and render html page ###
    writeGif("static/animation_" + station + ".gif",frames,duration=0.225)
    return render_template("radar.html", title=title, name=name, station=station)

# Prevent image from being cached --> so it reloads every time to get more recent images
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = -1
    return response
