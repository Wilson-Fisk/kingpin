# -*- coding: utf-8 -*-
"""
	kingpin Add-on
"""

from resources.lib.modules.control import addonPath, addonVersion, joinPath, existsPath
from resources.lib.windows.textviewer import TextViewerXML


def get(name):
	nameDict = {'kingpin': 'plugin.video.kingpin', 'MyAccounts': 'script.module.myaccounts', 'kingpinScrapers': 'script.module.kingpinscrapers'}
	addon_path = addonPath(nameDict[name])
	addon_version = addonVersion(nameDict[name])
	changelog_file = joinPath(addon_path, 'changelog.txt')
	if not existsPath(changelog_file):
		from resources.lib.modules.control import notification
		return notification(message='ChangeLog File not found.')
	f = open(changelog_file, 'r', encoding='utf-8', errors='ignore')
	text = f.read()
	f.close()
	heading = '[B]%s -  v%s - ChangeLog[/B]' % (name, addon_version)
	windows = TextViewerXML('textviewer.xml', addonPath('plugin.video.kingpin'), heading=heading, text=text)
	windows.run()
	del windows