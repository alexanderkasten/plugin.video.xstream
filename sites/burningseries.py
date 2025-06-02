# -*- coding: utf-8 -*-
# Python 3

# Always pay attention to the translations in the menu!
# Sprachauswahl für Hoster enthalten.
# Ajax Suchfunktion enthalten.
# HTML LangzeitCache hinzugefügt
# showValue:     24 Stunden
# showAllSeries: 24 Stunden
# showEpisodes:   4 Stunden
# SSsearch:      24 Stunden

# 2022-12-06 Heptamer - Suchfunktion überarbeitet

import xbmcgui
import xbmcaddon
import json
import requests
import time

from resources.lib.handler.ParameterHandler import ParameterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.tools import logger, cParser
from resources.lib.gui.guiElement import cGuiElement
from resources.lib.config import cConfig
from resources.lib.gui.gui import cGui

SITE_IDENTIFIER = 'burningseries'
SITE_NAME = 'BurningSeries'
SITE_ICON = 'burningseries.png'

# Global search function is thus deactivated!
if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'false':
    SITE_GLOBAL_SEARCH = False
    logger.info('-> [SitePlugin]: globalSearch for %s is deactivated.' % SITE_NAME)

# Domain Abfrage
DOMAIN = cConfig().getSetting('plugin_' + SITE_IDENTIFIER + '.domain') # Domain Auswahl über die xStream Einstellungen möglich
STATUS = cConfig().getSetting('plugin_' + SITE_IDENTIFIER + '_status') # Status Code Abfrage der Domain
ACTIVE = cConfig().getSetting('plugin_' + SITE_IDENTIFIER) # Ob Plugin aktiviert ist oder nicht
URL_LOGIN = ''
URL_MAIN = 'https://' + DOMAIN
REFERER = 'https://' + DOMAIN
URL_SERIES = URL_MAIN + '/andere-serien'
URL_NEW_SERIES = URL_MAIN + '/'
URL_NEW_EPISODES = URL_MAIN + '/'
URL_POPULAR = URL_MAIN + '/vorgeschlagene-serien'
URL_ALPHABET = URL_MAIN + '/serie-alphabet'
URL_GENRES = URL_MAIN + '/serie-genre'

def load(): # Menu structure of the site plugin
    logger.info('Load %s' % SITE_NAME)
    params = ParameterHandler()
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30518), SITE_IDENTIFIER, 'showAllSeries'), params)# All Series
    params.setParam('sUrl', URL_NEW_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30514), SITE_IDENTIFIER, 'showNewSeries'), params)  # New Series
    params.setParam('sUrl', URL_NEW_EPISODES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30516), SITE_IDENTIFIER, 'showNewEpisodes'), params)  # New Episodes
    params.setParam('sUrl', URL_POPULAR)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30519), SITE_IDENTIFIER, 'showEntries'), params)  # Popular Series
    params.setParam('sUrl', URL_ALPHABET)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30517), SITE_IDENTIFIER, 'showValue'), params)    # From A-Z
    params.setParam('sUrl', URL_GENRES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30506), SITE_IDENTIFIER, 'showValue'), params)    # Genre
    params.setParam('sUrl', URL_SERIES)
    cGui().addFolder(cGuiElement(cConfig().getLocalizedString(30520), SITE_IDENTIFIER, 'showSearch'), params)   # Search
    cGui().setEndOfDirectory()


def showValue():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    #sHtmlContent = cRequestHandler(sUrl).request()
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 24 # HTML Cache Zeit 1 Tag
    sHtmlContent = oRequest.request()
    isMatch, sContainer = cParser.parseSingleResult(sHtmlContent, '<ul[^>]*class="%s"[^>]*>(.*?)<\\/ul>' % params.getValue('sCont'))
    if isMatch:
        isMatch, aResult = cParser.parse(sContainer, '<li>\s*<a[^>]*href="([^"]*)"[^>]*>(.*?)<\\/a>\s*<\\/li>')
    if not isMatch:
        cGui().showInfo()
        return

    for sUrl, sName in aResult:
        sUrl = sUrl if sUrl.startswith('http') else URL_MAIN + sUrl
        params.setParam('sUrl', sUrl)
        cGui().addFolder(cGuiElement(sName, SITE_IDENTIFIER, 'showEntries'), params)
    cGui().setEndOfDirectory()


