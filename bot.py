import feedparser, requests, json, os, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TOKEN = os.environ["BOT_TOKEN"]
CHAT = os.environ["CHANNEL"]
FEEDS = [
    "https://www.ansa.it/valledaosta/notizie/valledaosta_rss.xml",
    "https://aostasera.it/feed",
    "https://www.gazzettamatin.com/feed/",
    "https://www.aostaoggi.it/rss",
    "https://www.lavalleenotizie.it/feed/",
    "https://www.valledaostaglocal.it/links/rss/argomenti/valledaostaglocalit/rss.xml",
    "https://aostanews24.it/feed/",
]
UA = "Mozilla/5.0 (compatible; link-bot)"
ROMA = ZoneInfo("Europe/Rome")

def quando(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    if not t:
        return None
    dt = datetime(*t[:6], tzinfo=timezone.utc).astimezone(ROMA)
    return dt.strftime("%d/%m/%Y %H:%M")

state = json.load(open("seen.json")) if os.path.exists("seen.json") else {"seen": [], "seeded": []}

for url in FEEDS:
    entries = feedparser.parse(url, agent=UA).entries
    print(f"{url}: {len(entries)} voci")
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
            r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                              data={"chat_id": CHAT, "text": text})
            if not r.ok:
                print("errore Telegram:", r.text)
                continue
            time.sleep(3)
        state["seen"].append(link)
    if first:
        state["seeded"].append(url)

state["seen"] = state["seen"][-5000:]
json.dump(state, open("seen.json", "w"))
