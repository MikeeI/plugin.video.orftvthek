#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket,datetime,time
from resources.lib.BeautifulSoup import BeautifulSoup
import os
import urlparse
import os.path
from xml.dom import Node;
from xml.dom import minidom;

version = "0.1.1"
plugin = "ORF-TVthek-" + version
author = "sofaking"

settings = xbmcaddon.Addon(id='plugin.video.orftvthek')
pluginhandle = int(sys.argv[1])
basepath = settings.getAddonInfo('path')
resourcespath = os.path.join(basepath,"resources")
mediapath =  os.path.join(resourcespath,"media")

base_url="http://tvthek.orf.at"
schedule_url = "http://tvthek.orf.at/schedule"

logopath = os.path.join(mediapath,"logos")
bannerpath = os.path.join(mediapath,"banners")
backdroppath = os.path.join(mediapath,"backdrops")
defaultbackdrop = os.path.join(basepath,"fanart.jpg")
defaultbanner = os.path.join(bannerpath,"Default.png")
defaultlogo = os.path.join(logopath,"Default.png")

mp4stream = settings.getSetting("mp4stream") == "true"
hdid = "Q6A"
sdid = "Q4A"


opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
 

def parameters_string_to_dict(parameters):
        paramDict = {}
        if parameters:
            paramPairs = parameters[1:].split("&")
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits)) == 2:
                    paramDict[paramSplits[0]] = paramSplits[1]
        return paramDict

def convertToSD(videobase):
        videourl = videobase.replace("%3A",":").replace("%2F","/").replace("mp4:","").replace("rtmp:","mms:").replace(".mp4",".wmv").replace("apasfw.apa.at","apasf.apa.at").replace("_%s" % hdid,"")
        return videourl

def convertToHD(videobase):
        videourl = videobase.replace("%3A",":").replace("%2F","/")
        return videourl

def createListItem(name,banner,summary,runtime,backdrop,videourl,playable,folder):
        if backdrop == '':
               backdrop = defaultbackdrop
        if banner == '':
               banner = defaultbanner
        liz=xbmcgui.ListItem(cleanText(name), iconImage=banner, thumbnailImage=banner)
        liz.setInfo( type="Video", infoLabels={ "Title": cleanText(name) } )
        liz.setInfo( type="Video", infoLabels={ "Plot": cleanText(summary) } )
        liz.setInfo( type="Video", infoLabels={ "Plotoutline": cleanText(summary) } )
        liz.setInfo( type="Video", infoLabels={ "tvshowtitle": cleanText(name) } )
        liz.setInfo( type="Video", infoLabels={ "Runtime": runtime } )
        liz.setProperty('fanart_image',backdrop)
        liz.setProperty('IsPlayable', playable)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=videourl, listitem=liz, isFolder=folder)


def addFile(name,videourl,banner,summary,runtime,backdrop):
        if not mp4stream and not ".sdp" in videourl:
            videourl = convertToSD(videourl)
        videourl = convertToHD(videourl)
        createListItem(name,banner,summary,runtime,backdrop,videourl,'true',False)

def addDirectory(title,banner,backdrop,link,mode):
        parameters = {"link" : link,"title" : title,"banner" : banner,"backdrop" : backdrop, "mode" : mode}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(title,banner,title,title,backdrop,u,'false',True)

def getBackdrop(html,show):
    cssVarReg = re.compile('<link .*?href="css/themes/.*?>')
    cssHrefVarReg = re.compile('href=".*?"')
    backdropVarReg = re.compile("/image.*?_image_page.png")
    backdropJPGVarReg = re.compile("/image.*?_image_page.jpg")
    try:
       css = cssVarReg.search(html).group()
       css = cssHrefVarReg.search(css).group().replace("href=","")
       css = css.replace('"',"")
       css = opener.open("%s/%s" % (base_url,css))
       css = css.read()
       backdrop = backdropVarReg.search(css).group()
       backdrop = "%s%s" % (base_url,backdrop)
       urllib.urlretrieve(backdrop, os.path.join(backdroppath, "%s.jpg" % show.replace(" ",".")))
       print "SAVING TO %s" % os.path.join(backdroppath, "%s.jpg" % show.replace(" ","."))
       return backdrop
    except:
       try:
          backdrop = backdropJPGVarReg.search(css).group()
          backdrop = "%s%s" % (base_url,backdrop)
          urllib.urlretrieve(backdrop, os.path.join(backdroppath, "%s.jpg" % show.replace(" ",".")))
          print "SAVING TO %s" % os.path.join(backdroppath, "%s.jpg" % show.replace(" ","."))
          return backdrop
       except:
          return defaultbackdrop

