import feedparser, requests, json, os, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import ansa

TOKEN = os.environ["BOT_TOKEN"]
CHAT = os.environ["CHANNEL"]
FEEDS = [
    "https://www.ansa.it/valledaosta/notizie/valledaosta_rss.xml",
    "https://aostasera.it/feed",
    "https://www.gazzettamatin.com/feed/",
    "https://www.aostaoggi.it/rss1?format=feed&type=rss",
    "https://www.lavalleenotizie.it/feed/",
    "https://www.valledaostaglocal.it/links/rss/argomenti/valledaostaglocalit/rss.xml",
    "https://aostanews24.it/feed/",
]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
ROMA = ZoneInfo("Europe/Rome")

def quando(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    if not t:
        return None
    dt = datetime(*t[:6], tzinfo=timezone.utc).astimezone(ROMA)
    return dt.strftime("%d/%m/%Y %H:%M")

state = json.load(open("seen.json")) if os.path.exists("seen.json") else {"seen": [], "seeded": []}

for url in FEEDS:
    d = feedparser.parse(url, agent=UA)
    entries = d.entries
    
    if url == ansa.FEED:
        entries = ansa.filtra(entries, state)
    print(f"{len(entries)} voci | HTTP {d.get('status')} | {d.get('bozo_exception')} | {url}")
    
    if not entries:
        continue
        
    first = url not in state["seeded"]
    
    for e in reversed(entries):
        link = e.get("link")
        
        if not link or link in state["seen"]:
            continue
            
        if not first:
            when = quando(e)
            text = f"{e.title}\n\n" + (f"{when}\n" if when else "") + link
            try:
                r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                                  data={"chat_id": CHAT, "text": text,
                                        # anteprima con immagine grande (Gazzetta Matin la mostrava piccola)
                                        "link_preview_options": json.dumps({"url": link, "prefer_large_media": True})},
                                  timeout=20)
            except requests.RequestException:
                print("errore di rete Telegram")
                continue
                
            if not r.ok:
                print("errore Telegram:", r.status_code)
                continue
            time.sleep(3)
        state["seen"].append(link)
        if url == ansa.FEED:
            ansa.registra(state, e)
    if first:
        state["seeded"].append(url)

state["seen"] = state["seen"][-5000:]
json.dump(state, open("seen.json", "w"))
