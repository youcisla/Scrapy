# Makefile minimal pour YouTube Title Psychology
PYTHON = C:/Users/Y.chehboub/Downloads/Projet/.venv/Scripts/python.exe
SCRAPY = $(PYTHON) -m scrapy

.PHONY: help run scrape analyze clean web

help:
	@echo "make run     - Scraper + Analyser"
	@echo "make scrape  - Scraper seulement"
	@echo "make analyze - Analyser seulement"
	@echo "make web     - Lancer l'interface web"
	@echo "make clean   - Nettoyer"

run: scrape analyze

scrape:
	$(SCRAPY) crawl youtube_trends -o tendances_youtube.json

analyze:
	$(PYTHON) analyser_resultats.py tendances_youtube.json

web:
	$(PYTHON) web_app.py

clean:
	@if exist *.json del /Q *.json
	@if exist .scrapy rmdir /S /Q .scrapy