def getLogo(html,show):
    suppn = BeautifulSoup(html)
    tmpimg = suppn.findAll('div',{'id':'more-episodes'})
    imgpath = os.path.join(logopath, "%s.jpg" % show.replace(" ","."))
    print "ISFILE: %s" % os.path.isfile(imgpath)
    for string in tmpimg:
       string = string.findAll('img')
       for img in string:
         print "IMG : %s" % img
         if img['src'] != None and img['src'] != '':
           urllib.urlretrieve(img['src'], imgpath)
           if (os.path.isfile(imgpath)):
             print "IMAGE EXISTS : %s" % imgpath
             return defaultlogo
           else:
             print "NO IMAGE EXISTS : %s" % defaultlogo
             return imgpath
    return defaultlogo
         

def getMoreShows(url,logo,backdrop):
    date = ""
    title = ""
    link = ""
    banner = ""
    oldDate = ""
    url = urllib.unquote(url)
    logo = urllib.unquote(logo)
    backdrop = urllib.unquote(backdrop)
    newtitleVarReg = re.compile("<title>.*?</title>")
    liVarReg = re.compile('<li.*?"/li>')
    html = opener.open(url).read()
    soup = BeautifulSoup(html)
    mainTitle  = soup.find('title').text.split("-")[1].strip()
    tmpimg = soup.findAll('div',{'id':'more-episodes'})
    for string in tmpimg:
       string = string.findAll('img')
       for img in string:
         logo = img['src']
         break
    tmp = soup.findAll('ul',{'class':'iscroll'})
    if mainTitle != "ORF TVthek":
       addDirectory("[Neu] %s" % mainTitle.encode('UTF-8'),logo,backdrop,url,"openSeries")
    else:
       addDirectory("Keine Sendung verfügbar",logo,backdrop,url,"openSeries")
    
    for string in tmp:
       children = string.findChildren()
       for child in children:
          tmps = child.findAll('a')
          for tmp in tmps:
           if tmp['href'] != '#':
             if date != oldDate:
                 title = "%s | %s" % (date.replace("&#160;"," "),tmp.text.encode('UTF-8').replace("&#160;"," "))
                 link = "%s%s" % (base_url,tmp['href'])
                 banner = logo
                 oldDate = date
                 addDirectory(title,banner,backdrop,link,"openSeries")
           else:
              date = tmp.text.encode('UTF-8')
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")
    xbmcplugin.setPluginFanart(int(sys.argv[1]), backdrop, color2='0xFFFF3300')

