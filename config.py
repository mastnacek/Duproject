#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konfigurační soubor pro aplikaci Python Project Finder.
Obsahuje konstanty a výchozí nastavení aplikace.
"""

# Názvy adresářů, které budou při vyhledávání ignorovány
IGNORED_DIRECTORIES = [
    '__pycache__', 
    'venv', 
    '.venv', 
    'env', 
    '.git', 
    '.idea', 
    '.vscode', 
    'node_modules',
    'build',
    'dist',
    '.pytest_cache',
    '.mypy_cache',
    '.tox',
    '.eggs',
    'cache',
    'thumbnails'
]

# Přípony souborů, které identifikují Python projekt
PYTHON_EXTENSIONS = ['.py', '.pyw', '.pyx', '.pyi', '.pyc']

# Přípony souborů, které budou při vyhledávání ignorovány (např. obrázky)
IGNORED_FILE_EXTENSIONS = [
    # Běžné formáty obrázků
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp', '.ico','.heic','.heif',
    # Soubory Photoshopu a dalších grafických editorů
    '.psd', '.ai', '.eps', '.raw', '.cr2', '.nef', '.dng',
    # Animované a videa
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'
]

# Soubory, které identifikují kořen projektu
PROJECT_ROOT_FILES = [
    'README.md',
    'README.txt',
    'readme.md',
    'readme.txt',
    '.env',
    'requirements.txt',
    'setup.py',
    'pyproject.toml',
    'Pipfile',
    'poetry.lock',
    '.gitignore',
    'LICENSE',
    'setup.cfg',
    'tox.ini',
    'manage.py',
    'README.rst',
    'MANIFEST.in',
    'Dockerfile',
    'docker-compose.yml'
]

# Výchozí cesta pro ukládání výsledků
DEFAULT_OUTPUT_FILE = 'python_projects.json'

# Nastavení GUI
GUI_TITLE = "Python Project Finder"
GUI_WIDTH = 1200
GUI_HEIGHT = 800

# Názvy sloupců pro tabulku s projekty
PROJECT_COLUMNS = ["Cesta", "Počet souborů", "Velikost", "Datum"]

# Názvy sloupců pro skupiny podobných projektů
GROUP_COLUMNS = ["Projekt", "Cesta", "Velikost", "Datum", "Podobnost", "Počet souborů", "Hash", "Poslední změna souboru"]

# Nastavení pro vyhledávání duplicit
SIMILARITY_THRESHOLD = 0.7  # Práh podobnosti pro označení duplicity 

# Barvy pro zvýraznění
HIGHLIGHT_COLOR = "#AAFFAA"  # Světle zelená pro zvýraznění
GROUP_HEADER_COLOR = "#EAEAEA"  # Šedá pro záhlaví skupin
DUPLICATE_COLOR = "#FFDDAA"  # Oranžová pro duplicity

# Seznam ignorovaných adresářů při výpočtu data poslední změny
IGNORED_DIRS = [
    "venv", 
    ".venv", 
    "__pycache__", 
    ".git", 
    ".idea", 
    ".vs", 
    ".vscode", 
    "node_modules",
    "build",
    "dist",
    ".pytest_cache",
    ".mypy_cache"
] 