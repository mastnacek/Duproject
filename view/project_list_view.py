#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Komponenta pro zobrazení seznamu nalezených Python projektů.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QHeaderView, 
    QAbstractItemView, QMenu, QLabel, QSplitter, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QAction, QColor
import os

from config import PROJECT_COLUMNS, GROUP_COLUMNS
from resources.style.themes import ThemeManager
from utils.folder_calculator import calculate_real_folder_sizes, _update_coloring_after_calculation, calculate_folder_hashes, calculate_last_file_modified


class ProjectTableModel(QAbstractTableModel):
    """Model dat pro tabulku s projekty."""
    
    def __init__(self, parent=None):
        """Inicializace modelu."""
        super().__init__(parent)
        self.projects = []
        self.column_names = PROJECT_COLUMNS
        self.duplicates = set()  # Množina indexů duplicitních projektů
        self.similarities = {}   # Slovník podobností mezi projekty
    
    def rowCount(self, parent=QModelIndex()):
        """Vrací počet řádků v modelu."""
        return len(self.projects)
    
    def columnCount(self, parent=QModelIndex()):
        """Vrací počet sloupců v modelu."""
        return len(self.column_names)
    
    def data(self, index, role=Qt.DisplayRole):
        """Vrací data pro daný index a roli."""
        if not index.isValid() or index.row() >= len(self.projects):
            return None
        
        project = self.projects[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:
                # Přidáme informaci o podobnosti k názvu projektu, pokud je k dispozici
                if project in self.similarities:
                    similarity = self.similarities[project]
                    similarity_percent = int(similarity * 100)
                    return f"{project.path} ({similarity_percent}%)"
                return project.path
            elif column == 1:
                return str(project.file_count)
            elif column == 2:
                return project.get_formatted_size()
            elif column == 3:
                return project.get_formatted_last_modified()
        
        elif role == Qt.ToolTipRole:
            if column == 0:
                # Přidáme informaci o projektových souborech do tooltipu
                tooltip = project.path
                if project.project_files:
                    tooltip += "\nProjektové soubory: " + ", ".join(
                        os.path.basename(f) for f in project.project_files
                    )
                # Přidáme informaci o podobnosti
                if project in self.similarities:
                    similarity = self.similarities[project]
                    similarity_percent = int(similarity * 100)
                    tooltip += f"\nPodobnost: {similarity_percent}%"
                return tooltip
            else:
                return project.path
        
        elif role == Qt.BackgroundRole:
            # Zvýraznění duplicitních projektů
            if index.row() in self.duplicates:
                return QColor(DUPLICATE_COLOR)  # Použití barvy z konfigurace
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Vrací data pro hlavičku tabulky."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.column_names[section]
        return None
    
    def set_projects(self, projects):
        """Nastaví nový seznam projektů."""
        self.beginResetModel()
        self.projects = projects
        self.duplicates = set()
        self.endResetModel()
    
    def add_project(self, project):
        """Přidá nový projekt do modelu."""
        self.beginInsertRows(QModelIndex(), len(self.projects), len(self.projects))
        self.projects.append(project)
        self.endInsertRows()
    
    def clear(self):
        """Vymaže všechny projekty z modelu."""
        self.beginResetModel()
        self.projects = []
        self.duplicates = set()
        self.endResetModel()
    
    def set_duplicates(self, duplicates_indices):
        """
        Nastaví indexy duplicitních projektů pro zvýraznění.
        
        Args:
            duplicates_indices (set): Množina indexů duplicitních projektů
        """
        self.duplicates = duplicates_indices
        # Obnovení zobrazení, aby se aplikovalo zvýraznění
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1)
        )
    
    def get_project(self, row):
        """
        Vrací projekt na daném řádku.
        
        Args:
            row (int): Index řádku
            
        Returns:
            ProjectModel: Projekt nebo None
        """
        if 0 <= row < len(self.projects):
            return self.projects[row]
        return None

    def set_similarities(self, similarities):
        """Nastaví nový slovník podobností."""
        self.similarities = similarities
        # Obnovení zobrazení, aby se aplikovalo zvýraznění
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1)
        )


