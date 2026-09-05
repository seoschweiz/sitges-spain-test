#!/usr/bin/env python3
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime,timezone
from pathlib import Path
from html import escape,unescape
import re

FEEDS=[
 ('Radio Maricel','https://feeds.feedburner.com/radiomaricel'),
 ('Sitges News EN','https://www.google.co.uk/alerts/feeds/13810406102390053383/16777662434324723099'),
 ('Sitges News DE','https://www.google.co.uk/alerts/feeds/13810406102390053383/8458409556936715825'),
 ('Sitges News FR','https://www.google.co.uk/alerts/feeds/13810406102390053383/17911084200607657881')]

def clean_title(s):
 s=unescape(re.sub(r'<[^>]+>',' ',s));s=re.sub(r'#[\wÀ-ÿ-]+',' ',s);s=re.sub(r'[|•◆▪■▶►★☆→←]+',' ',s);s=re.sub(r'[\U0001F000-\U0001FAFF\u2600-\u27BF]',' ',s);s=re.sub(r'\s+',' ',s).strip(' -–—:;,.!?')
 return s

def text(node,names):
 for name in names:
  v=node.findtext(name)
  if v:return re.sub(r'<[^>]+>',' ',v).strip()
 return ''
def dateval(s):
 try:return parsedate_to_datetime(s).astimezone(timezone.utc)
 except Exception:
  try:return datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(timezone.utc)
  except Exception:return datetime(1970,1,1,tzinfo=timezone.utc)
def read_feed(label,url):
 data=urlopen(Request(url,headers={'User-Agent':'SitgesSpainNews/1.0'}),timeout=25).read();root=ET.fromstring(data);out=[]
 nodes=root.findall('.//item')
 if not nodes:nodes=root.findall('.//{http://www.w3.org/2005/Atom}entry')
 for n in nodes[:12]:
  title=clean_title(text(n,['title','{http://www.w3.org/2005/Atom}title']));link=text(n,['link'])
  if not link:
   a=n.find('{http://www.w3.org/2005/Atom}link');link=a.attrib.get('href','') if a is not None else ''
  dt=text(n,['pubDate','date','{http://www.w3.org/2005/Atom}published','{http://www.w3.org/2005/Atom}updated'])
  if title and link:out.append({'title':title,'url':link,'source':label,'date':dateval(dt)})
 return out

items=[]
for label,url in FEEDS:
 try:items+=read_feed(label,url)
 except Exception as e:print(f'{label}: {e}')
seen=set();clean=[]
for x in sorted(items,key=lambda z:z['date'],reverse=True):
 key=re.sub(r'\W+','',x['title'].lower())
 if key in seen:continue
 seen.add(key);clean.append(x)
clean=clean[:30]
def card(x):
 d='' if x['date'].year==1970 else x['date'].strftime('%d %B %Y')
 return f'''<article class="card"><span class="eyebrow">{escape(x['source'])}</span><p class="meta">{d}</p><h2><a href="{escape(x['url'],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(x['title'])}</a></h2></article>'''
full='<div class="grid">'+''.join(card(x) for x in clean)+'</div>' if clean else '<p>No current external headlines are available.</p>'
latest='<section><h2>Latest Sitges News</h2><div class="grid">'+''.join(card(x) for x in clean[:6])+'</div><p><a href="sitges-news/index.html">View all current headlines</a></p></section>' if clean else '<section><h2>Latest Sitges News</h2><p>No current external headlines are available.</p></section>'
news=Path('sitges-news/index.html');s=news.read_text();s=re.sub(r'<!-- NEWS_ITEMS_START -->.*?<!-- NEWS_ITEMS_END -->','<!-- NEWS_ITEMS_START -->'+full+'<!-- NEWS_ITEMS_END -->',s,flags=re.S);news.write_text(s)
home=Path('index.html');s=home.read_text();s=re.sub(r'<!-- RSS_START -->.*?<!-- RSS_END -->','<!-- RSS_START -->'+latest+'<!-- RSS_END -->',s,flags=re.S);home.write_text(s)
print(f'Wrote {len(clean)} headlines')
