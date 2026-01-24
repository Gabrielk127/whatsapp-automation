#!/usr/bin/env python
"""Launcher script para WhatsApp Automation."""

import sys
import os

# Adiciona o diretório atual ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from src.main import main
    main()
