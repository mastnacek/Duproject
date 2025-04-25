#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility pro práci s JSON soubory.
"""

import json
import os
from datetime import datetime


def save_to_json(data, filename, indent=2, ensure_ascii=False):
    """
    Uloží data do JSON souboru.
    
    Args:
        data: Data k uložení (slovník nebo seznam)
        filename (str): Cesta k výstupnímu souboru
        indent (int): Odsazení pro formátování JSON (None pro kompaktní formát)
        ensure_ascii (bool): Zda použít pouze ASCII znaky
        
    Returns:
        bool: True, pokud se uložení podařilo, jinak False
    """
    try:
        # Vytvoření adresáře, pokud neexistuje
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        return True
    except Exception as e:
        print(f"Chyba při ukládání do JSON souboru: {str(e)}")
        return False


def load_from_json(filename):
    """
    Načte data z JSON souboru.
    
    Args:
        filename (str): Cesta ke vstupnímu souboru
        
    Returns:
        tuple: (data, chyba) - data nebo None v případě chyby, chyba je None nebo chybová zpráva
    """
    try:
        if not os.path.exists(filename):
            return None, f"Soubor {filename} neexistuje"
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Chyba při dekódování JSON: {str(e)}"
    except Exception as e:
        return None, f"Chyba při načítání z JSON souboru: {str(e)}"


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder s podporou pro datetime objekty."""
    
    def default(self, obj):
        """Převede objekty na serializovatelný formát."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj) 