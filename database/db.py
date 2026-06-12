# =============================================================================
# database/db.py
# =============================================================================

import os
import hashlib
from datetime import datetime
import pytz

PARIS_TZ = pytz.timezone("Europe/Paris")

def now_paris():
    return datetime.now(PARIS_TZ).strftime("%Y-%m-%d %H:%M:%S")

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    def get_connection():
        return psycopg2.connect(DATABASE_URL)
    def _convert(val):
        return val.strftime('%Y-%m-%d %H:%M:%S') if hasattr(val, 'strftime') else val
    def fetchall_as_dicts(cursor):
        cols = [d[0] for d in cursor.description]
        return [{c: _convert(v) for c, v in zip(cols, row)} for row in cursor.fetchall()]
    def fetchone_as_dict(cursor):
        cols = [d[0] for d in cursor.description]
        row = cursor.fetchone()
        return {c: _convert(v) for c, v in zip(cols, row)} if row else None
    PLACEHOLDER = "%s"
else:
    import sqlite3
    from config import DATABASE_PATH
    def get_connection():
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    def fetchall_as_dicts(cursor):
        return [dict(row) for row in cursor.fetchall()]
    def fetchone_as_dict(cursor):
        row = cursor.fetchone()
        return dict(row) if row else None
    PLACEHOLDER = "?"


def init_database():
    if not DATABASE_URL:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id               SERIAL PRIMARY KEY,
                ref_constructeur TEXT NOT NULL UNIQUE,
                ref_fournisseur  TEXT NOT NULL,
                nom              TEXT NOT NULL,
                description      TEXT,
                quantite         REAL DEFAULT 0,
                quantite_min     REAL DEFAULT 5,
                unite            TEXT DEFAULT 'unité',
                emplacement      TEXT,
                magasin          TEXT,
                fournisseur      TEXT,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id          SERIAL PRIMARY KEY,
                username    TEXT NOT NULL UNIQUE,
                password    TEXT NOT NULL,
                nom_complet TEXT,
                role        TEXT DEFAULT 'lecteur',
                email       TEXT,
                actif       INTEGER DEFAULT 1,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mouvements (
                id                   SERIAL PRIMARY KEY,
                article_id           INTEGER,
                article_nom_snapshot TEXT,
                article_ref_snapshot TEXT,
                user_id              INTEGER,
                operateur_nom        TEXT,
                type                 TEXT NOT NULL,
                quantite             REAL NOT NULL,
                quantite_avant       REAL,
                quantite_apres       REAL,
                emplacement          TEXT,
                commentaire          TEXT,
                created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id)    REFERENCES utilisateurs(id) ON DELETE SET NULL
            )
        """)
        for col_sql in [
            "ALTER TABLE articles ADD COLUMN magasin TEXT",
            "ALTER TABLE articles ADD COLUMN fournisseur TEXT",
            "ALTER TABLE articles ADD COLUMN ref_constructeur TEXT",
            "ALTER TABLE articles ADD COLUMN ref_fournisseur TEXT",
            "ALTER TABLE mouvements ADD COLUMN operateur_nom TEXT",
            "ALTER TABLE mouvements ADD COLUMN emplacement TEXT",
            "ALTER TABLE utilisateurs ADD COLUMN email TEXT",
        ]:
            try:
                cursor.execute(col_sql)
                conn.commit()
            except Exception:
                conn.rollback()
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ref_constructeur TEXT NOT NULL UNIQUE,
                ref_fournisseur  TEXT NOT NULL,
                nom TEXT NOT NULL, description TEXT,
                quantite REAL DEFAULT 0, quantite_min REAL DEFAULT 5,
                unite TEXT DEFAULT 'unité', emplacement TEXT, magasin TEXT,
                fournisseur TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL, nom_complet TEXT, role TEXT DEFAULT 'lecteur',
                email TEXT, actif INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mouvements (
                id INTEGER PRIMARY KEY AUTOINCREMENT, article_id INTEGER,
                article_nom_snapshot TEXT, article_ref_snapshot TEXT,
                user_id INTEGER, operateur_nom TEXT,
                type TEXT NOT NULL, quantite REAL NOT NULL,
                quantite_avant REAL, quantite_apres REAL,
                emplacement TEXT, commentaire TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL,
                FOREIGN KEY (user_id) REFERENCES utilisateurs(id) ON DELETE SET NULL)
        """)
        for col_sql in [
            "ALTER TABLE articles ADD COLUMN magasin TEXT",
            "ALTER TABLE articles ADD COLUMN fournisseur TEXT",
            "ALTER TABLE articles ADD COLUMN ref_constructeur TEXT",
            "ALTER TABLE articles ADD COLUMN ref_fournisseur TEXT",
            "ALTER TABLE mouvements ADD COLUMN operateur_nom TEXT",
            "ALTER TABLE mouvements ADD COLUMN emplacement TEXT",
            "ALTER TABLE utilisateurs ADD COLUMN email TEXT",
        ]:
            try:
                cursor.execute(col_sql)
            except Exception:
                pass

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM utilisateurs")
    row = cursor.fetchone()
    count = row[0] if DATABASE_URL else list(dict(row).values())[0]
    if count == 0:
        _creer_admin_par_defaut(cursor)
        conn.commit()
    conn.close()
    print("✅ Base de données initialisée.")


