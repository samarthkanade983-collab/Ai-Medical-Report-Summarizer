import sqlite3
import json
import traceback

try:
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM history ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    
    hist = []
    for r in rows:
        hist.append({
            'id': r['id'],
            'date_time': r['date_time'],
            'summary': r['summary'],
            'issues': json.loads(r['issues']) if r['issues'] else [],
            'diseases': json.loads(r['diseases']) if r['diseases'] else [],
            'text': r['report_text'],
            'data': json.loads(r['extracted_data']) if r['extracted_data'] else {}
        })
    print("SUCCESS", len(hist))
except Exception as e:
    traceback.print_exc()
