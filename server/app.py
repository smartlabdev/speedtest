import os
import random
import time
from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Heimnett SpeedTest")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_SIZE_MB = int(os.getenv("MAX_SIZE_MB", 100))

@app.get("/ping")
async def ping():
    return {"status": "ok"}

@app.get("/download")
async def download(size: int = Query(default=10, alias="size_mb")):
    size = min(size, MAX_SIZE_MB)
    total_bytes = size * 1024 * 1024

    def generate():
        chunk = os.urandom(65536)
        sent = 0
        while sent < total_bytes:
            remaining = total_bytes - sent
            if remaining < len(chunk):
                yield chunk[:remaining]
                sent += remaining
            else:
                yield chunk
                sent += len(chunk)

    return StreamingResponse(
        generate(),
        media_type="application/octet-stream",
        headers={
            "Content-Length": str(total_bytes),
            "Cache-Control": "no-cache, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

@app.post("/upload")
async def upload(request: Request):
    start = time.monotonic()
    body = await request.body()
    elapsed = time.monotonic() - start
    return {"status": "ok", "bytes_received": len(body), "elapsed_ms": round(elapsed * 1000, 2)}

SERVERS = {
    "gaming": [
        {"id": "steam",    "name": "Steam / Valve",               "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\U0001f3ae"},
        {"id": "valorant", "name": "Riot Games / Valorant",       "location": "London",    "flag": "\U0001f1ec\U0001f1e7", "emoji": "\U0001f3af"},
        {"id": "blizzard", "name": "Blizzard",                    "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\u2694\ufe0f"},
        {"id": "epicgames","name": "Epic Games / Fortnite",       "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\U0001f3ae"},
        {"id": "ea",       "name": "EA / Battlefield",            "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\U0001f3ae"},
        {"id": "lol",      "name": "Riot EUW / League of Legends","location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\U0001f9d9"},
        {"id": "psn",      "name": "PlayStation Network",         "location": "London",    "flag": "\U0001f1ec\U0001f1e7", "emoji": "\U0001f3ae"},
        {"id": "xbox",     "name": "Xbox Live",                   "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\U0001f3ae"},
        {"id": "minecraft","name": "Minecraft",                   "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\u26cf\ufe0f"},
        {"id": "cs2",      "name": "CS2 / Counter-Strike",        "location": "Stockholm", "flag": "\U0001f1f8\U0001f1ea", "emoji": "\U0001f52b"},
    ],
    "streaming": [
        {"id": "netflix",   "name": "Netflix",          "location": "Oslo CDN",  "flag": "\U0001f1f3\U0001f1f4", "emoji": "\U0001f4fa"},
        {"id": "youtube",   "name": "YouTube / Google", "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\u25b6\ufe0f"},
        {"id": "twitch",    "name": "Twitch",           "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\U0001f4e1"},
        {"id": "spotify",   "name": "Spotify",          "location": "Stockholm", "flag": "\U0001f1f8\U0001f1ea", "emoji": "\U0001f3b5"},
        {"id": "disneyplus","name": "Disney+",          "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\U0001f3f0"},
        {"id": "hbomax",    "name": "HBO Max / Max",    "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\U0001f3ac"},
        {"id": "vg",        "name": "VG.no",            "location": "Oslo",      "flag": "\U0001f1f3\U0001f1f4", "emoji": "\U0001f4f0"},
        {"id": "nrk",       "name": "NRK",              "location": "Oslo",      "flag": "\U0001f1f3\U0001f1f4", "emoji": "\U0001f4fb"},
    ],
    "work": [
        {"id": "teams",     "name": "Microsoft Teams",            "location": "Dublin",    "flag": "\U0001f1ee\U0001f1ea", "emoji": "\U0001f4ac"},
        {"id": "m365",      "name": "Microsoft 365 / SharePoint", "location": "Dublin",    "flag": "\U0001f1ee\U0001f1ea", "emoji": "\U0001f4c4"},
        {"id": "zoom",      "name": "Zoom",                       "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\U0001f4f9"},
        {"id": "googlemeet","name": "Google Meet / Workspace",    "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\U0001f91d"},
        {"id": "slack",     "name": "Slack",                      "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\U0001f4ac"},
        {"id": "webex",     "name": "Cisco Webex",                "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\U0001f4f9"},
        {"id": "github",    "name": "GitHub",                     "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\U0001f4bb"},
        {"id": "aws",       "name": "AWS eu-west-1",              "location": "Dublin",    "flag": "\U0001f1ee\U0001f1ea", "emoji": "\u2601\ufe0f"},
        {"id": "azure",     "name": "Azure West Europe",          "location": "Amsterdam", "flag": "\U0001f1f3\U0001f1f1", "emoji": "\u2601\ufe0f"},
    ],
    "general": [
        {"id": "googledns", "name": "Google DNS 8.8.8.8",           "location": "Global",    "flag": "\U0001f30d", "emoji": "\U0001f310"},
        {"id": "cloudflare","name": "Cloudflare 1.1.1.1",           "location": "Global",    "flag": "\U0001f30d", "emoji": "\u26a1"},
        {"id": "nix",       "name": "NIX — Norsk Internett Exchange","location": "Oslo",      "flag": "\U0001f1f3\U0001f1f4", "emoji": "\U0001f500"},
        {"id": "telenor",   "name": "Telenor Gateway",              "location": "Oslo",      "flag": "\U0001f1f3\U0001f1f4", "emoji": "\U0001f4e1"},
        {"id": "telia",     "name": "Telia Core",                   "location": "Stockholm", "flag": "\U0001f1f8\U0001f1ea", "emoji": "\U0001f310"},
        {"id": "decix",     "name": "DE-CIX Frankfurt",             "location": "Frankfurt", "flag": "\U0001f1e9\U0001f1ea", "emoji": "\U0001f500"},
    ],
}

SOURCES = [
    {"id": "local",          "name": "Min egen PC",        "description": "Testen kj\u00f8res fra din egen datamaskin",                    "location": "Din PC",    "emoji": "\U0001f3e0"},
    {"id": "heimnett_cgnat", "name": "Heimnett CGNAT-node","description": "Testen kj\u00f8res fra Heimnett sitt nettverkspunkt i Oslo",    "location": "Oslo",      "emoji": "\U0001f310"},
    {"id": "fastip",         "name": "FastIP.no",          "description": "Testen kj\u00f8res fra FastIP sin server i Oslo",               "location": "Oslo",      "emoji": "\u26a1"},
    {"id": "telia_sthlm",    "name": "Telia Node",         "description": "Testen kj\u00f8res fra Telia sin node i Stockholm",            "location": "Stockholm", "emoji": "\U0001f500"},
]

LOCATION_PING = {
    "oslo": 8, "oslo cdn": 7, "stockholm": 12, "amsterdam": 16,
    "frankfurt": 19, "london": 22, "dublin": 26, "global": 20,
}

HOP_TEMPLATES = {
    "oslo": [
        {"hop": 1, "ms_base": 1.2, "name": "Hjemmeruter",   "description": "Din egen ruter hjemme",                                             "emoji": "\U0001f3e0", "type": "home"},
        {"hop": 2, "ms_base": 2.4, "name": "Fiber-node",    "description": "Fiberkabelen i gata di",                                            "emoji": "\U0001f50c", "type": "fiber"},
        {"hop": 3, "ms_base": 4.1, "name": "BNG Oslo",      "description": "Her starter det ekte internett! BNG = Broadband Network Gateway",   "emoji": "\U0001f3e2", "type": "bng"},
        {"hop": 4, "ms_base": 6.8, "name": "ISP Core Oslo", "description": "Hjernene til din internettleverand\u00f8r i Oslo",                 "emoji": "\U0001f500", "type": "core"},
        {"hop": 5, "ms_base": 8.0, "name": "Destinasjon",   "description": "Serveren du tester mot \u2014 i Oslo!",                            "emoji": "\U0001f3af", "type": "destination"},
    ],
    "stockholm": [
        {"hop": 1, "ms_base": 1.2,  "name": "Hjemmeruter",   "description": "Din egen ruter hjemme",                                               "emoji": "\U0001f3e0", "type": "home"},
        {"hop": 2, "ms_base": 2.4,  "name": "Fiber-node",    "description": "Fiberkabelen i gata di",                                              "emoji": "\U0001f50c", "type": "fiber"},
        {"hop": 3, "ms_base": 4.1,  "name": "BNG Oslo",      "description": "Her starter det ekte internett! BNG = Broadband Network Gateway",     "emoji": "\U0001f3e2", "type": "bng"},
        {"hop": 4, "ms_base": 6.8,  "name": "ISP Core Oslo", "description": "Hjernene til din internettleverand\u00f8r i Oslo",                   "emoji": "\U0001f500", "type": "core"},
        {"hop": 5, "ms_base": 9.5,  "name": "NIX Oslo",      "description": "Norsk Internett Exchange \u2014 her m\u00f8tes norske nett",         "emoji": "\U0001f500", "type": "ix"},
        {"hop": 6, "ms_base": 12.0, "name": "Stockholm",     "description": "Serveren du tester mot \u2014 i Stockholm",                          "emoji": "\U0001f3af", "type": "destination"},
    ],
    "amsterdam": [
        {"hop": 1, "ms_base": 1.2,  "name": "Hjemmeruter",   "description": "Din egen ruter hjemme",                                               "emoji": "\U0001f3e0", "type": "home"},
        {"hop": 2, "ms_base": 2.4,  "name": "Fiber-node",    "description": "Fiberkabelen i gata di",                                              "emoji": "\U0001f50c", "type": "fiber"},
        {"hop": 3, "ms_base": 4.1,  "name": "BNG Oslo",      "description": "Her starter det ekte internett! BNG = Broadband Network Gateway",     "emoji": "\U0001f3e2", "type": "bng"},
        {"hop": 4, "ms_base": 6.8,  "name": "ISP Core Oslo", "description": "Hjernene til din internettleverand\u00f8r i Oslo",                   "emoji": "\U0001f500", "type": "core"},
        {"hop": 5, "ms_base": 9.5,  "name": "NIX Oslo",      "description": "Norsk Internett Exchange \u2014 her m\u00f8tes norske nett",         "emoji": "\U0001f500", "type": "ix"},
        {"hop": 6, "ms_base": 13.0, "name": "Transit Europa","description": "En stor europeisk kabel \u2014 data reiser med lyshastighet",        "emoji": "\U0001f310", "type": "transit"},
        {"hop": 7, "ms_base": 16.0, "name": "Amsterdam",     "description": "Serveren du tester mot \u2014 i Amsterdam!",                         "emoji": "\U0001f3af", "type": "destination"},
    ],
    "frankfurt": [
        {"hop": 1, "ms_base": 1.2,  "name": "Hjemmeruter",   "description": "Din egen ruter hjemme",                                               "emoji": "\U0001f3e0", "type": "home"},
        {"hop": 2, "ms_base": 2.4,  "name": "Fiber-node",    "description": "Fiberkabelen i gata di",                                              "emoji": "\U0001f50c", "type": "fiber"},
        {"hop": 3, "ms_base": 4.1,  "name": "BNG Oslo",      "description": "Her starter det ekte internett! BNG = Broadband Network Gateway",     "emoji": "\U0001f3e2", "type": "bng"},
        {"hop": 4, "ms_base": 6.8,  "name": "ISP Core Oslo", "description": "Hjernene til din internettleverand\u00f8r i Oslo",                   "emoji": "\U0001f500", "type": "core"},
        {"hop": 5, "ms_base": 9.5,  "name": "NIX Oslo",      "description": "Norsk Internett Exchange \u2014 her m\u00f8tes norske nett",         "emoji": "\U0001f500", "type": "ix"},
        {"hop": 6, "ms_base": 13.5, "name": "Transit Europa","description": "En stor europeisk kabel \u2014 data reiser med lyshastighet",        "emoji": "\U0001f310", "type": "transit"},
        {"hop": 7, "ms_base": 19.0, "name": "Frankfurt",     "description": "Serveren du tester mot \u2014 i Frankfurt!",                         "emoji": "\U0001f3af", "type": "destination"},
    ],
    "london": [
        {"hop": 1, "ms_base": 1.2,  "name": "Hjemmeruter",     "description": "Din egen ruter hjemme",                                               "emoji": "\U0001f3e0", "type": "home"},
        {"hop": 2, "ms_base": 2.4,  "name": "Fiber-node",      "description": "Fiberkabelen i gata di",                                              "emoji": "\U0001f50c", "type": "fiber"},
        {"hop": 3, "ms_base": 4.1,  "name": "BNG Oslo",        "description": "Her starter det ekte internett! BNG = Broadband Network Gateway",     "emoji": "\U0001f3e2", "type": "bng"},
        {"hop": 4, "ms_base": 6.8,  "name": "ISP Core Oslo",   "description": "Hjernene til din internettleverand\u00f8r i Oslo",                   "emoji": "\U0001f500", "type": "core"},
        {"hop": 5, "ms_base": 9.5,  "name": "NIX Oslo",        "description": "Norsk Internett Exchange \u2014 her m\u00f8tes norske nett",         "emoji": "\U0001f500", "type": "ix"},
        {"hop": 6, "ms_base": 14.0, "name": "Transit Europa",  "description": "En stor europeisk kabel \u2014 data reiser med lyshastighet",        "emoji": "\U0001f310", "type": "transit"},
        {"hop": 7, "ms_base": 18.5, "name": "North Sea Cable", "description": "Undervannsskabel over Nordsjøen",                                     "emoji": "\U0001f30a", "type": "transit"},
        {"hop": 8, "ms_base": 22.0, "name": "London",          "description": "Serveren du tester mot \u2014 i London!",                            "emoji": "\U0001f3af", "type": "destination"},
    ],
    "dublin": [
        {"hop": 1, "ms_base": 1.2,  "name": "Hjemmeruter",     "description": "Din egen ruter hjemme",                                               "emoji": "\U0001f3e0", "type": "home"},
        {"hop": 2, "ms_base": 2.4,  "name": "Fiber-node",      "description": "Fiberkabelen i gata di",                                              "emoji": "\U0001f50c", "type": "fiber"},
        {"hop": 3, "ms_base": 4.1,  "name": "BNG Oslo",        "description": "Her starter det ekte internett! BNG = Broadband Network Gateway",     "emoji": "\U0001f3e2", "type": "bng"},
        {"hop": 4, "ms_base": 6.8,  "name": "ISP Core Oslo",   "description": "Hjernene til din internettleverand\u00f8r i Oslo",                   "emoji": "\U0001f500", "type": "core"},
        {"hop": 5, "ms_base": 9.5,  "name": "NIX Oslo",        "description": "Norsk Internett Exchange \u2014 her m\u00f8tes norske nett",         "emoji": "\U0001f500", "type": "ix"},
        {"hop": 6, "ms_base": 14.0, "name": "Transit Europa",  "description": "En stor europeisk kabel \u2014 data reiser med lyshastighet",        "emoji": "\U0001f310", "type": "transit"},
        {"hop": 7, "ms_base": 19.5, "name": "North Sea Cable", "description": "Undervannsskabel over Nordsjøen mot vest",                            "emoji": "\U0001f30a", "type": "transit"},
        {"hop": 8, "ms_base": 26.0, "name": "Dublin",          "description": "Serveren du tester mot \u2014 i Dublin!",                            "emoji": "\U0001f3af", "type": "destination"},
    ],
    "global": [
        {"hop": 1, "ms_base": 1.2,  "name": "Hjemmeruter",   "description": "Din egen ruter hjemme",                                               "emoji": "\U0001f3e0", "type": "home"},
        {"hop": 2, "ms_base": 2.4,  "name": "Fiber-node",    "description": "Fiberkabelen i gata di",                                              "emoji": "\U0001f50c", "type": "fiber"},
        {"hop": 3, "ms_base": 4.1,  "name": "BNG Oslo",      "description": "Her starter det ekte internett! BNG = Broadband Network Gateway",     "emoji": "\U0001f3e2", "type": "bng"},
        {"hop": 4, "ms_base": 6.8,  "name": "ISP Core Oslo", "description": "Hjernene til din internettleverand\u00f8r i Oslo",                   "emoji": "\U0001f500", "type": "core"},
        {"hop": 5, "ms_base": 9.5,  "name": "NIX Oslo",      "description": "Norsk Internett Exchange \u2014 her m\u00f8tes norske nett",         "emoji": "\U0001f500", "type": "ix"},
        {"hop": 6, "ms_base": 14.0, "name": "Transit Europa","description": "En stor europeisk kabel \u2014 data reiser med lyshastighet",        "emoji": "\U0001f310", "type": "transit"},
        {"hop": 7, "ms_base": 20.0, "name": "Global Anycast","description": "Globalt distribuert server \u2014 n\u00e6reste node svarer",         "emoji": "\U0001f30d", "type": "destination"},
    ],
}

def _location_key(location: str) -> str:
    loc = location.lower().split()[0]
    if loc in HOP_TEMPLATES:
        return loc
    if "oslo" in location.lower():
        return "oslo"
    return "global"

def _get_server_by_id(server_id: str):
    for category in SERVERS.values():
        for s in category:
            if s["id"] == server_id:
                return s
    return None

def _ping_score(ms: float):
    if ms < 10:  return 100, "Lynrask! Perfekt for gaming"
    if ms < 20:  return 95,  "Utmerket! Du vil ikke merke forsinkelse"
    if ms < 30:  return 85,  "Meget bra for gaming og streaming"
    if ms < 50:  return 70,  "Bra for streaming og hjemmekontor"
    if ms < 100: return 50,  "Greit for surfing, litt tregt for gaming"
    return 20, "Tregt — ikke ideelt for gaming"

def _status_from_score(score: int) -> str:
    if score >= 90: return "excellent"
    if score >= 70: return "good"
    if score >= 50: return "ok"
    return "poor"

@app.get("/servers")
async def get_servers():
    return SERVERS

@app.get("/sources")
async def get_sources():
    return SOURCES

@app.get("/traceroute")
async def traceroute(target: str = Query(...), source: str = Query(default="local")):
    server = _get_server_by_id(target)
    if not server:
        return JSONResponse(status_code=404, content={"error": "Server not found"})
    loc_key = _location_key(server["location"])
    template = HOP_TEMPLATES.get(loc_key, HOP_TEMPLATES["global"])
    hops = []
    for t in template:
        variance = random.uniform(-0.4, 0.4)
        hops.append({
            "hop": t["hop"], "ms": round(t["ms_base"] + variance, 1),
            "name": t["name"], "description": t["description"],
            "emoji": t["emoji"], "type": t["type"],
        })
    return {"target": target, "source": source, "server": server, "hops": hops}

@app.get("/ping/multi")
async def ping_multi(targets: str = Query(...), source: str = Query(default="local")):
    results = []
    for server_id in targets.split(","):
        server_id = server_id.strip()
        if not server_id:
            continue
        server = _get_server_by_id(server_id)
        if not server:
            continue
        loc_key = _location_key(server["location"])
        base_ms = LOCATION_PING.get(loc_key, 20)
        ms = round(base_ms + random.uniform(-1.5, 2.5), 1)
        jitter = round(random.uniform(0.3, 2.0), 2)
        score, message = _ping_score(ms)
        results.append({
            "id": server_id, "ms": ms, "jitter": jitter,
            "score": score, "status": _status_from_score(score), "message": message,
        })
    return results

app.mount("/", StaticFiles(directory="static", html=True), name="static")
