#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Controller pro vyhledávání a správu Python projektů.
"""

from PySide6.QtCore import QObject, QThread, Signal, Slot, QTime
from PySide6.QtWidgets import QMessageBox
import os
import time

from model.finder_model import FinderModel


class SearchWorker(QObject):
    """Worker pro asynchronní vyhledávání projektů."""
    
    finished = Signal()
    
    def __init__(self, finder_model, directory):
        """
        Inicializace workeru.
        
        Args:
            finder_model (FinderModel): Model pro vyhledávání
            directory (str): Adresář pro vyhledávání
        """
        super().__init__()
        self.finder_model = finder_model
        self.directory = directory
        self.running = True
    
    def run(self):
        """Spustí vyhledávání projektů."""
        self.running = True
        self.finder_model.find_python_projects(self.directory, self)
        self.running = False
        self.finished.emit()
    
    def stop(self):
        """Zastaví vyhledávání."""
        self.running = False
        # Nastavíme příznak, který bude kontrolovat model při rekurzivním prohledávání
        self.finder_model.search_finished.emit(len(self.finder_model.projects))


class FinderController(QObject):
    """Controller pro vyhledávání a správu projektů."""
    
    def __init__(self, main_window):
        """
        Inicializace controlleru.
        
        Args:
            main_window (MainWindow): Hlavní okno aplikace
        """
        super().__init__()
        
        self.main_window = main_window
        self.finder_model = FinderModel()
        
        # Připojení signálů a slotů
        self.finder_model.project_found.connect(self.on_project_found)
        self.finder_model.search_started.connect(self.on_search_started)
        self.finder_model.search_finished.connect(self.on_search_finished)
        self.finder_model.search_error.connect(self.on_search_error)
        self.finder_model.directory_scanning.connect(self.on_directory_scanning)
        self.finder_model.file_scanning.connect(self.on_file_scanning)
        
        # Nastavení callbacků pro view
        self.setup_view_callbacks()
        
        # Thread pro vyhledávání
        self.search_thread = None
        self.search_worker = None
    
    def setup_view_callbacks(self):
        """Nastavení callbacků pro view."""
        # Propojení metod pro otevření složky a zobrazení detailů
        self.main_window.project_list_view.open_folder = self.open_folder
        self.main_window.project_list_view.show_project_details = self.show_project_details
    
    def find_projects(self, directory):
        """
        Spustí vyhledávání projektů v zadaném adresáři.
        
        Args:
            directory (str): Adresář pro vyhledávání
        """
        print(f"DEBUG: find_projects() zavolána s adresářem: {directory}")
        
        # Pokud již běží vyhledávání, zastavíme ho
        if self.search_thread and self.search_thread.isRunning():
            print("DEBUG: Předchozí vyhledávání stále běží, zastavuji ho...")
            self.stop_search()
            # Počkáme chvíli, než se vyhledávání zastaví
            time.sleep(0.5)
        
        # Vymazání starých výsledků
        self.main_window.project_list_view.clear()
        
        # Aktualizujeme informační štítek
        self.main_window.update_info_label(f"Probíhá vyhledávání projektů v adresáři: {directory}")
        
        # Vytvoření a spuštění vlákna pro vyhledávání
        self.search_thread = QThread()
        self.search_worker = SearchWorker(self.finder_model, directory)
        self.search_worker.moveToThread(self.search_thread)
        
        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.finished.connect(self.search_thread.quit)
        self.search_worker.finished.connect(self.search_worker.deleteLater)
        self.search_thread.finished.connect(self.search_thread.deleteLater)
        
        print("DEBUG: Spouštím vyhledávání ve vlákně...")
        self.search_thread.start()
    
    def stop_search(self):
        """Zastaví probíhající vyhledávání."""
        if self.search_worker and self.search_thread and self.search_thread.isRunning():
            self.search_worker.stop()
            self.main_window.update_status("Vyhledávání bylo zastaveno")
            self.main_window.update_info_label("Vyhledávání bylo zastaveno")
    
    def analyze_duplicates(self):
        """Analyzuje duplicitní projekty a seskupuje je do skupin."""
        if not self.finder_model.projects:
            self.main_window.show_message(
                "Žádné projekty", 
                "Nejsou k dispozici žádné projekty pro analýzu duplicit.",
                QMessageBox.Warning
            )
            return
        
        # Získáme skupiny duplicitních projektů
        groups = self.finder_model.group_duplicates()
        
        # Vždy zobrazíme seznam projektů ve stromovém pohledu
        self.main_window.project_list_view.show_all_projects(self.finder_model.projects)
        
        if groups:
            # Zobrazíme skupiny přímo v hlavním okně
            self.main_window.project_list_view.show_duplicate_groups(groups)
            self.main_window.update_status(f"Nalezeno {len(groups)} skupin podobných projektů")
            
            # Vytvoříme podrobnější zprávu pro uživatele
            report = f"<h3>Nalezeno {len(groups)} skupin podobných projektů</h3>"
            
            # Automaticky uložíme výsledky do JSON souboru v kořenovém adresáři programu
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"projekty_analyza_{timestamp}.json"
            
            try:
                self.export_projects(json_filename)
                self.main_window.update_status(f"Výsledky byly uloženy do souboru {json_filename}")
            except Exception as e:
                self.main_window.show_message(
                    "Chyba při ukládání", 
                    f"Nepodařilo se uložit výsledky do souboru: {str(e)}",
                    QMessageBox.Warning
                )
        else:
            # I když nejsou duplicity, zobrazíme zprávu a ponecháme seznam projektů v okně
            self.main_window.update_status("Analýza dokončena. Žádné duplicitní projekty nenalezeny.")
            self.main_window.update_info_label("Žádné duplicitní projekty. Zobrazuji všechny nalezené projekty.")
    
    def export_projects(self, filename):
        """
        Exportuje seznam projektů do JSON souboru.
        
        Args:
            filename (str): Cesta k výstupnímu souboru
            
        Returns:
            bool: True, pokud se export podařil, jinak False
        """
        if not self.finder_model.projects:
            self.main_window.show_message(
                "Žádné projekty", 
                "Nejsou k dispozici žádné projekty pro export.",
                QMessageBox.Warning
            )
            return False
        
        return self.finder_model.save_to_json(filename)
    
    def import_projects(self, filename):
        """
        Importuje seznam projektů z JSON souboru.
        
        Args:
            filename (str): Cesta ke vstupnímu souboru
            
        Returns:
            bool: True, pokud se import podařil, jinak False
        """
        # Vymazání starých výsledků
        self.main_window.project_list_view.clear()
        
        success = self.finder_model.load_from_json(filename)
        
        if success:
            self.main_window.update_info_label(f"Načteno {len(self.finder_model.projects)} projektů ze souboru: {filename}")
        
        return success
    
    def update_settings(self, settings):
        """
        Aktualizuje nastavení vyhledávače.
        
        Args:
            settings (dict): Slovník s nastaveními
        """
        self.finder_model.ignore_dirs = settings["ignored_dirs"]
        self.finder_model.python_extensions = settings["python_extensions"]
    
    def open_folder(self, path):
        """
        Otevře složku v souborovém manažeru.
        
        Args:
            path (str): Cesta ke složce
        """
        from controller.app_controller import AppController
        AppController.open_directory(path)
    
    def show_project_details(self, project):
        """
        Zobrazí detaily projektu.
        
        Args:
            project: Projekt, jehož detaily mají být zobrazeny
        """
        message = f"<h3>Detaily projektu</h3>"
        message += f"<p><b>Cesta:</b> {project.path}</p>"
        message += f"<p><b>Počet souborů:</b> {project.file_count}</p>"
        message += f"<p><b>Velikost:</b> {project.get_formatted_size()}</p>"
        message += f"<p><b>Poslední změna:</b> {project.get_formatted_last_modified()}</p>"
        
        # Přidání seznamu projektových souborů, pokud existují
        if project.project_files:
            message += f"<p><b>Projektové soubory:</b></p><ul>"
            for file in project.project_files:
                message += f"<li>{os.path.basename(file)}</li>"
            message += "</ul>"
        
        if project.python_files:
            message += f"<p><b>Python soubory:</b></p><ul>"
            # Omezíme počet zobrazených souborů, aby dialog nebyl příliš velký
            max_files = 10
            for i, file in enumerate(project.python_files[:max_files]):
                message += f"<li>{file}</li>"
            
            if len(project.python_files) > max_files:
                message += f"<li>... a dalších {len(project.python_files) - max_files} souborů</li>"
            
            message += "</ul>"
        
        self.main_window.show_message(f"Projekt: {project.name}", message)
    
    @Slot()
    def on_search_started(self):
        """Slot volaný při zahájení vyhledávání."""
        self.main_window.update_status("Vyhledávání projektů...")
        self.main_window.update_info_label("Probíhá vyhledávání projektů...")
    
    @Slot(object)
    def on_project_found(self, project):
        """
        Slot volaný při nalezení projektu.
        
        Args:
            project: Nalezený projekt
        """
        # Přidání projektu do seznamu
        self.main_window.project_list_view.add_project(project)
        
        # Aktualizace stavové lišty s počtem aktuálně nalezených projektů
        count = len(self.finder_model.projects)
        self.main_window.update_status(f"Probíhá vyhledávání... Nalezeno {count} projektů")
    
    @Slot(int)
    def on_search_finished(self, count):
        """
        Slot volaný při dokončení vyhledávání.
        
        Args:
            count (int): Počet nalezených projektů
        """
        if count == 0:
            self.main_window.update_info_label("Žádné Python projekty nebyly nalezeny.")
            self.main_window.update_status("Vyhledávání dokončeno. Žádné projekty nenalezeny.")
        else:
            self.main_window.update_info_label(f"Nalezeno {count} Python projektů.")
            self.main_window.update_status(f"Vyhledávání dokončeno. Nalezeno {count} projektů.")
        
            # Pokud bylo nalezeno více než 500 projektů, zobrazíme varování
            if count > 500:
                self.main_window.show_message(
                    "Velký počet projektů",
                    f"Bylo nalezeno {count} projektů, což je velké množství. Analýza duplicit může trvat déle.",
                    QMessageBox.Information
                )
    
    @Slot(str)
    def on_search_error(self, error_message):
        """
        Slot volaný při chybě vyhledávání.
        
        Args:
            error_message (str): Chybová zpráva
        """
        self.main_window.show_message("Chyba vyhledávání", error_message, QMessageBox.Critical)
        self.main_window.update_status("Vyhledávání selhalo: " + error_message)

    @Slot(str)
    def on_directory_scanning(self, directory):
        """
        Slot volaný při zahájení vyhledávání v zadaném adresáři.
        
        Args:
            directory (str): Adresář, ve kterém se vyhledává
        """
        # Zkrátíme dlouhé cesty pro lepší zobrazení ve stavovém řádku
        max_path_length = 50
        shortened_path = directory
        if len(directory) > max_path_length:
            # Zkrátíme cestu, ale zachováme začátek a konec
            parts = directory.split(os.sep)
            if len(parts) > 3:
                shortened_path = os.path.join(parts[0], '...', *parts[-2:])
            else:
                # Pokud je cesta krátká, jen zkrátíme střed
                shortened_path = directory[:20] + "..." + directory[-27:]
        
        # Aktualizujeme stavový řádek s informací o aktuálně prohledávaném adresáři a počtu projektů
        count = len(self.finder_model.projects)
        self.main_window.update_status(f"Prohledávám... Nalezeno: {count} projektů")
        self.main_window.update_scanning_directory(shortened_path)
        
        # Informační štítek aktualizujeme méně často, abychom nerušili uživatele
        # Aktualizujeme ho pouze při změně počtu nalezených projektů
        if count % 10 == 0 or count <= 10:
            self.main_window.update_info_label(f"Probíhá vyhledávání projektů... Nalezeno: {count}")

    @Slot(str)
    def on_file_scanning(self, file_path):
        """
        Slot volaný při zpracování souboru.
        
        Args:
            file_path (str): Cesta k souboru
        """
        # Zkrátíme dlouhé cesty pro lepší zobrazení ve stavovém řádku
        max_path_length = 50
        file_name = os.path.basename(file_path)
        
        # Pro stavový řádek použijeme jméno souboru a část cesty
        if len(file_path) > max_path_length:
            directory = os.path.dirname(file_path)
            parts = directory.split(os.sep)
            
            if len(parts) > 3:
                # Zobrazíme jen začátek a konec cesty
                short_dir = os.path.join(parts[0], '...', *parts[-2:])
                display_path = os.path.join(short_dir, file_name)
            else:
                # Ponecháme celou cestu ke složce a název souboru
                display_path = file_path
                
            if len(display_path) > max_path_length:
                # Pokud je i tak příliš dlouhá, zkrátíme ji
                display_path = "..." + display_path[-max_path_length+3:]
        else:
            display_path = file_path
        
        # Aktualizujeme stavový řádek s informací o aktuálně zpracovávaném souboru
        count = len(self.finder_model.projects)
        self.main_window.update_status(f"Prohledávám... Nalezeno: {count} projektů")
        self.main_window.update_scanning_directory(f"Soubor: {display_path}") 