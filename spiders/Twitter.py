
from . import Spider
from utils.jsontools import *
from utils.encodings import makeUTF8
from utils.html import getInnerText
from .impl.twitter_video_download import match1, r1, get_content, post_content

import re
import json

class Twitter( Spider ) :
	PATTERN = r'^(https:\/\/)?(www\.|mobile)?twitter\.com\/[\w]+\/status\/[\d]+'
	SHORT_PATTERN = r''
	HEADERS = makeUTF8({
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',  # noqa
		'Accept-Charset': 'UTF-8,*;q=0.5',
		'Accept-Encoding': 'gzip,deflate,sdch',
		'Accept-Language': 'en-US,en;q=0.8',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',  # noqa
	})
	LOCAL_THUMBNAIL = True

	def run( self, content, xpath, link ) :
		if re.match(r'https?://mobile', link): # normalize mobile URL
			link = 'https://' + match1(link, r'//mobile\.(.+)')
		screen_name = r1(r'twitter\.com/([^/]+)', link) or r1(r'data-screen-name="([^"]*)"', content) or \
			r1(r'<meta name="twitter:title" content="([^"]*)"', content)
		item_id = r1(r'twitter\.com/[^/]+/status/(\d+)', link) or r1(r'data-item-id="([^"]*)"', content) or \
			r1(r'<meta name="twitter:site:id" content="([^"]*)"', content)
		
		authorization = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'

		ga_url = 'https://api.twitter.com/1.1/guest/activate.json'
		ga_content = post_content(ga_url, headers={'authorization': authorization})
		guest_token = json.loads(ga_content)['guest_token']

		api_url = 'https://api.twitter.com/2/timeline/conversation/%s.json?tweet_mode=extended' % item_id
		api_content = get_content(api_url, headers={'authorization': authorization, 'x-guest-token': guest_token})

		info = json.loads(api_content)
		desc = info['globalObjects']['tweets'][item_id]['full_text']
		cover = info['globalObjects']['tweets'][item_id]['entities']['media'][0]['media_url']

		return makeResponseSuccess({
			'thumbnailURL': cover,
			'title' : 'Twitter:%s %s' % (screen_name, item_id),
			'desc' : desc,
			'site': 'twitter',
			"unique_id": "twitter:%s" % item_id
		})
		

