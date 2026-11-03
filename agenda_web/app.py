from __future__ import annotations

import json
import uuid
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DATA_FILE = Path(__file__).with_name("tasks.json")


def load_data() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        content = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return content if isinstance(content, dict) else {}


def save_data(data: dict) -> None:
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_title(text: str) -> str:
    return " ".join(text.strip().split())


def today_iso() -> str:
    return date.today().isoformat()


def tomorrow_iso(day: str | None = None) -> str:
    source = date.fromisoformat(day) if day else date.today()
    return (source + timedelta(days=1)).isoformat()


def get_day_tasks(data: dict, day: str) -> list[dict]:
    return data.get(day, [])


def add_task(day: str, title: str) -> dict:
    cleaned = normalize_title(title)
    if not cleaned:
        raise ValueError("Le titre de la tâche ne peut pas être vide.")

    data = load_data()
    tasks = data.setdefault(day, [])
    existing = {normalize_title(item.get("title", "")).lower() for item in tasks}
    if cleaned.lower() in existing:
        raise ValueError("Cette tâche existe déjà dans ce programme.")

    task = {
        "id": uuid.uuid4().hex,
        "title": cleaned,
        "done": False,
        "day": day,
    }
    tasks.append(task)
    save_data(data)
    return task


def toggle_task(day: str, task_id: str) -> dict | None:
    data = load_data()
    tasks = data.get(day, [])
    for item in tasks:
        if item.get("id") == task_id:
            item["done"] = not bool(item.get("done"))
            save_data(data)
            return item
    return None


def delete_task(day: str, task_id: str) -> bool:
    data = load_data()
    tasks = data.get(day, [])
    updated = [item for item in tasks if item.get("id") != task_id]
    if len(updated) == len(tasks):
        return False
    data[day] = updated
    save_data(data)
    return True


def finalize_day(day: str) -> dict:
    data = load_data()
    tasks = get_day_tasks(data, day)
    incomplete = [item["title"] for item in tasks if not item.get("done", False)]

    next_day = tomorrow_iso(day)
    next_tasks = data.setdefault(next_day, [])
    existing = {normalize_title(item.get("title", "")).lower() for item in next_tasks}

    for title in incomplete:
        key = normalize_title(title).lower()
        if key not in existing:
            next_tasks.append({
                "id": uuid.uuid4().hex,
                "title": normalize_title(title),
                "done": False,
                "day": next_day,
            })
            existing.add(key)

    save_data(data)

    return {
        "day": day,
        "reported_to": next_day,
        "incomplete": incomplete,
        "message": "Agent IA : les tâches non réalisées ont été reportées au lendemain." if incomplete else "Agent IA : excellent, toutes les tâches ont été respectées.",
    }


@app.get("/")
def index():
    day = request.args.get("day", today_iso())
    return render_template("index.html", selected_day=day)


@app.get("/api/tasks")
def api_get_tasks():
    day = request.args.get("day", today_iso())
    data = load_data()
    return jsonify({"day": day, "tasks": get_day_tasks(data, day)})


@app.post("/api/tasks")
def api_add_task():
    payload = request.get_json(silent=True) or {}
    day = payload.get("day") or today_iso()
    title = payload.get("title") or ""

    try:
        task = add_task(day, title)
        return jsonify({"success": True, "task": task}), 201
    except ValueError as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@app.post("/api/tasks/<task_id>/toggle")
def api_toggle_task(task_id: str):
    payload = request.get_json(silent=True) or {}
    day = payload.get("day") or today_iso()
    task = toggle_task(day, task_id)
    if not task:
        return jsonify({"success": False, "message": "Tâche introuvable."}), 404
    return jsonify({"success": True, "task": task})


@app.delete("/api/tasks/<task_id>")
def api_delete_task(task_id: str):
    payload = request.get_json(silent=True) or {}
    day = payload.get("day") or today_iso()
    removed = delete_task(day, task_id)
    if not removed:
        return jsonify({"success": False, "message": "Tâche introuvable."}), 404
    return jsonify({"success": True})


@app.post("/api/close-day")
def api_close_day():
    payload = request.get_json(silent=True) or {}
    day = payload.get("day") or today_iso()
    result = finalize_day(day)
    return jsonify({"success": True, **result})


if __name__ == "__main__":
    app.run(debug=True)
