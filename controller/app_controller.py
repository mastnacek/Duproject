#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hlavní controller aplikace Python Project Finder.
Propojuje modely a GUI komponenty.
"""

import os
import subprocess
import sys
from PySide6.QtCore import QObject, QThread, Signal, Slot, QSettings
from PySide6.QtWidgets import QMessageBox, QApplication

from view.main_window import MainWindow
from view.settings_dialog import SettingsDialog
from view.help_dialog import HelpDialog
from controller.finder_controller import FinderController
from config import DEFAULT_OUTPUT_FILE


class AppController(QObject):
    """Hlavní controller aplikace."""
    
    def __init__(self):
        """Inicializace controlleru."""
        super().__init__()
        
        # Inicializace nastavení aplikace
        QSettings.setDefaultFormat(QSettings.IniFormat)
        self.settings = QSettings("mastnacek", "PythonProjectFinder")
        
        # Vytvoření hlavního okna
        self.main_window = MainWindow()
        
        # Vytvoření controlleru pro vyhledávání
        self.finder_controller = FinderController(self.main_window)
        
        # Připojení signálů a slotů
        self.connect_signals()
        
        # Cesta k poslední použité složce
        self.last_directory = self.settings.value("app/last_directory", "")
        
        # Cesta k poslednímu použitému souboru pro export
        self.last_export_file = self.settings.value("app/last_export_file", DEFAULT_OUTPUT_FILE)
    
    def connect_signals(self):
        """Připojení signálů a slotů."""
        # Akce menu a toolbaru
        self.main_window.select_dir_action.triggered.connect(self.select_directory)
        self.main_window.find_projects_action.triggered.connect(self.find_projects)
        self.main_window.stop_search_action.triggered.connect(self.stop_search)
        self.main_window.analyze_action.triggered.connect(self.analyze_duplicates)
        self.main_window.export_action.triggered.connect(self.export_projects)
        self.main_window.import_action.triggered.connect(self.import_projects)
        self.main_window.preferences_action.triggered.connect(self.show_settings)
        self.main_window.help_action.triggered.connect(self.show_help)
        self.main_window.about_action.triggered.connect(self.show_about)
        self.main_window.exit_action.triggered.connect(self.exit_application)
    
    def start(self):
        """Spustí aplikaci."""
        self.main_window.show()
    
    def select_directory(self):
        """Zobrazí dialog pro výběr adresáře."""
        print("DEBUG: select_directory() zavolána")
        directory = self.main_window.select_directory()
        if directory:
            print(f"DEBUG: Vybrán adresář: {directory}")
            self.last_directory = directory
            self.settings.setValue("app/last_directory", directory)
            self.main_window.update_info_label(f"Vybraná složka: {directory}")
            self.main_window.update_status(f"Složka vybrána: {directory}")
            
            # Okamžitě spustíme vyhledávání projektů
            print("DEBUG: Volám self.find_projects()")
            self.find_projects()
            
            # Po dokončení vyhledávání rovnou spustíme analýzu duplicit
            # Poznámka: Toto se provede až po dokončení vyhledávání v separátním vlákně
            # Proto vytvoříme slot, který bude reagovat na dokončení vyhledávání
            self.finder_controller.finder_model.search_finished.connect(self.auto_analyze_duplicates)
        else:
            print("DEBUG: Nebyl vybrán žádný adresář")
    
    def find_projects(self):
        """Spustí vyhledávání projektů."""
        if not self.last_directory:
            self.main_window.show_message(
                "Chybí složka", 
                "Nejprve vyberte složku pro vyhledávání projektů.",
                QMessageBox.Warning
            )
            return
        
        self.finder_controller.find_projects(self.last_directory)
    
    def analyze_duplicates(self):
        """Spustí analýzu duplicitních projektů."""
        self.finder_controller.analyze_duplicates()
    
    def export_projects(self):
        """Exportuje nalezené projekty do JSON souboru."""
        filename = self.main_window.select_save_file(self.last_export_file)
        if filename:
            self.last_export_file = filename
            self.settings.setValue("app/last_export_file", filename)
            success = self.finder_controller.export_projects(filename)
            
            if success:
                self.main_window.update_status(f"Projekty byly exportovány do: {filename}")
                self.main_window.show_message(
                    "Export dokončen", 
                    f"Projekty byly úspěšně exportovány do souboru:\n{filename}"
                )
    
    def import_projects(self):
        """Importuje projekty z JSON souboru."""
        filename = self.main_window.select_open_file()
        if filename:
            success = self.finder_controller.import_projects(filename)
            
            if success:
                self.main_window.update_status(f"Projekty byly importovány ze souboru: {filename}")
                
                # Okamžitě provedeme analýzu duplicit po importu
                self.analyze_duplicates()
    
    def show_settings(self):
        """Zobrazí dialog s nastavením aplikace."""
        settings_dialog = SettingsDialog(self.main_window)
        if settings_dialog.exec():
            # Aktualizace nastavení v controlleru vyhledávání
            settings = settings_dialog.get_settings()
            self.finder_controller.update_settings(settings)
            self.main_window.update_status("Nastavení bylo aktualizováno")
    
    def show_help(self):
        """Zobrazí dialog s nápovědou."""
        help_dialog = HelpDialog(self.main_window)
        help_dialog.exec()
    
    def show_about(self):
        """Zobrazí informace o aplikaci."""
        QMessageBox.about(
            self.main_window,
            "O aplikaci",
            "<h3>Python Project Finder</h3>"
            "<p>Verze 1.0</p>"
            "<p>Aplikace pro vyhledávání a správu Python projektů.</p>"
            "<p>Autor: <a href='https://github.com/mastnacek'>mastnacek</a></p>"
            "<p>Vytvořeno pomocí PySide6</p>"
        )
    
    def exit_application(self):
        """Ukončí aplikaci."""
        # Pokud běží vyhledávání, ukončíme ho
        if hasattr(self.finder_controller, 'search_thread') and self.finder_controller.search_thread:
            if self.finder_controller.search_thread.isRunning():
                # Odpojíme signály, aby se nevyvolaly nechtěné události
                if hasattr(self.finder_controller, 'search_worker') and self.finder_controller.search_worker:
                    try:
                        # Zastavíme worker
                        self.finder_controller.search_worker.stop()
                        # Ukončíme vlákno
                        self.finder_controller.search_thread.quit()
                        # Počkáme na ukončení
                        if not self.finder_controller.search_thread.wait(1000):  # Počkáme 1 sekundu
                            # Pokud se vlákno neukončilo, přerušíme ho násilně
                            print("Vlákno se neukončilo včas, ukončuji násilně.")
                            self.finder_controller.search_thread.terminate()
                    except Exception as e:
                        print(f"Chyba při ukončování vyhledávacího vlákna: {str(e)}")
        
        # Uložíme nastavení
        self.settings.sync()
        
        # Zavřeme hlavní okno
        self.main_window.close()
    
    @staticmethod
    def open_directory(path):
        """
        Otevře složku v souborovém manažeru.
        
        Args:
            path (str): Cesta ke složce
        """
        try:
            if sys.platform == 'win32':
                os.startfile(path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', path])
            else:  # Linux a další Unix systémy
                subprocess.run(['xdg-open', path])
        except Exception as e:
            QMessageBox.warning(
                None, 
                "Chyba při otevírání složky", 
                f"Nepodařilo se otevřít složku: {str(e)}"
            )
    
    @staticmethod
    def update_projects_with_real_data():
        """
        Vyvolá export aktuálního stavu projektů po aktualizaci dat o skutečných velikostech a počtu souborů.
        
        Tato metoda je volána po vypočítání skutečných velikostí a počtu souborů v projektech
        a zajišťuje, že tyto údaje budou uloženy do JSON souboru při příštím exportu.
        """
        # Získáme hlavní okno aplikace
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, MainWindow):
                main_window = widget
                main_window.update_status("Projekty byly aktualizovány o skutečné velikosti, počty souborů a hashe")
                
                # Oznámení, že lze exportovat aktualizovaná data
                QMessageBox.information(
                    main_window,
                    "Data aktualizována",
                    "Projekty byly aktualizovány o skutečné velikosti, počty souborů a hashe.\n"
                    "Pro porovnání projektů podle hashe můžete použít funkci Analyzovat duplicity.\n"
                    "Pro uložení těchto dat použijte funkci Exportovat výsledky."
                )
                break
    
    @Slot(int)
    def auto_analyze_duplicates(self, count):
        """
        Automaticky spustí analýzu duplicit po dokončení vyhledávání.
        
        Args:
            count (int): Počet nalezených projektů
        """
        # Odpojíme signál, aby se neprováděla analýza při dalším vyhledávání,
        # pokud ji uživatel nechce
        self.finder_controller.finder_model.search_finished.disconnect(self.auto_analyze_duplicates)
        
        # I v případě, že nejsou žádné projekty, zobrazíme prázdný seznam
        if count == 0:
            self.main_window.project_list_view.show_all_projects([])
            return
            
        # Vždy zobrazíme seznam projektů, i když neprovádíme analýzu duplicit
        self.main_window.project_list_view.show_all_projects(self.finder_controller.finder_model.projects)
        
        # Spustíme analýzu pouze pokud byly nalezeny alespoň 2 projekty (aby mohly existovat duplicity)
        if count >= 2:
            self.analyze_duplicates()
    
    def stop_search(self):
        """Zastaví vyhledávání projektů."""
        self.finder_controller.stop_search() 