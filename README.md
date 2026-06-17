<div align="center">

# 🚀 FileServer Pro

### Solution Professionnelle de Centralisation et de Transfert Documentaire

### 👨‍💻 Développé par Omar Badrani

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&size=24&duration=3000&pause=1000&color=00BFFF&center=true&vCenter=true&width=900&lines=Centralisation+des+Documents;Transfert+Sécurisé+des+Fichiers;Suivi+Temps+Réel+des+Clients;Gestion+Documentaire+Professionnelle;Dashboard+et+Historique+Avancés" />

<br>

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-purple?style=for-the-badge)
![TCP/IP](https://img.shields.io/badge/Network-TCP/IP-success?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

# 📖 Présentation

**FileServer Pro** est une application client-serveur développée en Python permettant la réception, la centralisation, l'organisation et la supervision des transferts de fichiers sur un réseau local.

L'application a été conçue pour les entreprises, ateliers, services administratifs et environnements nécessitant un système fiable de gestion documentaire.

---

# ✨ Fonctionnalités

## 🔐 Authentification Sécurisée

- Connexion utilisateur sécurisée
- Gestion des sessions
- Protection contre les accès non autorisés
- Hachage des mots de passe

## 📁 Gestion Documentaire

- Réception automatique des fichiers
- Organisation par département
- Structure de stockage centralisée
- Navigation rapide dans les dossiers

## 📊 Tableau de Bord

- Nombre total de fichiers reçus
- Volume de données transférées
- Nombre de postes connectés
- Activité récente en temps réel

## 🖥️ Supervision Réseau

- Liste des clients connectés
- Adresse IP et nom des postes
- État des connexions
- Historique des connexions

## 📋 Historique des Transferts

- Date et heure
- Utilisateur
- Poste source
- Taille du fichier
- Dossier de destination

## 📝 Journalisation

- Logs temps réel
- Archivage automatique
- Traçabilité complète des opérations

---

# 🏗️ Architecture Générale

```mermaid
flowchart LR

A[🖥️ Atelier]
B[💼 Administration]
C[👨‍💼 RH]
D[📊 Comptabilité]
E[🌐 Commercial]

A --> S
B --> S
C --> S
D --> S
E --> S

S[🚀 FileServer Pro]

S --> F[📁 Stockage Central]
S --> G[📊 Dashboard]
S --> H[📋 Historique]
S --> I[📝 Logs]
```

---

# 🔄 Cycle de Traitement

```mermaid
sequenceDiagram

participant Client
participant Serveur
participant Stockage

Client->>Serveur: Envoi du fichier
Serveur->>Serveur: Vérification
Serveur->>Stockage: Sauvegarde
Serveur->>Serveur: Historisation
Serveur->>Client: Confirmation
```

---

# 📂 Structure du Projet

```text
FileServer-Pro/
│
├── server_app.py
├── client_app.py
├── requirements.txt
│
├── assets/
│   ├── icons/
│   └── images/
│
├── data/
│   ├── Production/
│   ├── Administration/
│   ├── RH/
│   ├── Commercial/
│   ├── Comptabilite/
│   ├── Informatique/
│   └── Logistique/
│
└── .logs/
    ├── connections.json
    ├── transfers.json
    └── archives/
```

---

# 📂 Organisation des Documents

```text
ServeurData/
│
├── Production/
├── Administration/
├── Commercial/
├── RH/
├── Comptabilite/
├── Informatique/
├── Logistique/
│
└── .logs/
```

---

# 📊 Tableau de Bord

Le dashboard permet de visualiser :

| Information | Description |
|------------|------------|
| 📄 Fichiers reçus | Nombre total de fichiers |
| 💾 Volume transféré | Quantité de données reçues |
| 🖥️ Clients connectés | Nombre de postes actifs |
| 📅 Activité du jour | Transferts quotidiens |
| 📋 Historique récent | Dernières opérations |

---

# 🔒 Sécurité

- Authentification sécurisée
- Hachage des mots de passe
- Journalisation complète
- Historique permanent
- Gestion des utilisateurs
- Contrôle des connexions
- Traçabilité des opérations

---

# ⚙️ Technologies Utilisées

| Technologie | Description |
|------------|------------|
| Python | Langage principal |
| CustomTkinter | Interface graphique moderne |
| Socket TCP/IP | Communication réseau |
| JSON | Stockage des données |
| Threading | Gestion multi-clients |
| Hashlib | Sécurité |
| Pillow | Gestion des images |

---

# 🚀 Installation

## Clonage

```bash
git clone https://github.com/omarbadrani/FileServer-Pro.git

cd FileServer-Pro
```

## Création d'un environnement virtuel

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux

```bash
python3 -m venv venv

source venv/bin/activate
```

## Installation des dépendances

```bash
pip install -r requirements.txt
```

## Lancement du serveur

```bash
python server_app.py
```

---

# 📦 Dépendances

```txt
customtkinter>=5.2.0
Pillow>=10.0.0
```

---

# 📸 Captures d'Écran

Ajoutez ici vos captures réelles :

### 🔐 Authentification

```text
Login sécurisé
```

### 📊 Dashboard

```text
Vue d'ensemble du serveur
```

### 📁 Gestion documentaire

```text
Explorateur des fichiers reçus
```

---

# 🎯 Évolutions Futures

```mermaid
mindmap
  root((FileServer Pro))

    Sécurité
      Chiffrement AES
      Gestion avancée des rôles
      Permissions granulaires

    Administration
      Base SQLite
      Sauvegardes automatiques
      Rapports PDF

    Réseau
      Multi-serveurs
      Synchronisation distante
      Réplication

    Interface
      Interface Web
      Application Mobile
      Mode sombre avancé

    Productivité
      Notifications temps réel
      Recherche intelligente
      Export Excel
```

---

# 🤝 Contribution

Les contributions sont les bienvenues.

```text
Fork
 ↓
Nouvelle branche
 ↓
Développement
 ↓
Commit
 ↓
Pull Request
```

---

# 📜 Licence

MIT License

Copyright (c) 2026 Omar Badrani

Permission est accordée à toute personne obtenant une copie de ce logiciel et de sa documentation associée d'utiliser, copier, modifier et distribuer le logiciel sous les conditions de la licence MIT.

---

# ⭐ Support du Projet

Si ce projet vous est utile :

⭐ Mettre une étoile sur GitHub

🐛 Signaler les bugs

💡 Proposer des améliorations

🤝 Participer au développement

---

<div align="center">

# 🚀 FileServer Pro

### Centraliser • Sécuriser • Superviser

### 👨‍💻 Omar Badrani

Développé avec Python & CustomTkinter

© 2026 Omar Badrani - Tous droits réservés

</div>
