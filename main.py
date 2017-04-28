# Acknowledgements: Lots of code from Mikey1234. Thanks.

from xbmcswift2 import Plugin, ListItem
from xbmcswift2 import actions
import xbmc,xbmcaddon,xbmcvfs,xbmcgui,xbmcplugin
import re
import requests,urllib
import os,sys
import xml.etree.ElementTree as ET
import base64
import datetime


plugin = Plugin()
big_list_view = False

def log(v):
    xbmc.log(repr(v))

def get_icon_path(icon_name):
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    return os.path.join(addon_path, 'resources', 'img', icon_name+".png")

def remove_formatting(label):
    label = re.sub(r"\[/?[BI]\]",'',label)
    label = re.sub(r"\[/?COLOR.*?\]",'',label)
    return label

def escape( str ):
    str = str.replace("'","&#39;")
    str = str.replace("&", "&amp;")
    str = str.replace("<", "&lt;")
    str = str.replace(">", "&gt;")
    str = str.replace("\"", "&quot;")
    return str

def unescape( str ):
    str = str.replace("&lt;","<")
    str = str.replace("&gt;",">")
    str = str.replace("&quot;","\"")
    str = str.replace("&amp;","&")
    str = str.replace("&#39;","'")
    return str

def get(url,proxy=False):
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; rv:50.0) Gecko/20100101 Firefox/50.0'}
    if proxy:
        headers['Referer'] = 'http://www.justproxy.co.uk/'
        url = 'http://www.justproxy.co.uk/index.php?q=%s' % base64.b64encode(url)
    try:
        r = requests.get(url,headers=headers,verify=False)
    except:
        return
    if r.status_code != requests.codes.ok:
        return
    html = r.content
    return html

@plugin.route('/xmltv_service')
def xmltv_service():
    pass

@plugin.route('/toggle_channel/<country>/<provider>/<channel>')
def toggle_channel(country,provider,channel):
    pass

@plugin.route('/channels/<country>/<provider>')
def channels(country,provider):
    items = []
    for channel in ["BBC1", "BBC2"]:
        items.append({
        'label': channel,
        'path': plugin.url_for('toggle_channel', country=country, provider=provider, channel=channel),
        'thumbnail':get_icon_path('settings'),
        })
    return items


@plugin.route('/providers/<country>')
def providers(country):
    items = []
    for provider in ["yo.tv"]:
        items.append({
        'label': provider,
        'path': plugin.url_for('channels', country=country, provider=provider),
        'thumbnail':get_icon_path('settings'),
        })
    return items

@plugin.route('/countries')
def countries():
    items = []
    for country in ["International","UK","USA"]:
        items.append({
        'label': country,
        'path': plugin.url_for('providers', country=country),
        'thumbnail':get_icon_path('settings'),
        })
    return items

@plugin.route('/')
def index():
    context_items = []
    items = [
    {
        'label': 'Countries',
        'path': plugin.url_for('countries'),
        'thumbnail':get_icon_path('settings')
    }
    ]
    return items


if __name__ == '__main__':
    plugin.run()
    if big_list_view == True:
        view_mode = int(plugin.get_setting('view_mode'))
        if view_mode:
            plugin.set_view_mode(view_mode)