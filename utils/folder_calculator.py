#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul pro výpočet skutečných velikostí složek a podobných operací s projekty.
"""

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from resources.style.themes import ThemeManager
from config import GROUP_COLUMNS
from PySide6.QtGui import QColor
import os

def calculate_real_folder_sizes(group_item, projects, status_label, callback_function):
    """
    Vypočítá skutečné velikosti složek a počty souborů pro projekty ve skupině.
    Zároveň zjistí datum poslední úpravy souboru v projektu.
    
    Args:
        group_item: Položka skupiny ve stromu
        projects: Seznam dvojic (item, projekt)
        status_label: QLabel pro zobrazení stavu operace
        callback_function: Funkce pro aktualizaci obarvení po dokončení výpočtu
    """
    # Indexy sloupců
    size_column = 2      # Sloupec pro velikost
    file_count_column = 5  # Sloupec pro počet souborů
    last_file_mod_column = 7  # Sloupec pro poslední změnu souboru
    
    # Pro každý projekt ve skupině
    for i in range(group_item.childCount()):
        # Nastavení kurzoru na čekání
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        child_item = group_item.child(i)
        project = child_item.data(0, Qt.UserRole)
        
        if project and hasattr(project, 'path'):
            # Výpočet skutečné velikosti složky a počtu souborů
            try:
                total_size = 0
                file_count = 0
                
                # Prochází rekurzivně všechny soubory ve složce (bez filtrování)
                for dirpath, dirnames, filenames in os.walk(project.path):
                    # Přidáme velikosti souborů
                    for file in filenames:
                        file_path = os.path.join(dirpath, file)
                        try:
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                        except (OSError, FileNotFoundError):
                            pass  # Ignorujeme soubory, ke kterým nemáme přístup
                
                # Aktualizace dat v tabulce
                if total_size >= 1024 * 1024 * 1024:  # Více než 1 GB
                    size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
                elif total_size >= 1024 * 1024:  # Více než 1 MB
                    size_str = f"{total_size / (1024 * 1024):.2f} MB"
                else:  # V KB
                    size_str = f"{total_size / 1024:.2f} KB"
                
                # Uložení skutečných hodnot do objektu projektu (pro ukládání do JSON)
                project.real_size = total_size
                project.real_file_count = file_count
                
                # Aktualizace dat v tabulce
                child_item.setText(size_column, size_str)  # Aktualizace sloupce s velikostí
                child_item.setText(file_count_column, str(file_count))  # Nastavení počtu souborů
                
                # Zjištění poslední změny souboru v projektu
                last_file_time = project.get_last_file_modified()
                child_item.setText(last_file_mod_column, project.get_formatted_last_file_modified())
                
                # Aktualizace stavového řádku
                status_label.setText(f"Načtena skutečná data pro: {project.name}")
            
            except Exception as e:
                status_label.setText(f"Chyba při načítání dat: {str(e)}")
        
        # Obnovení normálního kurzoru
        QApplication.restoreOverrideCursor()
    
    # Po výpočtu všech hodnot provedeme obarvení projektů se stejnými hodnotami
    callback_function(projects)

def _update_coloring_after_calculation(projects):
    """
    Aktualizuje obarvení projektů po výpočtu jejich skutečné velikosti, počtu souborů a hashů.
    
    Args:
        projects (list): Seznam dvojic (item, projekt)
    """
    # Získání aktuálního tématu z ThemeManager
    theme = ThemeManager.get_theme(ThemeManager.load_current_theme())
    
    # Zjištění indexů sloupců pro specifické údaje
    hash_column = GROUP_COLUMNS.index("Hash") if "Hash" in GROUP_COLUMNS else -1
    size_column = GROUP_COLUMNS.index("Velikost") if "Velikost" in GROUP_COLUMNS else -1
    file_count_column = GROUP_COLUMNS.index("Počet souborů") if "Počet souborů" in GROUP_COLUMNS else -1
    last_mod_column = GROUP_COLUMNS.index("Poslední změna souboru") if "Poslední změna souboru" in GROUP_COLUMNS else -1
    
    # Vytvoření slovníků pro seskupování projektů podle různých kritérií
    hash_groups = {}
    size_groups = {}
    file_count_groups = {}
    last_mod_groups = {}
    
    # Naplnění slovníků podle různých kritérií
    for item, project in projects:
        # Seskupení podle hashů
        if hasattr(project, 'folder_hash') and project.folder_hash is not None:
            if project.folder_hash in hash_groups:
                hash_groups[project.folder_hash].append((item, project))
            else:
                hash_groups[project.folder_hash] = [(item, project)]
        
        # Seskupení podle velikosti
        if hasattr(project, 'real_size') and project.real_size is not None:
            if project.real_size in size_groups:
                size_groups[project.real_size].append((item, project))
            else:
                size_groups[project.real_size] = [(item, project)]
        
        # Seskupení podle počtu souborů
        if hasattr(project, 'real_file_count') and project.real_file_count is not None:
            if project.real_file_count in file_count_groups:
                file_count_groups[project.real_file_count].append((item, project))
            else:
                file_count_groups[project.real_file_count] = [(item, project)]
        
        # Seskupení podle data poslední změny souboru
        if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
            if project.last_file_modified in last_mod_groups:
                last_mod_groups[project.last_file_modified].append((item, project))
            else:
                last_mod_groups[project.last_file_modified] = [(item, project)]
    
    # Obarvíme buňky s hashem pro projekty se shodným hashem (zelená)
    for hash_val, items_projects in hash_groups.items():
        if len(items_projects) > 1:  # Pouze pokud existuje více projektů se stejným hashem
            for item, _ in items_projects:
                item.setBackground(hash_column, QColor(theme["same_hash_color"]))
    
    # Obarvíme buňky s velikostí pro projekty se stejnou skutečnou velikostí (oranžová)
    for size, items_projects in size_groups.items():
        if len(items_projects) > 1:  # Pouze pokud existuje více projektů se stejnou velikostí
            for item, _ in items_projects:
                item.setBackground(size_column, QColor(theme["same_size_color"]))
    
    # Obarvíme buňky s počtem souborů pro projekty se stejným počtem souborů (modrá)
    for count, items_projects in file_count_groups.items():
        if len(items_projects) > 1:  # Pouze pokud existuje více projektů se stejným počtem souborů
            for item, _ in items_projects:
                item.setBackground(file_count_column, QColor(theme["same_files_color"]))
    
    # Obarvíme buňky s datem poslední změny souboru pro projekty se stejným datem (fialová)
    for date, items_projects in last_mod_groups.items():
        if len(items_projects) > 1:  # Pouze pokud existuje více projektů se stejným datem
            for item, _ in items_projects:
                item.setBackground(last_mod_column, QColor(theme["same_date_color"]))

def calculate_project_hash(item, project, status_label):
    """
    Vypočítá hash obsahu složky pro jeden projekt.
    
    Args:
        item: Položka ve stromovém pohledu
        project: Objekt projektu
        status_label: QLabel pro zobrazení stavu operace
    """
    from PySide6.QtWidgets import QApplication
    
    # Nastavení kurzoru na čekání
    QApplication.setOverrideCursor(Qt.WaitCursor)
    
    # Aktualizace stavového řádku
    status_label.setText(f"Výpočet hashe pro: {project.name}...")
    
    try:
        # Callback pro aktualizaci stavového řádku
        def file_callback(file_path):
            status_label.setText(f"Výpočet hashe - zpracovávám: {os.path.basename(file_path)}")
            QApplication.processEvents()  # Umožní aktualizaci UI během zpracování
        
        # Výpočet hashe projektu
        hash_value = project.calculate_folder_hash(file_callback=file_callback)
        
        if hash_value:
            # Zkrácení hashe pro zobrazení
            short_hash = hash_value[:12] + "..."
            
            # Index sloupce pro hash (standardně 6)
            hash_column = 6
            
            # Aktualizace dat v tabulce - hash přidáme do sloupce pro hash
            item.setText(hash_column, short_hash)
            item.setToolTip(hash_column, f"Úplný hash: {hash_value}")
            
            # Aktualizace stavového řádku
            status_label.setText(f"Hash vypočítán pro: {project.name}")
        else:
            status_label.setText(f"Nepodařilo se vypočítat hash pro: {project.name}")
    
    except Exception as e:
        status_label.setText(f"Chyba při výpočtu hashe: {str(e)}")
    
    # Obnovení normálního kurzoru
    QApplication.restoreOverrideCursor()

def calculate_folder_hashes(group_item, status_label, callback_function):
    """
    Vypočítá hashe obsahu složek pro projekty ve skupině.
    
    Args:
        group_item: Položka skupiny ve stromu
        status_label: QLabel pro zobrazení stavu operace
        callback_function: Funkce pro aktualizaci obarvení po dokončení výpočtu
    """
    from PySide6.QtWidgets import QApplication
    
    # Získáme všechny projekty ve skupině pro hledání shod
    projects = []
    for i in range(group_item.childCount()):
        child_item = group_item.child(i)
        project = child_item.data(0, Qt.UserRole)
        if project:
            projects.append((child_item, project))
    
    # Pro každý projekt ve skupině
    for i in range(group_item.childCount()):
        child_item = group_item.child(i)
        project = child_item.data(0, Qt.UserRole)
        
        if project and hasattr(project, 'path'):
            calculate_project_hash(child_item, project, status_label)
    
    # Po výpočtu všech hashů provedeme obarvení projektů se stejnými hodnotami
    callback_function(projects)
    
    # Aktualizace informace po dokončení
    status_label.setText(f"Hashe byly vypočítány pro všechny projekty ve skupině")
    
    # Signál pro aktualizaci projektů v modelu
    from controller.app_controller import AppController
    if hasattr(AppController, 'update_projects_with_real_data'):
        AppController.update_projects_with_real_data()

def calculate_last_file_modified(group_item, status_label):
    """
    Zjistí datum poslední úpravy libovolného souboru v projektech ve skupině.
    
    Args:
        group_item: Položka skupiny ve stromu
        status_label: QLabel pro zobrazení stavu operace
    """
    from PySide6.QtWidgets import QApplication
    
    # Nastavení sloupce pro poslední změnu souboru
    last_file_mod_column = 7
    
    # Získáme všechny projekty ve skupině
    projects = []
    for i in range(group_item.childCount()):
        child_item = group_item.child(i)
        project = child_item.data(0, Qt.UserRole)
        if project:
            projects.append((child_item, project))
    
    # Pro každý projekt ve skupině
    for i in range(group_item.childCount()):
        # Nastavení kurzoru na čekání
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        child_item = group_item.child(i)
        project = child_item.data(0, Qt.UserRole)
        
        if project and hasattr(project, 'path'):
            calculate_project_last_modified(child_item, project, status_label)
            
        # Obnovení normálního kurzoru
        QApplication.restoreOverrideCursor()
    
    # Aktualizace informace po dokončení
    status_label.setText(f"Data o poslední změně souborů načtena pro všechny projekty ve skupině")
    
    # Signál pro aktualizaci projektů v modelu
    from controller.app_controller import AppController
    if hasattr(AppController, 'update_projects_with_real_data'):
        AppController.update_projects_with_real_data()

def calculate_project_last_modified(item, project, status_label):
    """
    Zjistí datum poslední úpravy libovolného souboru v projektu.
    
    Args:
        item: Položka ve stromovém pohledu
        project: Objekt projektu
        status_label: QLabel pro zobrazení stavu operace
    """
    from PySide6.QtWidgets import QApplication
    
    # Nastavení kurzoru na čekání
    QApplication.setOverrideCursor(Qt.WaitCursor)
    
    # Aktualizace stavového řádku
    status_label.setText(f"Zjišťování data poslední změny pro: {project.name}...")
    
    try:
        # Získání data poslední změny souboru v projektu
        last_file_time = project.get_last_file_modified()
        formatted_time = project.get_formatted_last_file_modified()
        
        # Index sloupce pro poslední změnu souboru
        last_file_mod_column = 7
        
        # Aktualizace dat v tabulce
        item.setText(last_file_mod_column, formatted_time)
        
        # Aktualizace stavového řádku
        status_label.setText(f"Datum poslední změny zjištěno pro: {project.name}")
    
    except Exception as e:
        status_label.setText(f"Chyba při zjišťování data poslední změny: {str(e)}")
    
    # Obnovení normálního kurzoru
    QApplication.restoreOverrideCursor() 