import asyncio
import base64
import json
import os
import ssl
import sys
import time
import glob
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    import websockets
    from pymongo import MongoClient
    from bs4 import BeautifulSoup
    from pypasser import reCaptchaV3
except ModuleNotFoundError:
    os.system('apk -U upgrade && apk add ffmpeg aria2 rclone')
    os.system('pip install -U --no-cache-dir pymongo dnspython requests pypasser beautifulsoup4 websockets')
    import requests
    import websockets
    from pymongo import MongoClient
    from bs4 import BeautifulSoup
    from pypasser import reCaptchaV3

udb1 = 'bW9uZ29kYitzcnY6Ly92b3h6ZXI6MWZkMzQ1MDliOWQ5MDNlYzU4MmE3NjI1NDY0YWE1YTI='
udb2 = 'QGNsdXN0ZXIwLjB6Z2dlLm1vbmdvZGIubmV0L3ZveHplcj9yZXRyeVdyaXRlcz10cnVlJnc9bWFqb3JpdHk='
client = MongoClient(base64.b64decode(udb1).decode("utf-8") + base64.b64decode(udb2).decode("utf-8"))
db = client['voxzer']
rcap = 'https://www.google.com/recaptcha/api2/anchor'
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
scr_loc = Path(__file__).absolute().parent
fldr = str(scr_loc)+"\\sub\\"


async def id_generator():
    url = "wss://ws12.rabbitstream.net/socket.io/?EIO=4&transport=websocket"
    async with websockets.connect(url, ssl=ssl_context) as websocket:
        await websocket.recv()
        await websocket.send("40")
        doc = await websocket.recv()
        return json.loads(doc[2:])['sid']


def parse_rabbit(did):
    try:
        #sid = asyncio.run(id_generator())
        #token = reCaptchaV3(rcap + '?ar=1&k=6Lf2aYsgAAAAAFvU3-ybajmezOYy87U4fcEpWS4C&co=aHR0cHM6Ly93d3cuMmVtYmVkLnRvOjQ0Mw..&hl=en&v=pn3ro1xnhf4yB8qmnrhh9iD2&size=invisible&cb=n4ry8rlvxw4u')
        headers = {
            "Referer": "https://rabbitstream.net/",
            "User-Agent": ua
        }
        params = {'id': did}
        req = requests.get("https://rabbitstream.net/ajax/embed-5/getSources", headers=headers, params=params)
        print(req.text)
        if req.status_code != 200 or 'captions' not in req.text:
            return
        return req.json()['tracks']
    except:
        return


def test_rul(did):
    try:
        token = reCaptchaV3(rcap+'?ar=1&k=6Lf2aYsgAAAAAFvU3-ybajmezOYy87U4fcEpWS4C&co=aHR0cHM6Ly93d3cuMmVtYmVkLnRvOjQ0Mw..&hl=en&v=pn3ro1xnhf4yB8qmnrhh9iD2&size=invisible&cb=n4ry8rlvxw4u')
        uri = "https://www.2embed.to/ajax/embed/play"
        params = {'id': did, '_token': token}
        req = requests.get(uri, params=params)
        if req.status_code != 200 or 'sources' not in req.text:
            return
        return req.json()['link']
    except:
        return


def get_all_source(tp, did, ses, eps):
    try:
        uri = "https://www.2embed.to/embed/tmdb/"
        params = {'id': did, 's': ses, 'e': eps}
        req = requests.get(uri+tp, params=params)
        if req.status_code != 200 or 'show-name' not in req.text:
            return ["https://rabbitstream.net/embed-5/7o2sq5dyDA6y?z="]
        soup = BeautifulSoup(req.text, 'html.parser')
        uid = []
        for eid in soup.find_all('a', {"class": "dropdown-item item-server"}):
            urx = test_rul(eid['data-id'])
            uid.append(urx)
        return uid
    except:
        return


def down_rabbit(url, mid, epid):
    docs = parse_rabbit(urlparse(url).path.rpartition('/')[2])
    xfl = fldr+str(mid)+"-"+str(epid)+".vtt"
    if not docs or len(docs) < 1:
        open(xfl, 'w').close()
        return
    for x in docs:
        if 'default' in x:
            print("TRy:", x['file'])
            try:
                r = requests.get(x['file'], stream=True)
                with open(xfl, 'wb') as fl:
                    for chunk in r.iter_content(chunk_size=1024):
                        fl.write(chunk)
                return x['file']
            except:
                return
    return


def get_item_info(did):
    item = db.items.find_one({'data_id': int(did)})
    try:
        tmdb = item['tmdb_id']
        if len(str(tmdb)) < 0:
            return
        return item
    except (KeyError, TypeError):
        return


def get_null():
    items = db.videos.aggregate([
        {"$project": {"_id": 0}},
        {"$unwind": "$data"},
        {"$match": {
            "data.origin": {"$regex": ".*" + "drive.google" + ".*", "$options": "i"}
        }}
    ])
    item = [d for d in items]
    if len(item) < 0:
        return
    return item


def get_season(ttl):
    s = [int(s) for s in ttl.split() if s.isdigit()]
    if len(s) == 0:
        return
    return s[-1]


def cleaner():
    os.chdir(fldr)
    fileList=glob.glob("*.vtt")
    
    for filename in fileList:
        if os.stat(filename).st_size < 10:
            os.remove(filename)
    
    return "Done"


def main():
    cleaner()
    vids = get_null()
    if not vids:
        print("TMDB id not found")
        sys.stdout.flush()
        sys.exit()
    print(len(vids))
    for vid in sorted(vids, key=lambda d: d["data_id"], reverse=True):
        mid = vid['data_id']
        itm = get_item_info(mid)
        if itm:
            epid = vid['data']['ep_id']
            print(mid, epid)
            if not os.path.isfile(fldr+str(mid)+"-"+str(epid)+".vtt"):
                tmdb = itm['tmdb_id']
                tpy = 'movie' if itm['type'] == 'movies' else 'tv'
                ses = get_season(itm['title']) if tpy == 'tv' else 1
                print(tpy, tmdb, mid, ses, epid)
                sys.stdout.flush()
                task = get_all_source(tpy, tmdb, ses, epid)
                for x in task if task else []:
                    if 'rabbitstream' in str(x):
                        print("Download from:", x)
                        sys.stdout.flush()
                        doc = down_rabbit(x, mid, epid)
                        if doc and len(str(doc)) > 20:
                            print(doc)
                        else:
                            print("Subtitle not available")
                            sys.stdout.flush()
        else:
            print("No data found")
        sys.stdout.flush()
    time.sleep(1)
    os.system('git add .')
    time.sleep(1)
    os.system('git commit -am "Make it better"')
    time.sleep(1)
    os.system('git push origin master --force')
    print("Task done")
    sys.stdout.flush()


if __name__ == '__main__':
    main()
