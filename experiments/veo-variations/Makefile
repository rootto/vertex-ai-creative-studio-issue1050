# Makefile for Veo Variations Studio

.PHONY: help install clean api ui build

help:
	@echo "Usage:"
	@echo "  make install          Install dependencies"
	@echo "  make clean            Remove temporary files"
	@echo "  make api              Run FastAPI backend"
	@echo "  make ui               Run Lit frontend (Dev mode)"
	@echo "  make build            Build frontend for production"

install:
	export UV_DEFAULT_INDEX=https://pypi.org/simple && uv add fastapi uvicorn google-genai google-cloud-storage python-dotenv python-multipart mcp requests google-auth pyiqa opencv-python c2pa-python marked
	cd ui && npm install

clean:
	rm -f *.mp4 *.png
	rm -rf __pycache__ core/__pycache__ api/__pycache__ ui/dist
	@echo "Cleaned."

api:
	uv run uvicorn api.main:app --reload --port 8000

ui:
	cd ui && npm run dev

build:
	cd ui && npm run build
