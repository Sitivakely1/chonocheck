# Logiciel interne avec serveur API Flask

## Description

Ce projet permet de déployer un logiciel Python utilisé localement par les employés, qui envoient leurs résultats vers un serveur central interne via une API REST.  
Le serveur stocke les résultats dans une base de données SQLite et fournit une interface simple pour consulter les données.

---

## Contenu

- **serveur.py** : Serveur Flask API avec stockage SQLite.  
- **client_example.py** : Exemple simple de client Python envoyant un résultat au serveur.  
- **requirements.txt** : Liste des dépendances Python nécessaires.  

---

## Installation

### 1. Pré-requis

- Python 3.8+ installé sur le serveur et sur les postes clients.  
- Réseau interne configuré (tous les postes doivent pouvoir accéder à l’IP du serveur).  

### 2. Installer les dépendances

Sur le serveur **et** les clients :  

```bash
pip install -r requirements.txt
