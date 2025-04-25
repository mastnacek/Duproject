# Python Project Finder

Aplikace pro vyhledávání a správu Python projektů na disku.

## Funkce aplikace

- Vyhledávání Python projektů v zadaném adresáři a jeho podsložkách
- Zobrazení informací o nalezených projektech (cesta, počet souborů, velikost, poslední změna)
- Identifikace potenciálně duplicitních projektů na základě podobnosti souborů
- Export a import seznamu projektů do/z JSON souboru
- Konfigurace ignorovaných adresářů a přípon souborů

## Instalace

1. Naklonujte repozitář:

```bash
git clone https://github.com/mastnacek/python-project-finder.git
cd python-project-finder
```

2. Vytvořte a aktivujte virtuální prostředí:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Nainstalujte požadované závislosti:

```bash
pip install -r requirements.txt
```

## Spuštění aplikace

```bash
python python_project_finder/main.py
```

## Požadavky

- Python 3.6+
- PySide6

## Struktura projektu

```
python_project_finder/
├── config.py                # Konfigurační konstanty
├── main.py                  # Vstupní bod aplikace
├── model/
│   ├── __init__.py
│   ├── project_model.py     # Datový model projektu
│   └── finder_model.py      # Logika vyhledávání projektů
├── view/
│   ├── __init__.py
│   ├── main_window.py       # Hlavní okno aplikace
│   ├── project_list_view.py # Seznam nalezených projektů
│   ├── settings_dialog.py   # Dialog nastavení
│   └── help_dialog.py       # Dialog nápovědy
├── controller/
│   ├── __init__.py
│   ├── app_controller.py    # Hlavní controller aplikace
│   └── finder_controller.py # Controller pro vyhledávání
├── resources/
│   ├── icons/               # Ikony aplikace
│   └── style/               # CSS styly
└── utils/
    ├── __init__.py
    └── json_handler.py      # Práce s JSON soubory
```

## Licence

Tento projekt je licencován pod MIT licencí - podrobnosti viz soubor LICENSE.

## Autor

[mastnacek](https://github.com/mastnacek) 