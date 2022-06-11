# -*- coding: utf-8 -*-
"""
	kingpin Add-on
"""

from json import dumps as jsdumps
from urllib.parse import quote_plus
import xbmc
from resources.lib.modules.control import dialog, getHighlightColor, yesnoDialog, sleep, condVisibility
from resources.lib.modules import tools
from resources.lib.windows.base import BaseDialog

monitor = xbmc.Monitor()


class TraktEpisodeProgressManagerXML(BaseDialog):
	def __init__(self, *args, **kwargs):
		BaseDialog.__init__(self, args)
		self.window_id = 2060
		self.results = kwargs.get('results')
		self.total_results = str(len(self.results))
		self.selected_items = []
		self.make_items()
		self.set_properties()
		self.hasVideo = False

	def onInit(self):
		win = self.getControl(self.window_id)
		win.addItems(self.item_list)
		self.setFocusId(self.window_id)

	def run(self):
		self.doModal()
		self.clearProperties()
		return self.selected_items

	# def onClick(self, controlID):
		# from resources.lib.modules import log_utils
		# log_utils.log('controlID=%s' % controlID)

	def onAction(self, action):
		try:
			if action in self.selection_actions:
				focus_id = self.getFocusId()
				if focus_id == 2060: # listItems
					position = self.get_position(self.window_id)
					chosen_listitem = self.item_list[position]
					imdb = chosen_listitem.getProperty('kingpin.imdb')
					if chosen_listitem.getProperty('kingpin.isSelected') == 'true':
						chosen_listitem.setProperty('kingpin.isSelected', '')
						if imdb in str(self.selected_items):
							pos = next((index for (index, d) in enumerate(self.selected_items) if d["imdb"] == imdb), None)
							self.selected_items.pop(pos)
					else:
						chosen_listitem.setProperty('kingpin.isSelected', 'true')
						imdb = chosen_listitem.getProperty('kingpin.imdb')
						tvdb = chosen_listitem.getProperty('kingpin.tvdb')
						season = chosen_listitem.getProperty('kingpin.season')
						episode = chosen_listitem.getProperty('kingpin.episode')
						self.selected_items.append({'imdb': imdb, 'tvdb': tvdb, 'season': season, 'episode': episode})
				elif focus_id == 2061: # OK Button
					self.close()
				elif focus_id == 2062: # Cancel Button
					self.selected_items = None
					self.close()
				elif focus_id == 2063: # Select All Button
					for item in self.item_list:
						item.setProperty('kingpin.isSelected', 'true')
						self.selected_items.append({'imdb': item.getProperty('kingpin.imdb'), 'tvdb': item.getProperty('kingpin.tvdb'),
							'season': item.getProperty('kingpin.season'), 'episode': item.getProperty('kingpin.episode')})
				elif focus_id == 2045: # Stop Trailer Playback Button
					self.execute_code('PlayerControl(Stop)')
					sleep(500)
					self.setFocusId(self.window_id)

			elif action in self.context_actions:
				cm = []
				chosen_listitem = self.item_list[self.get_position(self.window_id)]
				# media_type = chosen_listitem.getProperty('kingpin.media_type')
				source_trailer = chosen_listitem.getProperty('kingpin.trailer')
				if not source_trailer:
					from resources.lib.modules import trailer
					source_trailer = trailer.Trailer().worker('show', chosen_listitem.getProperty('kingpin.tvshowtitle'), chosen_listitem.getProperty('kingpin.year'), None, chosen_listitem.getProperty('kingpin.imdb'))

				if source_trailer: cm += [('[B]Play Trailer[/B]', 'playTrailer')]
				cm += [('[B]Browse Series[/B]', 'browseSeries')]
				chosen_cm_item = dialog.contextmenu([i[0] for i in cm])
				if chosen_cm_item == -1: return
				cm_action = cm[chosen_cm_item][1]

				if cm_action == 'playTrailer':
					self.execute_code('PlayMedia(%s, 1)' % source_trailer)
					total_sleep = 0
					while True:
						sleep(500)
						total_sleep += 500
						self.hasVideo = condVisibility('Player.HasVideo')
						if self.hasVideo or total_sleep >= 10000: break
					if self.hasVideo:
						self.setFocusId(2045)
						while (condVisibility('Player.HasVideo') and not monitor.abortRequested()):
							self.setProgressBar()
							sleep(1000)
						self.hasVideo = False
						self.progressBarReset()
						self.setFocusId(self.window_id)
					else: self.setFocusId(self.window_id)

				if cm_action == 'browseSeries':
					systvshowtitle = quote_plus(chosen_listitem.getProperty('kingpin.tvshowtitle'))
					year = chosen_listitem.getProperty('kingpin.year')
					imdb = chosen_listitem.getProperty('kingpin.imdb')
					tmdb = chosen_listitem.getProperty('kingpin.tmdb')
					tvdb = chosen_listitem.getProperty('kingpin.tvdb')
					from resources.lib.modules.control import lang
					if not yesnoDialog(lang(32182), '', ''): return
					self.chosen_hide, self.chosen_unhide = None, None
					self.close()
					sysart = quote_plus(chosen_listitem.getProperty('kingpin.art'))
					self.execute_code('ActivateWindow(Videos,plugin://plugin.video.kingpin/?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tmdb=%s&tvdb=%s&art=%s,return)' % (
							systvshowtitle, year, imdb, tmdb, tvdb, sysart))
			elif action in self.closing_actions:
				self.selected_items = None
				if self.hasVideo: self.execute_code('PlayerControl(Stop)')
				else: self.close()
		except:
			from resources.lib.modules import log_utils
			log_utils.error()
			self.close()

	def setProgressBar(self):
		try: progress_bar = self.getControlProgress(2046)
		except: progress_bar = None
		if progress_bar is not None:
			progress_bar.setPercent(self.calculate_percent())

	def calculate_percent(self):
		return (xbmc.Player().getTime() / float(xbmc.Player().getTotalTime())) * 100

	def progressBarReset(self):
		try: progress_bar = self.getControlProgress(2046)
		except: progress_bar = None
		if progress_bar is not None:
			progress_bar.setPercent(0)

	def make_items(self):
		def builder():
			for count, item in enumerate(self.results, 1):
				try:
					listitem = self.make_listitem()
					tvshowtitle = item.get('tvshowtitle')
					listitem.setProperty('kingpin.tvshowtitle', tvshowtitle)
					listitem.setProperty('kingpin.year', str(item.get('year')))
					zoneTo, formatInput = 'utc', '%Y-%m-%d'
					if 'T' in str(item.get('premiered', '')): zoneTo, formatInput = 'local', '%Y-%m-%dT%H:%M:%S.000Z'
					new_date = tools.convert_time(stringTime=str(item.get('premiered', '')), formatInput=formatInput, formatOutput='%m-%d-%Y', zoneFrom='utc', zoneTo=zoneTo)
					listitem.setProperty('kingpin.premiered', new_date)
					season = str(item.get('season'))
					listitem.setProperty('kingpin.season', season)
					episode = str(item.get('episode'))
					listitem.setProperty('kingpin.episode', episode)
					label = '%s  -  %sx%s' % (tvshowtitle, season, episode.zfill(2))
					listitem.setProperty('kingpin.label', label)
					labelProgress = str(round(float(item['progress']), 1)) + '%'
					listitem.setProperty('kingpin.progress', '[' + labelProgress + ']')
					listitem.setProperty('kingpin.isSelected', '')
					listitem.setProperty('kingpin.imdb', item.get('imdb'))
					listitem.setProperty('kingpin.tvdb', item.get('tvdb'))
					listitem.setProperty('kingpin.rating', str(round(float(item.get('rating', '0')), 1)))
					listitem.setProperty('kingpin.trailer', item.get('trailer'))
					listitem.setProperty('kingpin.studio', item.get('studio'))
					listitem.setProperty('kingpin.genre', str(item.get('genre', '')))
					listitem.setProperty('kingpin.duration', str(item.get('duration')))
					listitem.setProperty('kingpin.mpaa', item.get('mpaa') or 'NA')
					listitem.setProperty('kingpin.plot', item.get('plot'))
					poster = item.get('season_poster', '') or item.get('poster', '') or item.get('poster2', '') or item.get('poster3', '')
					fanart = item.get('fanart', '') or item.get('fanart2', '') or item.get('fanart3', '')
					clearlogo = item.get('clearlogo', '')
					clearart = item.get('clearart', '')
					art = {'poster': poster, 'tvshow.poster': poster, 'fanart': fanart, 'icon': item.get('icon') or poster, 'thumb': item.get('thumb', ''), 'banner': item.get('banner2', ''), 'clearlogo': clearlogo,
								'tvshow.clearlogo': clearlogo, 'clearart': clearart, 'tvshow.clearart': clearart, 'landscape': item.get('landscape', '')}
					listitem.setProperty('kingpin.poster', poster)
					listitem.setProperty('kingpin.clearlogo', clearlogo)
					listitem.setProperty('kingpin.art', jsdumps(art))
					listitem.setProperty('kingpin.count', '%02d.)' % count)
					yield listitem
				except:
					from resources.lib.modules import log_utils
					log_utils.error()
		try:
			self.item_list = list(builder())
			self.total_results = str(len(self.item_list))
		except:
			from resources.lib.modules import log_utils
			log_utils.error()

	def set_properties(self):
		try:
			self.setProperty('kingpin.total_results', self.total_results)
			self.setProperty('kingpin.highlight.color', getHighlightColor())
		except:
			from resources.lib.modules import log_utils
			log_utils.error()