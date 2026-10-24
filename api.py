#!/usr/bin/env python3
"""Leaderboard API for Battle Beneath the Sea. Python standard library only, no install.

Run:  python3 api.py          then play at http://localhost:8000 (index.html from file:// works too)
Env:  HOST (default 127.0.0.1), PORT (default 8000)

Anti-cheat: the browser never sends a score.
  1. POST /api/start  -> the server opens a run and remembers when it started (server clock).
  2. During play the game logs every scoring event: [step, code] (step = 1/60 s of play).
  3. POST /api/finish -> the server replays the log with its own points table, checks it is
     possible (real time elapsed, minimum time per mission, enemy unlocks, event rate, one boss
     per boss mission) and stores the score it computed itself. Each run is finished only once.
  4. POST /api/name   -> the player adds a callsign to that stored score.
So `score = 999999` in DevTools or an edited request does nothing: a fake log has to stay within
what a real game can do in the real time spent. A bot that really plays the game is not stopped.
"""
import json, math, os, re, secrets, threading, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', 8000))
ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, 'leaderboard.json')

# Mirror of the game rules in index.html: keep in sync when points, levels or unlocks change
KILL_PTS = {'mine': 10, 'octo': 20, 'diver': 30, 'eel': 40, 'drone': 40, 'boat': 40, 'sub': 50, 'heli': 60, 'beluga': 100}  # x mission
BONUS_PTS = {'coin': 5, 'charge': 5, 'brk': 5, 'shot': 5, 'sam': 10, 'asm': 20}  # flat
BOSS_HP = {4: 10, 5: 20}             # boss pts = hp x 50 x mission
FROM_LEVEL = {'beluga': 2, 'diver': 2, 'eel': 2}
STEPS_PER_S = 60
EVENTS_PER_S = 1                     # a bot firing nonstop scored about 0.3 events per second
CLOCK_SLACK = 1.05                   # the game may run a bit fast against the server clock
RUN_TTL = 4 * 3600                   # an unfinished run expires after 4 h
STARTS_PER_HOUR = 60                 # per IP
MAX_EVENTS, MAX_BODY, TOP, KEEP = 20000, 512 * 1024, 10, 200


def level_steps(level):
    """Fewest play steps to finish a mission: levelLen / scroll, as in startLevel()."""
    return math.ceil((3000 + level * 900) / min(2, 0.8 + (level - 1) * 0.15) * 0.99)


def score_run(events, steps):
    """Replay the event log. Returns (score, level) or raises ValueError with the reason."""
    if not isinstance(steps, int) or not isinstance(events, list) or steps < 0 or len(events) > MAX_EVENTS:
        raise ValueError('bad log')
    score, level, level_start, last, n_level, boss_down, whales = 0, 1, 0, 0, 0, False, 0
    for ev in events:
        if not (isinstance(ev, list) and len(ev) == 2 and isinstance(ev[0], int) and isinstance(ev[1], str)):
            raise ValueError('bad event')
        step, code = ev
        if step < last or step > steps:
            raise ValueError('event out of order')
        last = step
        if code == 'L':  # mission accomplished, next one starts
            if step - level_start < level_steps(level):
                raise ValueError('mission %d too fast' % level)
            if level in BOSS_HP and not boss_down:
                raise ValueError('boss %d not sunk' % level)
            level, level_start, n_level, boss_down, whales = level + 1, step, 0, False, 0
            continue
        n_level += 1
        if n_level > (step - level_start) * EVENTS_PER_S / STEPS_PER_S + 30:
            raise ValueError('scoring too fast')
        if code == 'boss':
            if level not in BOSS_HP or boss_down or step - level_start < level_steps(level):
                raise ValueError('impossible boss')
            boss_down = True
            score += BOSS_HP[level] * 50 * level
        elif code in KILL_PTS:
            if code == 'beluga':
                whales += 1
                if whales > max(0, 2 * level - 3):  # exactly 2 x mission - 3 whales per mission
                    raise ValueError('too many belugas')
            if level < FROM_LEVEL.get(code, 1):
                raise ValueError('%s before mission %d' % (code, FROM_LEVEL[code]))
            score += KILL_PTS[code] * level
        elif code in BONUS_PTS:
            score += BONUS_PTS[code]
        else:
            raise ValueError('unknown event')
    return score, level


