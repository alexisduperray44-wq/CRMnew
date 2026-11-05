from datetime import date, timedelta

import db

db.init_db()

conn = db.get_db()
conn.execute("DELETE FROM actions")
conn.execute("DELETE FROM signaux")
conn.execute("DELETE FROM presse")
conn.execute("DELETE FROM feedbacks")
conn.execute("DELETE FROM comptes_rendus")
conn.execute("DELETE FROM opportunites")
conn.execute("DELETE FROM missions")
conn.execute("DELETE FROM contacts")
conn.execute("DELETE FROM societes")
conn.commit()

today = date.today()

s1 = db.execute(
    "INSERT INTO societes (nom, secteur, taille, site, note) VALUES (?,?,?,?,?)",
    ("Novatech", "ESN / conseil IT", "ETI", "https://novatech.example", "Client historique, forte appétence data."),
)
s2 = db.execute(
    "INSERT INTO societes (nom, secteur, taille, site, note) VALUES (?,?,?,?,?)",
    ("Banque Riviera", "Banque de détail", "Grand compte", "https://riviera.example", "Dossiers sensibles, circuit de décision long."),
)
s3 = db.execute(
    "INSERT INTO societes (nom, secteur, taille, site, note) VALUES (?,?,?,?,?)",
    ("GreenMobility", "Mobilité durable", "PME", "https://greenmobility.example", "Startup en croissance."),
)

db.execute(
    "INSERT INTO contacts (societe_id, prenom, nom, email, telephone, poste) VALUES (?,?,?,?,?,?)",
    (s1, "Claire", "Bertrand", "c.bertrand@novatech.example", "06 11 22 33 44", "DSI"),
)
db.execute(
    "INSERT INTO contacts (societe_id, prenom, nom, email, telephone, poste) VALUES (?,?,?,?,?,?)",
    (s1, "Marc", "Dubois", "m.dubois@novatech.example", "06 55 66 77 88", "RSSI"),
)
db.execute(
    "INSERT INTO contacts (societe_id, prenom, nom, email, telephone, poste) VALUES (?,?,?,?,?,?)",
    (s2, "Inès", "Fabre", "i.fabre@riviera.example", "06 99 88 77 66", "Directrice digitale"),
)
db.execute(
    "INSERT INTO contacts (societe_id, prenom, nom, email, telephone, poste) VALUES (?,?,?,?,?,?)",
    (s3, "Yanis", "Kaci", "y.kaci@greenmobility.example", "06 12 34 56 78", "CEO"),
)

m1 = db.execute(
    "INSERT INTO missions (societe_id, titre, consultant, statut, date_debut, date_fin) VALUES (?,?,?,?,?,?)",
    (s1, "Audit sécurité 2024", "Marc D.", "terminee", str(today - timedelta(days=120)), str(today - timedelta(days=30))),
)
db.execute(
    "INSERT INTO missions (societe_id, titre, consultant, statut, date_debut, date_fin) VALUES (?,?,?,?,?,?)",
    (s1, "Accompagnement migration cloud", "Claire B.", "en cours", str(today - timedelta(days=10)), None),
)
db.execute(
    "INSERT INTO missions (societe_id, titre, consultant, statut, date_debut, date_fin) VALUES (?,?,?,?,?,?)",
    (s2, "Refonte portail client", "Équipe Riviera", "en cours", str(today - timedelta(days=60)), None),
)

db.execute(
    "INSERT INTO opportunites (societe_id, titre, montant, etape, probabilite, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
    (s1, "Plateforme data lake", 180000, "devis", 50, str(today - timedelta(days=40)), str(today - timedelta(days=40))),
)
db.execute(
    "INSERT INTO opportunites (societe_id, titre, montant, etape, probabilite, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
    (s2, "Application mobile client", 320000, "prospect", 20, str(today - timedelta(days=5)), str(today - timedelta(days=5))),
)
db.execute(
    "INSERT INTO opportunites (societe_id, titre, montant, etape, probabilite, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
    (s3, "Pilot IoT bornes de recharge", 45000, "negociation", 70, str(today - timedelta(days=15)), str(today - timedelta(days=2))),
)

db.execute(
    "INSERT INTO comptes_rendus (societe_id, contact_id, date, type, contenu) VALUES (?,?,?,?,?)",
    (s2, None, str(today - timedelta(days=80)), "note", "Point projet portail : avancement conforme, recette prévue en juin."),
)
db.execute(
    "INSERT INTO comptes_rendus (societe_id, contact_id, date, type, contenu) VALUES (?,?,?,?,?)",
    (s3, None, str(today - timedelta(days=3)), "visio", "Yanis valide le périmètre IoT, attend le chiffrage final."),
)

db.execute(
    "INSERT INTO feedbacks (societe_id, mission_id, note, commentaire, date) VALUES (?,?,?,?,?)",
    (s1, m1, 2, "Mission livrée en retard, attentes pas totalement couvertes.", str(today - timedelta(days=25))),
)
db.execute(
    "INSERT INTO feedbacks (societe_id, mission_id, note, commentaire, date) VALUES (?,?,?,?,?)",
    (s3, None, 5, "Équipe très réactive et force de proposition.", str(today - timedelta(days=3))),
)

db.execute(
    "INSERT INTO presse (societe_id, titre, source, date, resume) VALUES (?,?,?,?,?)",
    (s1, "Novatech rachète un éditeur de data", "Les Échos Tech", str(today - timedelta(days=2)), "Opportunité de cross-sell sur la data."),
)
db.execute(
    "INSERT INTO presse (societe_id, titre, source, date, resume) VALUES (?,?,?,?,?)",
    (s2, "La banque Riviera accélère sur l'IA générative", "Le Figaro Économie", str(today - timedelta(days=6)), "Sujet à partager avec Inès Fabre."),
)

conn.close()
print("Données de démo insérées.")
