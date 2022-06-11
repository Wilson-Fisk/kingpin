# -*- coding: utf-8 -*-
"""
	kingpin Add-on
"""

from resources.lib.modules.control import addonPath, addonId, getkingpinVersion, joinPath
from resources.lib.windows.textviewer import TextViewerXML


def get(file):
	kingpin_path = addonPath(addonId())
	kingpin_version = getkingpinVersion()
	helpFile = joinPath(kingpin_path, 'resources', 'help', file + '.txt')
	f = open(helpFile, 'r', encoding='utf-8', errors='ignore')
	text = f.read()
	f.close()
	heading = '[B]kingpin -  v%s - %s[/B]' % (kingpin_version, file)
	windows = TextViewerXML('textviewer.xml', kingpin_path, heading=heading, text=text)
	windows.run()
	del windows