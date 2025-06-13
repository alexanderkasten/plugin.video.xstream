# -*- coding: utf-8 -*-
# Python 3

import json
import os
import sys
import xbmcaddon
import xbmc

from resources.lib.config import cConfig
from xbmc import LOGINFO as LOGNOTICE, LOGERROR, log
from resources.lib import utils
from resources.lib.handler.requestHandler import cRequestHandler
from urllib.parse import urlparse
from xbmcgui import Dialog
from xbmcaddon import Addon
from xbmcvfs import translatePath
from resources.lib.tools import platform


ADDON_PATH = translatePath(os.path.join('special://home/addons/', '%s'))
LOGMESSAGE = cConfig().getLocalizedString(30166)
class cPluginHandler:
    def __init__(self):
        self.addon = utils.addon
        self.rootFolder = utils.addonPath
        self.settingsFile = os.path.join(self.rootFolder, 'resources', 'settings.xml')
        self.profilePath = utils.profilePath
        self.pluginDBFile = os.path.join(self.profilePath, 'pluginDB')

        log(LOGMESSAGE + ' -> [pluginHandler]: profile folder: %s' % self.profilePath, LOGNOTICE)
        log(LOGMESSAGE + ' -> [pluginHandler]: root folder: %s' % self.rootFolder, LOGNOTICE)
        self.defaultFolder = os.path.join(self.rootFolder, 'sites')
        log(LOGMESSAGE + ' -> [pluginHandler]: default sites folder: %s' % self.defaultFolder, LOGNOTICE)


    def getAvailablePlugins(self):
        global globalSearchStatus
        pluginDB = self.__getPluginDB()
        # default plugins
        update = False
        fileNames = self.__getFileNamesFromFolder(self.defaultFolder)
        for fileName in fileNames:
            plugin = {'name': '', 'identifier': '', 'icon': '', 'domain': '', 'globalsearch': '', 'modified': 0}
            if fileName in pluginDB:
                plugin.update(pluginDB[fileName])
            try:
                modTime = os.path.getmtime(os.path.join(self.defaultFolder, fileName + '.py'))
            except OSError:
                modTime = 0
            try:
                globalSearchStatus = cConfig().getSetting('global_search_' + fileName)
            except Exception:
                pass
            if fileName not in pluginDB or modTime > plugin['modified'] or globalSearchStatus:
                log(LOGMESSAGE + ' -> [pluginHandler]: load plugin Informations for ' + str(fileName), LOGNOTICE)
                # try to import plugin
                pluginData = self.__getPluginData(fileName, self.defaultFolder)
                if pluginData:
                    pluginData['globalsearch'] = globalSearchStatus
                    pluginData['modified'] = modTime # Wenn Datei (Zeitstempel) verändert, werden die Daten aktualisiert
                    pluginDB[fileName] = pluginData
                    update = True
        # check pluginDB for obsolete entries
        deletions = []
        for pluginID in pluginDB:
            if pluginID not in fileNames:
                deletions.append(pluginID)
        for id in deletions:
            del pluginDB[id]
        if update or deletions:
            self.__updatePluginDB(pluginDB) # Aktualisiert PluginDB in Addon_data
            log(LOGMESSAGE + ' -> [pluginHandler]: PluginDB informations updated.', LOGNOTICE)
        return self.getAvailablePluginsFromDB()


    def getAvailablePluginsFromDB(self):
        plugins = []
        iconFolder = os.path.join(self.rootFolder, 'resources', 'art', 'sites')
        pluginDB = self.__getPluginDB() # Erstelle PluginDB
        # PluginID = Siteplugin Name
        for pluginID in pluginDB:
            plugin = pluginDB[pluginID] # Aus PluginDB lese PluginID
            pluginSettingsName = 'plugin_%s' % pluginID # Name des Siteplugins
            plugin['id'] = pluginID
            if 'icon' in plugin:
                plugin['icon'] = os.path.join(iconFolder, plugin['icon'])
            else:
                plugin['icon'] = ''
            # existieren zu diesem plugin die an/aus settings
            if cConfig().getSetting(pluginSettingsName) == 'true': # Lese aus settings.xml welche Plugins eingeschaltet sind
                plugins.append(plugin)
        return plugins


    def __updatePluginDB(self, data): # Aktualisiere PluginDB
        if not os.path.exists(self.profilePath):
            os.makedirs(self.profilePath)
        file = open(self.pluginDBFile, 'w')
        json.dump(data, file)
        file.close()


    def __getPluginDB(self): # Erstelle PluginDB
        if not os.path.exists(self.pluginDBFile): # Wenn Datei nicht verfügbar dann erstellen
            return dict()
        file = open(self.pluginDBFile, 'r')
        try:
            data = json.load(file)
        except ValueError:
            log(LOGMESSAGE + ' -> [pluginHandler]: pluginDB seems corrupt, creating new one', LOGERROR)
            data = dict()
        file.close()
        return data


    def __getFileNamesFromFolder(self, sFolder): # Hole Namen vom Dateiname.py
        aNameList = []
        items = os.listdir(sFolder)
        for sItemName in items:
            if sItemName.endswith('.py'):
                sItemName = os.path.basename(sItemName[:-3])
                aNameList.append(sItemName)
        return aNameList


    def __getPluginData(self, fileName, defaultFolder): # Hole Plugin Daten aus dem Siteplugin
        pluginData = {}
        if not defaultFolder in sys.path: sys.path.append(defaultFolder)
        try:
            plugin = __import__(fileName, globals(), locals())
            pluginData['name'] = plugin.SITE_NAME
        except Exception as e:
            log(LOGMESSAGE + " -> [pluginHandler]: Can't import plugin: %s" % fileName, LOGERROR)
            return False
        try:
            pluginData['identifier'] = plugin.SITE_IDENTIFIER
        except Exception:
            pass
        try:
            pluginData['icon'] = plugin.SITE_ICON
        except Exception:
            pass
        try:
            pluginData['domain'] = plugin.DOMAIN
        except Exception:
            pass
        try:
            pluginData['globalsearch'] = plugin.SITE_GLOBAL_SEARCH
        except Exception:
            pluginData['globalsearch'] = True
            pass
        return pluginData


    def __getPluginDataIndex(self, fileName, defaultFolder): # Hole Plugin Daten aus dem Siteplugin
        pluginData = {}
        if not defaultFolder in sys.path: sys.path.append(defaultFolder)
        try:
            plugin = __import__(fileName, globals(), locals())
            pluginData['name'] = plugin.SITE_NAME
        except Exception as e:
            log(LOGMESSAGE + " -> [pluginHandler]: Can't import plugin: %s" % fileName, LOGERROR)
            return False
        try:
            pluginData['active'] = plugin.ACTIVE
        except Exception:
            pass
        try:
            pluginData['domain'] = plugin.DOMAIN
        except Exception:
            pass
        try:
            pluginData['status'] = plugin.STATUS
            if '403' <= pluginData['status'] <= '503':
                pluginData['status'] = pluginData['status'] + ' - ' + cConfig().getLocalizedString(30429)
            elif '300' <= pluginData['status'] <= '400':
                pluginData['status'] = pluginData['status'] + ' - ' + cConfig().getLocalizedString(30428)
            elif pluginData['status'] == '200':
                pluginData['status'] = pluginData['status'] + ' - ' + cConfig().getLocalizedString(30427)
        except Exception:
            pass
        try:
            pluginData['globalsearch'] = plugin.SITE_GLOBAL_SEARCH
        except Exception:
            pluginData['globalsearch'] = True
            pass
        return pluginData


    def __getPluginDataDomain(self, fileName, defaultFolder): # Hole Plugin Daten für Domains
        pluginDataDomain = {}
        if not defaultFolder in sys.path: sys.path.append(defaultFolder)
        try:
            plugin = __import__(fileName, globals(), locals())
            pluginDataDomain['identifier'] = plugin.SITE_IDENTIFIER
        except Exception as e:
            log(LOGMESSAGE + " -> [pluginHandler]: Can't import plugin: %s" % fileName, LOGERROR)
            return False
        try:
            pluginDataDomain['domain'] = plugin.DOMAIN
        except Exception:
            pass
        return pluginDataDomain

    # Plugin Support Informationen
    def pluginInfo(self):
        # Erstelle Liste mit den Indexseiten Informationen
        list_of_plugins = []
        fileNames = self.__getFileNamesFromFolder(self.defaultFolder) # Hole Plugins aus xStream
        for fileName in fileNames:
            pluginData = self.__getPluginDataIndex(fileName, self.defaultFolder) # Hole Plugin Daten
            list_of_plugins.append(pluginData)
        result_list = [''.join([f"{key}:  {value}\n" for key, value in dictionary.items()]) for dictionary in list_of_plugins]
        # String Übersetzungen
        result_string = '\n'.join(result_list)
        result_string = result_string.replace('name', cConfig().getLocalizedString(30423))
        result_string = result_string.replace('active', cConfig().getLocalizedString(30430))
        result_string = result_string.replace('domain', cConfig().getLocalizedString(30424))
        result_string = result_string.replace('status', cConfig().getLocalizedString(30425))
        result_string = result_string.replace('globalsearch', cConfig().getLocalizedString(30426))
        result_string = result_string.replace('True', cConfig().getLocalizedString(30418))
        result_string = result_string.replace('False', cConfig().getLocalizedString(30419))
        result_string = result_string.replace('true', cConfig().getLocalizedString(30418))
        result_string = result_string.replace('false', cConfig().getLocalizedString(30419))
        list_of_PluginData = (result_string) # Ergebnis der Liste
        # Settings Abragen
        if xbmcaddon.Addon().getSetting('githubUpdateResolver') == 'true':  # Resolver Update An/Aus
            UPDATERU = cConfig().getLocalizedString(30415)  # Aktiv
        else:
            UPDATERU = cConfig().getLocalizedString(30416)  # Inaktiv
        if xbmcaddon.Addon().getSetting('bypassDNSlock') == 'true':  # DNS Bypass
            BYPASS = cConfig().getLocalizedString(30418)  # Aktiv
        else:
            BYPASS = cConfig().getLocalizedString(30419)  # Inaktiv
        if os.path.exists(ADDON_PATH % 'repository.resolveurl'):
            RESOLVEURL = Addon('repository.resolveurl').getAddonInfo('name') + ':  ' + Addon('repository.resolveurl').getAddonInfo('id') + ' - ' + Addon('repository.resolveurl').getAddonInfo('version') + '\n'
        else:
            RESOLVEURL = ''

        # Support Informationen anzeigen
        Dialog().textviewer(cConfig().getLocalizedString(30265),
            cConfig().getLocalizedString(30413) + '\n'  # Geräte Informationen
            + 'Kodi Version:  ' + xbmc.getInfoLabel('System.BuildVersion')[:4] + ' (Code Version: ' + xbmc.getInfoLabel('System.BuildVersionCode') + ')' + '\n'  # Kodi Version
            + cConfig().getLocalizedString(30266) + '   {0}'.format(platform().title()) + '\n'  # System Plattform
            + '\n'  # Absatz
            + cConfig().getLocalizedString(30414) + '\n'  # Plugin Informationen
            + Addon().getAddonInfo('name') + ' Version:  ' + Addon().getAddonInfo('id') + ' - ' + Addon().getAddonInfo('version') + '\n'  # xStream ID und Version
            + Addon('script.module.resolveurl').getAddonInfo('name') + ' Version:  ' + Addon('script.module.resolveurl').getAddonInfo('id') + ' - ' + Addon('script.module.resolveurl').getAddonInfo('version') + '\n'  # Resolver ID und Version
            + Addon('script.module.resolveurl').getAddonInfo('name') + ' Status:  ' + UPDATERU + Addon().getSettingString('resolver.branch') + '\n'  # Resolver Update Status und Branch
            + '\n'  # Absatz
            + cConfig().getLocalizedString(30420) + '\n'  # DNS Informationen
            + cConfig().getLocalizedString(30417) + ' ' + BYPASS + '\n'  # xStream DNS Bypass aktiv/inaktiv
            + '\n'  # Absatz
            + cConfig().getLocalizedString(30421) + '\n'  # Repo Informationen
            + Addon('repository.xstream').getAddonInfo('name') + ':  ' + Addon('repository.xstream').getAddonInfo('id') + ' - ' + Addon('repository.xstream').getAddonInfo('version') + '\n'  # xStream Repository ID und Version
            + RESOLVEURL
            + '\n'  # Absatz
            + cConfig().getLocalizedString(30422) + '\n'  # Indexseiten Informationen
            + list_of_PluginData # Liste mit den Indexseiten Informationen
            )

    # Überprüfung des Domain Namens. Leite um und hole neue URL und schreibe in die settings.xml. Bei nicht erreichen der Seite deaktiviere Globale Suche bis zum nächsten Start und überprüfe erneut.
    def checkDomain(self):
        import threading
        log(LOGMESSAGE + ' -> [checkDomain]: Query status code of the provider', LOGNOTICE)
        fileNames = self.__getFileNamesFromFolder(self.defaultFolder)
        threads = []
        for fileName in fileNames:
            try:
                pluginDataDomain = self.__getPluginDataDomain(fileName, self.defaultFolder)
                provider = pluginDataDomain['identifier']
                _domain = pluginDataDomain['domain']
                domain = cConfig().getSetting('plugin_' + provider + '.domain', _domain)
                base_link = 'http://' + domain + '/'  # URL_MAIN
                wrongDomain = 'site-maps.cc', 'www.drei.at', 'notice.cuii.info'
                if domain in wrongDomain:  # Falsche Umleitung ausschliessen
                    xbmcaddon.Addon().setSetting('plugin_' + provider + '.domain', '')  # Falls doch dann lösche Settings Eintrag
                    xbmcaddon.Addon().setSetting('plugin_' + provider + '_status', '')  # lösche Status Code in den Settings
                    continue
                
                if xbmcaddon.Addon().getSetting('plugin_' + provider) == 'false':  # Wenn SitePlugin deaktiviert
                    cConfig().setSetting('global_search_' + provider, 'false')  # setzte Globale Suche auf aus
                    cConfig().setSetting('plugin_' + provider + '_checkdomain', 'false')  # setzte Domain Check auf aus
                    cConfig().setSetting('plugin_' + provider + '.domain', '')  # lösche Settings Eintrag
                    cConfig().setSetting('plugin_' + provider + '_status', '')  # lösche Settings Eintrag
                    
                if xbmcaddon.Addon().getSetting('plugin_' + provider + '_checkdomain') == 'true':  # aut. Domainüberprüfung an ist überprüfe Status der Sitplugins
                    t = threading.Thread(target=self._checkdomain, args=(provider, base_link), name=fileName)
                    threads += [t]
                    t.start()
            except Exception:
                pass
        
        for count, t in enumerate(threads):
            t.join()

        log(LOGMESSAGE + ' -> [checkDomain]: Domains for all available Plugins updated', LOGNOTICE)
        
    def _checkdomain(self, provider, base_link):
        try:
            oRequest = cRequestHandler(base_link, caching=False, ignoreErrors=True)
            oRequest.request()
            status_code = int(oRequest.getStatus())
            cConfig().setSetting('plugin_' + provider + '_status', str(status_code))  # setzte Status Code in die settings
            log(LOGMESSAGE + ' -> [checkDomain]: Status Code ' + str(status_code) + '  ' + provider + ': - ' + base_link, LOGNOTICE)

            # Status 403 - bedeutet, dass der Zugriff auf eine angeforderte Ressource blockiert ist.
            # Status 404 - Seite nicht gefunden. Diese Meldung zeigt an, dass die Seite oder der Ordner auf dem Server, die aufgerufen werden sollten, nicht unter der angegebenen URL zu finden sind.
            if 403 <= status_code <= 503:  # Domain Interner Server Error und nicht erreichbar
                cConfig().setSetting('global_search_' + provider, 'false')  # deaktiviere Globale Suche
                log(LOGMESSAGE + ' -> [checkDomain]: Internal Server Error for ' + provider + ' (DDOS Guard, HTTP Error, Cloudflare or BlazingFast active)', LOGNOTICE)

            # Status 301 - richtet Ihr auf Eurem Server ein, wenn sich die URL geändert hat, Eure Domain umgezogen ist oder sich ein Inhalt anderweitig verschoben hat.
            elif 300 <= status_code <= 400:  # Domain erreichbar mit Umleitung
                url = oRequest.getRealUrl()
                cConfig().setSetting('plugin_' + provider + '.domain', urlparse(url).hostname)  # setze Domain in die settings.xml
                cConfig().setSetting('global_search_' + provider, 'true')  # aktiviere Globale Suche
                log(LOGMESSAGE + ' -> [checkDomain]: globalSearch for ' + provider + ' is activated.', LOGNOTICE)

            # Status 200 - Dieser Code wird vom Server zurückgegeben, wenn er den Request eines Browsers korrekt zurückgeben kann. Für die Ausgabe des Codes und des Inhalts der Seite muss der Server die Anfrage zunächst akzeptieren.
            elif status_code == 200:  # Domain erreichbar
                cConfig().setSetting('plugin_' + provider + '.domain', urlparse(base_link).hostname)  # setze URL_MAIN in die settings.xml
                cConfig().setSetting('global_search_' + provider, 'true')  # aktiviere Globale Suche
                log(LOGMESSAGE + ' -> [checkDomain]: globalSearch for ' + provider + ' is activated.', LOGNOTICE)
            # Wenn keiner der Status oben greift
            else:
                log(LOGMESSAGE + ' -> [checkDomain]: Error ' + provider + ' not available.', LOGNOTICE)
                cConfig().setSetting('global_search_' + provider, 'false')  # deaktiviere Globale Suche
                xbmcaddon.Addon().setSetting('plugin_' + provider + '.domain', '')  # lösche Settings Eintrag
                log(LOGMESSAGE + ' -> [checkDomain]: globalSearch for ' + provider + ' is deactivated.', LOGNOTICE)
        except:
            # Wenn Timeout und die Seite Offline ist
            cConfig().setSetting('global_search_' + provider, 'false')  # deaktiviere Globale Suche
            xbmcaddon.Addon().setSetting('plugin_' + provider + '.domain', '')  # lösche Settings Eintrag
            log(LOGMESSAGE + ' -> [checkDomain]: Error ' + provider + ' not available.', LOGNOTICE)
            pass
