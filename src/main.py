""" Main entry point for the application."""

from src.services.application_service import ApplicationService, AutomationMode


def main() -> None:
    """Run the application."""
    print("\n" + "="*60)
    print("🤖 WhatsApp Automation")
    print("="*60 + "\n")
    
    # Executa automação com MongoDB logging habilitado
    application = ApplicationService(mode=AutomationMode.SEND, include_mongodb=True)
    application.run_sync()


if __name__ == "__main__":
    main()
