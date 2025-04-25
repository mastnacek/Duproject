#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datový model pro Python projekt.
Obsahuje struktury dat a business logiku pro reprezentaci Python projektu.
"""

import os
from datetime import datetime
from pathlib import Path
from config import PROJECT_ROOT_FILES, IGNORED_FILE_EXTENSIONS, IGNORED_DIRS


class ProjectModel:
    """Třída reprezentující Python projekt."""
    
    def __init__(self, path, project_files=None, name=None):
        """
        Inicializace modelu projektu.
        
        Args:
            path (str): Cesta k projektu
            project_files (list, optional): Seznam souborů projektu
            name (str, optional): Název projektu
        """
        self.path = path
        self.name = name or os.path.basename(path)
        self.size = 0
        self.last_modified = 0
        self.project_files = project_files or []
        self.features = set()  # Množina vlastností projektu
        
        # Atributy pro skutečné velikosti a hashe
        self.real_size = None
        self.real_file_count = None
        self.folder_hash = None
        self.last_file_modified = None  # Datum poslední změny souboru v projektu
        
        # Načtení základních dat
        try:
            stat_info = os.stat(path)
            self.size = stat_info.st_size
            self.last_modified = stat_info.st_mtime
        except (FileNotFoundError, PermissionError):
            pass
        
        self.file_count = 0
        self.python_files = []
        self.ignored_file_extensions = IGNORED_FILE_EXTENSIONS
        
        # Analýzu provedeme až na vyžádání, ne automaticky v konstruktoru
    
    def _analyze_project(self, file_callback=None):
        """
        Analyzuje projekt a sbírá informace o souborech.
        
        Args:
            file_callback: Volitelná callback funkce pro informování o zpracovávaných souborech
        """
        if not os.path.exists(self.path) or not os.path.isdir(self.path):
            return
        
        total_size = 0
        last_mod_time = 0
        python_files = []
        project_files = []
        
        # Nejprve zkontrolujeme projektové soubory v kořenu
        for file in os.listdir(self.path):
            # Soustředíme se pouze na soubory, které jsou potenciálně projektové soubory
            if file in PROJECT_ROOT_FILES:
                file_path = os.path.join(self.path, file)
                
                if os.path.isfile(file_path):
                    # Přeskočíme soubory s ignorovanými příponami
                    if any(file.lower().endswith(ext) for ext in self.ignored_file_extensions):
                        continue
                    
                    # Informujeme o zpracovávaném souboru, pokud je poskytnut callback
                    if file_callback:
                        file_callback(file_path)
                    
                    project_files.append(file_path)
                    
                    try:
                        stats = os.stat(file_path)
                        total_size += stats.st_size
                        
                        if stats.st_mtime > last_mod_time:
                            last_mod_time = stats.st_mtime
                    except OSError:
                        continue
        
        # Pak projdeme všechny Python soubory (pouze je)
        for root, _, files in os.walk(self.path):
            for file in files:
                # Soustředíme se pouze na Python soubory - zrychlení vyhledávání
                if not file.endswith('.py'):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Informujeme o zpracovávaném souboru, pokud je poskytnut callback
                if file_callback:
                    file_callback(file_path)
                
                # Přidáme soubor do seznamu Python souborů
                python_files.append(file_path)
                
                try:
                    stats = os.stat(file_path)
                    total_size += stats.st_size
                    
                    if stats.st_mtime > last_mod_time:
                        last_mod_time = stats.st_mtime
                except OSError:
                    continue
        
        self.file_count = len(python_files)
        self.size = total_size
        self.python_files = python_files
        self.project_files = project_files
        
        if last_mod_time > 0:
            self.last_modified = datetime.fromtimestamp(last_mod_time)
    
    def to_dict(self):
        """
        Převede projekt na slovník.
        
        Returns:
            dict: Slovník s informacemi o projektu
        """
        result = {
            "path": self.path,
            "name": self.name,
            "file_count": self.file_count,
            "size": self.size,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "python_files": self.python_files,
            "project_files": self.project_files
        }
        
        # Přidáme skutečné hodnoty, pokud jsou k dispozici
        if self.real_size is not None:
            result["real_size"] = self.real_size
        if self.real_file_count is not None:
            result["real_file_count"] = self.real_file_count
        if self.folder_hash is not None:
            result["folder_hash"] = self.folder_hash
            
        return result
    
    @classmethod
    def from_dict(cls, data):
        """
        Vytvoří projekt ze slovníku.
        
        Args:
            data (dict): Slovník s informacemi o projektu
            
        Returns:
            ProjectModel: Instance projektu
        """
        project = cls(data["path"])
        project.name = data.get("name", os.path.basename(data["path"]))
        project.file_count = data.get("file_count", 0)
        project.size = data.get("size", 0)
        
        if "last_modified" in data and data["last_modified"]:
            project.last_modified = datetime.fromisoformat(data["last_modified"])
        
        project.python_files = data.get("python_files", [])
        project.project_files = data.get("project_files", [])
        
        # Načtení skutečných hodnot
        project.real_size = data.get("real_size", None)
        project.real_file_count = data.get("real_file_count", None)
        project.folder_hash = data.get("folder_hash", None)
        
        return project
    
    def get_formatted_size(self):
        """
        Vrací formátovanou velikost projektu (KB, MB).
        
        Returns:
            str: Formátovaná velikost
        """
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.2f} MB"
    
    def get_formatted_last_modified(self):
        """
        Vrací formátované datum poslední změny.
        
        Returns:
            str: Formátované datum
        """
        if not self.last_modified:
            return "Neznámé"
        return self.last_modified.strftime("%d.%m.%Y %H:%M")
    
    def has_project_files(self):
        """
        Zjistí, zda projekt obsahuje soubory typické pro kořen projektu.
        
        Returns:
            bool: True, pokud obsahuje projektové soubory, jinak False
        """
        return len(self.project_files) > 0
    
    def calculate_folder_hash(self, file_callback=None):
        """
        Vypočítá hash celé složky projektu pro přesné porovnání.
        Používá kombinaci SHA-256 pro obsah souborů a metadata (cesty, velikosti, data změn).
        
        Args:
            file_callback: Volitelná callback funkce pro informování o zpracovávaných souborech
            
        Returns:
            str: Hexadecimální řetězec hash hodnoty
        """
        import hashlib
        import fnmatch
        
        if not os.path.exists(self.path) or not os.path.isdir(self.path):
            return None
            
        # Seznam všech souborů v adresáři
        all_files = []
        for root, _, files in os.walk(self.path):
            for file in files:
                # Přeskočení ignorovaných formátů souborů
                if any(fnmatch.fnmatch(file.lower(), pattern) for pattern in self.ignored_file_extensions):
                    continue
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        # Seřazení souborů pro konzistentní hash
        all_files.sort()
        
        # Vytvoření hash objektu
        folder_hasher = hashlib.sha256()
        
        # Zpracování každého souboru
        for file_path in all_files:
            try:
                # Relativní cesta k souboru (pro konzistenci napříč různými umístěními)
                rel_path = os.path.relpath(file_path, self.path)
                
                # Informujeme o zpracovávaném souboru, pokud je poskytnut callback
                if file_callback:
                    file_callback(file_path)
                
                # Získání metadat souboru
                stats = os.stat(file_path)
                file_size = stats.st_size
                file_mtime = int(stats.st_mtime)
                
                # Hash z metadat a cesty
                metadata = f"{rel_path}|{file_size}|{file_mtime}"
                folder_hasher.update(metadata.encode('utf-8'))
                
                # Pro menší soubory (<10MB) počítáme hash z obsahu
                if file_size < 10 * 1024 * 1024:  # 10MB
                    file_hasher = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        # Čteme soubor po blocích, abychom nespotřebovali příliš paměti
                        for chunk in iter(lambda: f.read(4096), b''):
                            file_hasher.update(chunk)
                    # Přidáme hash obsahu souboru k celkovému hashi
                    folder_hasher.update(file_hasher.digest())
                else:
                    # Pro větší soubory hash jen z prvních a posledních 1MB
                    file_hasher = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        # Prvních 1MB
                        file_hasher.update(f.read(1024 * 1024))
                        # Přeskočíme do konce - velikost - 1MB
                        f.seek(-1024 * 1024, 2)
                        # Posledních 1MB
                        file_hasher.update(f.read(1024 * 1024))
                    # Přidáme hash částí souboru k celkovému hashi
                    folder_hasher.update(file_hasher.digest())
            except (OSError, IOError, PermissionError):
                # Ignorujeme soubory, ke kterým nemáme přístup
                continue
        
        # Uložíme výsledný hash
        self.folder_hash = folder_hasher.hexdigest()
        return self.folder_hash
    
    def get_folder_size(self):
        """
        Získání velikosti složky.
        
        Returns:
            int: Velikost složky v bajtech
        """
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(self.path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except (OSError, FileNotFoundError):
                        pass  # Ignorujeme soubory, ke kterým nemáme přístup
            return total_size
        except (OSError, FileNotFoundError):
            return 0
    
    def get_folder_last_modified(self):
        """
        Získání data poslední změny složky.
        
        Returns:
            float: Časová známka poslední změny
        """
        try:
            return os.path.getmtime(self.path)
        except (OSError, FileNotFoundError):
            return 0
    
    def get_last_file_modified(self):
        """
        Získání data poslední úpravy libovolného souboru v projektu.
        Ignoruje soubory v adresářích definovaných v IGNORED_DIRS.
        
        Returns:
            float: Časová známka poslední změny (0 pokud není dostupná)
        """
        if self.last_file_modified is not None:
            return self.last_file_modified
            
        try:
            latest_time = 0
            for dirpath, dirnames, filenames in os.walk(self.path):
                # Odstranění ignorovaných adresářů z procházení
                dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
                
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        mtime = os.path.getmtime(fp)
                        if mtime > latest_time:
                            latest_time = mtime
                    except (OSError, FileNotFoundError):
                        pass  # Ignorujeme soubory, ke kterým nemáme přístup
            
            self.last_file_modified = latest_time
            return latest_time
        except (OSError, FileNotFoundError):
            self.last_file_modified = 0
            return 0
    
    def get_formatted_last_file_modified(self):
        """
        Formátované datum poslední úpravy libovolného souboru v projektu.
        
        Returns:
            str: Datum poslední změny ve formátu DD.MM.YYYY HH:MM
        """
        last_file_time = self.get_last_file_modified()
        if last_file_time == 0:
            return "-"
        return datetime.fromtimestamp(last_file_time).strftime("%d.%m.%Y %H:%M")
    
    def check_feature(self, feature_name):
        """
        Kontrola, zda projekt má danou vlastnost.
        
        Args:
            feature_name (str): Název vlastnosti
            
        Returns:
            bool: True, pokud projekt má danou vlastnost
        """
        return feature_name in self.features
    
    def add_feature(self, feature_name):
        """
        Přidání vlastnosti projektu.
        
        Args:
            feature_name (str): Název vlastnosti
        """
        self.features.add(feature_name)
    
    def __str__(self):
        """Textová reprezentace projektu."""
        return f"{self.name} ({self.path})"
    
    def __eq__(self, other):
        """Porovnání dvou projektů."""
        if not isinstance(other, ProjectModel):
            return False
        return self.path == other.path
    
    def __hash__(self):
        """Hash projektu pro použití v množinách a slovnících."""
        return hash(self.path) 