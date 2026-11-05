from flask import Flask, redirect, render_template, request, url_for

import agent
import db

app = Flask(__name__)
app.secret_key = "crm-maison-dev"

db.init_db()

ETAPES_OPP = ["prospect", "devis", "negociation", "gagne", "perdu"]
STATUTS_MISSION = ["en cours", "terminee", "en pause"]
STATUTS_TRI = ["propose", "accepte", "modifie", "rejete"]
STATUTS_BACKLOG = ["a_faire", "en_cours", "fait"]
PRIORITES = ["basse", "normale", "moyenne", "haute"]


@app.route("/")
def dashboard():
    stats = {
        "societes": db.query("SELECT COUNT(*) c FROM societes")[0]["c"],
        "contacts": db.query("SELECT COUNT(*) c FROM contacts")[0]["c"],
        "opportunites": db.query("SELECT COUNT(*) c FROM opportunites WHERE etape NOT IN ('gagne','perdu')")[0]["c"],
        "en_cours": db.query("SELECT COUNT(*) c FROM actions WHERE statut != 'fait' AND statut_tri IN ('accepte','modifie')")[0]["c"],
    }
    signaux = db.query(
        """
        SELECT s.*, so.nom AS societe FROM signaux s
        JOIN societes so ON so.id = s.societe_id
        WHERE s.traite = 0 ORDER BY
        CASE s.gravite WHEN 'risque' THEN 0 WHEN 'opportunite' THEN 1 ELSE 2 END, s.created_at DESC
        LIMIT 20
        """
    )
    backlog = db.query(
        """
        SELECT a.*, so.nom AS societe FROM actions a
        JOIN societes so ON so.id = a.societe_id
        WHERE a.statut_tri IN ('accepte','modifie') AND a.statut != 'fait'
        ORDER BY CASE a.priorite WHEN 'haute' THEN 0 WHEN 'moyenne' THEN 1 ELSE 2 END, a.created_at
        LIMIT 20
        """
    )
    return render_template("dashboard.html", stats=stats, signaux=signaux, backlog=backlog)


@app.route("/societes")
def societes():
    rows = db.query(
        """
        SELECT so.*, (SELECT COUNT(*) FROM contacts c WHERE c.societe_id = so.id) AS nb_contacts
        FROM societes so ORDER BY so.nom
        """
    )
    return render_template("societes.html", societes=rows)


@app.route("/societes/new", methods=["GET", "POST"])
def societe_new():
    if request.method == "POST":
        db.execute(
            "INSERT INTO societes (nom, secteur, taille, site, note) VALUES (?,?,?,?,?)",
            (request.form["nom"], request.form.get("secteur"), request.form.get("taille"),
             request.form.get("site"), request.form.get("note")),
        )
        return redirect(url_for("societes"))
    return render_template("societe_form.html", societe=None)


@app.route("/societes/<int:sid>")
def societe_detail(sid):
    so = db.query("SELECT * FROM societes WHERE id = ?", (sid,), one=True)
    if not so:
        return "Société introuvable", 404
    data = {
        "contacts": db.query("SELECT * FROM contacts WHERE societe_id = ? ORDER BY nom", (sid,)),
        "missions": db.query("SELECT * FROM missions WHERE societe_id = ? ORDER BY date_debut DESC", (sid,)),
        "opportunites": db.query("SELECT * FROM opportunites WHERE societe_id = ? ORDER BY updated_at DESC", (sid,)),
        "crs": db.query(
            """SELECT cr.*, c.nom AS contact_nom, c.prenom AS contact_prenom FROM comptes_rendus cr
               LEFT JOIN contacts c ON c.id = cr.contact_id
               WHERE cr.societe_id = ? ORDER BY cr.date DESC""", (sid,)),
        "feedbacks": db.query(
            """SELECT f.*, m.titre AS mission_titre FROM feedbacks f
               LEFT JOIN missions m ON m.id = f.mission_id
               WHERE f.societe_id = ? ORDER BY f.date DESC""", (sid,)),
        "presse": db.query("SELECT * FROM presse WHERE societe_id = ? ORDER BY date DESC", (sid,)),
        "actions": db.query("SELECT * FROM actions WHERE societe_id = ? ORDER BY created_at DESC", (sid,)),
    }
    return render_template("societe_detail.html", societe=so, data=data,
                           etapes=ETAPES_OPP, statuts_mission=STATUTS_MISSION)


@app.route("/societes/<int:sid>/edit", methods=["GET", "POST"])
def societe_edit(sid):
    so = db.query("SELECT * FROM societes WHERE id = ?", (sid,), one=True)
    if not so:
        return "Société introuvable", 404
    if request.method == "POST":
        db.execute(
            "UPDATE societes SET nom=?, secteur=?, taille=?, site=?, note=? WHERE id=?",
            (request.form["nom"], request.form.get("secteur"), request.form.get("taille"),
             request.form.get("site"), request.form.get("note"), sid),
        )
        return redirect(url_for("societe_detail", sid=sid))
    return render_template("societe_form.html", societe=so)


