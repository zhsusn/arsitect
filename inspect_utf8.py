import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r'D:\srccode\arsitect\backend\data\sdlc-visualizer.db')
c = conn.cursor()
c.execute("SELECT title, page_desc FROM user_stories WHERE page_desc IS NOT NULL LIMIT 5")
for row in c.fetchall():
    print("=" * 60)
    print("Title:", row[0])
    print("PageDesc:")
    print(row[1])
conn.close()
