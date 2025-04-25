#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog pro nastavení aplikace Python Project Finder.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QCheckBox, QDialogButtonBox,
    QListWidget, QListWidgetItem, QPushButton, QGroupBox
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QDoubleValidator

from config import IGNORED_DIRECTORIES, PYTHON_EXTENSIONS, SIMILARITY_THRESHOLD


class SettingsDialog(QDialog):
    """Dialog pro nastavení aplikace."""
    
    def __init__(self, parent=None):
        """Inicializace dialogu."""
        super().__init__(parent)
        
        self.setWindowTitle("Nastavení aplikace")
        self.resize(500, 400)
        
        # Načtení aktuálního nastavení
        self.settings = QSettings("mastnacek", "PythonProjectFinder")
        
        # Ignorované adresáře
        self.ignored_dirs = self.settings.value(
            "finder/ignored_dirs", 
            IGNORED_DIRECTORIES, 
            list
        )
        
        # Přípony souborů
        self.python_extensions = self.settings.value(
            "finder/python_extensions", 
            PYTHON_EXTENSIONS, 
            list
        )
        
        # Práh podobnosti
        self.similarity_threshold = self.settings.value(
            "finder/similarity_threshold", 
            SIMILARITY_THRESHOLD, 
            float
        )
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializace uživatelského rozhraní dialogu."""
        layout = QVBoxLayout(self)
        
        # Sekce pro ignorované adresáře
        ignored_group = QGroupBox("Ignorované adresáře")
        ignored_layout = QVBoxLayout(ignored_group)
        
        self.ignored_list = QListWidget()
        self.ignored_list.setSelectionMode(QListWidget.SingleSelection)
        for directory in self.ignored_dirs:
            QListWidgetItem(directory, self.ignored_list)
        
        ignored_layout.addWidget(self.ignored_list)
        
        ignored_buttons_layout = QHBoxLayout()
        self.add_ignored_button = QPushButton("Přidat")
        self.add_ignored_button.clicked.connect(self.add_ignored_dir)
        ignored_buttons_layout.addWidget(self.add_ignored_button)
        
        self.remove_ignored_button = QPushButton("Odebrat")
        self.remove_ignored_button.clicked.connect(self.remove_ignored_dir)
        ignored_buttons_layout.addWidget(self.remove_ignored_button)
        
        ignored_layout.addLayout(ignored_buttons_layout)
        layout.addWidget(ignored_group)
        
        # Sekce pro přípony souborů
        extensions_group = QGroupBox("Přípony Python souborů")
        extensions_layout = QVBoxLayout(extensions_group)
        
        self.extensions_list = QListWidget()
        self.extensions_list.setSelectionMode(QListWidget.SingleSelection)
        for extension in self.python_extensions:
            QListWidgetItem(extension, self.extensions_list)
        
        extensions_layout.addWidget(self.extensions_list)
        
        extensions_buttons_layout = QHBoxLayout()
        self.add_extension_button = QPushButton("Přidat")
        self.add_extension_button.clicked.connect(self.add_extension)
        extensions_buttons_layout.addWidget(self.add_extension_button)
        
        self.remove_extension_button = QPushButton("Odebrat")
        self.remove_extension_button.clicked.connect(self.remove_extension)
        extensions_buttons_layout.addWidget(self.remove_extension_button)
        
        extensions_layout.addLayout(extensions_buttons_layout)
        layout.addWidget(extensions_group)
        
        # Sekce pro nastavení duplicit
        duplicates_group = QGroupBox("Nastavení detekce duplicit")
        duplicates_layout = QFormLayout(duplicates_group)
        
        self.threshold_edit = QLineEdit(str(self.similarity_threshold))
        self.threshold_edit.setValidator(QDoubleValidator(0.0, 1.0, 2))
        duplicates_layout.addRow("Práh podobnosti (0.0 - 1.0):", self.threshold_edit)
        
        layout.addWidget(duplicates_group)
        
        # Tlačítka OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def add_ignored_dir(self):
        """Přidá nový ignorovaný adresář do seznamu."""
        text, ok = self.get_text_input("Přidat ignorovaný adresář", "Název adresáře:")
        if ok and text:
            if text not in self.ignored_dirs:
                QListWidgetItem(text, self.ignored_list)
                self.ignored_dirs.append(text)
    
    def remove_ignored_dir(self):
        """Odebere vybraný ignorovaný adresář ze seznamu."""
        selected_items = self.ignored_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        directory = item.text()
        
        row = self.ignored_list.row(item)
        self.ignored_list.takeItem(row)
        self.ignored_dirs.remove(directory)
    
    def add_extension(self):
        """Přidá novou příponu souboru do seznamu."""
        text, ok = self.get_text_input("Přidat příponu Python souboru", "Přípona (např. .py):")
        if ok and text:
            if not text.startswith('.'):
                text = '.' + text
            
            if text not in self.python_extensions:
                QListWidgetItem(text, self.extensions_list)
                self.python_extensions.append(text)
    
    def remove_extension(self):
        """Odebere vybranou příponu souboru ze seznamu."""
        selected_items = self.extensions_list.selectedItems()
        if not selected_items:
            return
        
        item = selected_items[0]
        extension = item.text()
        
        row = self.extensions_list.row(item)
        self.extensions_list.takeItem(row)
        self.python_extensions.remove(extension)
    
    def get_text_input(self, title, label):
        """
        Zobrazí dialog pro zadání textu.
        
        Args:
            title (str): Titulek dialogu
            label (str): Popisek pro textové pole
            
        Returns:
            tuple: (zadaný_text, stav_ok)
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        text_edit = QLineEdit()
        form_layout.addRow(label, text_edit)
        layout.addLayout(form_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        result = dialog.exec()
        return text_edit.text(), result == QDialog.Accepted
    
    def accept(self):
        """Zpracování dialogu při potvrzení."""
        # Uložení nastavení
        try:
            threshold = float(self.threshold_edit.text())
            if 0.0 <= threshold <= 1.0:
                self.similarity_threshold = threshold
            else:
                self.similarity_threshold = SIMILARITY_THRESHOLD
        except ValueError:
            self.similarity_threshold = SIMILARITY_THRESHOLD
        
        # Uložení nastavení do QSettings
        self.settings.setValue("finder/ignored_dirs", self.ignored_dirs)
        self.settings.setValue("finder/python_extensions", self.python_extensions)
        self.settings.setValue("finder/similarity_threshold", self.similarity_threshold)
        
        super().accept()
    
    def get_settings(self):
        """
        Vrací aktuální nastavení dialogu.
        
        Returns:
            dict: Slovník s nastaveními
        """
        return {
            "ignored_dirs": self.ignored_dirs,
            "python_extensions": self.python_extensions,
            "similarity_threshold": self.similarity_threshold
        } 