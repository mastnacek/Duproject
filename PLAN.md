# Plán nahrání projektu na GitHub

Tento dokument popisuje kroky potřebné k nahrání projektu "Python Project Finder" do nově vytvořeného GitHub repozitáře.

**URL repozitáře:** `https://github.com/mastnacek/Duproject.git`

## Kroky implementace:

1.  **Vytvoření souboru `.gitignore`:**
    *   Vytvoří se soubor s názvem `.gitignore` v kořenovém adresáři projektu.
    *   Do souboru se zapíše následující obsah pro ignorování nepotřebných souborů:
        ```gitignore
        # Virtual Environment
        venv/
        .venv/
        env/
        ENV/

        # Byte-compiled / optimized / DLL files
        __pycache__/
        *.py[cod]
        *$py.class

        # Distribution / packaging
        .Python
        build/
        develop-eggs/
        dist/
        downloads/
        eggs/
        .eggs/
        lib/
        lib64/
        parts/
        sdist/
        var/
        wheels/
        pip-wheel-metadata/
        share/python-wheels/
        *.egg-info/
        .installed.cfg
        *.egg
        MANIFEST

        # PyInstaller
        # Usually these files are written by a python script from a template
        # before PyInstaller builds the exe, so as to inject date/other infos into it.
        *.manifest
        *.spec

        # Installer logs
        pip-log.txt
        pip-delete-this-directory.txt

        # Unit test / coverage reports
        htmlcov/
        .tox/
        .nox/
        .coverage
        .coverage.*
        .cache
        nosetests.xml
        coverage.xml
        *.cover
        *.py,cover
        .hypothesis/
        .pytest_cache/

        # Jupyter Notebook
        .ipynb_checkpoints

        # Environments
        .env
        .env.*
        env.yaml

        # IDE files
        .idea/
        .vscode/
        *.swp
        *.swo
        ```

2.  **Inicializace Git repozitáře:**
    *   Spustí se příkaz: `git init`

3.  **Přidání všech souborů do Gitu (staging):**
    *   Spustí se příkaz: `git add .` (Poznámka: `PLAN.md` bude také přidán)

4.  **Vytvoření prvního commitu:**
    *   Spustí se příkaz: `git commit -m "Initial commit of Python Project Finder"`

5.  **Přejmenování hlavní větve na 'main':**
    *   Spustí se příkaz: `git branch -M main`

6.  **Propojení lokálního repozitáře se vzdáleným na GitHubu:**
    *   Spustí se příkaz: `git remote add origin https://github.com/mastnacek/Duproject.git`

7.  **Nahrání kódu na GitHub:**
    *   Spustí se příkaz: `git push -u origin main`