@app.route("/societes/<int:sid>/delete", methods=["POST"])
def societe_delete(sid):
    db.execute("DELETE FROM societes WHERE id = ?", (sid,))
    return redirect(url_for("societes"))


@app.route("/contacts")
def contacts():
    rows = db.query(
        """SELECT c.*, so.nom AS societe FROM contacts c
           LEFT JOIN societes so ON so.id = c.societe_id ORDER BY c.nom, c.prenom"""
    )
    return render_template("contacts.html", contacts=rows)


@app.route("/contacts/new", methods=["GET", "POST"])
def contact_new():
    if request.method == "POST":
        db.execute(
            "INSERT INTO contacts (societe_id, prenom, nom, email, telephone, poste) VALUES (?,?,?,?,?,?)",
            (request.form.get("societe_id") or None, request.form["prenom"], request.form["nom"],
             request.form.get("email"), request.form.get("telephone"), request.form.get("poste")),
        )
        return redirect(url_for("contacts"))
    return render_template("contact_form.html", contact=None,
                           societes=db.query("SELECT id, nom FROM societes ORDER BY nom"))


@app.route("/contacts/<int:cid>/edit", methods=["GET", "POST"])
def contact_edit(cid):
    c = db.query("SELECT * FROM contacts WHERE id = ?", (cid,), one=True)
    if not c:
        return "Contact introuvable", 404
    if request.method == "POST":
        db.execute(
            "UPDATE contacts SET societe_id=?, prenom=?, nom=?, email=?, telephone=?, poste=? WHERE id=?",
            (request.form.get("societe_id") or None, request.form["prenom"], request.form["nom"],
             request.form.get("email"), request.form.get("telephone"), request.form.get("poste"), cid),
        )
        return redirect(url_for("contacts"))
    return render_template("contact_form.html", contact=c,
                           societes=db.query("SELECT id, nom FROM societes ORDER BY nom"))


@app.route("/contacts/<int:cid>/delete", methods=["POST"])
def contact_delete(cid):
    db.execute("DELETE FROM contacts WHERE id = ?", (cid,))
    return redirect(url_for("contacts"))


def _add_sous_entite(table, sid, fields, redirect_endpoint="societe_detail"):
    values = [request.form.get(f) or None for f in fields]
    placeholders = ",".join("?" for _ in fields)
    db.execute(
        f"INSERT INTO {table} (societe_id, {','.join(fields)}) VALUES (?, {placeholders})",
        [sid] + values,
    )
    return redirect(url_for(redirect_endpoint, sid=sid))


@app.route("/societes/<int:sid>/mission/new", methods=["POST"])
def mission_new(sid):
    return _add_sous_entite("missions", sid, ["titre", "consultant", "statut", "date_debut", "date_fin"])


@app.route("/societes/<int:sid>/opportunite/new", methods=["POST"])
def opportunite_new(sid):
    db.execute(
        "INSERT INTO opportunites (societe_id, titre, montant, etape, probabilite) VALUES (?,?,?,?,?)",
        (sid, request.form["titre"], request.form.get("montant") or None,
         request.form.get("etape", "prospect"), request.form.get("probabilite", 20)),
    )
    return redirect(url_for("societe_detail", sid=sid))


@app.route("/societes/<int:sid>/opportunite/<int:oid>/etape", methods=["POST"])
def opportunite_etape(sid, oid):
    db.execute(
        "UPDATE opportunites SET etape = ?, updated_at = datetime('now') WHERE id = ?",
        (request.form["etape"], oid),
    )
    return redirect(url_for("societe_detail", sid=sid))


@app.route("/societes/<int:sid>/cr/new", methods=["POST"])
def cr_new(sid):
    db.execute(
        "INSERT INTO comptes_rendus (societe_id, contact_id, date, type, contenu) VALUES (?,?,?,?,?)",
        (sid, request.form.get("contact_id") or None, request.form.get("date"),
         request.form.get("type", "note"), request.form["contenu"]),
    )
    return redirect(url_for("societe_detail", sid=sid))


@app.route("/societes/<int:sid>/feedback/new", methods=["POST"])
def feedback_new(sid):
    db.execute(
        "INSERT INTO feedbacks (societe_id, mission_id, note, commentaire, date) VALUES (?,?,?,?,?)",
        (sid, request.form.get("mission_id") or None, request.form.get("note") or None,
         request.form.get("commentaire"), request.form.get("date")),
    )
    return redirect(url_for("societe_detail", sid=sid))


@app.route("/societes/<int:sid>/presse/new", methods=["POST"])
def presse_new(sid):
    return _add_sous_entite("presse", sid, ["titre", "source", "date", "resume"])


@app.route("/opportunites")
def opportunites():
    rows = db.query(
        """SELECT o.*, so.nom AS societe FROM opportunites o
           JOIN societes so ON so.id = o.societe_id
           WHERE o.etape NOT IN ('gagne','perdu')
           ORDER BY CASE o.etape WHEN 'prospect' THEN 0 WHEN 'devis' THEN 1 ELSE 2 END, o.montant DESC"""
    )
    return render_template("opportunites.html", opportunites=rows, etapes=ETAPES_OPP)


