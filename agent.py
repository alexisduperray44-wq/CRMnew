from datetime import date, timedelta

from db import execute, query

JOURS_INACTIVITE = 45
JOURS_DEvis = 30


def _derniere_activite(societe_id):
    row = query(
        """
        SELECT MAX(d) AS d FROM (
            SELECT MAX(date) AS d FROM comptes_rendus WHERE societe_id = ?
            UNION ALL
            SELECT MAX(created_at) AS d FROM actions WHERE societe_id = ?
            UNION ALL
            SELECT MAX(date) AS d FROM feedbacks WHERE societe_id = ?
        )
        """,
        (societe_id, societe_id, societe_id),
        one=True,
    )
    return row["d"] if row and row["d"] else None


def _creer_signal(societe_id, type_, message, gravite, action_titre, action_desc, priorite):
    existe = query(
        "SELECT id FROM signaux WHERE societe_id = ? AND type = ? AND traite = 0",
        (societe_id, type_),
        one=True,
    )
    if existe:
        return 0
    execute(
        "INSERT INTO signaux (societe_id, type, message, gravite) VALUES (?, ?, ?, ?)",
        (societe_id, type_, message, gravite),
    )
    execute(
        """
        INSERT INTO actions (societe_id, titre, description, origine, priorite, statut_tri, statut)
        VALUES (?, ?, ?, 'agent', ?, 'propose', 'a_faire')
        """,
        (societe_id, action_titre, action_desc, priorite),
    )
    return 1


def run_agent():
    crees = 0
    societes = query("SELECT id, nom FROM societes")
    for s in societes:
        sid, nom = s["id"], s["nom"]

        dernier = _derniere_activite(sid)
        if dernier is None or date.fromisoformat(dernier[:10]) < date.today() - timedelta(days=JOURS_INACTIVITE):
            crees += _creer_signal(
                sid, "relance",
                f"Aucun compte rendu depuis plus de {JOURS_INACTIVITE} jours chez {nom}.",
                "risque",
                f"Reprendre contact avec {nom}",
                "Envoyer un message de relance et proposer un point d'avancement.",
                "haute",
            )

        fb = query(
            "SELECT note, commentaire, date FROM feedbacks WHERE societe_id = ? ORDER BY date DESC LIMIT 1",
            (sid,), one=True,
        )
        if fb and fb["note"] is not None and fb["note"] <= 2:
            crees += _creer_signal(
                sid, "feedback_negatif",
                f"Dernier avis de {nom} : {fb['note']}/5. Risque de satisfaction client.",
                "risque",
                f"Plan d'action correctif pour {nom}",
                "Analyser le commentaire du dernier avis et proposer des mesures correctives.",
                "haute",
            )

        opp = query(
            """
            SELECT titre, etape, updated_at FROM opportunites
            WHERE societe_id = ? AND etape NOT IN ('gagne', 'perdu')
            ORDER BY updated_at DESC LIMIT 1
            """,
            (sid,), one=True,
        )
        if opp and date.fromisoformat(opp["updated_at"][:10]) < date.today() - timedelta(days=JOURS_DEvis):
            crees += _creer_signal(
                sid, "opportunite",
                f"L'opportunité '{opp['titre']}' ({opp['etape']}) n'a pas bougé depuis plus de {JOURS_DEvis} jours.",
                "opportunite",
                f"Relancer l'opportunité '{opp['titre']}'",
                "Vérifier l'avancement du dossier côté client et mettre à jour l'étape.",
                "moyenne",
            )

        mission_sans_fb = query(
            """
            SELECT m.titre FROM missions m
            WHERE m.societe_id = ? AND m.statut = 'terminee'
              AND NOT EXISTS (SELECT 1 FROM feedbacks f WHERE f.mission_id = m.id)
            LIMIT 1
            """,
            (sid,), one=True,
        )
        if mission_sans_fb:
            crees += _creer_signal(
                sid, "feedback_manquant",
                f"La mission '{mission_sans_fb['titre']}' est terminée sans avis client.",
                "info",
                f"Demander un avis sur la mission '{mission_sans_fb['titre']}'",
                "Solliciter un feedback de satisfaction sur la mission livrée.",
                "basse",
            )

        art = query(
            "SELECT titre, source FROM presse WHERE societe_id = ? ORDER BY date DESC LIMIT 1",
            (sid,), one=True,
        )
        if art:
            crees += _creer_signal(
                sid, "veille",
                f"Veille : '{art['titre']}' ({art['source']}) pourrait intéresser {nom}.",
                "opportunite",
                f"Partager l'article '{art['titre']}' avec {nom}",
                "Envoyer la veille au client avec un commentaire personnalisé (cross-sell / référence).",
                "basse",
            )

    return crees
