import base64
import glob
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from pymongo import MongoClient
    from bs4 import BeautifulSoup
except ModuleNotFoundError:
    os.system('apk -U upgrade && apk add ffmpeg aria2 rclone')
    os.system('pip install -U --no-cache-dir pymongo dnspython requests pypasser beautifulsoup4 websockets')
    import requests
    from pymongo import MongoClient
    from bs4 import BeautifulSoup

udb1 = 'bW9uZ29kYitzcnY6Ly92b3h6ZXI6MWZkMzQ1MDliOWQ5MDNlYzU4MmE3NjI1NDY0YWE1YTI='
udb2 = 'QGNsdXN0ZXIwLjB6Z2dlLm1vbmdvZGIubmV0L3ZveHplcj9yZXRyeVdyaXRlcz10cnVlJnc9bWFqb3JpdHk='
client = MongoClient(base64.b64decode(udb1).decode("utf-8") + base64.b64decode(udb2).decode("utf-8"))
db = client['voxzer']
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0"
scr_loc = Path(__file__).absolute().parent
fldr = str(scr_loc) + "\\sub\\"


def parse_vtt(did):
    try:
        headers = {
        'Host': 'rabbitstream.net',
        'User-Agent': ua,
        'Referer': 'https://rabbitstream.net/embed-4/' + did + '?z=',
        'X-Requested-With': 'XMLHttpRequest'
        }
        urx = 'https://rabbitstream.net/ajax/embed-4/getSources?id='
        req = requests.get(urx + did, headers=headers)
        if req.status_code != 200 or 'captions' not in req.text:
            return
        return req.json()['tracks']
    except:
        return


def down_rabbit(url, mid, epid):
    docs = parse_vtt(urlparse(url).path.rpartition('/')[2])
    xfl = fldr + str(mid) + "-" + str(epid) + ".vtt"
    if not docs or len(docs) < 1:
        open(xfl, 'w').close()
        return
    for x in docs:
        if 'default' in x:
            print("Try:", x['file'], flush=True)
            try:
                r = requests.get(x['file'], stream=True)
                with open(xfl, 'wb') as fl:
                    for chunk in r.iter_content(chunk_size=1024):
                        fl.write(chunk)
                return x['file']
            except:
                return
    return


def get_source(vido):
    try:
        headers = {'user-agent': ua, 'referer': 'https://sflix.to/'}
        uri = "https://sflix.to/ajax/sources/"
        req = requests.get(uri+vido, headers=headers)
        if req.status_code != 200 or 'sources' not in req.text:
            return
        return req.json()['link'].split('/')[-1].split('?')[0]
    except:
        return


def get_null():
    items = db.videos.aggregate([
        {"$project": {"_id": 0}},
        {"$unwind": "$data"},
        {"$match": {
            "$and": [
                {"data.sv_8": {"$ne": "none"}},
                {"data.sv_8": {"$ne": ""}},
                {"data.sv_8": {"$ne": None}},
                {"$expr": {"$gt": [{"$strLenCP": "$data.sv_8"}, 3]}}
            ]
        }}
    ])
    item = [d for d in items]
    if len(item) < 0:
        return
    return item


def cleaner():
    os.chdir(fldr)
    filelist = glob.glob("*.vtt")
    for filename in filelist:
        if os.stat(filename).st_size < 10:
            os.remove(filename)
    return "Done"


def main():
    cleaner()
    vids = get_null()
    if not vids:
        print("Data not found", flush=True)
        sys.exit()
    print(len(vids), flush=True)
    for vid in sorted(vids, key=lambda d: d["data_id"], reverse=True):
        mid = vid['data_id']
        epid = vid['data']['ep_id']
        vido = vid['data']['sv_8']
        print(mid, epid, vido, flush=True)
        if not os.path.isfile(fldr + str(mid) + "-" + str(epid) + ".vtt"):
            task = get_source(vido)
            if task:
                doc = down_rabbit(task, mid, epid)
                if doc and len(str(doc)) > 20:
                    print(doc, flush=True)
                else:
                    print("Subtitle not available", flush=True)
    time.sleep(1)
    print("Task done", flush=True)


if __name__ == '__main__':
    main()
