import sqlite3, json
conn = sqlite3.connect(r'D:\srccode\arsitect\backend\data\sdlc-visualizer.db')
c = conn.cursor()
c.execute("SELECT story_id, title, page_desc, description FROM user_stories WHERE page_desc IS NOT NULL LIMIT 5")
for row in c.fetchall():
    print("=" * 60)
    print("Title:", row[1])
    print("PageDesc:\n", row[2])
    print("Description:\n", row[3] and row[3][:300])
conn.close()
