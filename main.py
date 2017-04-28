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
import json
import HTMLParser


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

class yo_tv:
    def __init__(self):
        pass

    def get_countries(self):
        html = requests.get("http://www.yo.tv").content
        #log(html)
        match = re.findall(r'<li><a href="http://(.*?)\.yo\.tv"  >(.*?)</a></li>',html,flags=(re.DOTALL | re.MULTILINE))
        self.country_codes = {m[1]: m[0] for m in match}
        #log(self.country_codes)
        countries = sorted(self.country_codes)
        #log(countries)
        return countries

    def get_providers(self, country):
        log(country)
        countries = self.get_countries()
        log(countries)
        log(self.country_codes)
        country_code = self.country_codes[country]
        log(country_code)
        if country_code == "uk":
            url = "http://uk.yo.tv/api/setting?id=1594745998&lookupid=3"
        else:
            zips = plugin.get_storage('zips')
            zip_code = zips.get(country)
            log(zip_code)
            if not zip_code:
                set_zip_code(country)
                zip_code = zips.get(country)
                if not zip_code:
                    return []
            url = "http://%s.yo.tv/api/setting?id=%s&lookupid=1" % (country_code,zip_code)

        log(url)
        j = requests.get(url).content
        log(j)
        if not j:
            return
        data = json.loads(j)
        log(data)
        self.headends = {x["Name"] : x["Value"] for x in data}
        providers = [x["Name"] for x in data]
        return providers
        #index = d.select("%s provider:" % country,providers)
        #if index == -1:
        #    return
        #headend = data[index]["Value"]
        #xbmcaddon.Addon(id = 'script.tvguide.fullscreen').setSetting('yo.%s.headend' % country, headend)

    def get_channels(self,country,provider):
        providers = self.get_providers(country)
        country_id = self.country_codes.get(country)
        headend = self.headends.get(provider)
        
        s = requests.Session()
        headers = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'}
        #headend = ADDON.getSetting("yo.%s.headend" % country_id)
        if headend:
            url = 'http://%s.yo.tv/settings/headend/%s' % (country_id,headend)
            log(url)
            r = s.get(url,headers=headers)
        url = 'http://%s.yo.tv/' % country_id
        log(url)
        r = s.get(url,headers=headers)
        html = HTMLParser.HTMLParser().unescape(r.content.decode('utf-8'))
        log(html)
        channel_names = []
        channels = html.split('<li><a data-ajax="false"')
        for channel in channels:
            log(channel)
            img_url = ''
            img_match = re.search(r'<img class="lazy" src="/Content/images/yo/program_logo.gif" data-original="(.*?)"', channel)
            if img_match:
                img_url = img_match.group(1)

            name_match = re.search(r'href="/tv_guide/channel/(.*?)/(.*?)"', channel)
            if name_match:
                channel_number = name_match.group(1)
                channel_name = name_match.group(2)
                log(channel_name)
                channel_names.append(channel_name)
        
        return channel_names


@plugin.route('/set_zip_code/<country>')
def set_zip_code(country): 
    zips = plugin.get_storage('zips')
    d = xbmcgui.Dialog()
    zip_code = d.input("%s Zip/Post Code" % country)
    if zip_code:
        zips[country] = zip_code

@plugin.route('/list_channels/<country>/<provider>')
def list_channels(country,provider):
    items = []
    #if provider == "yo.tv":
    channels = yo_tv().get_channels(country,provider)
    for channel in channels:
        items.append({
        'label': channel,
        'path': plugin.url_for('toggle_channel', country=country, provider=provider, channel=channel),
        'thumbnail':get_icon_path('settings'),
        })
    return items


@plugin.route('/list_providers/<country>')
def list_providers(country):
    items = []
    providers = yo_tv().get_providers(country)
    for provider in providers:
        context_items = []
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Zip/Post Code', 'XBMC.RunPlugin(%s)' %
        (plugin.url_for('set_zip_code', country=country))))
        items.append({
        'label': provider,
        'path': plugin.url_for('list_channels', country=country, provider=provider),
        'thumbnail':get_icon_path('settings'),
        'context_menu': context_items,
        })
    return items

@plugin.route('/list_countries')
def list_countries():
    items = []
    countries = yo_tv().get_countries()
    #for country in ["International","UK","USA"]:
    for country in countries:
        context_items = []
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Zip/Post Code', 'XBMC.RunPlugin(%s)' %
        (plugin.url_for('set_zip_code', country=country))))    
        items.append({
        'label': country,
        'path': plugin.url_for('list_providers', country=country),
        'thumbnail':get_icon_path('settings'),
        'context_menu': context_items,
        })
    return items

@plugin.route('/')
def index():
    context_items = []
    items = [
    {
        'label': 'Countries',
        'path': plugin.url_for('list_countries'),
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