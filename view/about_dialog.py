#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog zobrazující informace o aplikaci "Vyhledávač Python projektů".
Obsahuje název aplikace, verzi, popis, autora a licenci.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSizePolicy, QSpacerItem
)
from PySide6.QtGui import QPixmap, QFont, QDesktopServices
from PySide6.QtCore import Qt, QSize, QUrl

import sys
import os
from pathlib import Path

# Import konfiguračních konstant
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import APP_VERSION


class AboutDialog(QDialog):
    """Dialog zobrazující informace o aplikaci."""
    
    def __init__(self, parent=None):
        """
        Inicializace dialogu About.
        
        Args:
            parent: Rodičovské okno
        """
        super().__init__(parent)
        self.setWindowTitle("O aplikaci")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setModal(True)
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializace uživatelského rozhraní dialogu."""
        # Hlavní layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)
        
        # Nadpis aplikace
        title_label = QLabel("Vyhledávač Python projektů")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Verze aplikace
        version_label = QLabel(f"Verze: {APP_VERSION}")
        version_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(version_label)
        
        # Mezera
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Popis aplikace
        description = (
            "Aplikace pro vyhledávání a analýzu Python projektů na disku. "
            "Umožňuje identifikovat duplicitní projekty a získat přehled "
            "o všech projektech v dané složce a jejích podsložkách."
        )
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        main_layout.addWidget(description_label)
        
        # Mezera
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Informace o autorovi a licenci
        info_layout = QVBoxLayout()
        author_label = QLabel("Autor: Jan Ranš (mastnacek)")
        license_label = QLabel("Licence: MIT")
        info_layout.addWidget(author_label)
        info_layout.addWidget(license_label)
        main_layout.addLayout(info_layout)
        
        # GitHub odkaz
        github_button = QPushButton("GitHub repozitář")
        github_button.clicked.connect(self._open_github)
        main_layout.addWidget(github_button)
        
        # Mezera
        main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Tlačítko Zavřít
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        close_button = QPushButton("Zavřít")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)
    
    def _open_github(self):
        """Otevře GitHub repozitář projektu v prohlížeči."""
        QDesktopServices.openUrl(QUrl("https://github.com/mastnacek/py-project-finder")) 