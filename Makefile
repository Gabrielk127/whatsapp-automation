db-push:
	@echo "🔄 Pushing database schema changes with Prisma..."
	prisma db push

start:db-push
	@echo "🚀 Executing main program..."
	python -m src.main

server:db-push
	@echo "🌐 Starting Flask server..."
	python -m src.app_server

install:pre-commit-install
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

clean:
	@echo "🧹 Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

freeze:
	@echo "📜 Saving updated dependencies..."
	pip freeze > requirements.txt

pre-commit-install:
	@echo "🔧 Configuring pre-commit hooks..."
	pre-commit install

format:
	@echo "📝 Formatting code with Black..."
	pre-commit run --all-files

help:
	@echo "Available commands:"
	@echo "  make start       - Configure permissions and execute the program"
	@echo "  make server      - Start the Flask server"
	@echo "  make test-server - Test the Flask server"
	@echo "  make setup       - Configure X11 permissions only"
	@echo "  make run         - Execute the program without configuring permissions"
	@echo "  make install     - Install dependencies from requirements.txt"
	@echo "  make clean       - Remove Python cache (__pycache__, *.pyc)"
	@echo "  make freeze      - Save current dependencies to requirements.txt"
	@echo "  make help        - Show this help message"
