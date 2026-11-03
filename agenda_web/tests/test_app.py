import json
import os

from app import add_task, finalize_day, load_data


def test_add_task_and_finalize_day(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.environ.pop('FLASK_ENV', None)

    task = add_task('2026-10-23', 'Lire 20 pages')
    assert task['title'] == 'Lire 20 pages'

    task2 = add_task('2026-10-23', 'Faire du sport')
    assert task2['title'] == 'Faire du sport'

    data = load_data()
    data['2026-10-23'][0]['done'] = False
    data['2026-10-23'][1]['done'] = True
    with open('tasks.json', 'w', encoding='utf-8') as f:
        json.dump(data, f)

    result = finalize_day('2026-10-23')
    assert result['incomplete'] == ['Lire 20 pages']
    assert result['reported_to'] == '2026-10-24'

    next_data = load_data()
    pending = next_data['2026-10-24']
    assert any(item['title'] == 'Lire 20 pages' for item in pending)
