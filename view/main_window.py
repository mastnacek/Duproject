#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hlavní okno aplikace Python Project Finder.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QToolBar, QStatusBar, QFileDialog, QMessageBox,
    QLabel
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction

from view.project_list_view import ProjectListView
from view.settings_dialog import SettingsDialog
from view.help_dialog import HelpDialog
from config import GUI_TITLE, GUI_WIDTH, GUI_HEIGHT


class MainWindow(QMainWindow):
    """Hlavní okno aplikace."""
    
    def __init__(self):
        """Inicializace hlavního okna aplikace."""
        super().__init__()
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializace uživatelského rozhraní."""
        # Základní nastavení okna
        self.setWindowTitle(GUI_TITLE)
        self.resize(GUI_WIDTH, GUI_HEIGHT)
        
        # Centrální widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hlavní layout
        main_layout = QVBoxLayout(central_widget)
        
        # Informační štítek
        self.info_label = QLabel("Vyberte složku a spusťte vyhledávání Python projektů")
        self.info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_label)
        
        # Seznam projektů - nyní bude zabírat větší část okna
        self.project_list_view = ProjectListView()
        main_layout.addWidget(self.project_list_view)
        
        # Vytvoření akcí
        self.create_actions()
        
        # Toolbar
        self.create_toolbar()
        
        # Vylepšený status bar se štítky pro podrobnější informace
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Přidáme permanentní štítky do stavového řádku
        self.dir_label = QLabel()
        self.status_bar.addPermanentWidget(self.dir_label)
        
        # Nastavíme výchozí zprávu
        self.status_bar.showMessage("Připraveno")
    
    def create_actions(self):
        """Vytvoření akcí pro toolbar."""
        self.select_dir_action = QAction("Vybrat složku", self)
        self.select_dir_action.setShortcut("Ctrl+O")
        
        self.find_projects_action = QAction("Vyhledat projekty", self)
        self.find_projects_action.setShortcut("F5")
        
        self.stop_search_action = QAction("Zastavit vyhledávání", self)
        self.stop_search_action.setShortcut("Esc")
        
        self.analyze_action = QAction("Analyzovat duplicity", self)
        self.analyze_action.setShortcut("F6")
        
        self.export_action = QAction("Uložit výsledky", self)
        self.export_action.setShortcut("Ctrl+S")
        
        self.import_action = QAction("Načíst výsledky", self)
        self.import_action.setShortcut("Ctrl+L")
        
        self.preferences_action = QAction("Konfigurace aplikace", self)
        self.preferences_action.setShortcut("Ctrl+P")
        
        self.help_action = QAction("Jak používat", self)
        self.help_action.setShortcut("F1")
        
        self.about_action = QAction("O aplikaci", self)
        
        self.exit_action = QAction("Ukončit", self)
        self.exit_action.setShortcut("Ctrl+Q")
    
    def create_toolbar(self):
        """Vytvoření panelu nástrojů."""
        toolbar = QToolBar("Hlavní panel")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.select_dir_action)
        toolbar.addAction(self.find_projects_action)
        toolbar.addAction(self.stop_search_action)
        toolbar.addAction(self.export_action)
        toolbar.addAction(self.import_action)
        toolbar.addSeparator()
        toolbar.addAction(self.preferences_action)
        toolbar.addAction(self.help_action)
        toolbar.addAction(self.about_action)
        toolbar.addSeparator()
        toolbar.addAction(self.exit_action)
    
    def show_message(self, title, message, icon=QMessageBox.Information):
        """
        Zobrazí dialogové okno se zprávou.
        
        Args:
            title (str): Titulek okna
            message (str): Zpráva
            icon: Ikona okna (QMessageBox.Information, QMessageBox.Warning, ...)
        """
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    def select_directory(self):
        """
        Zobrazí dialog pro výběr adresáře.
        
        Returns:
            str: Cesta k vybranému adresáři nebo None
        """
        directory = QFileDialog.getExistingDirectory(
            self,
            "Vyberte složku pro vyhledávání projektů",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        return directory if directory else None
    
    def select_save_file(self, default_filename="python_projects.json"):
        """
        Zobrazí dialog pro výběr souboru pro uložení.
        
        Args:
            default_filename (str): Výchozí název souboru
            
        Returns:
            str: Cesta k vybranému souboru nebo None
        """
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Uložit výsledky",
            default_filename,
            "JSON soubory (*.json);;Všechny soubory (*)"
        )
        
        return filename if filename else None
    
    def select_open_file(self):
        """
        Zobrazí dialog pro výběr souboru pro otevření.
        
        Returns:
            str: Cesta k vybranému souboru nebo None
        """
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Načíst výsledky",
            "",
            "JSON soubory (*.json);;Všechny soubory (*)"
        )
        
        return filename if filename else None
    
    def update_status(self, message):
        """
        Aktualizuje zprávu ve stavovém řádku.
        
        Args:
            message (str): Zpráva k zobrazení
        """
        self.status_bar.showMessage(message)
    
    def update_scanning_directory(self, directory):
        """
        Aktualizuje štítek s aktuálně prohledávaným adresářem.
        
        Args:
            directory (str): Aktuálně prohledávaný adresář
        """
        self.dir_label.setText(f"Adresář: {directory}")
        
    def update_info_label(self, message):
        """
        Aktualizuje informační štítek.
        
        Args:
            message (str): Zpráva k zobrazení
        """
        self.info_label.setText(message) 