@app.route("/backlog")
def backlog():
    a_trier = db.query(
        """SELECT a.*, so.nom AS societe FROM actions a JOIN societes so ON so.id = a.societe_id
           WHERE a.statut_tri = 'propose' ORDER BY a.created_at"""
    )
    a_faire = db.query(
        """SELECT a.*, so.nom AS societe FROM actions a JOIN societes so ON so.id = a.societe_id
           WHERE a.statut_tri IN ('accepte','modifie') AND a.statut = 'a_faire'
           ORDER BY CASE a.priorite WHEN 'haute' THEN 0 WHEN 'moyenne' THEN 1 ELSE 2 END"""
    )
    en_cours = db.query(
        """SELECT a.*, so.nom AS societe FROM actions a JOIN societes so ON so.id = a.societe_id
           WHERE a.statut_tri IN ('accepte','modifie') AND a.statut = 'en_cours'
           ORDER BY a.created_at"""
    )
    fait = db.query(
        """SELECT a.*, so.nom AS societe FROM actions a JOIN societes so ON so.id = a.societe_id
           WHERE a.statut = 'fait' ORDER BY a.updated_at DESC LIMIT 30"""
    )
    return render_template("backlog.html", a_trier=a_trier, a_faire=a_faire,
                           en_cours=en_cours, fait=fait, statuts_tri=STATUTS_TRI,
                           statuts=STATUTS_BACKLOG, priorites=PRIORITES)


@app.route("/actions/new", methods=["GET", "POST"])
def action_new():
    if request.method == "POST":
        db.execute(
            """INSERT INTO actions (societe_id, titre, description, origine, priorite, statut_tri, statut)
               VALUES (?,?,?,?,?,?,?)""",
            (request.form.get("societe_id"), request.form["titre"], request.form.get("description"),
             "manuel", request.form.get("priorite", "normale"), "accepte", "a_faire"),
        )
        return redirect(url_for("backlog"))
    return render_template("action_form.html", action=None,
                           societes=db.query("SELECT id, nom FROM societes ORDER BY nom"),
                           priorites=PRIORITES)


@app.route("/actions/<int:aid>/tri", methods=["POST"])
def action_tri(aid):
    statut_tri = request.form.get("statut_tri", "accepte")
    if statut_tri not in STATUTS_TRI:
        statut_tri = "accepte"
    db.execute(
        "UPDATE actions SET statut_tri = ?, updated_at = datetime('now') WHERE id = ?",
        (statut_tri, aid),
    )
    if statut_tri == "accepte" or statut_tri == "modifie":
        db.execute(
            "UPDATE signaux SET traite = 1 WHERE societe_id = (SELECT societe_id FROM actions WHERE id = ?) AND traite = 0",
            (aid,),
        )
    return redirect(url_for("backlog"))


@app.route("/actions/<int:aid>/statut", methods=["POST"])
def action_statut(aid):
    statut = request.form.get("statut", "a_faire")
    if statut not in STATUTS_BACKLOG:
        statut = "a_faire"
    db.execute(
        "UPDATE actions SET statut = ?, updated_at = datetime('now') WHERE id = ?",
        (statut, aid),
    )
    return redirect(url_for("backlog"))


@app.route("/actions/<int:aid>/edit", methods=["GET", "POST"])
def action_edit(aid):
    a = db.query("SELECT * FROM actions WHERE id = ?", (aid,), one=True)
    if not a:
        return "Action introuvable", 404
    if request.method == "POST":
        db.execute(
            "UPDATE actions SET societe_id=?, titre=?, description=?, priorite=?, statut_tri=?, statut=?, updated_at=datetime('now') WHERE id=?",
            (request.form.get("societe_id"), request.form["titre"], request.form.get("description"),
             request.form.get("priorite", "normale"), request.form.get("statut_tri", "propose"),
             request.form.get("statut", "a_faire"), aid),
        )
        return redirect(url_for("backlog"))
    return render_template("action_form.html", action=a,
                           societes=db.query("SELECT id, nom FROM societes ORDER BY nom"),
                           priorites=PRIORITES)


@app.route("/actions/<int:aid>/delete", methods=["POST"])
def action_delete(aid):
    db.execute("DELETE FROM actions WHERE id = ?", (aid,))
    return redirect(url_for("backlog"))


@app.route("/signaux/<int:sid>/traiter", methods=["POST"])
def signal_traiter(sid):
    db.execute("UPDATE signaux SET traite = 1 WHERE id = ?", (sid,))
    return redirect(url_for("dashboard"))


@app.route("/agent/run", methods=["POST"])
def agent_run():
    n = agent.run_agent()
    return redirect(url_for("dashboard") + f"?agent={n}")


@app.route("/societes/<int:sid>/<table>/<int:rid>/delete", methods=["POST"])
def sous_entite_delete(sid, table, rid):
    allowed = {"missions", "opportunites", "comptes_rendus", "feedbacks", "presse"}
    if table not in allowed:
        return "Table interdite", 400
    db.execute(f"DELETE FROM {table} WHERE id = ?", (rid,))
    return redirect(url_for("societe_detail", sid=sid))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
