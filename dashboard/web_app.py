"""
Application web Flask pour visualiser les tendances YouTube
"""
from flask import Flask, render_template, jsonify, request, send_file, abort, Response, stream_with_context
import json
import os
from datetime import datetime
from collections import Counter
import multiprocessing
import sys
from pathlib import Path
import time
import subprocess

# Safe __file__ fallback
try:
    _current_file = Path(__file__).resolve()
except NameError:
    _current_file = Path(os.getcwd()) / 'dashboard' / 'web_app.py'

# Add yt_title_psychology directory to path to import utiles
sys.path.insert(0, str(_current_file.parents[1] / 'yt_title_psychology'))

# optional: import helpers to read status
try:
    # Try the package-qualified import first (helps linters/IDEs resolve the module)
    from yt_title_psychology.utiles import read_scrape_status  # type: ignore
except Exception:
    try:
        # Fallback to a plain import if running from the project root
        from utiles import read_scrape_status  # type: ignore
    except Exception:
        # Final fallback: provide a noop implementation so the app can continue running
        def read_scrape_status():
            return {}

app = Flask(__name__, template_folder='templates')

# Config: optional secret token and rate limit in seconds
app.config.setdefault('SCRAPE_SECRET', os.environ.get('SCRAPE_SECRET'))
app.config.setdefault('RATE_LIMIT_SECONDS', int(os.environ.get('RATE_LIMIT_SECONDS', '120')))
app.config.setdefault('LAST_SCRAPE_TRIGGER', {})  # maps ip -> timestamp

def charger_donnees():
    """Charge les données depuis MongoDB si disponible, sinon depuis JSON.

    Ordre de priorité:
    1. MongoDB (si connexion configurée et disponible)
    2. Fichier JSON actif (runs/<id>/tendances_youtube.json)
    3. Fichier JSON du run le plus récent
    4. Fallback parsing strategies (concatenated JSON, line-by-line)
    """
    # Check if MongoDB is disabled via environment variable
    use_mongodb = os.environ.get('USE_MONGODB', 'true').lower() in ('true', '1', 'yes')
    
    # Try MongoDB first only if enabled
    if use_mongodb:
        try:
            # Prefer package-qualified import (helps when running from project root or packaging)
            try:
                from yt_title_psychology.utiles import MongoClientWrapper  # type: ignore
            except Exception:
                try:
                    from utiles import MongoClientWrapper  # type: ignore
                except Exception:
                    MongoClientWrapper = None

            if MongoClientWrapper:
                mongo_uri = os.environ.get('MONGO_URI', 'mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/?appName=LocalCluster')
                mongo_db = os.environ.get('MONGO_DATABASE', 'youtube')
                mongo_collection = os.environ.get('MONGO_COLLECTION', 'youtube')
                
                # Use shorter timeout (2 seconds instead of 5)
                mongo_client = MongoClientWrapper(mongo_uri, mongo_db, mongo_collection, timeout_ms=2000)
                mongo_client.connect()
                # fetch all documents from collection
                cursor = mongo_client.collection.find({}).sort('date_scraping', -1)
                docs = list(cursor)
                mongo_client.close()
                if docs:
                    # Convert ObjectId to string for JSON serialization
                    for doc in docs:
                        if '_id' in doc:
                            doc['_id'] = str(doc['_id'])
                    print(f"Chargement depuis MongoDB: {len(docs)} documents")
                    return docs
        except Exception as e:
            print(f"MongoDB non disponible, fallback sur JSON: {e}")
    
    # Fallback to JSON files
    # Prefer the active run's output file (runs/<id>/tendances_youtube.json) if present.
    json_file = Path('tendances_youtube.json')

    try:
        _active = app.config.get('ACTIVE_SCRAPES', {})
        # check active scrapes first (most-recent)
        for pid, proc in reversed(list(_active.items())):
            try:
                if hasattr(proc, 'run_dir'):
                    candidate = Path(getattr(proc, 'run_dir')) / 'tendances_youtube.json'
                    if candidate.exists():
                        json_file = candidate
                        break
            except Exception:
                continue

        # if no active-run file, fallback to the most recent run folder on disk
        if not json_file.exists():
            project_root = _current_file.parents[1]
            runs_dir = project_root / 'runs'
            if runs_dir.exists():
                # pick latest run folder by mtime
                candidates = [d for d in runs_dir.iterdir() if d.is_dir()]
                if candidates:
                    latest = max(candidates, key=lambda d: d.stat().st_mtime)
                    candidate = latest / 'tendances_youtube.json'
                    if candidate.exists():
                        json_file = candidate

        if not json_file.exists():
            return []

        try:
            content = json_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Erreur lors de l'ouverture du fichier JSON: {e}")
            return []

    except Exception as e:
        print(f"Erreur lors de la preparation du fichier JSON: {e}")
        return []

    # Try simple load first
    try:
        data = json.loads(content)
        return data if isinstance(data, list) else []
    except Exception:
        pass

    # Try to decode multiple JSON values sequentially (handles concatenated JSON)
    try:
        decoder = json.JSONDecoder()
        idx = 0
        n = len(content)
        items = []
        while idx < n:
            # skip whitespace and commas
            while idx < n and content[idx] in '\n\r\t \u00A0,':
                idx += 1
            if idx >= n:
                break
            obj, end = decoder.raw_decode(content, idx)
            idx = end
            # If the decoded object is a list, extend; else append
            if isinstance(obj, list):
                items.extend(obj)
            else:
                items.append(obj)
        if items:
            return items
    except Exception:
        pass

    # Fallback: try line-by-line JSON (NDJSON-ish)
    try:
        videos = []
        for line in content.split('\n'):
            line = line.strip().rstrip(',')
            if not line or line in ('[', ']'):
                continue
            try:
                videos.append(json.loads(line))
            except Exception:
                continue
        return videos
    except Exception as e:
        print(f"Erreur lors du parsing fallback JSON: {e}")
        return []