def getLinks(url,quality):
    playlist.clear()
    url = urllib.unquote(url)
    html = opener.open(url).read()
    
    flashVarReg = re.compile("ORF.flashXML = '.*?'");
    xmlVarRef =  re.compile("%3C.*%3E")
    imgVarRef = re.compile("assets/.*?/orf_segments/image.*?.jpeg")
    cssVarReg = re.compile('<link .*?href="css/themes/.*?>')
    cssHrefVarReg = re.compile('href=".*?"')
    backdropVarReg = re.compile("/images/themes/.*?_image_page.png")

    csspath = cssHrefVarReg.search(cssVarReg.search(html).group()).group().replace("href=","").replace('"',"")
    css = opener.open("%s/%s" % (base_url,csspath)).read()

    try:
      backdrop = backdropVarReg.search(css).group()
      backdrop = "%s%s" % (base_url,backdrop)
    except:
      backdrop = ""
    flashVars = flashVarReg.findall(html)
    for flashVar in flashVars:
        xml = xmlVarRef.search(flashVar).group()
        image = "%s/%s" % (base_url,imgVarRef.search(html).group())
        flashDom = minidom.parseString(urllib.unquote(xml))
        asxurl = ""
        asxUrls = flashDom.getElementsByTagName("AsxUrl")
        for asxUrl in asxUrls:
            asxurl = "%s%s" % (base_url,asxUrl.firstChild.data)
        itemNode = flashDom.getElementsByTagName("Item")
        if len(itemNode) > 1:
           parameters = {"mode" : "playList"}
           u = sys.argv[0] + '?' + urllib.urlencode(parameters)
           createListItem("[ Alle abspielen ]",image,"Alle Beiträge abspielen","",defaultbackdrop,u,'false',False)
        for item in itemNode:
         videoUrl = ""
         title = ""
         runtime = ""
         description = ""
         title = item.getElementsByTagName("Title")[0].firstChild.data
         try:
           description = item.getElementsByTagName("Description")[0].firstChild.data.replace('\\n', '').encode('UTF-8')
         except:
           description = "Keine Beschreibung"
         videoUrls = item.getElementsByTagName("VideoUrl")
         try:
           runtime = item.getElementsByTagName("Duration")[0].firstChild.data
           runtime = int(runtime)/1000
         except:
           runtime = "0 min"
         for url in videoUrls:
               print url.firstChild.data
               if "%s.mp4" % quality in url.firstChild.data:
                 videoUrl = url.firstChild.data
         if videoUrl != '':
            liz=xbmcgui.ListItem(title, iconImage=image, thumbnailImage=image)
            liz.setInfo( type="Video", infoLabels={ "Title": title } )
            if mp4stream:
               playlist.add(convertToHD(videoUrl),liz)
            else:
               playlist.add(convertToSD(videoUrl),liz)
            addFile(title,videoUrl,image,description,runtime,backdrop)
    print "--------------------------------------------------------------------------------"
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")
    

def getMainMenu():
    addDirectory("Aktuell","",defaultbackdrop,"","getAktuelles")
    addDirectory("Sendungen","",defaultbackdrop,"","getSendungen")
    addDirectory("Themen","",defaultbackdrop,"","getThemen")
    addDirectory("Live","",defaultbackdrop,"","getLive")
    addDirectory("ORF Tipps","",defaultbackdrop,"","getTipps")
    addDirectory("Neu","",defaultbackdrop,"","getNeu")
    addDirectory("Meist gesehen","",defaultbackdrop,"","getMostViewed")
    addDirectory("Sendung verpasst?","",defaultbackdrop,"","getArchiv")
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")
    xbmcplugin.setPluginFanart(int(sys.argv[1]), defaultbackdrop, color2='0xFFFF3300')

def cleanText(string):
    string = string.replace('\\n', '').replace("&#160;"," ").replace("&quot;","'").replace('&amp;', '&')
    return string

