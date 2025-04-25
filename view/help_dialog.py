#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dialog s nápovědou pro aplikaci Python Project Finder.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QTextBrowser, 
    QDialogButtonBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class HelpDialog(QDialog):
    """Dialog s nápovědou pro aplikaci."""
    
    def __init__(self, parent=None):
        """Inicializace dialogu."""
        super().__init__(parent)
        
        self.setWindowTitle("Nápověda")
        self.resize(600, 500)
        
        self.init_ui()
    
    def init_ui(self):
        """Inicializace uživatelského rozhraní dialogu."""
        layout = QVBoxLayout(self)
        
        # Nadpis
        title_label = QLabel("Python Project Finder - Nápověda")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Záložky s obsahem nápovědy
        tab_widget = QTabWidget()
        
        # Záložka "Základní použití"
        basic_tab = QTextBrowser()
        basic_tab.setOpenExternalLinks(True)
        basic_tab.setHtml(self.get_basic_usage_text())
        tab_widget.addTab(basic_tab, "Základní použití")
        
        # Záložka "Vyhledávání projektů"
        search_tab = QTextBrowser()
        search_tab.setOpenExternalLinks(True)
        search_tab.setHtml(self.get_search_text())
        tab_widget.addTab(search_tab, "Vyhledávání projektů")
        
        # Záložka "Analýza duplicit"
        duplicates_tab = QTextBrowser()
        duplicates_tab.setOpenExternalLinks(True)
        duplicates_tab.setHtml(self.get_duplicates_text())
        tab_widget.addTab(duplicates_tab, "Analýza duplicit")
        
        # Záložka "Nastavení"
        settings_tab = QTextBrowser()
        settings_tab.setOpenExternalLinks(True)
        settings_tab.setHtml(self.get_settings_text())
        tab_widget.addTab(settings_tab, "Nastavení")
        
        layout.addWidget(tab_widget)
        
        # Tlačítko pro zavření
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_basic_usage_text(self):
        """Vrací HTML text pro záložku "Základní použití"."""
        return """
        <h2>Základní použití aplikace</h2>
        <p>Python Project Finder je nástroj pro vyhledávání a správu Python projektů na vašem počítači.</p>
        <p>Hlavní funkce aplikace:</p>
        <ul>
            <li>Vyhledávání Python projektů v zadaném adresáři a jeho podsložkách</li>
            <li>Zobrazení informací o nalezených projektech</li>
            <li>Identifikace potenciálně duplicitních projektů</li>
            <li>Export a import seznamu projektů do/z JSON souboru</li>
        </ul>
        
        <h3>Kroky pro základní použití:</h3>
        <ol>
            <li>Vyberte složku, ve které chcete vyhledat Python projekty pomocí tlačítka "Vybrat složku" nebo volby v menu Soubor</li>
            <li>Klikněte na tlačítko "Vyhledat projekty" pro zahájení vyhledávání</li>
            <li>Po dokončení vyhledávání se nalezené projekty zobrazí v tabulce</li>
            <li>Se seznamem projektů můžete dále pracovat - analyzovat duplicity, exportovat, apod.</li>
        </ol>
        """
    
    def get_search_text(self):
        """Vrací HTML text pro záložku "Vyhledávání projektů"."""
        return """
        <h2>Vyhledávání Python projektů</h2>
        <p>Aplikace vyhledává složky, které obsahují alespoň jeden soubor s příponou typickou pro Python projekty (výchozí: .py, .pyw, .pyx, .pyd).</p>
        
        <h3>Jak probíhá vyhledávání:</h3>
        <ol>
            <li>Aplikace začne v zadaném adresáři</li>
            <li>Zkontroluje, zda adresář obsahuje Python soubory</li>
            <li>Pokud ano, označí ho jako Python projekt a nepokračuje do jeho podsložek</li>
            <li>Pokud ne, prohledává rekurzivně všechny podsložky</li>
            <li>Některé složky jsou automaticky ignorovány (např. __pycache__, venv, .git)</li>
        </ol>
        
        <h3>Zobrazené informace o projektech:</h3>
        <ul>
            <li><strong>Cesta</strong> - Absolutní cesta k adresáři projektu</li>
            <li><strong>Počet souborů</strong> - Počet Python souborů v projektu</li>
            <li><strong>Velikost</strong> - Celková velikost Python souborů</li>
            <li><strong>Poslední změna</strong> - Datum a čas poslední změny v projektu</li>
        </ul>
        
        <h3>Tipy pro vyhledávání:</h3>
        <ul>
            <li>Můžete přizpůsobit ignorované adresáře v nastavení aplikace</li>
            <li>Vyhledávání ve velkých adresářových strukturách může trvat delší dobu</li>
            <li>Pro filtrování výsledků můžete použít funkci vyhledávání v seznamu projektů</li>
        </ul>
        """
    
    def get_duplicates_text(self):
        """Vrací HTML text pro záložku "Analýza duplicit"."""
        return """
        <h2>Analýza duplicitních projektů</h2>
        <p>Tato funkce pomáhá identifikovat potenciálně duplicitní projekty na základě podobnosti souborů.</p>
        
        <h3>Jak funguje detekce duplicit:</h3>
        <ol>
            <li>Aplikace porovnává názvy Python souborů mezi projekty</li>
            <li>Výpočet podobnosti je založen na algoritmu SequenceMatcher z modulu difflib</li>
            <li>Projekty s podobností vyšší než nastavený práh jsou označeny jako potenciální duplicity</li>
            <li>V tabulce jsou duplicitní projekty zvýrazněny žlutou barvou</li>
        </ol>
        
        <h3>Doporučení pro práci s duplicitami:</h3>
        <ul>
            <li>Prohlédněte si označené duplicitní projekty a rozhodněte, zda jde skutečně o duplicity</li>
            <li>Můžete upravit práh podobnosti v nastavení aplikace</li>
            <li>Pro podrobnější porovnání doporučujeme použít specializované nástroje pro porovnání obsahu souborů</li>
        </ul>
        
        <h3>Limitace:</h3>
        <p>Detekce duplicit je založena pouze na názvech souborů, nikoliv na jejich obsahu. To může v některých případech vést k falešně pozitivním nebo falešně negativním výsledkům. Pro přesnější analýzu je vhodné použít specializované nástroje.</p>
        """
    
    def get_settings_text(self):
        """Vrací HTML text pro záložku "Nastavení"."""
        return """
        <h2>Nastavení aplikace</h2>
        <p>V dialogu nastavení můžete přizpůsobit chování aplikace podle svých potřeb.</p>
        
        <h3>Dostupná nastavení:</h3>
        
        <h4>Ignorované adresáře</h4>
        <p>Seznam adresářů, které budou při vyhledávání přeskočeny. Typicky se jedná o adresáře, které neobsahují zdrojový kód projektu nebo jsou generovány automaticky.</p>
        <p>Výchozí hodnoty: __pycache__, venv, .venv, env, .git, .idea, .vscode, node_modules</p>
        
        <h4>Přípony Python souborů</h4>
        <p>Seznam přípon souborů, které budou považovány za Python soubory. Pokud adresář obsahuje alespoň jeden soubor s takovou příponou, bude označen jako Python projekt.</p>
        <p>Výchozí hodnoty: .py, .pyw, .pyx, .pyd</p>
        
        <h4>Nastavení detekce duplicit</h4>
        <p><strong>Práh podobnosti</strong> - Hodnota mezi 0.0 a 1.0 určující minimální podobnost mezi projekty, aby byly označeny jako potenciální duplicity. Vyšší hodnota znamená přísnější kritérium (vyžaduje větší podobnost).</p>
        <p>Výchozí hodnota: 0.8</p>
        
        <h3>Ukládání nastavení</h3>
        <p>Všechna nastavení jsou automaticky ukládána mezi spuštěními aplikace.</p>
        """ 