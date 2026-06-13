import sqlite3

DB_PATH = r'D:\srccode\arsitect\backend\data\sdlc-visualizer.db'


def fix_sketches_table(conn: sqlite3.Connection) -> None:
    """Rebuild sketches table if its schema is outdated (legacy columns or old CHECK)."""
    c = conn.cursor()
    c.execute("PRAGMA table_info(sketches)")
    cols = {col[1] for col in c.fetchall()}

    # Determine whether we need to rebuild
    needs_rebuild = False
    legacy_cols = {'image_url', 'annotations'}
    if legacy_cols & cols:
        needs_rebuild = True
        print(f'Found legacy columns: {legacy_cols & cols}')

    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='sketches'")
    create_sql = c.fetchone()[0]
    expected_statuses = (
        "status IN ('DRAFT','GENERATING','GENERATED','REVIEW_PENDING','APPROVED','REJECTED','ARCHIVED')"
    )
    if expected_statuses not in create_sql:
        needs_rebuild = True
        print('Found outdated ck_sketch_status constraint')

    if not needs_rebuild:
        print('sketches schema is up-to-date')
        return

    # SQLite does not support DROP CONSTRAINT; rebuild the table.
    print('Rebuilding sketches table...')
    c.execute('ALTER TABLE sketches RENAME TO sketches_old')
    c.execute('''
        CREATE TABLE sketches (
            sketch_id VARCHAR(36) NOT NULL,
            project_id VARCHAR(36) NOT NULL,
            name VARCHAR(128) NOT NULL,
            source_story_ids TEXT,
            page_count INTEGER,
            coverage_percent INTEGER,
            status VARCHAR(16) NOT NULL DEFAULT 'DRAFT',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (sketch_id),
            CONSTRAINT ck_sketch_status CHECK (
                status IN ('DRAFT','GENERATING','GENERATED','REVIEW_PENDING','APPROVED','REJECTED','ARCHIVED')
            ),
            FOREIGN KEY(project_id) REFERENCES projects (project_id) ON DELETE CASCADE
        )
    ''')
    # Migrate any existing data (column intersection only)
    common_cols = cols & {
        'sketch_id', 'project_id', 'name', 'source_story_ids',
        'page_count', 'coverage_percent', 'status', 'created_at', 'updated_at'
    }
    if common_cols:
        col_list = ', '.join(common_cols)
        c.execute(f'INSERT INTO sketches ({col_list}) SELECT {col_list} FROM sketches_old')
        print(f'Migrated rows: {c.rowcount}')
    c.execute('DROP TABLE sketches_old')
    conn.commit()
    print('sketches table rebuilt successfully')


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON')
    fix_sketches_table(conn)
    conn.close()
    print('Done')


if __name__ == '__main__':
    main()