def _creer_admin_par_defaut(cursor):
    h = hasher_mot_de_passe("admin123")
    p = PLACEHOLDER
    cursor.execute(f"INSERT INTO utilisateurs (username,password,nom_complet,role) VALUES ({p},{p},{p},{p})",
                   ("admin", h, "Administrateur SDEL", "admin"))


def hasher_mot_de_passe(mdp):
    return hashlib.sha256(mdp.encode()).hexdigest()


# =============================================================================
# UTILISATEURS
# =============================================================================

def verifier_utilisateur(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM utilisateurs WHERE username={PLACEHOLDER} AND password={PLACEHOLDER} AND actif=1",
                   (username, hasher_mot_de_passe(password)))
    user = fetchone_as_dict(cursor)
    conn.close()
    return user


def verifier_utilisateur_par_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT id FROM utilisateurs WHERE id={PLACEHOLDER} AND actif=1", (user_id,))
    user = fetchone_as_dict(cursor)
    conn.close()
    return user


def get_tous_utilisateurs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, nom_complet, role, email, actif, created_at FROM utilisateurs")
    users = fetchall_as_dicts(cursor)
    conn.close()
    return users


def get_emails_alertes():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT email FROM utilisateurs
            WHERE actif=1 AND email IS NOT NULL AND email != ''
            AND role IN ('admin','operateur')
        """)
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"[MAIL] get_emails_alertes erreur: {e}")
        return []


def reset_password_utilisateur(user_id, nouveau_mdp):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE utilisateurs SET password={PLACEHOLDER} WHERE id={PLACEHOLDER}",
                   (hasher_mot_de_passe(nouveau_mdp), user_id))
    conn.commit()
    conn.close()


def supprimer_utilisateur(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM utilisateurs WHERE id={PLACEHOLDER}", (user_id,))
    conn.commit()
    conn.close()


def creer_utilisateur(username, password, nom_complet, role, email=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        p = PLACEHOLDER
        cursor.execute(f"INSERT INTO utilisateurs (username,password,nom_complet,role,email) VALUES ({p},{p},{p},{p},{p})",
                       (username, hasher_mot_de_passe(password), nom_complet, role, email or None))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


# =============================================================================
# ARTICLES
# =============================================================================

def get_tous_articles():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *, CASE WHEN quantite <= quantite_min THEN 1 ELSE 0 END AS stock_bas
        FROM articles ORDER BY nom
    """)
    articles = fetchall_as_dicts(cursor)
    conn.close()
    return articles