@app.route('/')
def index():
    """Page d'accueil"""
    # Add a cache-busting version to static asset URLs
    try:
        ver = int(datetime.now().timestamp())
    except Exception:
        ver = 0
    return render_template('index.html', version=ver)


@app.route('/api/scrape/progress-sse')
def scrape_progress_sse():
    """SSE endpoint streaming scrape_status.json updates for a given run.

    Query param: run=<run_id> (optional). If not provided, uses active run.
    """
    run_id = request.args.get('run')
    project_root = _current_file.parents[1]

    # Determine status file
    status_path = None
    if run_id:
        candidate = project_root / 'runs' / run_id / 'scrape_status.json'
        if candidate.exists():
            status_path = candidate
    else:
        # prefer active run
        _active = app.config.get('ACTIVE_SCRAPES', {})
        for pid, proc in reversed(list(_active.items())):
            try:
                if hasattr(proc, 'run_dir'):
                    candidate = Path(getattr(proc, 'run_dir')) / 'scrape_status.json'
                    if candidate.exists():
                        status_path = candidate
                        break
            except Exception:
                continue

    # fallback to global
    if status_path is None:
        candidate = project_root / 'scrape_status.json'
        if candidate.exists():
            status_path = candidate

    def generate():
        last_mtime = 0
        while True:
            try:
                if status_path and status_path.exists():
                    mtime = status_path.stat().st_mtime
                    if mtime != last_mtime:
                        last_mtime = mtime
                        try:
                            data = status_path.read_text(encoding='utf-8')
                            yield f"data: {data}\n\n"
                        except Exception:
                            pass
                time.sleep(0.8)
            except GeneratorExit:
                break
            except Exception:
                time.sleep(1)

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/stats')
def get_stats():
    """API pour obtenir les statistiques"""
    videos = charger_donnees()
    
    if not videos:
        return jsonify({
            'total': 0,
            'message': 'Aucune donnée disponible'
        })
    
    # Calculer les statistiques
    total = len(videos)
    pays_count = Counter(v.get('pays', 'Unknown') for v in videos)
    canaux_count = Counter(v.get('canal', 'Unknown') for v in videos)
    
    # Scores psychologiques
    scores = [v.get('score_psychologique', 0) for v in videos if v.get('score_psychologique')]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    # Features moyennes
    longueurs = [v.get('features', {}).get('longueur', 0) for v in videos]
    emojis = [v.get('features', {}).get('nb_emojis', 0) for v in videos]
    hashtags = [v.get('features', {}).get('nb_hashtags', 0) for v in videos]
    exclamations = [v.get('features', {}).get('nb_exclamations', 0) for v in videos]
    questions = [v.get('features', {}).get('nb_questions', 0) for v in videos]
    majuscules = [v.get('features', {}).get('pourcentage_majuscules', 0) for v in videos]
    
    return jsonify({
        'total': total,
        'avg_score': round(avg_score, 2),
        'pays': dict(pays_count.most_common(10)),
        'top_canaux': dict(canaux_count.most_common(10)),
        'features_moyennes': {
            'longueur': round(sum(longueurs) / len(longueurs), 1) if longueurs else 0,
            'emojis': round(sum(emojis) / len(emojis), 2) if emojis else 0,
            'hashtags': round(sum(hashtags) / len(hashtags), 2) if hashtags else 0,
            'exclamations': round(sum(exclamations) / len(exclamations), 2) if exclamations else 0,
            'questions': round(sum(questions) / len(questions), 2) if questions else 0,
            'majuscules': round(sum(majuscules) / len(majuscules), 2) if majuscules else 0
        }
    })

