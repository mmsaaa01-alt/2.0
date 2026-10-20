# database.py
import json
import os
import threading

DB_FILE = "progress.json"
_LOCK = threading.RLock()   # ✅ RLock = reentrant. Fixes the freeze/deadlock bug.
_CACHE = None               # {"users": {"<user_id>": {topic: True}}}

def _empty():
    return {"users": {}}

def _load_raw():
    if not os.path.exists(DB_FILE):
        return None
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _save_unlocked():
    tmp = DB_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(_CACHE, f, ensure_ascii=False)
    os.replace(tmp, DB_FILE)

def load_progress():
    """Full DB: {"users": {user_id: {topic: True}}}"""
    global _CACHE
    with _LOCK:
        if _CACHE is None:
            raw = _load_raw()
            if raw is None:
                _CACHE = _empty()
            elif isinstance(raw.get("users"), dict):
                _CACHE = raw
            else:
                # Old flat format {topic: bool} -> migrate under "legacy"
                legacy = {k: v for k, v in raw.items() if isinstance(v, bool)}
                _CACHE = {"users": {"legacy": legacy}} if legacy else _empty()
            _save_unlocked()
        return _CACHE

def save_progress():
    with _LOCK:
        if _CACHE is not None:
            _save_unlocked()

def get_user_progress(user_id):
    db = load_progress()
    return db["users"].setdefault(str(user_id), {})

def mark_unit_done(user_id, unit_name=None, done=True):
    # Tolerates old-style call mark_unit_done(topic)
    if unit_name is None:
        user_id, unit_name = "legacy", user_id
    with _LOCK:
        db = load_progress()
        db["users"].setdefault(str(user_id), {})[unit_name] = bool(done)
        _save_unlocked()

def toggle_unit(user_id, unit_name=None):
    # Tolerates old-style call toggle_unit(topic)
    if unit_name is None:
        user_id, unit_name = "legacy", user_id
    with _LOCK:
        db = load_progress()
        u = db["users"].setdefault(str(user_id), {})
        new = not u.get(unit_name, False)
        u[unit_name] = new
        _save_unlocked()
        return new

def is_done(user_id, unit_name=None):
    if unit_name is None:
        user_id, unit_name = "legacy", user_id
    return get_user_progress(user_id).get(unit_name, False)

def merge_restore(data):
    """Merge a restored Telegram backup into current DB (union of done topics)."""
    with _LOCK:
        db = load_progress()
        for uid, topics in (data.get("users") or {}).items():
            if not isinstance(topics, dict):
                continue
            bucket = db["users"].setdefault(str(uid), {})
            for t, v in topics.items():
                if v:
                    bucket[t] = True
        _save_unlocked()

def user_count():
    return len(load_progress()["users"])

def get_subject_stats(curriculum_data, user_id=None):
    if user_id is None:
        user_id = "legacy"
    user_data = get_user_progress(user_id)
    stats = {}
    for key, val in curriculum_data.items():
        if not (key.startswith("Grade 9") or key.startswith("Grade 10")):
            continue
        for month, weeks in val.items():
            for week, days in weeks.items():
                for day, subjects in days.items():
                    for subject, topics in subjects.items():
                        s = stats.setdefault(subject, {"total": 0, "completed": 0})
                        for topic in topics:
                            s["total"] += 1
                            if user_data.get(topic, False):
                                s["completed"] += 1
    return stats