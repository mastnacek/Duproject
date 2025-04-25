#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vstupní bod aplikace Python Project Finder.
Spouští hlavní aplikaci GUI pro vyhledávání a analýzu Python projektů.
"""

import sys
from PySide6.QtWidgets import QApplication
from controller.app_controller import AppController


def main():
    """Hlavní funkce aplikace."""
    app = QApplication(sys.argv)
    app.setApplicationName("Python Project Finder")
    app.setOrganizationName("mastnacek")
    
    # Vytvoření a spuštění hlavního controlleru
    controller = AppController()
    controller.start()
    
    # Spuštění hlavní smyčky aplikace
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 