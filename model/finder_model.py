#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model pro vyhledávání Python projektů.
Obsahuje logiku pro procházení souborového systému a identifikaci Python projektů.
"""

import os
import json
import sys
import difflib
from pathlib import Path
from PySide6.QtCore import QObject, Signal
from model.project_model import ProjectModel
from config import IGNORED_DIRECTORIES, PYTHON_EXTENSIONS, SIMILARITY_THRESHOLD, PROJECT_ROOT_FILES, IGNORED_FILE_EXTENSIONS


class FinderModel(QObject):
    """Model pro vyhledávání Python projektů."""
    
    # Signály pro komunikaci s GUI
    project_found = Signal(object)
    search_finished = Signal(int)  # počet nalezených projektů
    search_started = Signal()
    search_error = Signal(str)
    directory_scanning = Signal(str)  # signál pro aktuálně zpracovávaný adresář
    file_scanning = Signal(str)  # signál pro aktuálně zpracovávaný soubor
    
    def __init__(self):
        """Inicializace modelu."""
        super().__init__()
        self.projects = []
        self.ignore_dirs = IGNORED_DIRECTORIES
        self.python_extensions = PYTHON_EXTENSIONS
        self.project_root_files = PROJECT_ROOT_FILES
        self.ignored_file_extensions = IGNORED_FILE_EXTENSIONS
        
        # Zvýšíme limit rekurze v Pythonu
        sys.setrecursionlimit(10000)  # Výchozí hodnota je 1000
    
    def is_python_project(self, directory_path):
        """
        Zkontroluje, zda adresář obsahuje alespoň jeden Python soubor.
        
        Args:
            directory_path (str): Cesta k adresáři
        
        Returns:
            bool: True, pokud adresář obsahuje Python soubor, jinak False
        """
        try:
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isfile(item_path):
                    # Přeskočíme soubory s ignorovanými příponami
                    if any(item.lower().endswith(ext) for ext in self.ignored_file_extensions):
                        continue
                    
                    # Oznámíme zpracování souboru pouze pro Python soubory
                    if any(item.endswith(ext) for ext in self.python_extensions):
                        self.file_scanning.emit(item_path)
                        return True
        except (PermissionError, OSError):
            # Ignorujeme chyby při přístupu k některým adresářům
            pass
            
        return False
    
    def is_project_root(self, directory_path):
        """
        Zkontroluje, zda adresář obsahuje soubory typické pro kořen projektu.
        
        Args:
            directory_path (str): Cesta k adresáři
        
        Returns:
            bool: True, pokud adresář obsahuje soubory typické pro kořen projektu, jinak False
        """
        try:
            files = os.listdir(directory_path)
            for root_file in self.project_root_files:
                if root_file in files:
                    file_path = os.path.join(directory_path, root_file)
                    if os.path.isfile(file_path):
                        # Přeskočíme soubory s ignorovanými příponami
                        if any(root_file.lower().endswith(ext) for ext in self.ignored_file_extensions):
                            continue
                        
                        # Oznámíme zpracování souboru, který je projektovým souborem
                        self.file_scanning.emit(file_path)
                        return True
        except (PermissionError, OSError):
            # Ignorujeme chyby při přístupu k některým adresářům
            pass
            
        return False
    
    def find_python_projects(self, root_path, worker=None):
        """
        Projde rekurzivně adresáře a najde všechny složky s Python soubory.
        Za projekt považujeme první složku z cesty, která:
        - obsahuje Python soubor, nebo
        - obsahuje některý z typických souborů pro kořen projektu (README.md, .env, atd.)
        
        Args:
            root_path (str): Kořenový adresář pro vyhledávání
            worker (SearchWorker): Worker, který lze použít pro kontrolu, zda pokračovat ve vyhledávání
        
        Returns:
            list: Seznam projektů (ProjectModel)
        """
        self.projects = []
        self.search_started.emit()
        
        if not os.path.exists(root_path):
            self.search_error.emit(f"Cesta {root_path} neexistuje.")
            self.search_finished.emit(0)
            return self.projects
            
        # Pokud vstupní cesta je kořen disku, převedeme na absolutní cestu
        if root_path.endswith(':') or root_path.endswith(':\\'):
            root_path = os.path.abspath(root_path)
        
        if not os.path.isdir(root_path):
            self.search_error.emit(f"Cesta {root_path} není adresář.")
            self.search_finished.emit(0)
            return self.projects
        
        # Rekurzivní funkce pro hledání projektů
        def find_projects_recursive(path, is_root_dir=False, parent_has_python=False, parent_is_project_root=False):
            # Kontrola, zda máme pokračovat
            if worker and not worker.running:
                return
                
            # Emitujeme signál s aktuálně zpracovávaným adresářem
            self.directory_scanning.emit(path)
                
            # Přeskočíme cesty, které jsou příliš dlouhé pro Windows
            if len(path) > 255:
                return
                
            # Kontrola, zda složka obsahuje Python soubor nebo je kořenem projektu
            try:
                is_python = self.is_python_project(path)
                is_project_root = self.is_project_root(path)
            except (PermissionError, OSError):
                # Ignorujeme chyby při čtení obsahu adresáře
                return
            
            # Pokud je to Python projekt nebo kořen projektu a rodičovská složka 
            # není ani jedno, přidáme ho a neprohledáváme podsložky
            # VÝJIMKA: pokud je to kořenový adresář, který uživatel zvolil k prohledání,
            # tak ho nikdy nepovažujeme za projekt a vždy prohledáváme jeho podsložky
            if not is_root_dir and (is_python or is_project_root) and not (parent_has_python or parent_is_project_root):
                try:
                    # Zde vytvoříme callback pro emitování signálu o zpracovávaném souboru
                    def file_scan_callback(file_path):
                        self.file_scanning.emit(file_path)
                    
                    # Předáme callback při vytváření projektu
                    project = ProjectModel(path)
                    project._analyze_project(file_callback=file_scan_callback)
                    
                    self.projects.append(project)
                    self.project_found.emit(project)
                except Exception as e:
                    # Pokud se projekt nepodaří vytvořit, pokračujeme bez přidání
                    print(f"Chyba při vytváření projektu {path}: {str(e)}")
                return
            
            # Jinak procházíme podsložky
            try:
                items = os.listdir(path)
                for item in items:
                    # Kontrola, zda máme pokračovat
                    if worker and not worker.running:
                        return
                        
                    # Přeskočíme soubory, zajímají nás jen adresáře
                    item_path = os.path.join(path, item)
                    if not os.path.isdir(item_path):
                        continue
                        
                    # Přeskočíme ignorované adresáře
                    if item in self.ignore_dirs:
                        continue
                        
                    find_projects_recursive(
                        item_path,
                        is_root_dir=False,  # Podsložky již nejsou kořenovými složkami
                        parent_has_python=parent_has_python or is_python,
                        parent_is_project_root=parent_is_project_root or is_project_root
                    )
            except (PermissionError, OSError) as e:
                # Ignorujeme chyby při čtení obsahu adresáře
                # Pouze zaznamenáme do logu, že adresář nemohl být přečten
                print(f"Nelze číst adresář {path}: {str(e)}")
                return
        
        try:
            # Spustíme rekurzivní vyhledávání
            find_projects_recursive(root_path, is_root_dir=True)  # Označíme kořenový adresář speciálním příznakem
            self.search_finished.emit(len(self.projects))
        except Exception as e:
            self.search_error.emit(f"Neočekávaná chyba při prohledávání: {str(e)}")
            self.search_finished.emit(0)
            
        return self.projects
    
    def save_to_json(self, output_file):
        """
        Uloží seznam projektů do JSON souboru.
        
        Args:
            output_file (str): Cesta k výstupnímu souboru
            
        Returns:
            bool: True, pokud se uložení podařilo, jinak False
        """
        data = {
            "python_projects": [project.to_dict() for project in self.projects]
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.search_error.emit(f"Chyba při ukládání do souboru {output_file}: {str(e)}")
            return False
    
    def load_from_json(self, input_file):
        """
        Načte seznam projektů z JSON souboru.
        
        Args:
            input_file (str): Cesta ke vstupnímu souboru
            
        Returns:
            bool: True, pokud se načtení podařilo, jinak False
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.projects = []
            for project_data in data.get("python_projects", []):
                project = ProjectModel.from_dict(project_data)
                self.projects.append(project)
                self.project_found.emit(project)
            
            self.search_finished.emit(len(self.projects))
            return True
        except Exception as e:
            self.search_error.emit(f"Chyba při načítání souboru {input_file}: {str(e)}")
            return False
    
    def _calculate_similarity(self, project1, project2):
        """
        Vypočítá podobnost mezi dvěma projekty na základě jejich souborů.
        
        Args:
            project1 (ProjectModel): První projekt
            project2 (ProjectModel): Druhý projekt
            
        Returns:
            float: Hodnota podobnosti mezi 0.0 a 1.0
        """
        # Pokud nemáme dostatek dat pro porovnání, vrátíme nízkou podobnost
        if not project1.python_files or not project2.python_files:
            return 0.0
        
        # Pokud mají oba projekty hash, nejprve zkontrolujeme přesnou shodu podle hashe
        if project1.folder_hash and project2.folder_hash:
            if project1.folder_hash == project2.folder_hash:
                return 1.0  # 100% shoda, když jsou hashe identické
        
        # Porovnáme seznam souborů (jejich názvy)
        file_similarity = difflib.SequenceMatcher(
            None, 
            sorted([os.path.basename(f) for f in project1.python_files]),
            sorted([os.path.basename(f) for f in project2.python_files])
        ).ratio()
        
        # Porovnáme názvy projektů
        name_similarity = difflib.SequenceMatcher(
            None, 
            project1.name, 
            project2.name
        ).ratio()
        
        # Přidáme porovnání velikostí, pokud jsou k dispozici skutečné velikosti
        size_similarity = 0.0
        if project1.real_size is not None and project2.real_size is not None and project1.real_size > 0 and project2.real_size > 0:
            # Poměr menší/větší velikost pro podobnost (0.0-1.0)
            smaller = min(project1.real_size, project2.real_size)
            larger = max(project1.real_size, project2.real_size)
            size_similarity = smaller / larger
        
        # Váhy pro jednotlivé složky podobnosti
        file_weight = 0.6
        name_weight = 0.2
        size_weight = 0.2
        
        # Celková podobnost (pokud nemáme velikosti, používáme původní váhy)
        if project1.real_size is not None and project2.real_size is not None:
            total_similarity = (
                file_similarity * file_weight + 
                name_similarity * name_weight + 
                size_similarity * size_weight
            )
        else:
            # Původní váhy
            file_weight = 0.7
            name_weight = 0.3
            total_similarity = (file_similarity * file_weight) + (name_similarity * name_weight)
        
        return total_similarity
    
    def find_duplicates(self):
        """
        Najde duplicitní projekty na základě podobnosti obsahu.
        
        Returns:
            list: Seznam dvojic projektů, které jsou si podobné
        """
        duplicates = []
        similarities = {}  # Slovník pro ukládání podobností mezi projekty
        
        # Porovnání všech projektů mezi sebou
        for i, project1 in enumerate(self.projects):
            for j, project2 in enumerate(self.projects[i+1:], i+1):
                # Porovnání podobnosti projektů
                similarity = self._calculate_similarity(project1, project2)
                
                # Ukládáme podobnost pro oba směry
                similarities[(project1, project2)] = similarity
                similarities[(project2, project1)] = similarity
                
                # Pokud je podobnost nad prahem, považujeme za potenciální duplicitu
                if similarity >= SIMILARITY_THRESHOLD:
                    duplicates.append((project1, project2, similarity))
        
        return duplicates, similarities
    
    def group_duplicates(self):
        """
        Seskupí duplicitní projekty do skupin.
        
        Returns:
            list: Seznam skupin duplicitních projektů, kde každá skupina obsahuje
                  list projektů a slovník podobností
        """
        # Nejprve získáme všechny duplicity a podobnosti
        duplicates, similarities = self.find_duplicates()
        
        if not duplicates:
            return []
        
        # Vytvoříme skupiny projektů
        groups = []
        processed_projects = set()
        
        # Pro každou dvojici duplicitních projektů
        for project1, project2, similarity in sorted(duplicates, key=lambda x: x[2], reverse=True):
            # Pokud oba projekty již byly zpracovány, přeskočíme
            if project1 in processed_projects and project2 in processed_projects:
                continue
            
            # Hledáme existující skupinu, kam by projekty patřily
            found_group = None
            for group in groups:
                group_projects = group['projects']
                if project1 in group_projects or project2 in group_projects:
                    found_group = group
                    break
            
            # Pokud skupinu nenajdeme, vytvoříme novou
            if not found_group:
                found_group = {
                    'projects': [],
                    'similarities': {}
                }
                groups.append(found_group)
            
            # Přidáme projekty do skupiny, pokud tam ještě nejsou
            group_projects = found_group['projects']
            if project1 not in group_projects:
                group_projects.append(project1)
                processed_projects.add(project1)
            if project2 not in group_projects:
                group_projects.append(project2)
                processed_projects.add(project2)
            
            # Aktualizujeme podobnosti pro konkrétní pár projektů
            found_group['similarities'][(project1, project2)] = similarity
            found_group['similarities'][(project2, project1)] = similarity
        
        # Zarovnáme skupiny podle velikosti (počtu projektů)
        groups.sort(key=lambda x: len(x['projects']), reverse=True)
        
        return groups
    
    def find_identical_by_hash(self):
        """
        Najde projekty s identickým hashem, které jsou tedy 100% duplicitní.
        
        Returns:
            list: Seznam skupin identických projektů podle hashe
        """
        # Kontrola, zda máme vůbec projekty s hashem
        projects_with_hash = [p for p in self.projects if hasattr(p, 'folder_hash') and p.folder_hash]
        
        if not projects_with_hash:
            return []
            
        # Slovník hashů a příslušných projektů
        hash_groups = {}
        
        # Roztřídění projektů podle hashů
        for project in projects_with_hash:
            if project.folder_hash in hash_groups:
                hash_groups[project.folder_hash].append(project)
            else:
                hash_groups[project.folder_hash] = [project]
        
        # Vybereme pouze skupiny s více než jedním projektem (duplicity)
        identical_groups = [group for group in hash_groups.values() if len(group) > 1]
        
        return identical_groups 