@app.route('/api/videos')
def get_videos():
    """API pour obtenir la liste des vidéos"""
    videos = charger_donnees()
    
    # Trier par score psychologique décroissant
    videos_sorted = sorted(videos, 
                          key=lambda x: x.get('score_psychologique', 0), 
                          reverse=True)
    
    return jsonify(videos_sorted)

@app.route('/api/top/<int:n>')
def get_top_videos(n):
    """API pour obtenir le top N des vidéos"""
    videos = charger_donnees()
    
    # Trier par score psychologique décroissant
    videos_sorted = sorted(videos, 
                          key=lambda x: x.get('score_psychologique', 0), 
                          reverse=True)
    
    return jsonify(videos_sorted[:n])

@app.route('/api/scrape', methods=['POST'])
def start_scraping():
    """API pour lancer le scraping"""
    # Spawn a separate Python process that runs the Scrapy crawler programmatically.
    # We use a separate process so Twisted's reactor can be started/cleaned up safely.
    # Check rate-limit / auth
    allowed, msg, code = _check_scrape_allowed(request)
    if not allowed:
        return jsonify({'status': 'error', 'message': msg}), code

    try:
        p = _spawn_scrape_process('tendances_youtube.json')

        return jsonify({
            'status': 'started',
            'message': 'Scraping lance avec succes',
            'pid': p.pid
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


def _check_scrape_allowed(req):
    """Return (allowed, message, status_code). Implements optional secret and basic rate-limiting by IP."""
    secret = app.config.get('SCRAPE_SECRET')
    rate_limit = int(app.config.get('RATE_LIMIT_SECONDS', 120))

    # If a secret is configured, require it (header X-Scrape-Token or JSON body secret)
    if secret:
        token = req.headers.get('X-Scrape-Token') or (req.get_json(silent=True) or {}).get('secret')
        if not token or str(token) != str(secret):
            return False, 'Unauthorized: invalid scrape token', 401

    # Rate-limit by remote IP to avoid accidental repeated triggers
    ip = req.headers.get('X-Forwarded-For', req.remote_addr)
    last = app.config.setdefault('LAST_SCRAPE_TRIGGER', {})
    now = time.time()
    last_ts = last.get(ip)
    if last_ts and (now - last_ts) < rate_limit:
        return False, f'Rate limit: please wait {int(rate_limit - (now - last_ts))}s', 429

    # record trigger
    last[ip] = now
    app.config['LAST_SCRAPE_TRIGGER'] = last
    return True, 'ok', 200


def _spawn_scrape_process(output_file: str = 'tendances_youtube.json'):
    """Start a child Scrapy process writing into a run-specific directory and register it.

    Returns a subprocess.Popen object with attributes `run_dir` and `run_id` set.
    """
    project_root = _current_file.parents[1]

    # Create runs dir if needed
    runs_dir = project_root / 'runs'
    runs_dir.mkdir(exist_ok=True)

    # Build run id and directory (timestamp)
    base_id = datetime.now().strftime('%Y%m%dT%H%M%S')
    run_dir = runs_dir / base_id
    i = 1
    while run_dir.exists():
        run_dir = runs_dir / f"{base_id}-{i}"
        i += 1
    run_dir.mkdir()

    # Paths for this run
    out_file = run_dir / output_file
    log_file = run_dir / 'scrape_output.log'
    status_file = run_dir / 'scrape_status.json'

    python_exe = sys.executable or 'python'
    cmd = [python_exe, '-m', 'scrapy', 'crawl', 'youtube_trends', '-o', str(out_file), '-s', f'LOG_FILE={str(log_file)}', '-s', 'LOG_LEVEL=INFO']

    print(f"[DEBUG] Starting scrape process:")
    print(f"[DEBUG]   Command: {' '.join(cmd)}")
    print(f"[DEBUG]   CWD: {project_root}")
    print(f"[DEBUG]   Run dir: {run_dir}")
    print(f"[DEBUG]   Log file: {log_file}")

    # Prepare environment for child process: pass SCRAPE_RUN_DIR so spider writes status there
    env = os.environ.copy()
    env['SCRAPE_RUN_DIR'] = str(run_dir)

    # Open log file for child stdout/stderr
    try:
        logf = open(str(log_file), 'a', encoding='utf-8')
    except Exception:
        logf = None

    creationflags = 0
    if os.name == 'nt':
        try:
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
        except Exception:
            creationflags = 0

    try:
        p = subprocess.Popen(cmd, cwd=str(project_root), env=env, stdout=logf or subprocess.DEVNULL, stderr=logf or subprocess.DEVNULL, creationflags=creationflags)
        print(f"[DEBUG] Process started with PID: {p.pid}")
    except Exception as e:
        with open(project_root / 'scrape_error.log', 'a', encoding='utf-8') as ef:
            ef.write(f"{datetime.utcnow().isoformat()} - spawn subprocess failed: {e}\n")
        raise

    # Save run metadata
    meta = {
        'run_id': run_dir.name,
        'started_at': datetime.now().isoformat(),
        'pid': p.pid,
        'out_file': str(out_file),
        'log_file': str(log_file),
        'status_file': str(status_file)
    }
    try:
        with open(run_dir / 'meta.json', 'w', encoding='utf-8') as mf:
            json.dump(meta, mf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # register process for status checks
    _active_scrapes = app.config.setdefault('ACTIVE_SCRAPES', {})
    _active_scrapes[p.pid] = p
    app.config['ACTIVE_SCRAPES'] = _active_scrapes  # Ensure it's saved back

    # attach run info
    setattr(p, 'run_dir', str(run_dir))
    setattr(p, 'run_id', run_dir.name)
    
    # Debug logging
    print(f"[DEBUG] Spawned process PID {p.pid}, registered in ACTIVE_SCRAPES")
    print(f"[DEBUG] ACTIVE_SCRAPES now contains: {list(_active_scrapes.keys())}")
    
    return p

@app.route('/api/scrape/status')
def scraping_status():
    """API pour vérifier si un scraping est en cours"""
    import psutil

    scraping = False
    active = []

    # First check processes we spawned and stored in app config
    _active_scrapes = app.config.setdefault('ACTIVE_SCRAPES', {})
    
    print(f"[DEBUG] Status check: ACTIVE_SCRAPES contains {len(_active_scrapes)} processes: {list(_active_scrapes.keys())}")
    
    # Get progress information from status file first (to check if finished)
    progress_data = {}
    scrape_finished = False
    
    for pid, proc in list(_active_scrapes.items()):
        try:
            # Check status file first to see if scraping is actually finished
            print(f"[DEBUG] PID {pid}: Checking for run_dir attribute...")
            if hasattr(proc, 'run_dir'):
                from pathlib import Path
                print(f"[DEBUG] PID {pid}: run_dir = {proc.run_dir}")
                status_file = Path(proc.run_dir) / 'scrape_status.json'
                print(f"[DEBUG] PID {pid}: Checking status file: {status_file}")
                if status_file.exists():
                    import json
                    progress_data = json.loads(status_file.read_text(encoding='utf-8'))
                    print(f"[DEBUG] PID {pid}: Status file content: status={progress_data.get('status')}, countries={progress_data.get('countries_done')}/{progress_data.get('countries_total')}, items={progress_data.get('items_scraped')}")
                    
                    # Check if status is 'finished' OR if all countries are processed
                    is_finished = progress_data.get('status') == 'finished'
                    countries_done = progress_data.get('countries_done', 0)
                    countries_total = progress_data.get('countries_total')
                    items_scraped = progress_data.get('items_scraped', 0)
                    
                    # Consider finished if explicitly marked OR if all countries done with items scraped
                    # Only check progress if countries_total is not None
                    progress_complete = (countries_total is not None and 
                                       countries_total > 0 and 
                                       countries_done >= countries_total and 
                                       items_scraped > 0)
                    
                    if is_finished or progress_complete:
                        scrape_finished = True
                        print(f"[DEBUG] PID {pid}: Scraping considered finished (explicit={is_finished}, progress complete={progress_complete})")
                        # Remove from active scrapes
                        _active_scrapes.pop(pid, None)
                        active.append({'pid': pid, 'alive': False, 'status': 'finished'})
                        continue
                else:
                    print(f"[DEBUG] PID {pid}: Status file does not exist")
            else:
                print(f"[DEBUG] PID {pid}: No run_dir attribute found")
            
            # Check if process is still alive
            alive = None
            if hasattr(proc, 'poll'):
                poll_result = proc.poll()
                alive = (poll_result is None)
                print(f"[DEBUG] PID {pid}: poll() returned {poll_result}, alive={alive}")
            elif hasattr(proc, 'is_alive'):
                alive = proc.is_alive()
                print(f"[DEBUG] PID {pid}: is_alive() returned {alive}")

            if alive:
                scraping = True
                active.append({'pid': pid, 'alive': True})
                print(f"[DEBUG] PID {pid} is ALIVE, scraping=True")
            else:
                active.append({'pid': pid, 'alive': False})
                _active_scrapes.pop(pid, None)
                print(f"[DEBUG] PID {pid} is DEAD, removed from ACTIVE_SCRAPES")
        except Exception as e:
            print(f"[DEBUG] PID {pid}: Exception checking status: {e}")
            _active_scrapes.pop(pid, None)

    # Fallback: search for scrapy processes in system process list (only if not finished)
    if not scraping and not scrape_finished:
        print(f"[DEBUG] No active scrapes detected, checking psutil for scrapy processes...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline') or []
                if cmdline and any('scrapy' in str(c) for c in cmdline):
                    scraping = True
                    active.append({'pid': proc.info.get('pid'), 'alive': True, 'cmdline': cmdline})
                    print(f"[DEBUG] Found scrapy process via psutil: PID {proc.info.get('pid')}")
                    break
            except Exception as e:
                pass
    
    print(f"[DEBUG] Final status: scraping={scraping}, scrape_finished={scrape_finished}, active={active}")
    
    result = {
        'scraping': scraping,
        'active': active,
        'videos_count': len(charger_donnees())
    }
    
    # Add progress data if available
    if progress_data:
        result.update(progress_data)
    
    return jsonify(result)


@app.route('/api/scrape/stop', methods=['POST'])
def stop_scraping():
    """API pour arrêter le scraping en cours"""
    import signal
    
    stopped_pids = []
    errors = []
    
    # Get active scrapes
    _active_scrapes = app.config.setdefault('ACTIVE_SCRAPES', {})
    
    for pid, proc in list(_active_scrapes.items()):
        try:
            # Check if process is still alive
            alive = None
            if hasattr(proc, 'poll'):
                alive = (proc.poll() is None)
            elif hasattr(proc, 'is_alive'):
                alive = proc.is_alive()
            
            if alive:
                # Try to terminate gracefully
                if hasattr(proc, 'terminate'):
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)  # Wait up to 5 seconds
                    except:
                        # Force kill if still running
                        if hasattr(proc, 'kill'):
                            proc.kill()
                stopped_pids.append(pid)
            
            # Remove from active list
            _active_scrapes.pop(pid, None)
        except Exception as e:
            errors.append(f"PID {pid}: {str(e)}")
            _active_scrapes.pop(pid, None)
    
    if stopped_pids or not _active_scrapes:
        return jsonify({
            'status': 'stopped',
            'message': f'Scraping arrêté. PIDs: {stopped_pids}',
            'stopped_pids': stopped_pids,
            'errors': errors if errors else None
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Aucun scraping actif trouvé',
            'errors': errors if errors else None
        }), 404


@app.route('/api/scrape/wait', methods=['POST'])
def start_scraping_and_wait():
    """Start scraping and wait until it finishes or a timeout (seconds) occurs.

    Request JSON may include { "timeout": 120 } to set a timeout in seconds.
    """
    from flask import request

    try:
        payload = request.get_json(silent=True) or {}
        timeout = int(payload.get('timeout', 300))
    except Exception:
        timeout = 300

    try:
        p = _spawn_scrape_process('tendances_youtube.json')
        # Wait for completion or timeout (works for subprocess.Popen)
        finished = False
        try:
            # subprocess.Popen.wait accepts timeout
            if hasattr(p, 'wait'):
                p.wait(timeout)
                finished = True
            else:
                # fallback for multiprocessing.Process
                p.join(timeout)
                finished = not p.is_alive()
        except Exception:
            # timeout or other issue
            finished = (not hasattr(p, 'poll')) or (p.poll() is not None)
        result = {
            'pid': p.pid,
            'finished': finished,
            'videos_count': len(charger_donnees())
        }

        if not finished:
            result['message'] = 'Timeout reached; scrape still running'

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape/logs')
def scrape_logs():
    """Server-Sent Events endpoint streaming the Scrapy log file (scrape_output.log).

    Clients can connect and will receive new log lines as they are appended.
    """
    from flask import Response, stream_with_context

    # Prefer active run's log if available
    log_path = Path('scrape_output.log')
    _active_scrapes = app.config.setdefault('ACTIVE_SCRAPES', {})
    # pick the most recent active process that has run_dir
    for pid, proc in reversed(list(_active_scrapes.items())):
        try:
            if hasattr(proc, 'poll') and proc.poll() is None and hasattr(proc, 'run_dir'):
                candidate = Path(getattr(proc, 'run_dir')) / 'scrape_output.log'
                if candidate.exists():
                    log_path = candidate
                    break
        except Exception:
            continue

    def generate():
        # If file doesn't exist yet, wait until it appears
        last_size = 0
        while True:
            try:
                if log_path.exists():
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as lf:
                        lf.seek(last_size)
                        while True:
                            line = lf.readline()
                            if not line:
                                break
                            last_size = lf.tell()
                            yield f"data: {line.strip()}\n\n"
                # sleep briefly
                import time
                time.sleep(0.5)
            except GeneratorExit:
                break
            except Exception:
                import time
                time.sleep(1)

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/scrape/logs/download')
def download_logs():
    """Return the scrape log file as an attachment if available."""
    # Prefer latest run's log if available
    log_file = Path('scrape_output.log')
    _active_scrapes = app.config.setdefault('ACTIVE_SCRAPES', {})
    for pid, proc in reversed(list(_active_scrapes.items())):
        try:
            if hasattr(proc, 'run_dir'):
                candidate = Path(getattr(proc, 'run_dir')) / 'scrape_output.log'
                if candidate.exists():
                    log_file = candidate
                    break
        except Exception:
            continue
    if not log_file.exists():
        return jsonify({'error': 'No log file available'}), 404
    try:
        return send_file(str(log_file), as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


### Runs API
@app.route('/api/runs')
def list_runs():
    """List past runs under the runs/ directory with meta information."""
    project_root = _current_file.parents[1]
    runs_dir = project_root / 'runs'
    runs = []
    if not runs_dir.exists():
        return jsonify([])

    for child in sorted(runs_dir.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        meta_file = child / 'meta.json'
        meta = {}
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text(encoding='utf-8'))
            except Exception:
                meta = {}
        else:
            # fallback: minimal meta
            meta = {'run_id': child.name, 'started_at': datetime.utcfromtimestamp(child.stat().st_mtime).isoformat()}
        runs.append(meta)
    return jsonify(runs)


@app.route('/api/runs/<run_id>/meta')
def run_meta(run_id):
    project_root = _current_file.parents[1]
    meta_file = project_root / 'runs' / run_id / 'meta.json'
    if not meta_file.exists():
        return jsonify({'error': 'run not found'}), 404
    try:
        return jsonify(json.loads(meta_file.read_text(encoding='utf-8')))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/<run_id>/status')
def run_status(run_id):
    project_root = _current_file.parents[1]
    status_file = project_root / 'runs' / run_id / 'scrape_status.json'
    if not status_file.exists():
        return jsonify({}), 200
    try:
        return jsonify(json.loads(status_file.read_text(encoding='utf-8')))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/runs/<run_id>/logs')
def run_logs(run_id):
    """SSE stream for a specific run's log file."""
    project_root = _current_file.parents[1]
    log_path = project_root / 'runs' / run_id / 'scrape_output.log'
    if not log_path.exists():
        return jsonify({'error': 'log not found'}), 404

    def generate():
        last_size = 0
        while True:
            try:
                if log_path.exists():
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as lf:
                        lf.seek(last_size)
                        while True:
                            line = lf.readline()
                            if not line:
                                break
                            last_size = lf.tell()
                            yield f"data: {line.strip()}\n\n"
                import time
                time.sleep(0.5)
            except GeneratorExit:
                break
            except Exception:
                import time
                time.sleep(1)

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@app.route('/api/runs/<run_id>/logs/download')
def run_logs_download(run_id):
    project_root = _current_file.parents[1]
    log_file = project_root / 'runs' / run_id / 'scrape_output.log'
    if not log_file.exists():
        return jsonify({'error': 'no log for run'}), 404
    try:
        return send_file(str(log_file), as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scrape/progress')
def scrape_progress():
    """Return the current scrape progress written by the spider (scrape_status.json)."""
    try:
        # Prefer active run status file
        _active_scrapes = app.config.setdefault('ACTIVE_SCRAPES', {})
        for pid, proc in reversed(list(_active_scrapes.items())):
            try:
                if hasattr(proc, 'run_dir'):
                    status_path = Path(getattr(proc, 'run_dir')) / 'scrape_status.json'
                    if status_path.exists():
                        return jsonify(json.loads(status_path.read_text(encoding='utf-8')))
            except Exception:
                continue

        data = read_scrape_status() or {}
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/clear', methods=['POST'])
def clear_database():
    """Efface toutes les données de MongoDB et tous les fichiers JSON dans runs/.
    
    Cette fonctionnalité permet de repartir à zéro pour une démonstration en direct.
    """
    try:
        cleared = {
            'mongodb': False,
            'json_files': 0,
            'runs_deleted': 0
        }
        
        # Always try to clear MongoDB first
        try:
            from pymongo import MongoClient
            mongo_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://admin:admin@localcluster.ovkh1ky.mongodb.net/')
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            db = client['youtube']
            collection = db['youtube']
            
            # Delete all documents
            result = collection.delete_many({})
            cleared['mongodb'] = True
            cleared['mongodb_deleted_count'] = result.deleted_count
            
            print(f"MongoDB effacée: {result.deleted_count} documents supprimés")
        except Exception as e:
            print(f"Impossible d'effacer MongoDB: {e}")
        
        # Clear all JSON files in runs/
        project_root = _current_file.parents[1]
        runs_dir = project_root / 'runs'
        
        if runs_dir.exists():
            import shutil
            for run_folder in runs_dir.iterdir():
                if run_folder.is_dir():
                    try:
                        # Count JSON files before deletion
                        json_files = list(run_folder.glob('*.json'))
                        cleared['json_files'] += len(json_files)
                        
                        # Delete entire run folder
                        shutil.rmtree(run_folder)
                        cleared['runs_deleted'] += 1
                    except Exception as e:
                        print(f"Erreur lors de la suppression de {run_folder}: {e}")
        
        print(f"Base de données nettoyée: {cleared['runs_deleted']} runs supprimés, {cleared['json_files']} fichiers JSON effacés")
        
        return jsonify({
            'success': True,
            'message': f"Base de données effacée avec succès",
            'details': cleared
        })
        
    except Exception as e:
        print(f"Erreur lors du nettoyage de la base de données: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("=" * 80)
    print("Serveur web demarre sur http://localhost:5000")
    print("=" * 80)
    # Disable debug/reloader for more predictable behavior when spawning subprocesses
    app.run(debug=False, host='0.0.0.0', port=5000)
