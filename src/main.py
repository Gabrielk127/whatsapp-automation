""" Main entry point for the application."""

from src.services.application_service import ApplicationService


def main() -> None:
    """Run the application."""
    application = ApplicationService()
    application.run_sync()


if __name__ == "__main__":
    main()
