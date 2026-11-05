# CRM Maison

Petit CRM web local (Flask + SQLite) construit selon l'architecture fonctionnelle :

- **Fiche client 360** : société + contacts, missions, opportunités, comptes rendus, feedbacks, presse & veille, actions.
- **Couche agent** : règles locales qui détectent des signaux (inactivité, avis négatif, opportunité bloquée, mission sans avis, veille) et proposent des actions prioritaires.
- **Cockpit commercial** : tri des propositions (accepter / modifier / rejeter) puis backlog (à faire → en cours → fait).

## Lancement

```bash
cd crm
python3 seed.py        # données de démo (optionnel)
python3 app.py         # http://127.0.0.1:5000
```

## Parcours

1. Ouvrir le **Cockpit** et cliquer sur « Lancer l'agent » pour générer signaux et actions.
2. Consulter les **Sociétés** → fiche 360 par client.
3. Gérer le **Backlog** : trier les propositions, puis avancer les actions.
4. Suivre le **pipeline** dans Opportunités.

## Structure

```
crm/
├── app.py       # routes Flask
├── db.py        # schéma SQLite + helpers
├── agent.py     # moteur de règles (signaux → actions)
├── seed.py      # données de démo
├── templates/   # vues Jinja
└── static/      # CSS
```

Les connecteurs Outlook/Gmail du schéma d'origine sont remplacés ici par une saisie manuelle structurée (CR, presse, feedbacks) ; la couche IA est remplacée par un moteur de règles local, sans dépendance externe.