class ProjectListView(QWidget):
    """Widget pro zobrazení seznamu projektů."""
    
    def __init__(self, parent=None):
        """Inicializace widgetu."""
        super().__init__(parent)
        
        self.init_ui()
        self.duplicate_groups = []  # Seznam skupin duplicitních projektů
    
    def init_ui(self):
        """Inicializace uživatelského rozhraní."""
        layout = QVBoxLayout(self)
        
        # Hlavní layout bez rozdělení na panely
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Nadpis pro skupiny projektů
        self.groups_label = QLabel("Skupiny podobných projektů")
        self.groups_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(self.groups_label)
        
        # Vytvoření tabulky pro skupiny podobných projektů
        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabels(GROUP_COLUMNS)  # Použití sloupců z konfigurace
        
        # Nastavení šířky sloupců
        self._update_column_widths()
        
        # Aktivace řazení pro stromový pohled
        self.groups_tree.setSortingEnabled(True)
        self.groups_tree.header().setSortIndicatorShown(True)
        self.groups_tree.header().setSectionsClickable(True)
        
        # Změna: Používáme dvojklik místo jednoho kliknutí pro otevření složky
        self.groups_tree.itemDoubleClicked.connect(self.on_group_doubleClicked)
        # Přidání kontextového menu pro stromový pohled
        self.groups_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.groups_tree.customContextMenuRequested.connect(self.show_groups_context_menu)
        
        # Nastavení vzhledu skupin - nyní získáme aktuální barevné schéma z ThemeManager
        theme = ThemeManager.get_theme(ThemeManager.load_current_theme())
        self.groups_tree.setAlternatingRowColors(True)
        self.groups_tree.setStyleSheet(f"""
            QTreeWidget::item:has-children {{
                font-weight: bold;
                background-color: {theme["tree_header_background"]};
            }}
            
            /* Zajištění čitelnosti textu při výběru položky */
            QTreeWidget::item:selected {{
                color: {theme["selected_item_text"]};
                background-color: {theme["selected_item_background"]};
            }}
            
            /* Zajištění čitelnosti textu při výběru položky skupiny */
            QTreeWidget::item:has-children:selected {{
                color: {theme["selected_item_text"]};
                background-color: {theme["selected_item_background"]};
                font-weight: bold;
            }}
        """)
        
        main_layout.addWidget(self.groups_tree)
        
        # Přidání legendy pro barevné označení
        self.color_legend = self.create_color_legend()
        main_layout.addWidget(self.color_legend)
        
        # Informační štítek na spodní straně
        self.status_label = QLabel("Žádné projekty")
        main_layout.addWidget(self.status_label)
        
        # Skryté komponenty pro kompatibilitu
        self.table_view = QTableView()
        self.project_model = ProjectTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.project_model)
        
        # Nastavení hlavního layoutu
        widget = QWidget()
        widget.setLayout(main_layout)
        layout.addWidget(widget)
    
    def set_projects(self, projects):
        """
        Nastaví nový seznam projektů.
        
        Args:
            projects (list): Seznam projektů
        """
        self.project_model.set_projects(projects)
        self.update_status_label()
    
    def add_project(self, project):
        """
        Přidá nový projekt do seznamu.
        
        Args:
            project: Projekt k přidání
        """
        self.project_model.add_project(project)
        self.update_status_label()
    
    def clear(self):
        """Vymaže všechny projekty ze seznamu."""
        self.project_model.clear()
        self.update_status_label()
    
    def update_status_label(self):
        """Aktualizuje informační štítek."""
        count = self.project_model.rowCount()
        if count == 0:
            self.status_label.setText("Žádné projekty")
        else:
            self.status_label.setText(f"Nalezeno {count} projektů")
    
    def set_filter(self, text):
        """
        Nastaví filtr pro tabulku.
        
        Args:
            text (str): Filtrační text
        """
        self.proxy_model.setFilterFixedString(text)
    
    def highlight_duplicates(self, duplicates):
        """
        Zpracuje duplicitní projekty.
        Tato metoda je zachována pro zpětnou kompatibilitu.
        
        Args:
            duplicates (list): Seznam dvojic (projekt1, projekt2, podobnost)
        """
        # Metoda je prázdná, protože tabulka projektů již není zobrazena
        pass
    
    def show_duplicate_groups(self, groups):
        """
        Zobrazí skupiny duplicitních projektů.
        
        Args:
            groups (list): Seznam skupin duplicitních projektů
        """
        # Získání aktuálního tématu z ThemeManager
        theme = ThemeManager.get_theme(ThemeManager.load_current_theme())
        
        self.duplicate_groups = groups
        
        # Vyčistíme strom skupin
        self.groups_tree.clear()
        
        # Definice sloupců pro jednotlivé hodnoty
        similarity_column = 4  # Sloupec pro podobnost
        hash_column = 6      # Sloupec pro hash
        size_column = 2      # Sloupec pro velikost
        file_count_column = 5  # Sloupec pro počet souborů
        last_file_mod_column = 7  # Sloupec pro poslední změnu souboru
        
        # Naplnění stromu skupinami
        for i, group_data in enumerate(groups):
            group = group_data['projects']
            similarities = group_data['similarities']
            
            # Vytvoříme položku skupiny s informacemi o počtu projektů
            group_item = QTreeWidgetItem(self.groups_tree)
            group_item.setText(0, f"Skupina {i+1}")
            group_item.setData(0, Qt.UserRole, i)  # Uložíme index skupiny
            
            # Zjistíme, zda máme projekty s hashem v této skupině
            projects_with_hash = [p for p in group if hasattr(p, 'folder_hash') and p.folder_hash]
            hash_groups = {}
            
            # Vytvoříme slovník projektů podle hashů
            for project in projects_with_hash:
                if project.folder_hash in hash_groups:
                    hash_groups[project.folder_hash].append(project)
                else:
                    hash_groups[project.folder_hash] = [project]
            
            # Vytvoříme skupiny projektů podle jejich skutečných velikostí
            size_groups = {}
            for project in group:
                if hasattr(project, 'real_size') and project.real_size is not None:
                    if project.real_size in size_groups:
                        size_groups[project.real_size].append(project)
                    else:
                        size_groups[project.real_size] = [project]
            
            # Vytvoříme skupiny projektů podle jejich skutečného počtu souborů
            file_count_groups = {}
            for project in group:
                if hasattr(project, 'real_file_count') and project.real_file_count is not None:
                    if project.real_file_count in file_count_groups:
                        file_count_groups[project.real_file_count].append(project)
                    else:
                        file_count_groups[project.real_file_count] = [project]
            
            # Vytvoříme skupiny projektů podle data poslední změny souboru
            last_mod_groups = {}
            for project in group:
                if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
                    if project.last_file_modified in last_mod_groups:
                        last_mod_groups[project.last_file_modified].append(project)
                    else:
                        last_mod_groups[project.last_file_modified] = [project]
            
            # Pro všechny projekty ve skupině
            for project in group:
                project_item = QTreeWidgetItem(group_item)
                
                # Nastavíme data pro každý sloupec
                # Sloupec 0: Jméno projektu
                basename = os.path.basename(project.path)
                project_item.setText(0, basename if basename else project.name)
                
                # Sloupec 1: Cesta projektu
                project_item.setText(1, project.path)
                
                # Sloupec 2: Velikost projektu
                project_item.setText(2, project.get_formatted_size())
                
                # Sloupec 3: Datum poslední změny
                project_item.setText(3, project.get_formatted_last_modified())
                
                # Sloupec 4: Podobnost v procentech
                # Najdeme nejvyšší podobnost pro tento projekt
                max_similarity = 0
                for other_project in group:
                    if project != other_project and (project, other_project) in similarities:
                        max_similarity = max(max_similarity, similarities[(project, other_project)])
                
                # Zobrazíme podobnost jako procenta
                if max_similarity > 0:
                    similarity_percent = int(max_similarity * 100)
                    project_item.setText(4, f"{similarity_percent}%")
                    
                    # Obarvení celého řádku podle podobnosti
                    if max_similarity >= 0.99:  # 99% a více považujeme za "100%"
                        # Obarvíme celý řádek světle zeleně pro vysokou podobnost
                        for col in range(self.groups_tree.columnCount()):
                            project_item.setBackground(col, QColor("#AAFFAA"))  # Světle zelená
                
                # Uložíme projekt do dat položky
                project_item.setData(0, Qt.UserRole, project)
                
                # Obarvíme buňku s hashem pro projekty se shodným hashem
                if hasattr(project, 'folder_hash') and project.folder_hash:
                    # Pokud existují alespoň dva projekty se stejným hashem
                    if project.folder_hash in hash_groups and len(hash_groups[project.folder_hash]) > 1:
                        project_item.setBackground(hash_column, QColor(theme["same_hash_color"]))
                
                # Obarvíme buňku s velikostí pro projekty se stejnou skutečnou velikostí
                if hasattr(project, 'real_size') and project.real_size is not None:
                    if project.real_size in size_groups and len(size_groups[project.real_size]) > 1:
                        project_item.setBackground(size_column, QColor(theme["same_size_color"]))
                
                # Obarvíme buňku s počtem souborů pro projekty se stejným počtem souborů
                if hasattr(project, 'real_file_count') and project.real_file_count is not None:
                    if project.real_file_count in file_count_groups and len(file_count_groups[project.real_file_count]) > 1:
                        project_item.setBackground(file_count_column, QColor(theme["same_files_color"]))
                
                # Obarvíme buňku s datem poslední změny souboru pro projekty se stejným datem
                if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
                    if project.last_file_modified in last_mod_groups and len(last_mod_groups[project.last_file_modified]) > 1:
                        project_item.setBackground(last_file_mod_column, QColor(theme["same_date_color"]))
                
                # Přidáme datum poslední úpravy souboru
                try:
                    project_item.setText(last_file_mod_column, project.get_formatted_last_file_modified())
                except Exception as e:
                    project_item.setText(last_file_mod_column, "-")
        
        # Zobrazíme sekci skupin, pokud existují skupiny
        if groups:
            # Rozbalíme všechny skupiny pro lepší přehlednost
            for i in range(self.groups_tree.topLevelItemCount()):
                group_item = self.groups_tree.topLevelItem(i)
                self.groups_tree.expandItem(group_item)
                
            # Aktualizujeme informaci o počtu skupin
            self.status_label.setText(f"Nalezeno {len(groups)} skupin podobných projektů")
        else:
            self.groups_tree.clear()
            self.status_label.setText("Žádné skupiny podobných projektů")
    
    def on_group_doubleClicked(self, item, column=0):
        """
        Zpracování dvojkliku na položku ve stromu skupin.
        
        Args:
            item: Položka, na kterou bylo kliknuto
            column: Index sloupce, na který bylo kliknuto
        """
        # Pokud má položka uložená data, zpracujeme je
        if hasattr(item, 'data'):
            data = item.data(0, Qt.UserRole)
            if data and hasattr(data, 'path'):
                # Otevření složky s projektem
                from controller.app_controller import AppController
                AppController.open_directory(data.path)
                
                # Zobrazení detailů ve stavovém řádku
                self.status_label.setText(f"Otevřen projekt: {data.name} ({data.path})")
    
    def get_selected_project(self):
        """
        Vrací vybraný projekt.
        
        Returns:
            ProjectModel: Vybraný projekt nebo None
        """
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return None
        
        # Převod indexu z proxy modelu na index zdrojového modelu
        source_index = self.proxy_model.mapToSource(indexes[0])
        return self.project_model.get_project(source_index.row())
    
    def show_context_menu(self, position):
        """
        Zobrazí kontextové menu pro tabulku.
        
        Args:
            position: Pozice, kde se má menu zobrazit
        """
        selected_project = self.get_selected_project()
        if not selected_project:
            return
        
        context_menu = QMenu(self)
        
        # Akce pro kontextové menu
        open_folder_action = QAction("Otevřít složku", self)
        context_menu.addAction(open_folder_action)
        
        show_details_action = QAction("Zobrazit detaily", self)
        context_menu.addAction(show_details_action)
        
        # Zobrazení menu
        action = context_menu.exec(self.table_view.mapToGlobal(position))
        
        # Zpracování vybrané akce
        if action == open_folder_action:
            self.open_folder()
        elif action == show_details_action:
            self.show_project_details(selected_project)
    
    def open_folder(self):
        """Otevře složku vybraného projektu v souborovém manažeru."""
        project = self.get_selected_project()
        if project:
            from controller.app_controller import AppController
            AppController.open_directory(project.path)
    
    def show_project_details(self, project):
        """
        Zobrazí detaily projektu.
        
        Args:
            project: Projekt, jehož detaily mají být zobrazeny
        """
        # Tento signal bude implementován v controlleru
        pass

    def show_all_projects(self, projects):
        """
        Zobrazí všechny nalezené projekty ve stromovém pohledu.
        
        Args:
            projects (list): Seznam všech projektů
        """
        if not projects:
            return
            
        # Vyčistíme strom skupin
        self.groups_tree.clear()
        
        # Definice sloupců pro jednotlivé hodnoty
        hash_column = 6      # Sloupec pro hash
        size_column = 2      # Sloupec pro velikost
        file_count_column = 5  # Sloupec pro počet souborů
        last_file_mod_column = 7  # Sloupec pro poslední změnu souboru
        
        # Vytvoříme skupinu pro všechny projekty
        all_projects_group = QTreeWidgetItem(self.groups_tree)
        all_projects_group.setText(0, "Všechny nalezené projekty")
        all_projects_group.setData(0, Qt.UserRole, -1)  # Speciální hodnota pro skupinu všech projektů
        
        # Vytvoříme slovník projektů podle hashů
        hash_groups = {}
        for project in projects:
            if hasattr(project, 'folder_hash') and project.folder_hash:
                if project.folder_hash in hash_groups:
                    hash_groups[project.folder_hash].append(project)
                else:
                    hash_groups[project.folder_hash] = [project]
        
        # Vytvoříme skupiny projektů podle jejich skutečných velikostí
        size_groups = {}
        for project in projects:
            if hasattr(project, 'real_size') and project.real_size is not None:
                if project.real_size in size_groups:
                    size_groups[project.real_size].append(project)
                else:
                    size_groups[project.real_size] = [project]
        
        # Vytvoříme skupiny projektů podle jejich skutečného počtu souborů
        file_count_groups = {}
        for project in projects:
            if hasattr(project, 'real_file_count') and project.real_file_count is not None:
                if project.real_file_count in file_count_groups:
                    file_count_groups[project.real_file_count].append(project)
                else:
                    file_count_groups[project.real_file_count] = [project]
        
        # Vytvoříme skupiny projektů podle data poslední změny souboru
        last_mod_groups = {}
        for project in projects:
            if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
                if project.last_file_modified in last_mod_groups:
                    last_mod_groups[project.last_file_modified].append(project)
                else:
                    last_mod_groups[project.last_file_modified] = [project]
        
        # Přidáme všechny projekty do skupiny
        for project in projects:
            project_item = QTreeWidgetItem(all_projects_group)
            
            # Nastavíme data pro každý sloupec
            basename = os.path.basename(project.path)
            project_item.setText(0, basename if basename else project.name)
            project_item.setText(1, project.path)
            project_item.setText(2, project.get_formatted_size())
            project_item.setText(3, project.get_formatted_last_modified())
            
            # Uložíme projekt do dat položky
            project_item.setData(0, Qt.UserRole, project)
            
            # Obarvíme buňku s hashem pro projekty se shodným hashem
            if hasattr(project, 'folder_hash') and project.folder_hash:
                # Pokud existují alespoň dva projekty se stejným hashem
                if project.folder_hash in hash_groups and len(hash_groups[project.folder_hash]) > 1:
                    project_item.setBackground(hash_column, QColor(theme["same_hash_color"]))
            
            # Obarvíme buňku s velikostí pro projekty se stejnou skutečnou velikostí
            if hasattr(project, 'real_size') and project.real_size is not None:
                if project.real_size in size_groups and len(size_groups[project.real_size]) > 1:
                    project_item.setBackground(size_column, QColor(theme["same_size_color"]))
            
            # Obarvíme buňku s počtem souborů pro projekty se stejným počtem souborů
            if hasattr(project, 'real_file_count') and project.real_file_count is not None:
                if project.real_file_count in file_count_groups and len(file_count_groups[project.real_file_count]) > 1:
                    project_item.setBackground(file_count_column, QColor(theme["same_files_color"]))
            
            # Obarvíme buňku s datem poslední změny souboru pro projekty se stejným datem
            if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
                if project.last_file_modified in last_mod_groups and len(last_mod_groups[project.last_file_modified]) > 1:
                    project_item.setBackground(last_file_mod_column, QColor(theme["same_date_color"]))
            
            # Přidáme datum poslední úpravy souboru
            try:
                project_item.setText(last_file_mod_column, project.get_formatted_last_file_modified())
            except Exception as e:
                project_item.setText(last_file_mod_column, "-")
        
        # Rozbalíme skupinu
        self.groups_tree.expandItem(all_projects_group)
        
        # Aktualizujeme informační štítek
        self.status_label.setText(f"Nalezeno {len(projects)} projektů")

    def show_groups_context_menu(self, position):
        """
        Zobrazí kontextové menu pro strom skupin.
        
        Args:
            position: Pozice, kde se má menu zobrazit
        """
        # Získání položky pod kurzorem
        item = self.groups_tree.itemAt(position)
        if not item:
            return
            
        # Vytvoření kontextového menu
        context_menu = QMenu(self)
        
        # Zjistíme, zda je to položka skupiny (má potomky)
        is_group = item.childCount() > 0
        
        if is_group:
            # Akce pro kontextové menu skupiny
            calculate_real_size_action = QAction("Načíst skutečné velikosti složek", self)
            context_menu.addAction(calculate_real_size_action)
            
            calculate_hash_action = QAction("Vypočítat hash obsahu složek", self)
            context_menu.addAction(calculate_hash_action)
            
            calculate_last_mod_action = QAction("Zjistit datum poslední změny souborů", self)
            context_menu.addAction(calculate_last_mod_action)
            
            # Přidání oddělovače
            context_menu.addSeparator()
            
            # Přidání nové položky pro výpočet všech údajů najednou
            calculate_all_data_action = QAction("Vypočítat všechny údaje najednou", self)
            context_menu.addAction(calculate_all_data_action)
            
            # Přidání oddělovače
            context_menu.addSeparator()
            
            # Přidání položek pro řazení
            sort_submenu = context_menu.addMenu("Seřadit projekty ve skupině podle")
            
            sort_by_name_action = QAction("Názvu", self)
            sort_submenu.addAction(sort_by_name_action)
            
            sort_by_path_action = QAction("Cesty", self)
            sort_submenu.addAction(sort_by_path_action)
            
            sort_by_size_action = QAction("Velikosti", self)
            sort_submenu.addAction(sort_by_size_action)
            
            sort_by_date_action = QAction("Data úpravy", self)
            sort_submenu.addAction(sort_by_date_action)
            
            sort_by_similarity_action = QAction("Podobnosti", self)
            sort_submenu.addAction(sort_by_similarity_action)
            
            sort_by_file_count_action = QAction("Počtu souborů", self)
            sort_submenu.addAction(sort_by_file_count_action)
            
            sort_by_hash_action = QAction("Hashe", self)
            sort_submenu.addAction(sort_by_hash_action)
            
            sort_by_last_file_mod_action = QAction("Data poslední změny souboru", self)
            sort_submenu.addAction(sort_by_last_file_mod_action)
            
            # Zobrazení menu
            action = context_menu.exec(self.groups_tree.mapToGlobal(position))
            
            # Zpracování vybrané akce
            if action == calculate_real_size_action:
                self.calculate_real_folder_sizes_action()
            elif action == calculate_hash_action:
                self.calculate_folder_hashes_action()
            elif action == calculate_last_mod_action:
                self.calculate_last_file_modified_action()
            elif action == calculate_all_data_action:
                self.calculate_all_data_action()
            elif action == sort_by_name_action:
                self.sort_group(item, 0)
            elif action == sort_by_path_action:
                self.sort_group(item, 1)
            elif action == sort_by_size_action:
                self.sort_group(item, 2)
            elif action == sort_by_date_action:
                self.sort_group(item, 3)
            elif action == sort_by_similarity_action:
                self.sort_group(item, 4)
            elif action == sort_by_file_count_action:
                self.sort_group(item, 5)
            elif action == sort_by_hash_action:
                self.sort_group(item, 6)
            elif action == sort_by_last_file_mod_action:
                self.sort_group(item, 7)
        else:
            # Akce pro kontextové menu projektu
            open_folder_action = QAction("Otevřít složku", self)
            context_menu.addAction(open_folder_action)
            
            calculate_hash_action = QAction("Vypočítat hash obsahu složky", self)
            context_menu.addAction(calculate_hash_action)
            
            calculate_last_mod_action = QAction("Zjistit datum poslední změny souborů", self)
            context_menu.addAction(calculate_last_mod_action)
            
            # Přidání oddělovače
            context_menu.addSeparator()
            
            # Přidání položky pro výpočet všech údajů najednou
            calculate_all_data_action = QAction("Vypočítat všechny údaje najednou", self)
            context_menu.addAction(calculate_all_data_action)
            
            # Zobrazení menu
            action = context_menu.exec(self.groups_tree.mapToGlobal(position))
            
            # Zpracování vybrané akce
            if action == open_folder_action:
                data = item.data(0, Qt.UserRole)
                if data and hasattr(data, 'path'):
                    from controller.app_controller import AppController
                    AppController.open_directory(data.path)
            elif action == calculate_hash_action:
                data = item.data(0, Qt.UserRole)
                if data and hasattr(data, 'path'):
                    self.calculate_project_hash(item, data)
            elif action == calculate_last_mod_action:
                data = item.data(0, Qt.UserRole)
                if data and hasattr(data, 'path'):
                    self.calculate_project_last_modified(item, data)
            elif action == calculate_all_data_action:
                data = item.data(0, Qt.UserRole)
                if data and hasattr(data, 'path'):
                    self.calculate_all_data_for_project(item, data)
    
    def sort_group(self, group_item, column):
        """
        Seřadí položky ve skupině podle vybraného sloupce.
        
        Args:
            group_item: Položka skupiny v QTreeWidget
            column: Index sloupce, podle kterého se má řadit
        """
        # Nastavení indikátoru řazení na hlavičce sloupce
        self.groups_tree.header().setSortIndicator(column, Qt.AscendingOrder)
        
        # Získání všech potomků skupiny
        children = []
        for i in range(group_item.childCount()):
            child = group_item.child(i)
            children.append(child)
        
        # Odebrání potomků z položky
        for child in children:
            group_item.removeChild(child)
        
        # Seřazení potomků podle textu v daném sloupci
        children.sort(key=lambda x: x.text(column))
        
        # Přidání seřazených potomků zpět do položky
        for child in children:
            group_item.addChild(child)
            
        # Aktualizace informace ve stavovém řádku
        self.status_label.setText(f"Projekty seřazeny podle sloupce {self.groups_tree.headerItem().text(column)}")
    
    def calculate_all_data(self, group_item):
        """
        Vypočítá všechny dodatečné údaje pro projekty ve skupině.
        
        Args:
            group_item: Položka skupiny v QTreeWidget
        """
        # Aktualizace informace ve stavovém řádku
        self.status_label.setText("Výpočet všech údajů pro skupinu projektů...")
        
        # Získáme všechny projekty ve skupině
        projects = []
        for i in range(group_item.childCount()):
            child_item = group_item.child(i)
            project = child_item.data(0, Qt.UserRole)
            if project:
                projects.append((child_item, project))
        
        # Nejprve vypočítáme skutečné velikosti a počty souborů
        calculate_real_folder_sizes(group_item, projects, self.status_label, self._update_coloring_after_calculation)
        
        # Pak vypočítáme hash pro každý projekt
        calculate_folder_hashes(group_item, self.status_label, self._update_coloring_after_calculation)
        
        # Nakonec zjistíme datum poslední změny souboru
        calculate_last_file_modified(group_item, self.status_label)
        
        # Aktualizace informace ve stavovém řádku
        self.status_label.setText(f"Všechny údaje byly vypočítány pro skupinu projektů")

    def calculate_all_data_for_project(self, item, project):
        """
        Vypočítá všechny dodatečné údaje pro jeden projekt.
        
        Args:
            item: Položka v QTreeWidget
            project: Objekt projektu
        """
        from PySide6.QtWidgets import QApplication
        
        # Nastavení kurzoru na čekání
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        # Aktualizace informace ve stavovém řádku
        self.status_label.setText(f"Výpočet všech údajů pro projekt: {project.name}...")
        
        try:
            # Nejprve vypočítáme skutečnou velikost a počet souborů
            total_size = 0
            file_count = 0
            
            # Prochází rekurzivně všechny soubory ve složce (bez filtrování)
            for dirpath, dirnames, filenames in os.walk(project.path):
                # Odstranění ignorovaných adresářů z procházení
                dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
                
                # Přidáme velikosti souborů
                for file in filenames:
                    file_path = os.path.join(dirpath, file)
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except (OSError, FileNotFoundError):
                        pass  # Ignorujeme soubory, ke kterým nemáme přístup
            
            # Uložení skutečných hodnot do objektu projektu
            project.real_size = total_size
            project.real_file_count = file_count
            
            # Aktualizace dat v tabulce
            if total_size >= 1024 * 1024 * 1024:  # Více než 1 GB
                size_str = f"{total_size / (1024 * 1024 * 1024):.2f} GB"
            elif total_size >= 1024 * 1024:  # Více než 1 MB
                size_str = f"{total_size / (1024 * 1024):.2f} MB"
            else:  # V KB
                size_str = f"{total_size / 1024:.2f} KB"
            
            size_column = 2      # Sloupec pro velikost
            file_count_column = 5  # Sloupec pro počet souborů
            
            item.setText(size_column, size_str)  # Aktualizace sloupce s velikostí
            item.setText(file_count_column, str(file_count))  # Nastavení počtu souborů
            
            # Pak vypočítáme hash
            self.calculate_project_hash(item, project)
            
            # Nakonec zjistíme datum poslední změny souboru
            self.calculate_project_last_modified(item, project)
            
            # Aktualizace informace ve stavovém řádku
            self.status_label.setText(f"Všechny údaje byly vypočítány pro projekt: {project.name}")
            
        except Exception as e:
            self.status_label.setText(f"Chyba při výpočtu údajů: {str(e)}")
        
        # Obnovení normálního kurzoru
        QApplication.restoreOverrideCursor()

    def calculate_real_folder_sizes_action(self):
        """
        Akce pro výpočet skutečných velikostí složek pro vybranou skupinu.
        Tato metoda vyzve k výpočtu skutečných velikostí
        složek a počtu souborů pro všechny projekty ve vybrané skupině.
        """
        # Získáme aktuálně vybranou položku ve stromu
        selected_items = self.groups_tree.selectedItems()
        if not selected_items:
            self.status_label.setText("Vyberte skupinu projektů pro výpočet velikostí složek.")
            return
        
        # Vybereme první vybranou položku
        selected_item = selected_items[0]
        
        # Pokud je vybrán projekt, vybereme jeho rodiče (skupinu)
        if selected_item.parent():
            group_item = selected_item.parent()
        else:
            group_item = selected_item
        
        # Načteme všechny projekty ve skupině
        projects = []
        for i in range(group_item.childCount()):
            child_item = group_item.child(i)
            project = child_item.data(0, Qt.UserRole)
            if project:
                projects.append((child_item, project))
        
        # Spustíme výpočet skutečných velikostí složek
        self.status_label.setText("Výpočet skutečných velikostí složek...")
        calculate_real_folder_sizes(group_item, projects, self.status_label, self._update_coloring_after_calculation)
        self.status_label.setText("Výpočet velikostí složek dokončen.")

    def calculate_folder_hashes_action(self):
        """
        Akce pro výpočet hashů obsahu složek pro vybranou skupinu.
        Tato metoda vyzve k výpočtu hashů pro všechny projekty ve vybrané skupině.
        """
        # Získáme aktuálně vybranou položku ve stromu
        selected_items = self.groups_tree.selectedItems()
        if not selected_items:
            self.status_label.setText("Vyberte skupinu projektů pro výpočet hashů.")
            return
        
        # Vybereme první vybranou položku
        selected_item = selected_items[0]
        
        # Pokud je vybrán projekt, vybereme jeho rodiče (skupinu)
        if selected_item.parent():
            group_item = selected_item.parent()
        else:
            group_item = selected_item
        
        # Načteme všechny projekty ve skupině
        projects = []
        for i in range(group_item.childCount()):
            child_item = group_item.child(i)
            project = child_item.data(0, Qt.UserRole)
            if project:
                projects.append((child_item, project))
        
        # Spustíme výpočet hashů pro všechny projekty ve skupině
        self.status_label.setText("Výpočet hashů obsahu složek...")
        calculate_folder_hashes(group_item, self.status_label, self._update_coloring_after_calculation)
        self.status_label.setText("Výpočet hashů dokončen.")

    def calculate_last_file_modified_action(self):
        """
        Akce pro výpočet datumu poslední úpravy souborů pro vybranou skupinu.
        Tato metoda vyzve k výpočtu datumu poslední úpravy souborů
        pro všechny projekty ve vybrané skupině.
        """
        # Získáme aktuálně vybranou položku ve stromu
        selected_items = self.groups_tree.selectedItems()
        if not selected_items:
            self.status_label.setText("Vyberte skupinu projektů pro výpočet datumů.")
            return
        
        # Vybereme první vybranou položku
        selected_item = selected_items[0]
        
        # Pokud je vybrán projekt, vybereme jeho rodiče (skupinu)
        if selected_item.parent():
            group_item = selected_item.parent()
        else:
            group_item = selected_item
        
        # Načteme všechny projekty ve skupině
        projects = []
        for i in range(group_item.childCount()):
            child_item = group_item.child(i)
            project = child_item.data(0, Qt.UserRole)
            if project:
                projects.append((child_item, project))
        
        # Spustíme výpočet datumů poslední úpravy souborů pro všechny projekty ve skupině
        self.status_label.setText("Výpočet datumů poslední úpravy souborů...")
        calculate_last_file_modified(group_item, self.status_label)
        self.status_label.setText("Výpočet datumů dokončen.")

    def calculate_all_data_action(self):
        """
        Akce pro výpočet všech údajů pro vybranou skupinu.
        Tato metoda vyzve k výpočtu všech údajů
        pro všechny projekty ve vybrané skupině.
        """
        # Získáme aktuálně vybranou položku ve stromu
        selected_items = self.groups_tree.selectedItems()
        if not selected_items:
            self.status_label.setText("Vyberte skupinu projektů pro výpočet všech údajů.")
            return
        
        # Vybereme první vybranou položku
        selected_item = selected_items[0]
        
        # Pokud je vybrán projekt, vybereme jeho rodiče (skupinu)
        if selected_item.parent():
            group_item = selected_item.parent()
        else:
            group_item = selected_item
        
        # Načteme všechny projekty ve skupině
        projects = []
        for i in range(group_item.childCount()):
            child_item = group_item.child(i)
            project = child_item.data(0, Qt.UserRole)
            if project:
                projects.append((child_item, project))
        
        # Spustíme výpočet všech údajů pro všechny projekty ve skupině
        self.status_label.setText("Výpočet všech údajů pro skupinu projektů...")
        self.calculate_all_data(group_item)
        self.status_label.setText("Výpočet všech údajů dokončen.")

    def calculate_project_hash(self, item, project):
        """
        Vypočítá hash obsahu složky pro jeden projekt.
        
        Args:
            item: Položka ve stromovém pohledu
            project: Objekt projektu
        """
        from PySide6.QtWidgets import QApplication
        
        # Nastavení kurzoru na čekání
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        # Aktualizace stavového řádku
        self.status_label.setText(f"Výpočet hashe pro: {project.name}...")
        
        try:
            # Callback pro aktualizaci stavového řádku
            def file_callback(file_path):
                self.status_label.setText(f"Výpočet hashe - zpracovávám: {os.path.basename(file_path)}")
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
                self.status_label.setText(f"Hash vypočítán pro: {project.name}")
            else:
                self.status_label.setText(f"Nepodařilo se vypočítat hash pro: {project.name}")
        
        except Exception as e:
            self.status_label.setText(f"Chyba při výpočtu hashe: {str(e)}")
        
        # Obnovení normálního kurzoru
        QApplication.restoreOverrideCursor()

    def _update_column_widths(self):
        """
        Aktualizuje šířky sloupců po přidání nového sloupce.
        """
        # Nastavení šířky sloupců podle jejich obsahu
        column_count = self.groups_tree.columnCount()
        
        # Standardní šířky sloupců
        standard_widths = {
            0: 200,  # Projekt
            1: 400,  # Cesta
            2: 100,  # Velikost
            3: 150,  # Datum
            4: 100,  # Podobnost
            5: 100,  # Počet souborů
            6: 150,  # Hash
            7: 150,  # Poslední změna souboru
        }
        
        # Nastavení šířek pro všechny sloupce
        for col, width in standard_widths.items():
            if col < column_count:
                self.groups_tree.setColumnWidth(col, width)
                
    def create_color_legend(self):
        """
        Vytvoří legendu pro barevné označení projektů.
        
        Returns:
            QWidget: Widget s legendou barev
        """
        # Získání aktuálního tématu z ThemeManager
        theme = ThemeManager.get_theme(ThemeManager.load_current_theme())
        
        # Vytvoření rámečku pro legendu
        legend_frame = QFrame()
        legend_frame.setObjectName("color_legend")  # Pro speciální stylování v CSS
        legend_frame.setFrameShape(QFrame.StyledPanel)
        
        # Layout pro legendu
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setContentsMargins(5, 5, 5, 5)
        
        # Přidání popisků s barevnými čtverečky
        colors = [
            ("Celý řádek zeleně - podobné projekty", theme["similar_color"]),
            ("Zelená buňka - stejný hash", theme["same_hash_color"]),
            ("Oranžová buňka - stejná velikost", theme["same_size_color"]),
            ("Modrá buňka - stejný počet souborů", theme["same_files_color"]),
            ("Fialová buňka - stejné datum změny souboru", theme["same_date_color"])
        ]
        
        for text, color in colors:
            # Barevný čtvereček
            color_box = QFrame()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid {theme['highlight_background']};")
            
            # Popisek
            label = QLabel(text)
            
            # Přidání do layoutu legendy
            box_layout = QHBoxLayout()
            box_layout.setContentsMargins(5, 0, 15, 0)
            box_layout.addWidget(color_box)
            box_layout.addWidget(label)
            
            # Přidání do hlavního layoutu legendy
            legend_layout.addLayout(box_layout)
        
        # Přidání pružiny, aby se barevné boxy zarovnaly doleva
        legend_layout.addStretch(1)
        
        return legend_frame

    def calculate_project_last_modified(self, item, project):
        """
        Zjistí datum poslední úpravy libovolného souboru v projektu.
        
        Args:
            item: Položka ve stromovém pohledu
            project: Objekt projektu
        """
        from PySide6.QtWidgets import QApplication
        
        # Nastavení kurzoru na čekání
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        # Aktualizace stavového řádku
        self.status_label.setText(f"Zjišťování data poslední změny pro: {project.name}...")
        
        try:
            # Získání data poslední změny souboru v projektu
            last_file_time = project.get_last_file_modified()
            formatted_time = project.get_formatted_last_file_modified()
            
            # Index sloupce pro poslední změnu souboru
            last_file_mod_column = 7
            
            # Aktualizace dat v tabulce
            item.setText(last_file_mod_column, formatted_time)
            
            # Aktualizace stavového řádku
            self.status_label.setText(f"Datum poslední změny zjištěno pro: {project.name}")
        
        except Exception as e:
            self.status_label.setText(f"Chyba při zjišťování data poslední změny: {str(e)}")
        
        # Obnovení normálního kurzoru
        QApplication.restoreOverrideCursor() 

    def show_similar_projects(self, projects, groups):
        """
        Zobrazí skupiny podobných projektů.
        
        Args:
            projects (list): Seznam projektů
            groups (list): Seznam skupin podobných projektů
        """
        # Získání aktuálního tématu z ThemeManager
        theme = ThemeManager.get_theme(ThemeManager.load_current_theme())
        
        # Uložení skupin pro pozdější použití (např. pro kontextové menu)
        self.duplicate_groups = groups
        
        # Vyčištění stromu
        self.groups_tree.clear()
        
        # Počítadlo celkového počtu podobných projektů
        total_duplicates = 0
        
        # Nastavení resizeMode na první spuštění, aby byly sloupce správně zarovnány
        for i in range(len(GROUP_COLUMNS)):
            self.groups_tree.header().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Přidání skupin do stromu
        for group_id, group in enumerate(groups):
            # Vytvoření položky pro skupinu
            group_item = QTreeWidgetItem(self.groups_tree)
            
            # Nastavení textu pro název skupiny (první sloupec)
            group_item.setText(0, f"Skupina {group_id + 1}")
            
            # Zvýraznění celé skupiny pomocí barvy na pozadí
            for col in range(len(GROUP_COLUMNS)):
                group_item.setBackground(col, QColor(theme["tree_header_background"]))
            
            # Sečtení počtu projektů v této skupině
            group_size = len(group)
            total_duplicates += group_size
            
            # Přidání informací o projektech ve skupině
            for idx, project_idx in enumerate(group):
                project = projects[project_idx]
                
                # Vytvoření podpoložky pro projekt ve skupině
                project_item = QTreeWidgetItem(group_item)
                
                # Nastavení textu pro jednotlivé sloupce
                basename = os.path.basename(project.path)
                project_item.setText(0, basename if basename else project.name)
                project_item.setText(1, project.path)
                project_item.setText(2, project.get_formatted_size())
                project_item.setText(3, project.get_formatted_last_modified())
                
                # Pokud máme informace o podobnosti, zobrazíme je
                if hasattr(project, 'similarity') and project.similarity is not None:
                    similarity_percent = f"{project.similarity * 100:.0f}%"
                    project_item.setText(4, similarity_percent)
                
                # Pokud máme informaci o počtu souborů, zobrazíme ji
                if hasattr(project, 'real_file_count') and project.real_file_count is not None:
                    project_item.setText(5, str(project.real_file_count))
                
                # Pokud máme informaci o hashi, zobrazíme ji
                if hasattr(project, 'folder_hash') and project.folder_hash is not None:
                    project_item.setText(6, project.folder_hash[:8])  # Zkrácení hashe pro lepší zobrazení
                
                # Pokud máme informaci o poslední změně souboru, zobrazíme ji
                if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
                    project_item.setText(7, project.get_formatted_last_file_modified())
                
                # Zvýraznění řádku projektu podobného ostatním v této skupině
                for col in range(len(GROUP_COLUMNS)):
                    project_item.setBackground(col, QColor(theme["similar_color"]))
                
                # Uložíme projekt do dat položky
                project_item.setData(0, Qt.UserRole, project)
                
                # Nastavení identifikátoru skupiny
                project_item.setData(0, Qt.UserRole + 1, group_id)
        
        # Přidání všech projektů do samostatné skupiny
        self._add_all_projects_group(projects)
        
        # Obnovíme přirozené nastavení šířky sloupců po naplnění daty
        self._update_column_widths()
        
        # Rozbalení všech skupin
        self.groups_tree.expandAll()
        
        # Aktualizace stavového řádku
        self.status_label.setText(f"Nalezeno {len(projects)} projektů, {len(groups)} " +
                                  f"skupin podobných projektů s celkem {total_duplicates} potenciálními duplicitami.")

    def _add_all_projects_group(self, projects):
        """
        Přidá skupinu se všemi projekty do stromu.
        
        Args:
            projects (list): Seznam všech projektů
        """
        # Získání aktuálního tématu z ThemeManager
        theme = ThemeManager.get_theme(ThemeManager.load_current_theme())
        
        # Vytvoření skupiny pro všechny projekty
        all_projects_group = QTreeWidgetItem(self.groups_tree)
        all_projects_group.setText(0, "Všechny projekty")
        
        # Nastavení pozadí pro všechny sloupce
        for col in range(len(GROUP_COLUMNS)):
            all_projects_group.setBackground(col, QColor(theme["tree_header_background"]))
        
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
        for project in projects:
            # Seskupení podle hashů
            if hasattr(project, 'folder_hash') and project.folder_hash:
                if project.folder_hash in hash_groups:
                    hash_groups[project.folder_hash].append(project)
                else:
                    hash_groups[project.folder_hash] = [project]
            
            # Seskupení podle velikosti
            if hasattr(project, 'real_size') and project.real_size is not None:
                if project.real_size in size_groups:
                    size_groups[project.real_size].append(project)
                else:
                    size_groups[project.real_size] = [project]
            
            # Seskupení podle počtu souborů
            if hasattr(project, 'real_file_count') and project.real_file_count is not None:
                if project.real_file_count in file_count_groups:
                    file_count_groups[project.real_file_count].append(project)
                else:
                    file_count_groups[project.real_file_count] = [project]
            
            # Seskupení podle data poslední změny souboru
            if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
                if project.last_file_modified in last_mod_groups:
                    last_mod_groups[project.last_file_modified].append(project)
                else:
                    last_mod_groups[project.last_file_modified] = [project]
        
        # Přidáme všechny projekty do skupiny
        for project in projects:
            project_item = QTreeWidgetItem(all_projects_group)
            
            # Nastavíme data pro každý sloupec
            basename = os.path.basename(project.path)
            project_item.setText(0, basename if basename else project.name)
            project_item.setText(1, project.path)
            project_item.setText(2, project.get_formatted_size())
            project_item.setText(3, project.get_formatted_last_modified())
            
            # Uložíme projekt do dat položky
            project_item.setData(0, Qt.UserRole, project)
            
            # Obarvíme buňku s hashem pro projekty se shodným hashem
            if hasattr(project, 'folder_hash') and project.folder_hash:
                # Pokud existují alespoň dva projekty se stejným hashem
                if project.folder_hash in hash_groups and len(hash_groups[project.folder_hash]) > 1:
                    project_item.setBackground(hash_column, QColor(theme["same_hash_color"]))
            
            # Obarvíme buňku s velikostí pro projekty se stejnou skutečnou velikostí
            if hasattr(project, 'real_size') and project.real_size is not None:
                if project.real_size in size_groups and len(size_groups[project.real_size]) > 1:
                    project_item.setBackground(size_column, QColor(theme["same_size_color"]))
            
            # Obarvíme buňku s počtem souborů pro projekty se stejným počtem souborů
            if hasattr(project, 'real_file_count') and project.real_file_count is not None:
                if project.real_file_count in file_count_groups and len(file_count_groups[project.real_file_count]) > 1:
                    project_item.setBackground(file_count_column, QColor(theme["same_files_color"]))
            
            # Obarvíme buňku s datem poslední změny souboru pro projekty se stejným datem
            if hasattr(project, 'last_file_modified') and project.last_file_modified is not None:
                if project.last_file_modified in last_mod_groups and len(last_mod_groups[project.last_file_modified]) > 1:
                    project_item.setBackground(last_mod_column, QColor(theme["same_date_color"]))
            
            # Přidáme datum poslední úpravy souboru
            try:
                project_item.setText(last_file_mod_column, project.get_formatted_last_file_modified())
            except Exception as e:
                project_item.setText(last_file_mod_column, "-")
        
        # Rozbalíme skupinu
        self.groups_tree.expandItem(all_projects_group)
        
        # Aktualizujeme informační štítek
        self.status_label.setText(f"Nalezeno {len(projects)} projektů")

    # Přidám metodu pro aktualizaci obarvení po výpočtu
    def _update_coloring_after_calculation(self, projects):
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