class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.runs = {}      # id -> {start, ip, done, score, level, named}
        self.starts = {}    # ip -> [start times] (rate limit)
        try:
            with open(DB) as f:
                self.board = json.load(f)
        except (OSError, ValueError):
            self.board = []

    def save(self):
        tmp = DB + '.tmp'
        with open(tmp, 'w') as f:
            json.dump(self.board, f, indent=1)
        os.replace(tmp, DB)  # atomic: no half-written file

    def top(self):
        return self.board[:TOP]

    def rank(self, score):
        return 1 + sum(1 for e in self.board if e['score'] >= score)


store = Store()
NAME_RE = re.compile(r'[^A-Z0-9 _.-]')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, fmt, *args):
        if self.path.startswith('/api/'):
            super().log_message(fmt, *args)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')  # the game also runs from file://
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        super().end_headers()

    def reply(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/leaderboard':
            with store.lock:
                return self.reply(200, {'top': store.top()})
        if self.path.split('?')[0] not in ('/', '/index.html'):  # serve the game only, not api.py or the data
            return self.reply(404, {'error': 'not found'})
        self.path = '/index.html'
        super().do_GET()

    def do_POST(self):
        try:
            n = int(self.headers.get('Content-Length', 0))
            if n > MAX_BODY:
                return self.reply(413, {'error': 'too big'})
            data = json.loads(self.rfile.read(n) or b'{}')
            if not isinstance(data, dict):
                raise ValueError
        except ValueError:
            return self.reply(400, {'error': 'bad json'})
        route = {'/api/start': self.api_start, '/api/finish': self.api_finish, '/api/name': self.api_name}.get(self.path)
        if not route:
            return self.reply(404, {'error': 'not found'})
        with store.lock:
            return route(data)

    def api_start(self, data):
        now, ip = time.time(), self.client_address[0]
        for rid in [k for k, r in store.runs.items() if now - r['start'] > RUN_TTL]:
            del store.runs[rid]
        recent = [t for t in store.starts.get(ip, []) if now - t < 3600]
        if len(recent) >= STARTS_PER_HOUR:
            return self.reply(429, {'error': 'too many games'})
        store.starts[ip] = recent + [now]
        rid = secrets.token_urlsafe(18)
        store.runs[rid] = {'start': now, 'ip': ip, 'done': False, 'named': False}
        return self.reply(200, {'id': rid})

    def api_finish(self, data):
        run = store.runs.get(data.get('id'))
        if not run or run['done']:
            return self.reply(404, {'error': 'unknown run'})
        run['done'] = True  # one shot: a rejected log can't be retried
        steps = data.get('steps')
        try:
            if not isinstance(steps, int) or steps > (time.time() - run['start']) * STEPS_PER_S * CLOCK_SLACK + 120:
                raise ValueError('faster than real time')
            score, level = score_run(data.get('events'), steps)
        except ValueError as e:
            self.log_message('rejected run: %s', e)
            return self.reply(422, {'error': 'run rejected'})
        run.update(score=score, level=level)
        return self.reply(200, {'score': score, 'level': level, 'rank': store.rank(score), 'top': store.top()})

    def api_name(self, data):
        run = store.runs.get(data.get('id'))
        if not run or 'score' not in run or run['named']:
            return self.reply(404, {'error': 'unknown run'})
        name = NAME_RE.sub('', str(data.get('name', '')).upper()).strip()[:12] or 'UNKNOWN'
        run['named'] = True
        entry = {'name': name, 'score': run['score'], 'level': run['level'], 'date': time.strftime('%Y-%m-%d'), 'id': data['id'][:8]}
        store.board.append(entry)
        store.board.sort(key=lambda e: -e['score'])  # stable: equal scores keep the older entry first
        del store.board[KEEP:]
        store.save()
        rank = store.board.index(entry) + 1 if entry in store.board else None
        return self.reply(200, {'rank': rank, 'top': store.top()})


if __name__ == '__main__':
    print('Leaderboard API on http://%s:%d  (game at /, data in %s)' % (HOST, PORT, DB))
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