def showAllSeries(entryUrl=False, sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl: entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 24 # HTML Cache Zeit 1 Tag
    sHtmlContent = oRequest.request()
    # pattern = '<a[^>]*href="(serie\\/[^"]*)"\\stitle="(.*?)"[^>]*>.*</a>'
    # works
    # pattern = '<a[^>]*href="(serie\/[^"]*)"[^>]*title="([^"]*)"'
        # Optimiertes Pattern: weniger Backtracking, keine unnötigen Gruppen, kein .* am Ende
    # Ursprünglich: pattern = '<a[^>]*href="(serie\/[^"]*)"[^>]*title="([^"]*)"'
    # Optimiert:
    pattern = r'<a[^>]+href="(serie/[^"]+)"[^>]+title="([^"]+)"'
    # pattern = <a[^>]*href="(serie\\/[^"]*)"[^>]*title="([^"]*)"
    # pattern = <a[^>]*href="(serie/[^"]*)"[^>]*title="([^"]*)"
    # pattern = '<a[^>]*href="(\\/serie\\/[^"]*)"[^>]*>(.*?)</a>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aResult)
    for sUrl, sName in aResult:
        if sSearchText and not cParser().search(sSearchText, sName):
            continue
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons')
        oGuiElement.setMediaType('tvshow')
        params.setParam('sUrl', URL_MAIN + '/' + sUrl)
        params.setParam('TVShowTitle', sName)
        oGui.addFolder(oGuiElement, params, True, total)
    if not sGui:
        oGui.setView('tvshows')
        oGui.setEndOfDirectory()



def showNewEpisodes(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    sHtmlContent = oRequest.request()
    sectionPattern = r'<section[^>]*id="newest_episodes"[^>]*>.*?<ul[^>]*>(.*?)</ul>.*?</section>'
    isMatch, aResult = cParser.parseSingleResult(sHtmlContent, sectionPattern)

    logger.info('BurningSeries: showNewEpisodes: isMatch: %s, aResult: %s' % (isMatch, aResult))
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    isEpisodesMatch, aEpisodes = cParser.parse(aResult, r'<li[^>]*>\s*<a href="([^"]+)"[^>]*class="title"[^>]*>([^<]+)</a>\s*<div class="info">([^<]+)<i[^>]*title="([^"]+)"[^>]*></i></div>\s*</li>')

    logger.info('BurningSeries: showNewEpisodes: isEpisodesMatch: %s, aEpisodes: %s' % (isEpisodesMatch, aEpisodes))
    if not isEpisodesMatch:
        if not sGui: oGui.showInfo()
        return
    total = len(aEpisodes)
    for sUrl, sName, sInfo, sLang in aEpisodes:
        sMovieTitle = sName + ' ' + sInfo + ' (' + sLang + ')'
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons')
        oGuiElement.setMediaType('tvshow')
        oGuiElement.setTitle(sMovieTitle)
        params.setParam('sUrl', URL_MAIN + '/' + sUrl)
        params.setParam('TVShowTitle', sMovieTitle)

        oGui.addFolder(oGuiElement, params, True, total)
    if not sGui:
        oGui.setView('tvshows')
        oGui.setEndOfDirectory()


def showNewSeries(entryUrl=False, sGui=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    if not entryUrl:
        entryUrl = params.getValue('sUrl')
    oRequest = cRequestHandler(entryUrl, ignoreErrors=(sGui is not False))
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 6  # 6 Stunden
    sHtmlContent = oRequest.request()

    pattern = r'<section[^>]*id="newest_series"[^>]*>.*?<ul[^>]*>(.*?)</ul>.*?</section>'
    isMatch, aResult = cParser.parseSingleResult(sHtmlContent, pattern)

    logger.info('BurningSeries: showNewSeries: isMatch: %s, aResult: %s' % (isMatch, aResult))
    if not isMatch:
        if not sGui: oGui.showInfo()
        return

    series_pattern = r'<li><a href="([^"]+)">([^<]+)</a></li>'
    isSeriesMatch, aSeriesResult = cParser.parse(aResult, series_pattern)

    logger.info('BurningSeries: showNewSeries: isSeriesMatch: %s, aSeriesResult: %s' % (isSeriesMatch, aSeriesResult))
    if not isSeriesMatch:
        if not sGui: oGui.showInfo()
        return

    total = len(aSeriesResult)
    for sUrl, sName in aSeriesResult:
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showSeasons')
        oGuiElement.setMediaType('tvshow')
        params.setParam('sUrl', URL_MAIN + '/' + sUrl)
        params.setParam('TVShowTitle', sName)
        oGui.addFolder(oGuiElement, params, True, total)
    if not sGui:
        oGui.setView('tvshows')
        oGui.setEndOfDirectory()


def showSeasons():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    oRequest = cRequestHandler(sUrl)
    sHtmlContent = oRequest.request()
    pattern = r'<li class="s(\d+)(?:\s+active)?"><a href="([^"]+)">([^<]+)</a></li>'
    isMatch, aResult = cParser.parse(sHtmlContent, pattern)
    if not isMatch:
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, r'<div id="sp_left">.*?<p>(.*?)</p>')
    isThumbnail, sThumbnail = cParser.parseSingleResult(sHtmlContent, r'<div id="sp_right"[^>]*>.*?<img[^>]*src="([^"]+)"')
    if isThumbnail:
        if sThumbnail.startswith('/'):
            sThumbnail = URL_MAIN + sThumbnail

    total = len(aResult)
    for sNr, sUrl, sName in aResult:
        isMovie = sNr.startswith('0')
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showEpisodes')
        oGuiElement.setMediaType('season')
        logger.info('BurningSeries: showSeasons: sNr: %s, sUrl: %s, sName: %s' % (sNr, sUrl, sName))
        # oGuiElement.setMediaType('season' if not isMovie else 'movie')
        if isThumbnail:
            oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if not isMovie:
            oGuiElement.setTVShowTitle(sTVShowTitle)
            oGuiElement.setSeason(sNr)
            params.setParam('sSeason', sNr)
        params.setParam('sThumbnail', sThumbnail)
        params.setParam('sUrl', URL_MAIN + '/' + sUrl)
        cGui().addFolder(oGuiElement, params, True, total)
    cGui().setView('seasons')
    cGui().setEndOfDirectory()


def showEpisodes():
    params = ParameterHandler()
    sUrl = params.getValue('sUrl')
    sTVShowTitle = params.getValue('TVShowTitle')
    sSeason = params.getValue('sSeason')
    sThumbnail = params.getValue('sThumbnail')

    logger.info('BurningSeries: showEpisodes: sUrl: %s, sTVShowTitle: %s, sSeason: %s, sThumbnail: %s' % (sUrl, sTVShowTitle, sSeason, sThumbnail))
    if not sSeason:
        sSeason = '1'
    isMovieList = sUrl.endswith('filme')
    oRequest = cRequestHandler(sUrl)
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 4  # HTML Cache Zeit 4 Stunden
    sHtmlContent = oRequest.request()
    pattern = r'<tr[^>]*>\s*<td><a href="([^"]+)" title="([^"]+)">(\d+)</a></td>\s*<td>.*?<a href="([^"]+)" title="([^"]+)">.*?</td>\s*<td>(.*?)</td>\s*</tr>'
    isMatch, sEpisodes = cParser.parse(sHtmlContent, pattern)

    logger.info('BurningSeries: showEpisodes: isMatch: %s, sEpisodes: %s' % (isMatch, sEpisodes))
    # if isMatch:
    #     pattern = '<tr[^>]*data-episode-season-id="(\d+).*?<a href="([^"]+).*?(?:<strong>(.*?)</strong>.*?)?(?:<span>(.*?)</span>.*?)?<'
    #     isMatch, aResult = cParser.parse(sContainer, pattern)
    if not isMatch:
        logger.error('BurningSeries: showEpisodes: No episodes found for URL: %s' % sUrl)
        cGui().showInfo()
        return

    isDesc, sDesc = cParser.parseSingleResult(sHtmlContent, r'<div id="sp_left">.*?<p>(.*?)</p>')
    total = len(sEpisodes)
    for eLink, eTitle, sNumber, eLink2, eTitle2, eHosterContent in sEpisodes:
        sName = eTitle
        oGuiElement = cGuiElement(sName, SITE_IDENTIFIER, 'showHosters')
        oGuiElement.setMediaType('episode')
        oGuiElement.setThumbnail(sThumbnail)
        if isDesc:
            oGuiElement.setDescription(sDesc)
        if not isMovieList:
            oGuiElement.setSeason(sSeason)
            oGuiElement.setEpisode(int(sNumber))
            oGuiElement.setTVShowTitle(sTVShowTitle)
        params.setParam('sUrl', URL_MAIN + '/' + eLink2)
        params.setParam('entryUrl', sUrl)
        params.setParam('eHosterContent', eHosterContent)
        cGui().addFolder(oGuiElement, params, False, total)
    cGui().setView('episodes')
    cGui().setEndOfDirectory()


def showHosters():
    hosters = []
    sUrl = ParameterHandler().getValue('sUrl')
    sHtmlContent = cRequestHandler(sUrl, caching=False).request()

    hosterTabspattern = r'<ul class="hoster-tabs[^"]*"[^>]*>(.*?)</ul>'
    hosterPattern = r'<a[^>]*href="([^"]+)"[^>]*>(?:.*?<i[^>]*></i>)?([^<]+)</a>';
    languagesPattern = 'itemprop="keywords".content=".*?Season...([^"]+).S.*?' # HD Kennzeichen

    # TODO: Sprachauswahl

    # data-lang-key="1" Deutsch
    # data-lang-key="2" Englisch
    # data-lang-key="3" Englisch mit deutschen Untertitel

    isMatchHosterTabs, rHosterTabs = cParser.parseSingleResult(sHtmlContent, hosterTabspattern)
    if not isMatchHosterTabs:
        cGui().showInfo()
        return
    # isMatchLang, aResult2 = cParser.parseSingleResult(sHtmlContent, languagesPattern)
    isMatch, aResult = cParser.parse(rHosterTabs, hosterPattern)
    sLang = '(DE)'
    sQuality = '720'
    if isMatch:
        for sUrl, sName in aResult:
            if cConfig().isBlockedHoster(sName)[0]: continue # Hoster aus settings.xml oder deaktivierten Resolver ausschließen
            # sLanguage = cConfig().getSetting('prefLanguage')
            sName = sName.strip()

                # Ab hier wird der sName mit abgefragt z.B:
                # aus dem Log [burningseries]: ['/redirect/12286260', 'VOE']
                # hier ist die sUrl = '/redirect/12286260' und der sName 'VOE'
                # hoster.py 194
            hoster = {'link': [sUrl, sName], 'name': sName, 'displayedName': '%s [I]%s [%sp][/I]' % (sName, sLang, sQuality), 'quality': sQuality, 'languageCode': sLang} # Language Code für hoster.py Sprache Prio
            hosters.append(hoster)
        if hosters:
            hosters.append('getHosterUrl')
        if not hosters:
            cGui().showLanguage()
        return hosters

def get_twoCaptcha_answer_sync(captcha_id: str):
    password = cConfig().getSetting('2captcha.pass')
    twoCaptchaApiRes = 'https://2captcha.com/res.php'
    while True:
        logger.info(f'captcha id: {captcha_id}')

        url = f"{twoCaptchaApiRes}?key={password}&json=1&action=get&id={captcha_id}"

        try:
            response = requests.get(url, headers={'Content-Type': 'application/json'})
            json_res = response.json()
            logger.info(f'captcha res: {json_res}')

            if json_res.get('status') == 1:
                return json_res.get('request')
            elif json_res.get('request') != 'CAPCHA_NOT_READY':
                error_msg = f"Error while solving captcha: {json.dumps(json_res, indent=2)} \nid: {captcha_id}"
                logger.error(error_msg)
                raise Exception(error_msg)

            time.sleep(2)

        except requests.RequestException as e:
            error_msg = f"HTTP error while polling captcha: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

def getHosterUrl(hUrl):
    if type(hUrl) == str: hUrl = eval(hUrl)
    password = cConfig().getSetting('2captcha.pass')
    twoCaptchaApiIn = 'https://2captcha.com/in.php'

    logger.info('BurningSeries: getHosterUrl: hUrl: %s' % hUrl)
    logger.info('BurningSeries: getHosterUrl: password: %s' % (password))

    Request = cRequestHandler(URL_MAIN + '/' + hUrl[0], caching=False)
    Request.addHeaderEntry('Referer', ParameterHandler().getValue('entryUrl'))
    Request.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    htmlContent = Request.request()
    logger.info('BurningSeries: getHosterUrl: HTML content received. %s' % (htmlContent))
    # not working
    # sitekey_regex = r"series\.init\s*$$\s*\d+\s*,\s*\d+\s*,\s*'([^']*)'\s*$$"
    sitekey_regex = r"series\.init\s*\(\s*\d+\s*,\s*\d+\s*,\s*'([^']+)'\s*\)\s*;"
    # not working
    # sitekey_regex = r"series\.init\s*$$\s*\d+\s*,\s*\d+\s*,\s*'([^']+)'\s*$$"
    # sitekey_regex = r"series\.init\s*$$\s*\d+\s*,\s*\d+\s*,\s*'([^']+?)'\s*$$"
    # r"series\.init\s*$$\s*\d+\s*,\s*\d+\s*,\s*'([^']+)'\s*$$"
    # sitekey_regex = r"series.init\s\(\d*,\s\d*,\s'(.*)'\)"
    isMatch, sitekey = cParser.parseSingleResult(htmlContent, sitekey_regex)
    if not isMatch:
        logger.error('BurningSeries: getHosterUrl: No sitekey found in HTML content.')
        # return None?
        return [{'streamUrl': '', 'resolved': False}]
    logger.info('BurningSeries: getHosterUrl: sitekey: %s' % sitekey)
    sUrl = Request.getRealUrl()

    params = {
        'key': password,
        'method': 'userrecaptcha',
        'googlekey': sitekey,
        'pageurl': sUrl,
        'json': 1,
        'soft_id': '2496',
    }

    logger.info('BurningSeries: getHosterUrl: sUrl: %s' % sUrl)

    response = requests.post(
        twoCaptchaApiIn,
        data=json.dumps(params),
        headers={'Content-Type': 'application/json'}
    )
    json_response = response.json()

    if 'request' not in json_response:
        raise Exception(f"Invalid response from captcha service: {json_response}")

    captcha_id = json_response['request']
    logger.info(f'Captcha request submitted with ID: {captcha_id}')

    google_captcha_token = get_twoCaptcha_answer_sync(captcha_id)
    lIDMatch, lID = cParser.parseSingleResult(htmlContent, r'data-lid="([^"]+)"')
    securityTokenMatch, securityToken = cParser.parseSingleResult(htmlContent, r'security_token" content="([^"]+)"')
    logger.info('BurningSeries: getHosterUrl: lID: %s' % lID)
    logger.info('BurningSeries: getHosterUrl: google_captcha_token: %s' % google_captcha_token)
    logger.info('BurningSeries: getHosterUrl: securityToken: %s' % securityToken)
    if not lIDMatch:
        logger.error('BurningSeries: getHosterUrl: No lID found in HTML content.')
        # return None?
        return [{'streamUrl': '', 'resolved': False}]

    if not securityTokenMatch:
        logger.error('BurningSeries: getHosterUrl: No securityToken found in HTML content.')
        # return None?
        return [{'streamUrl': '', 'resolved': False}]


    responseHeader = Request.getResponseHeader()
    setCookieHeaders = responseHeader.get_all('Set-Cookie') if hasattr(responseHeader, 'get_all') else responseHeader.getheaders('Set-Cookie')

    cookie_string_parts = []

    for header in setCookieHeaders:
        name_value = header.split(";", 1)[0].strip() 
        if "=" in name_value:
            cookie_string_parts.append(name_value)

    cookie_header = "; ".join(cookie_string_parts)

    curl_cmd = [
        "curl",
        f"'{URL_MAIN}/ajax/embed.php'",
        "-X", "POST",
        "-H", "'accept: application/json, text/javascript, */*; q=0.01'",
        "-H", "'accept-language: de-DE,de;q=0.9'",
        "-H", "'content-type: application/x-www-form-urlencoded; charset=UTF-8'",
        f"-b '{cookie_header}'",
        f"-H 'origin: {URL_MAIN}'",
        "-H 'priority: u=1, i'",
        f"-H 'referer: {sUrl}'",
        "-H 'sec-ch-ua: \"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"'",
        "-H 'sec-ch-ua-mobile: ?0'",
        "-H 'sec-ch-ua-platform: \"macOS\"'",
        "-H 'sec-fetch-dest: empty'",
        "-H 'sec-fetch-mode: cors'",
        "-H 'sec-fetch-site: same-origin'",
        "-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'",
        "-H 'x-requested-with: XMLHttpRequest'",
        f"--data-raw 'token={securityToken}&LID={lID}&ticket={google_captcha_token}'"
    ]
    logger.info("BurningSeries: getHosterUrl: curl command for debugging: %s" % " ".join(curl_cmd))
    logger.info(" ".join(curl_cmd))


    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'de-DE,de;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': URL_MAIN,
        'priority': 'u=1, i',
        'referer': sUrl,
        'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    cookies = {}
    for part in cookie_string_parts:
        if "=" in part:
            name, value = part.split("=", 1)
            cookies[name.strip()] = value.strip()


    data = {
        'token': securityToken,
        'LID': lID,
        'ticket': google_captcha_token
    }

    response = requests.post(f'{URL_MAIN}/ajax/embed.php', headers=headers, cookies=cookies, data=data)


    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Response Headers: {response.headers}")
    logger.info(f"Response Body: {response.text}")
    parsedJson = json.loads(response.text) 
    if not parsedJson:
        logger.error('BurningSeries: getHosterUrl: No result from resolve request.')
        # return None?
        return [{'streamUrl': '', 'resolved': False}]

    return [{'streamUrl': parsedJson['link'], 'resolved': False}]


def showSearch():
    sSearchText = cGui().showKeyBoard(sHeading=cConfig().getLocalizedString(30281))
    if not sSearchText: return
    _search(False, sSearchText)
    cGui().setEndOfDirectory()


def _search(oGui, sSearchText):
    SSsearch(oGui, sSearchText)


def SSsearch(sGui=False, sSearchText=False):
    oGui = sGui if sGui else cGui()
    params = ParameterHandler()
    params.getValue('sSearchText')

    oRequest = cRequestHandler(URL_SERIES, caching=True, ignoreErrors=(sGui is not False))
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', REFERER  + '/serien')
    oRequest.addHeaderEntry('Origin', REFERER)
    oRequest.addHeaderEntry('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
    oRequest.addHeaderEntry('Upgrade-Insecure-Requests', '1')
    if cConfig().getSetting('global_search_' + SITE_IDENTIFIER) == 'true':
        oRequest.cacheTime = 60 * 60 * 24  # HTML Cache Zeit 1 Tag
    sHtmlContent = oRequest.request()
    if not sHtmlContent:
            return

    sst = sSearchText.lower()

    pattern = '<li><a data.+?href="([^"]+)".+?">(.*?)\<\/a><\/l' #link - title

    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, pattern)

    if not aResult[0]:
        oGui.showInfo()
        return

    total = len(aResult[1])
    for link, title in aResult[1]:
        if not sst in title.lower():
            continue
        else:
            #get images thumb / descr pro call. (optional)
            try:
                sThumbnail, sDescription = getMetaInfo(link, title)
                oGuiElement = cGuiElement(title, SITE_IDENTIFIER, 'showSeasons')
                oGuiElement.setThumbnail(URL_MAIN + sThumbnail)
                oGuiElement.setDescription(sDescription)
                oGuiElement.setTVShowTitle(title)
                oGuiElement.setMediaType('tvshow')
                params.setParam('sUrl', URL_MAIN + link)
                params.setParam('sName', title)
                oGui.addFolder(oGuiElement, params, True, total)
            except Exception:
                oGuiElement = cGuiElement(title, SITE_IDENTIFIER, 'showSeasons')
                oGuiElement.setTVShowTitle(title)
                oGuiElement.setMediaType('tvshow')
                params.setParam('sUrl', URL_MAIN + link)
                params.setParam('sName', title)
                oGui.addFolder(oGuiElement, params, True, total)


        if not sGui:
            oGui.setView('tvshows')


def getMetaInfo(link, title):   # Setzen von Metadata in Suche:
    oGui = cGui()
    oRequest = cRequestHandler(URL_MAIN + link, caching=False)
    oRequest.addHeaderEntry('X-Requested-With', 'XMLHttpRequest')
    oRequest.addHeaderEntry('Referer', REFERER + '/serien')
    oRequest.addHeaderEntry('Origin', REFERER)

    #GET CONTENT OF HTML
    sHtmlContent = oRequest.request()
    if not sHtmlContent:
        return

    pattern = 'seriesCoverBox">.*?data-src="([^"]+).*?data-full-description="([^"]+)"' #img , descr

    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, pattern)

    if not aResult[0]:
        return

    for sImg, sDescr in aResult[1]:
        return sImg, sDescr
