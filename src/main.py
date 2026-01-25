""" Main entry point for the application."""

from src.services.application_service import ApplicationService, AutomationMode


def main() -> None:
    """Run the application."""
    print("\n" + "="*60)
    print("🤖 WhatsApp Automation")
    print("="*60 + "\n")
    
    # Executa automação completa
    application = ApplicationService(mode=AutomationMode.FULL, include_mongodb=False)
    application.run_sync()


if __name__ == "__main__":
    main()
