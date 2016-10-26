import urllib.request
import glob
import os
import overlay
from lxml import etree
from flask import Flask
from flask import request
from flask import render_template
from PIL import Image
from images2gif import writeGif

class GetImgs(object):
    def __init__(self,station):
        self.station = station
        self.warnings_url = "http://radar.weather.gov/ridge/Warnings/Short/" + station + "/"
        self.radar_url = "http://radar.weather.gov/ridge/RadarImg/N0R/" + station + "/"
        self.warnings_path = "static/warning_"
        self.radar_path = "static/radar_"
    def get_imgs_srcs(self,type,num):
        num += 1
        if type == "radar":
            url = self.radar_url
        elif type == "warnings":
            url = self.warnings_url
            num = num * 2
        html = urllib.request.urlopen(url)
        tree = etree.parse(html, etree.HTMLParser())
        imgs_srcs = []
        for element in tree.findall(".//table"):
            table = element
        for i in range(len(table),len(table) - num,-1):
            for img_src in table[i-1].findall(".//a"):
                imgs_srcs.append(img_src.get("href"))
        if type == "radar":
            self.radar_srcs = imgs_srcs
        elif type == "warnings":
            self.warnings_srcs = imgs_srcs[1:-1:2]
    def get_imgs(self):
        count = 0
        for src in self.radar_srcs:
            urllib.request.urlretrieve(self.radar_url + src, self.radar_path + ("%02d" % (count)) + ".gif")
            count += 1
        count = 0
        for src in self.warnings_srcs:
            urllib.request.urlretrieve(self.warnings_url + src, self.warnings_path + ("%02d" % (count)) + ".gif")
            count += 1
    def get_name(self):
        if len(self.station) != 3:
            return ("short","short")
        else:
            local, headers = urllib.request.urlretrieve("http://radar.weather.gov/ridge/radar_lite.php?rid=" + self.station)
            html = open(local)
            if html.read() == "Did not get any records from ridge table<br>\n":
                return (None,None)
            else:
                html = open(local)
                tree = etree.parse(html, etree.HTMLParser())
                title_element = tree.find(".//title")
                title_element = title_element.text
                location = title_element[36:]
                name = location + " Weather Radar"
                title = location + " Radar"
                return (title,name)

app = Flask(__name__)

@app.route('/')
def index():
    images = glob.glob("static/*.gif")
    for image in images:
        os.remove(image)
    img_num = 15
    station = request.args.get("station")
    if not station:
        return render_template("home.html")
    else:
        station = station.upper()
        fetch = GetImgs(station)
        title, name = fetch.get_name()
        if title == None:
            return render_template("nostation.html", station=station)
        elif title == "short":
            return render_template("tooshort.html")
        if not os.path.isfile("static/Overlay_" + station + ".png"):
            overlay.make_overlay(station)
    fetch.get_imgs_srcs("radar",img_num)
    fetch.get_imgs_srcs("warnings",img_num)
    fetch.get_imgs()
    imgoverlay = Image.open("static/Overlay_" + station + ".png")
    frames = []
    img_num += -1
    for i in range(img_num,0,-1):
        background = Image.open("static/Background.png")
        img = ("%02d" % i)
        radar = Image.open("static/radar_" + img + ".gif")
        os.remove("static/radar_" + img + ".gif")
        radar = radar.convert("RGBA")
        warnings = Image.open("static/warning_" + img + ".gif")
        os.remove("static/warning_" + img + ".gif")
        warnings = warnings.convert("RGBA")
        background.paste(radar,(0,0),radar)
        background.paste(warnings,(0,0),warnings)
        background.paste(imgoverlay,(0,0),imgoverlay)
        background.convert("RGB").convert("P", palette=Image.ADAPTIVE)
        frames.append(background)
    writeGif("static/animation_" + station + ".gif",frames,duration=0.225)
    return render_template("radar.html", title=title, name=name, station=station)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = -1
    return response
