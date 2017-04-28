# Acknowledgements: Lots of code from Mikey1234. Thanks.

from xbmcswift2 import Plugin, ListItem
from xbmcswift2 import actions
import xbmc,xbmcaddon,xbmcvfs,xbmcgui,xbmcplugin
import re
import requests,urllib
import os,sys
import xml.etree.ElementTree as ET
import base64
import time,datetime
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

def utc2local (utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.datetime.fromtimestamp (epoch) - datetime.datetime.utcfromtimestamp (epoch)
    return utc + offset


def local_time(ttime,year,month,day):
    match = re.search(r'(.{1,2}):(.{2}) {0,1}(.{2})',ttime)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm = match.group(3)
        if ampm == "pm":
            if hour < 12:
                hour = hour + 12
                hour = hour % 24
        else:
            if hour == 12:
                hour = 0

        utc_dt = datetime.datetime(int(year),int(month),int(day),hour,minute,0)
        loc_dt = utc2local(utc_dt)
        ttime = "%02d:%02d" % (loc_dt.hour,loc_dt.minute)
    return ttime

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
        #log(country)
        countries = self.get_countries()
        #log(countries)
        #log(self.country_codes)
        country_code = self.country_codes[country]
        #log(country_code)
        if country_code == "uk":
            url = "http://uk.yo.tv/api/setting?id=1594745998&lookupid=3"
        else:
            zips = plugin.get_storage('zips')
            zip_code = zips.get(country)
            #log(zip_code)
            if not zip_code:
                set_zip_code(country)
                zip_code = zips.get(country)
                if not zip_code:
                    return []
            url = "http://%s.yo.tv/api/setting?id=%s&lookupid=1" % (country_code,zip_code)

        #log(url)
        j = requests.get(url).content
        #log(j)
        if not j:
            return
        data = json.loads(j)
        #log(data)
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
        #TODO get nice formatted channel names
        s = requests.Session()
        headers = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'}
        if headend:
            url = 'http://%s.yo.tv/settings/headend/%s' % (country_id,headend)
            #log(url)
            r = s.get(url,headers=headers)
        url = 'http://%s.yo.tv/' % country_id
        #log(url)
        r = s.get(url,headers=headers)
        html = HTMLParser.HTMLParser().unescape(r.content.decode('utf-8'))
        #log(html)
        channel_data = []
        channels = html.split('<li><a data-ajax="false"')
        for channel in channels:
            #log(channel)
            img_url = ''
            img_match = re.search(r'<img class="lazy" src="/Content/images/yo/program_logo.gif" data-original="(.*?)"', channel)
            if img_match:
                img_url = img_match.group(1)

            name_match = re.search(r'href="/tv_guide/channel/(.*?)/(.*?)"', channel)
            if name_match:
                channel_number = name_match.group(1)
                channel_name = name_match.group(2)
                #log(channel_name)
                channel_data.append((channel_name,channel_number,img_url))

        return channel_data

    def get_listing(self,country_id,channel_number,channel_name):
        #log2(channel_name)
        #'http://uk.yo.tv/tv_guide/channel/240713/bbc_one_london'
        channel_url = 'http://%s.yo.tv/tv_guide/channel/%s/%s' % (country_id,channel_number,channel_name)
        log(channel_url)
        #channel_url = 'http://uk.yo.tv/tv_guide/channel/240713/bbc_one_london'
        headers = {'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1'}
        html = requests.get(channel_url,headers=headers).content
        log(html)
        items = []
        month = ""
        day = ""
        year = ""

        tables = html.split('<a data-ajax="false"')

        for table in tables:

            thumb = ''
            season = '0'
            episode = '0'
            episode_title = ''
            genre = ''
            plot = ''

            match = re.search(r'<span class="episode">Season (.*?) Episode (.*?)<span>(.*?)</span>.*?</span>(.*?)<',table,flags=(re.DOTALL | re.MULTILINE))
            if match:
                season = match.group(1).strip('\n\r\t ')
                episode = match.group(2).strip('\n\r\t ')
                episode_title = match.group(3).strip('\n\r\t ')
                plot = match.group(4).strip('\n\r\t ')
            else:
                match = re.search(r'<div class="desc">(.*?)<',table,flags=(re.DOTALL | re.MULTILINE))
                if match:
                    plot = match.group(1).strip()


            ttime = ''
            match = re.search(r'<span class="time">(.*?)</span>',table)
            if match:
                ttime = local_time(match.group(1),year,month,day)

            title = ''
            match = re.search(r'<h2> (.*?) </h2>',table)
            if match:
                title = match.group(1)

            path = ""#plugin.url_for('play', country_id=country_id, channel_name=channel_name, channel_number=channel_number,title=title.encode("utf8"),season=season,episode=episode)

            if title:
                nice_name = re.sub('_',' ',channel_name)
                #log2(nice_name)
                if  plugin.get_setting('show_channel_name') == 'true':
                    if plugin.get_setting('show_plot') == 'true':
                        label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR] %s" % (nice_name,ttime,title,plot)
                    else:
                        label = "[COLOR yellow][B]%s[/B][/COLOR] %s [COLOR orange][B]%s[/B][/COLOR]" % (nice_name,ttime,title)
                else:
                    if plugin.get_setting('show_plot') == 'true':
                        label = "%s [COLOR orange][B]%s[/B][/COLOR] %s" % (ttime,title,plot)
                    else:
                        label = "%s [COLOR orange][B]%s[/B][/COLOR]" % (ttime,title)
                item = {'label': label,  'thumbnail': thumb, 'info': {'plot':plot, 'season':season, 'episode':episode, 'genre':genre}}
                if path:
                    item['path'] = path
                else:
                    item['is_playable'] = False
                items.append(item)
            else:
                pass

            match = re.search(r'<li class="dt">(.*?)</li>',table)
            if match:
                date_str = match.group(1)
                label = "[COLOR red][B]%s[/B][/COLOR]" % (date_str)
                #items.append({'label':label,'is_playable':True,'path':plugin.url_for('listing', country_id=country_id, channel_name=channel_name,channel_number=channel_number,channel_url=channel_url)})
                match = re.search(r'(.*?), (.*?) (.*?), (.*)',date_str)
                if match:
                    weekday = match.group(1)
                    Month = match.group(2)
                    months={"January":"1","February":"2","March":"3","April":"4","May":"5","June":"6","July":"7","August":"8","September":"9","October":"10","November":"11","December":"12"}
                    month = months[Month]
                    day = match.group(3)
                    year = match.group(4)
        log(items)
        return items


@plugin.route('/set_zip_code/<country>')
def set_zip_code(country):
    zips = plugin.get_storage('zips')
    d = xbmcgui.Dialog()
    zip_code = d.input("%s Zip/Post Code" % country)
    if zip_code:
        zips[country] = zip_code

@plugin.route('/listing/<country_id>/<provider>/<channel_id>/<channel_name>')
def listing(country_id,provider,channel_id,channel_name):
    return yo_tv().get_listing(country_id,channel_id,channel_name)

@plugin.route('/list_channels/<country>/<provider>')
def list_channels(country,provider):
    items = []
    #if provider == "yo.tv":
    yo = yo_tv()
    channel_data = yo.get_channels(country,provider)
    country_id = yo.country_codes.get(country)
    for name,id,img in channel_data:
        items.append({
        'label': "%s [%s]" % (name,id),
        'path': plugin.url_for('listing', country_id=country_id, provider=provider, channel_id=id, channel_name=name),
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