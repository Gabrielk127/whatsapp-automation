""" Main entry point for the application."""

import sys
from src.services.application_service import ApplicationService, AutomationMode


def main() -> None:
    """Run the application."""
    # Detecta modo de automação a partir de argumentos de linha de comando
    mode = AutomationMode.FULL  # Padrão: automação completa
    include_mongodb = False
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "auth":
            mode = AutomationMode.AUTHENTICATE
        elif arg == "send":
            mode = AutomationMode.SEND
        elif arg == "full":
            mode = AutomationMode.FULL
        elif arg == "--mongodb":
            include_mongodb = True
        
        # Detecta segundo argumento
        if len(sys.argv) > 2 and sys.argv[2] == "--mongodb":
            include_mongodb = True
    
    print(f"\n{'='*60}")
    print(f"🤖 WhatsApp Automation - Modo: {mode.value.upper()}")
    print(f"{'='*60}\n")
    
    # Cria e executa o serviço
    application = ApplicationService(mode=mode, include_mongodb=include_mongodb)
    application.run_sync()


if __name__ == "__main__":
    main()