def get_article_par_id(article_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT *, CASE WHEN quantite <= quantite_min THEN 1 ELSE 0 END AS stock_bas
        FROM articles WHERE id={PLACEHOLDER}
    """, (article_id,))
    article = fetchone_as_dict(cursor)
    conn.close()
    return article


def get_article_par_ref_constructeur(ref_constructeur):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM articles WHERE ref_constructeur={PLACEHOLDER}", (ref_constructeur,))
    article = fetchone_as_dict(cursor)
    conn.close()
    return article


def creer_article(ref_constructeur, ref_fournisseur, nom, description,
                  quantite, quantite_min, unite, emplacement, magasin="", fournisseur=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        p = PLACEHOLDER
        if DATABASE_URL:
            cursor.execute(f"""
                INSERT INTO articles
                (ref_constructeur,ref_fournisseur,nom,description,quantite,quantite_min,unite,emplacement,magasin,fournisseur)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p}) RETURNING id
            """, (ref_constructeur, ref_fournisseur, nom, description,
                  float(quantite), float(quantite_min), unite, emplacement, magasin, fournisseur))
            article_id = cursor.fetchone()[0]
        else:
            cursor.execute(f"""
                INSERT INTO articles
                (ref_constructeur,ref_fournisseur,nom,description,quantite,quantite_min,unite,emplacement,magasin,fournisseur)
                VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
            """, (ref_constructeur, ref_fournisseur, nom, description,
                  float(quantite), float(quantite_min), unite, emplacement, magasin, fournisseur))
            article_id = cursor.lastrowid
        conn.commit()
        return article_id
    except Exception:
        conn.rollback()
        return None
    finally:
        conn.close()


def modifier_article(article_id, ref_fournisseur, nom, description,
                     quantite_min, unite, emplacement, magasin="", fournisseur=""):
    conn = get_connection()
    cursor = conn.cursor()
    p = PLACEHOLDER
    cursor.execute(f"""
        UPDATE articles SET ref_fournisseur={p}, nom={p}, description={p},
        quantite_min={p}, unite={p}, emplacement={p}, magasin={p},
        fournisseur={p}, updated_at={p} WHERE id={p}
    """, (ref_fournisseur, nom, description, float(quantite_min),
          unite, emplacement, magasin, fournisseur, now_paris(), article_id))
    conn.commit()
    conn.close()


def modifier_stock(article_id, nouvelle_quantite, type_mouvement, user_id,
                   commentaire="", operateur_nom=None, emplacement=None):
    conn = get_connection()
    cursor = conn.cursor()
    p = PLACEHOLDER
    cursor.execute(f"""
        SELECT quantite, nom, ref_constructeur, quantite_min, magasin, emplacement
        FROM articles WHERE id={p}
    """, (article_id,))
    row = fetchone_as_dict(cursor)
    if not row:
        conn.close()
        return False, False, None
    quantite_avant = row["quantite"]
    if emplacement:
        cursor.execute(f"UPDATE articles SET quantite={p}, emplacement={p}, updated_at={p} WHERE id={p}",
                       (float(nouvelle_quantite), emplacement, now_paris(), article_id))
    else:
        cursor.execute(f"UPDATE articles SET quantite={p}, updated_at={p} WHERE id={p}",
                       (float(nouvelle_quantite), now_paris(), article_id))
    cursor.execute(f"""
        INSERT INTO mouvements
        (article_id,article_nom_snapshot,article_ref_snapshot,user_id,operateur_nom,
         type,quantite,quantite_avant,quantite_apres,emplacement,commentaire,created_at)
        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})
    """, (article_id, row["nom"], row["ref_constructeur"], user_id, operateur_nom,
          type_mouvement, abs(float(nouvelle_quantite) - float(quantite_avant)),
          float(quantite_avant), float(nouvelle_quantite),
          emplacement or "", commentaire, now_paris()))
    conn.commit()
    conn.close()
    sous_seuil = float(nouvelle_quantite) <= float(row["quantite_min"])
    return True, sous_seuil, row


def supprimer_article(article_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM articles WHERE id={PLACEHOLDER}", (article_id,))
    conn.commit()
    conn.close()


def clear_historique():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mouvements")
    conn.commit()
    conn.close()


# =============================================================================
# IMPORT / EXPORT EXCEL
# =============================================================================

COLONNES_EXCEL = [
    "ref_constructeur", "ref_fournisseur", "nom", "description",
    "quantite", "quantite_min", "unite", "emplacement", "magasin", "fournisseur"
]


def exporter_inventaire_excel():
    articles = get_tous_articles()
    return [{col: a.get(col, "") for col in COLONNES_EXCEL} for a in articles]


def importer_depuis_excel(lignes, user_id, operateur_nom="Import Excel"):
    nb_crees = 0
    nb_mis_a_jour = 0
    erreurs = []

    for i, ligne in enumerate(lignes, start=2):
        ref_c = str(ligne.get("ref_constructeur", "")).strip()
        ref_f = str(ligne.get("ref_fournisseur", "")).strip()
        nom   = str(ligne.get("nom", "")).strip()

        if not ref_c or not ref_f or not nom:
            erreurs.append(f"Ligne {i} : ref_constructeur, ref_fournisseur et nom sont obligatoires.")
            continue

        try:
            quantite = float(ligne.get("quantite", 0) or 0)
        except ValueError:
            quantite = 0

        article_existant = get_article_par_ref_constructeur(ref_c)

        if article_existant:
            nouvelle_quantite = float(article_existant["quantite"]) + quantite
            ok, _, _ = modifier_stock(
                article_existant["id"], nouvelle_quantite, "entree",
                user_id, commentaire="Import Excel", operateur_nom=operateur_nom
            )
            if ok:
                nb_mis_a_jour += 1
            else:
                erreurs.append(f"Ligne {i} : erreur lors de la mise à jour de {ref_c}.")
        else:
            article_id = creer_article(
                ref_constructeur = ref_c,
                ref_fournisseur  = ref_f,
                nom              = nom,
                description      = str(ligne.get("description", "") or ""),
                quantite         = quantite,
                quantite_min     = float(ligne.get("quantite_min", 5) or 5),
                unite            = str(ligne.get("unite", "unité") or "unité"),
                emplacement      = str(ligne.get("emplacement", "") or ""),
                magasin          = str(ligne.get("magasin", "") or ""),
                fournisseur      = str(ligne.get("fournisseur", "") or ""),
            )
            if article_id:
                nb_crees += 1
            else:
                erreurs.append(f"Ligne {i} : impossible de créer {ref_c} (doublon ?).")

    return nb_crees, nb_mis_a_jour, erreurs


# =============================================================================
# HISTORIQUE
# =============================================================================

def get_historique(limite=100):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT m.*, COALESCE(a.nom, m.article_nom_snapshot) AS article_nom,
               COALESCE(a.ref_constructeur, m.article_ref_snapshot) AS article_ref,
               u.nom_complet AS user_nom
        FROM mouvements m
        LEFT JOIN articles a ON m.article_id = a.id
        LEFT JOIN utilisateurs u ON m.user_id = u.id
        ORDER BY m.created_at DESC LIMIT {PLACEHOLDER}
    """, (limite,))
    data = fetchall_as_dicts(cursor)
    conn.close()
    return data