def getCategoryList(category):
    print "GET CAT"
    category =  urllib.unquote(category)
    html = opener.open(base_url)
    html = html.read()
    soup = BeautifulSoup(html)
    categorymenu = soup.findAll('div',{'class':'column'})
    for column in categorymenu:
       if cleanText(column.find('h4').text).encode('UTF-8') == cleanText(category):
         shows = column.findAll('a')
         for show in shows:
          html = ""
          title = show.text
          link = "%s%s" % (base_url,show['href'])
          imgFile = os.path.join(logopath, "%s.jpg" % title.encode('ascii','ignore').replace(" ","."))
          backdropFile = os.path.join(backdroppath, "%s.jpg" % title.encode('ascii','ignore').replace(" ","."))
          if (not os.path.isfile(backdropFile)):
                if html == '':
                   html = opener.open(link)
                   html = html.read()
                backdrop = getBackdrop(html,title.encode('ascii','ignore'))
          else:
                backdrop = backdropFile
          if (not os.path.isfile(imgFile)):
                if html == '':
                   html = opener.open(link)
                   html = html.read()
                logo = getLogo(html,title.encode('ascii','ignore'))
          else:
                logo = imgFile
          parameters = {"link" : link,"title" : title.encode('UTF-8'),"mode" : "openShowList","logo":logo,"backdrop":backdrop}
          u = sys.argv[0] + '?' + urllib.urlencode(parameters)
          createListItem(cleanText(title),logo,cleanText(title),cleanText(title),backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")


def getLiveStreams():
    liveurl = "%s/%s" % (base_url,"live")
    flashVarReg = re.compile("ORF.flashXML = '.*?'");
    xmlVarRef =  re.compile("%3C.*%3E")
    imgVarRef = re.compile("assets/.*?/orf_segments/image.*?.jpeg")
    cssVarReg = re.compile('<link .*?href="css/themes/.*?>')
    cssHrefVarReg = re.compile('href=".*?"')
    backdropVarReg = re.compile("/images/themes/.*?_image_page.png")
    videoUrl = ""
    title = ""
    runtime = ""
    description = ""
    backdrop = ""
    image = ""
    quality = "q6a"
    html = opener.open(liveurl)
    html = html.read()
    soup = BeautifulSoup(html)
    flashVars = flashVarReg.findall(html)
    for flashVar in flashVars:
        xml = xmlVarRef.search(flashVar).group()
        image =  ""
        flashDom = minidom.parseString(urllib.unquote(xml))
        itemNode = flashDom.getElementsByTagName("Item")
        for item in itemNode:
         videoUrl = ""
         title = ""
         runtime = ""
         description = ""
         title = item.getElementsByTagName("Title")[0].firstChild.data.encode('UTF-8')
         try:
           description = item.getElementsByTagName("Description")[0].firstChild.data.replace('\\n', '').encode('UTF-8')
         except:
           description = "Keine Beschreibung"
         videoUrls = item.getElementsByTagName("VideoUrl")
         try:
           runtime = item.getElementsByTagName("Duration")[0].firstChild.data
           runtime = int(runtime)/1000
         except:
           runtime = "0 min"
         for url in videoUrls:
               if quality in url.firstChild.data:
                 videoUrl = url.firstChild.data
    if videoUrl != '':
       addFile(title,videoUrl,image,description,runtime,backdrop)
    

    teaserbox = soup.findAll('div',{'id':'more_livestreams'})
    for teasers in teaserbox:
         for teaser in teasers.findAll('li',{'class':'vod'}):
            title = teaser.find('strong').text.encode('UTF-8').replace("&#160;"," ").replace("&quot;","'")
            try:
               desc = teaser.find('span',{'class':'desc'}).text.encode('UTF-8').replace("&quot;","").replace("&#160;"," ")
            except:
               desc = "Keine Beschreibung"
            image = teaser.find('img')['src']
            link = "%s%s" % (base_url,teaser.find('a')['href'])
            html = opener.open(link)
            html = html.read()
            
            flashVars = flashVarReg.findall(html)
            for flashVar in flashVars:
               print urllib.unquote(flashVar)
               xml = xmlVarRef.search(flashVar).group()
               image =  ""
               flashDom = minidom.parseString(urllib.unquote(xml))
               itemNode = flashDom.getElementsByTagName("Item")
               for item in itemNode:
                  videoUrl = ""
                  title = ""
                  runtime = ""
                  description = ""
                  title = item.getElementsByTagName("Title")[0].firstChild.data.encode('UTF-8')
                  try:
                    description = item.getElementsByTagName("Description")[0].firstChild.data.replace('\\n', '').encode('UTF-8')
                  except:
                    description = "Keine Beschreibung"
                  videoUrls = item.getElementsByTagName("VideoUrl")
                  try:
                    runtime = item.getElementsByTagName("Duration")[0].firstChild.data
                    runtime = int(runtime)/1000
                  except:
                    runtime = "0 min"
                  for url in videoUrls:
                      if quality in url.firstChild.data:
                         videoUrl = url.firstChild.data
            if videoUrl != '':
               addFile(title,videoUrl,image,description,runtime,backdrop)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

def getRecentlyAdded():
    html = opener.open(base_url)
    html = html.read()
    soup = BeautifulSoup(html)
    teaserbox = soup.findAll('div',{'id':'teaser-container'})
    for teasers in teaserbox:
         for teaser in teasers.findAll('li',{'class':'vod'}):
            backdrop = ""
            title = teaser.find('strong',{'class':'highlightteasertitle'}).text.encode('UTF-8').replace("&#160;"," ").replace("&quot;","'")
            backdropFile = os.path.join(backdroppath, "%s.jpg" % title.replace(" ","."))
            if os.path.isfile(backdropFile):
                  backdrop = backdropFile
            desc = teaser.find('span',{'class':'bg'}).text.encode('UTF-8').replace("&quot;","").replace("&#160;"," ")
            image = teaser.find('img',{'class':'teaser-img'})['src']
            link = "%s%s" % (base_url,teaser.find('a')['href'])
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : backdrop, "mode" : "openSeries"}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem(cleanText(title),image,cleanText(desc),cleanText(title),backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

def getArchiv(url):
    base_schedule = "%s/schedule/last/" % base_url
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    html = opener.open(url)
    html = html.read()
    suppn = BeautifulSoup(html)
    links = suppn.findAll('button')
    for link in links:
        title = link['title'].replace("Sendungen vom","").replace("den","").replace(",  ","").replace(". anzeigen...","").strip()
        if link['name'].replace("day[","").replace("]","") == 'older':
            url = "%sarchiv" % base_schedule
        else:
            url = "%s%s" % (base_schedule, link['name'].replace("day[","").replace("]",""))
        parameters = {"link" : url, "mode" : "openArchiv"}
        u = sys.argv[0] + '?' + urllib.urlencode(parameters)
        createListItem(cleanText(title),defaultbanner,cleanText(title),"",defaultbackdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

	
def openArchiv(url):
    url = urllib.unquote(url)
    html = opener.open(url)
    html = html.read()
    suppn = BeautifulSoup(html)
    try:
       links = suppn.find('table',{'id':'broadcasts'})
       clips = links.findAll('tr')
    except:
      try:
       links = suppn.find('div',{'id':'broadcasts'})
       clips = links.findAll('tr')
      except:
       links = ""
       clips = ""
    for clip in clips:
        title = ''
        description = ''
        duration = ''
        time = ''
        url = ''
        image = ''
        channellogo = ''
        channel = ''
        backdrop = ''
        descinfos = clip.findAll('td',{'class':'info'})
        for desc in descinfos:
            title = desc.find('a').text
            description = desc.find('p',{'class':'descr'}).text
            try:
               duration = desc.find('p',{'class':'duration'}).text.replace('&#160;',' ')
            except:
               duration = ""
        links = clip.findAll('td',{'class':'episode'})
        for link in links:
            url = "%s%s" % (base_url,link.find('a')['href'])
            image = link.find('img')['src']
        dateinfos = clip.findAll('td',{'class':'time'})
        for date in dateinfos:
            time = (date.text).replace('&#160;',' ')
            channel = (date.find('img')['alt']).replace('Logo','').strip()
            channellogo = "%s/%s" % (base_url,date.find('img')['src'])
        if title != '':
           backdropFile = os.path.join(backdroppath, "%s.jpg" % title.replace(" ","."))
           if os.path.isfile(backdropFile):
                  backdrop = backdropFile
           title = "[%s] [%s] %s"  % (channel,time,title)
           parameters = {"link" : url,"title" : cleanText(title).encode('UTF-8'),"banner" : image,"backdrop" : "", "mode" : "openSeries"}
           u = sys.argv[0] + '?' + urllib.urlencode(parameters)
           
           createListItem(cleanText(title),image,cleanText(description),cleanText(channel),backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

def getThemenListe(topicurl,title):
    topicurl = urllib.unquote(topicurl)
    backdrop = ""
    html = opener.open(topicurl)
    html = html.read()
    soup = BeautifulSoup(html)
    backdrop = getBackdrop(html,title.encode('ascii','ignore'))
    topics = soup.findAll('li',{'class':'vod'})
    for topic in topics:
            title = topic.find('strong').text.encode('UTF-8').replace("&#160;"," ").replace("&quot;","'")
            desc = topic.find('span',{'class':'desc'}).text.encode('UTF-8').replace("&#160;"," ").replace("&quot;","'")
            link = "%s%s" % (base_url,topic.find('a')['href'])
            image = topic.find('img')['src']
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : backdrop, "mode" : "openSeries"}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem(cleanText(title),image,cleanText(desc),cleanText(title),backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

def playFile():
    player = xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER)
    player.play(playlist)
    if not player.isPlayingVideo():
        d = xbmcgui.Dialog()
        d.ok('VIDEO QUEUE EMPTY', 'The XBMC video queue is empty.','Add more links to video queue.')




def getThemen():
    topicurl = "http://tvthek.orf.at/topics"
    backdrop = ""
    html = opener.open(topicurl)
    html = html.read()
    soup = BeautifulSoup(html)
    
    topics = soup.findAll('div',{'class':'row reduced topic-row'})
    for topic in topics:
            title = topic.find('h3',{'class':'title'}).find('span').text.encode('UTF-8').replace("&#160;"," ").replace("&quot;","'")
            desc = ""
            try:
              link = "%s%s" % (base_url,topic.find('h3',{'class':'title'}).find('a',{'class':'more'})['href'])
            except:
               print "WARNING %s" % topic.find('h3',{'class':'title'}).find('a',{'class':'more'})
            image = topic.find('img')['src']
            topic_vods = topic.findAll('li',{'class':'vod'})
            for vod in topic_vods:
                desc += vod.find('strong').text.encode('UTF-8').replace("&#160;"," ").replace("&quot;",'"')
                desc += " | "
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : backdrop, "mode" : "openTopicPosts"}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem(cleanText(title),image,cleanText(desc),cleanText(title),backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

def getTabVideos(div):
    backdrop = ""
    html = opener.open(base_url)
    html = html.read()
    soup = BeautifulSoup(html)
    tipbox = soup.findAll('div',{'id':div})
    for tipps in tipbox:
         for tipp in tipps.findAll('li'):
            title = tipp.find('strong').text.encode('UTF-8').replace("&#160;"," ").replace("&quot;","'")
            desc = tipp.find('span',{'class':'desc'}).text.encode('UTF-8').replace("&quot;","").replace("&#160;"," ")
            image = tipp.find('img')['src']
            link = "%s%s" % (base_url,tipp.find('a')['href'])
            parameters = {"link" : link,"title" : title,"banner" : image,"backdrop" : backdrop, "mode" : "openSeries"}
            u = sys.argv[0] + '?' + urllib.urlencode(parameters)
            createListItem(cleanText(title),image,cleanText(desc),cleanText(title),backdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

def getCategories():
    html = opener.open(base_url)
    html = html.read()
    
    soup = BeautifulSoup(html)
    categorymenu = soup.findAll('div',{'class':'column'})
    for column in categorymenu:
       description = ""
       categories = column.findAll('h4')
       for category in categories:
          title = category.text
          shows = column.findAll('a')
          for show in shows:
             description += show.text
             description += " | "
          if title.encode('UTF-8') != "Wetter":
             parameters = {"title" : title.encode('UTF-8'),"mode" : "openCategoryList","category" : title.encode('UTF-8')}
             u = sys.argv[0] + '?' + urllib.urlencode(parameters)
             createListItem(cleanText(title),defaultbanner,cleanText(description),cleanText(description),defaultbackdrop,u,'false',True)
    xbmcplugin.setContent(pluginhandle,'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin("Container.SetViewMode(503)")

#Getting Parameters
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
title=params.get('title')
link=params.get('link')
logo=params.get('logo')
category=params.get('category')
backdrop=params.get('backdrop')


if mode == 'openSeries':
    getLinks(link,hdid)
elif mode == 'openShowList':
    getMoreShows(link,logo,backdrop)
elif mode == 'openCategoryList':
    getCategoryList(category)
elif mode == 'getSendungen':
    getCategories()
elif mode == 'getAktuelles':
    getRecentlyAdded()
elif mode == 'getLive':
    getLiveStreams()
elif mode == 'getTipps':
    getTabVideos('tipp-tab')
elif mode == 'getNeu':
    getTabVideos('news-tab')
elif mode == 'getMostViewed':
    getTabVideos('mostviewed-tab')
elif mode == 'getThemen':
    getThemen()
elif mode == 'openTopicPosts':
    getThemenListe(link,title)
elif mode == 'playVideo':
    playFile()
elif mode == 'playList':
    playFile()
elif mode == 'getArchiv':
    getArchiv(schedule_url)
elif mode == 'openArchiv':
    openArchiv(link)
else:
    getMainMenu()
