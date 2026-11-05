import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "crm.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS societes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    secteur TEXT,
    taille TEXT,
    site TEXT,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    prenom TEXT NOT NULL,
    nom TEXT NOT NULL,
    email TEXT,
    telephone TEXT,
    poste TEXT
);
CREATE TABLE IF NOT EXISTS missions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    titre TEXT NOT NULL,
    consultant TEXT,
    statut TEXT DEFAULT 'en cours',
    date_debut TEXT,
    date_fin TEXT
);
CREATE TABLE IF NOT EXISTS opportunites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    titre TEXT NOT NULL,
    montant REAL,
    etape TEXT DEFAULT 'prospect',
    probabilite INTEGER DEFAULT 20,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS comptes_rendus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL,
    date TEXT DEFAULT (date('now')),
    type TEXT DEFAULT 'note',
    contenu TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedbacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    mission_id INTEGER REFERENCES missions(id) ON DELETE SET NULL,
    note INTEGER,
    commentaire TEXT,
    date TEXT DEFAULT (date('now'))
);
CREATE TABLE IF NOT EXISTS presse (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    titre TEXT NOT NULL,
    source TEXT,
    date TEXT DEFAULT (date('now')),
    resume TEXT
);
CREATE TABLE IF NOT EXISTS signaux (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    gravite TEXT DEFAULT 'info',
    created_at TEXT DEFAULT (datetime('now')),
    traite INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    societe_id INTEGER REFERENCES societes(id) ON DELETE CASCADE,
    titre TEXT NOT NULL,
    description TEXT,
    origine TEXT DEFAULT 'manuel',
    priorite TEXT DEFAULT 'normale',
    statut_tri TEXT DEFAULT 'propose',
    statut TEXT DEFAULT 'a_faire',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def query(sql, params=(), one=False):
    conn = get_db()
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id