def get_historique_article(article_id, limite=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT m.*, u.nom_complet AS user_nom
        FROM mouvements m
        LEFT JOIN utilisateurs u ON m.user_id = u.id
        WHERE m.article_id = {PLACEHOLDER}
        ORDER BY m.created_at DESC LIMIT {PLACEHOLDER}
    """, (article_id, limite))
    data = fetchall_as_dicts(cursor)
    conn.close()
    return data


# =============================================================================
# STATISTIQUES
# =============================================================================

def get_statistiques():
    conn = get_connection()
    cursor = conn.cursor()
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM articles")
    stats["total_articles"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM articles WHERE quantite <= quantite_min AND quantite > 0")
    stats["stock_bas"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM articles WHERE quantite = 0")
    stats["rupture"] = cursor.fetchone()[0]
    today = datetime.now(PARIS_TZ).strftime("%Y-%m-%d")
    if DATABASE_URL:
        cursor.execute(f"SELECT COUNT(*) FROM mouvements WHERE created_at::date = {PLACEHOLDER}", (today,))
    else:
        cursor.execute(f"SELECT COUNT(*) FROM mouvements WHERE created_at LIKE {PLACEHOLDER}", (f"{today}%",))
    stats["mouvements_aujourd_hui"] = cursor.fetchone()[0]
    conn.close()
    return stats
