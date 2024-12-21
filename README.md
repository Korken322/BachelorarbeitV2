# Werbetext Generator

Dieses Projekt implementiert einen Prototyp zur Generierung von Werbetexten mittels attributbasierter Large Language Models. Der Prototyp basiert auf Python, Flask, MySQL und der OpenAI-API.

---

## 📋 Inhalt
- [Beschreibung](#-beschreibung)
- [Voraussetzungen](#-voraussetzungen)
- [Installation](#-installation)
- [Verwendung](#-verwendung)
- [Projektstruktur](#-projektstruktur)
- [Troubleshooting](#-troubleshooting)
- [Lizenz](#-lizenz)
- [Mitwirken](#-mitwirken)

---

## 🖋️ Beschreibung

Der **Werbetext Generator** ermöglicht:
1. **Hochladen von Produktattributen**: Daten können importiert und analysiert werden.
2. **Generierung von Merkmalen**: Basierend auf Produktattributen werden relevante Merkmale generiert.
3. **Erstellung von Werbetexten**: Mit Hilfe der OpenAI-API können automatisch Werbetexte erstellt werden.
4. **Feedback und Optimierung**: Bereits generierte Texte können angepasst werden.

Das Ziel des Projekts ist es, datenbasierte und automatisierte Werbetexte effizient zu erstellen.

---

## ✅ Voraussetzungen

Bevor du das Projekt installierst, stelle sicher, dass folgende Voraussetzungen erfüllt sind:

- **Python**: Version 3.9 oder höher
- **MySQL**: Zum Speichern der Daten
- **Git**: Zum Klonen des Repositories
- **API-Schlüssel**: Zugang zur OpenAI-API

### Python-Abhängigkeiten:
- Flask
- mysql-connector-python
- pandas
- python-dotenv
- openai

---

## 🚀 Installation

### 1. Repository klonen
```bash
git clone https://github.com/Korken322/BachelorarbeitV2.git
cd BachelorarbeitV2

### 2. Virtuelle Umgebung erstellen
python -m venv env
source env/bin/activate  # macOS/Linux
env\Scripts\activate     # Windows

### 3. Requirements installieren 
pip install -r requirements.txt


### 4. Datenbank erstellen 
mysql -u root -p
CREATE DATABASE werbetext_generator;
SOURCE data/Werbetext_generator_DB.sql;

### 5. .env Datei erstellen
OPENAI_API_KEY=your-openai-api-key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-database-password
DB_NAME=werbetext_generator
FLASK_ENV=development

### 6.App Starten
flask run

Die App ist unter http://127.0.0.1:5000 erreichbar.