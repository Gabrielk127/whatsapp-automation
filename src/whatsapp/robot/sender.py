"""Mass message sending script via WhatsApp."""
import pandas as pd
from playwright.sync_api import sync_playwright
import urllib.parse
import time
import random
import os
import atexit
import signal
from loguru import logger

from ..config import (
    STATE_FILE, EXCEL_FILE, MESSAGE_TEMPLATE_1, MESSAGE_TEMPLATE_2, MESSAGE_TEMPLATE_3,
    PHONE_COLUMNS, DELAY_MIN, DELAY_MAX, DELAY_BETWEEN_MESSAGES, USER_AGENT, CONDOMINIO,
    MAX_CONTACTS_PER_SESSION, BASE_NUMBER
)
from ..utils import clean_phone_number, format_name, is_mobile_phone
from ...repositories.mongo_repository import mongo_repo
from ...utils.structured_logger import StructuredLogger
from ...utils.metrics import SessionMetrics


# Global variables for cleanup
_context = None
_browser = None


def _save_session_and_cleanup():
    """
    Close the persistent context (with launch_persistent_context, session is saved automatically).
    
    The persistent context saves automatically:
    - Cookies
    - LocalStorage
    - SessionStorage
    - IndexedDB
    - Service Workers
    
    Everything is persisted in the .whatsapp_profile directory
    """
    global _context, _browser
    
    if _context:
        try:
            _context.close()
            logger.debug("✅ Persistent context closed (session saved automatically)")
        except Exception as e:
            logger.debug(f"Error closing context: {e}")
    
    if _browser:
        try:
            _browser.close()
            logger.debug("Browser closed")
        except Exception as e:
            logger.debug(f"Error closing browser: {e}")


def _handle_interrupt(signum, frame):
    """Handler for Ctrl+C."""
    logger.warning("⏸️  Interrupt detected. Saving session...")
    _save_session_and_cleanup()
    exit(0)


# Register handler for Ctrl+C
signal.signal(signal.SIGINT, _handle_interrupt)
atexit.register(_save_session_and_cleanup)


def send_messages():
    """
    Send mass messages via WhatsApp Web.
    
    Reads contacts from Excel file (contatos.xlsx) and sends 2 messages to each.
    Uses launch_persistent_context to maintain authentication between executions.
    
    Expected Excel structure:
        - Column 'Nome': Contact name (will be formatted)
        - Columns 'Tel1', 'Tel2', etc: Phone numbers
    """
    # CONNECT TO MONGODB (simple PyMongo - no Prisma)
    logger.info("🔌 Connecting to MongoDB...")
    db_connected = mongo_repo.connect()
    
    if db_connected:
        logger.success("✅ MongoDB connected!")
    else:
        logger.warning("⚠️ Continuing without database...")
    
    # Initialize metrics tracking
    metrics = SessionMetrics()
    
    # Load data
    try:
        df = pd.read_excel(EXCEL_FILE)
        logger.info(f"📊 File '{EXCEL_FILE}' loaded successfully. {len(df)} contacts found.")
        
        # Initialize session in MongoDB for ETA calculations
        if db_connected:
            mongo_repo.init_session(
                total_rows=len(df),
                delay_min=DELAY_MIN,
                delay_max=DELAY_MAX,
                delay_between=DELAY_BETWEEN_MESSAGES
            )
            
    except FileNotFoundError:
        logger.error(f"Error: File '{EXCEL_FILE}' not found.")
        return
        
    # Load history for deduplication
    logger.info("📚 Loading history from database...")
    if db_connected:
        already_sent_phones = mongo_repo.get_all_successful_phones()
        logger.info(f"📚 {len(already_sent_phones)} unique numbers loaded from history.")
    else:
        already_sent_phones = set()
        logger.warning("⚠️ No database connection - Duplicate check disabled.")
    print(already_sent_phones)
    with sync_playwright() as p:


        global _browser, _context
        
        # Ensure data directory exists
        user_data_dir = os.path.join(os.path.dirname(STATE_FILE), '.whatsapp_profile')
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Use launch_persistent_context for more reliable session
        logger.info("🔄 Starting browser with persistent context...")
        _context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo"
        )
        
        _browser = None  # launch_persistent_context returns context, not browser
        
        logger.success("✅ Persistent context created!")
        page = _context.new_page()
        
        # User Agent
        page.set_extra_http_headers({"User-Agent": USER_AGENT})

        logger.info("🌐 Accessing WhatsApp Web...")
        page.goto("https://web.whatsapp.com/")
        
        # Wait for chat list to load OR wait for user to scan QR
        try:
            logger.info("⏳ Waiting for authentication (max 2 minutes to scan QR Code)...")
            StructuredLogger.log_authentication("started")
            page.wait_for_selector("#pane-side", timeout=120000)
            logger.success("✅ WhatsApp loaded and authenticated!")
            StructuredLogger.log_authentication("success")
            time.sleep(5)  # Wait a bit to ensure everything loaded
            
            # ✅ With launch_persistent_context, session is saved automatically!
            logger.success("✅ Session will be persisted automatically by browser.")
                
        except Exception as e:
            logger.error(f"❌ Error connecting to WhatsApp: {e}")
            StructuredLogger.log_authentication("failed", error=str(e))
            _save_session_and_cleanup()
            return
        
        logger.info("Loading WhatsApp...")
        try:
            page.goto("https://web.whatsapp.com/")
            page.wait_for_selector("#pane-side", timeout=40000)
            logger.success("✅ WhatsApp loaded. Starting message dispatch...")
        except Exception as e:
            logger.error(f"Error loading WhatsApp: {e}")
            _save_session_and_cleanup()
            return

        total_sent = 0
        contacts_successfully_processed = 0
        logger.info(f"ℹ️  Contact limit per session: {MAX_CONTACTS_PER_SESSION} (Successful Contacts)")

        for count, (index, row) in enumerate(df.iterrows(), 1):
            if contacts_successfully_processed >= MAX_CONTACTS_PER_SESSION:
                logger.warning(f"🛑 Limit of {MAX_CONTACTS_PER_SESSION} SUCCESSFUL contacts reached for this session.")
                logger.info("   Finishing execution safely...")
                break

            raw_name = row['Nome'] if not pd.isna(row['Nome']) else "Cliente"
            # Format name: lowercase with first letter capitalized, first name only
            formatted_name = format_name(raw_name)
            
            logger.debug(f"DEBUG: Processing row {count}: {raw_name} -> {formatted_name}")
            metrics.record_contact_processed()
            
            # Track all phones and their statuses for this contact
            phones_sent = []
            contact_status = "PENDING"
            
            # Iterate over ALL phone columns for this contact
            for phone_col in PHONE_COLUMNS:
                if phone_col not in df.columns: 
                    logger.debug(f"DEBUG: Column {phone_col} doesn't exist in Excel")
                    continue
                
                raw_phone = row[phone_col]
                
                # IMPORTANT: Skip empty cells silently without counting as invalid
                if pd.isna(raw_phone) or str(raw_phone).strip() == "" or raw_phone == 0:
                    continue
                
                logger.debug(f"DEBUG: Raw phone from {phone_col}: {raw_phone}")
                
                phone = clean_phone_number(raw_phone)
                logger.debug(f"DEBUG: Clean phone: {phone}")
                
                if not phone:
                    # Only record as invalid if there was actually something in the cell
                    metrics.record_invalid_phone()
                    continue

                # Validate: only mobile phones (skip landlines)
                if not is_mobile_phone(phone):
                    logger.warning(f"   ⏭️ Skipping landline: {phone} (not mobile)")
                    continue  # Skip landlines

                # DUPLICATE CHECK: Skip if already sent
                if phone in already_sent_phones:
                    logger.warning(f"   ⏩ Skipping duplicate: {phone} (already sent)")
                    continue

                logger.success(f"✅ Valid mobile: {phone}")
                metrics.record_phone_processed()
                messages_sent_for_phone = 0  # Reset counter for each phone

                # --- SEND 3 MESSAGES PER PHONE ---
                for msg_num in [1, 2, 3]:
                    if msg_num == 1:
                        message = MESSAGE_TEMPLATE_1.format(name=formatted_name)
                        logger.info(f"[{count}] 📱 Processing {formatted_name} - {phone}... (Message {msg_num}/3)")
                    elif msg_num == 2:
                        message = MESSAGE_TEMPLATE_2.format(name=formatted_name, condominio=CONDOMINIO)
                        logger.info(f"   → Sending second message...")
                    else:
                        message = MESSAGE_TEMPLATE_3.format(name=formatted_name) if "{name}" in MESSAGE_TEMPLATE_3 else MESSAGE_TEMPLATE_3
                        logger.info(f"   → Sending third message...")
                    
                    encoded_message = urllib.parse.quote(message)
                    
                    # URL Injection
                    link = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
                    
                    # --- Decision Logic (Race Condition) ---
                    # SPECIFIC selectors for MESSAGE field (not search)
                    input_selector = 'div[data-lexical-editor="true"][aria-label*="Digitar"]'
                    input_selector_alt = 'div[data-lexical-editor="true"]'
                    input_selector_fallback = 'div[aria-placeholder="Digite uma mensagem"]'
                    
                    try:
                        page.goto(link)
                        
                        # Wait for page to load chat or error
                        page.wait_for_load_state("networkidle")
                        
                        # VALIDATION 1: Check for specific error messages from WhatsApp
                        error_detected = False
                        error_reason = ""
                        
                        # Wait a moment for potential popups
                        time.sleep(1.5)

                        # SPECIAL HANDLING: "Number not on WhatsApp" Popup (with OK button)
                        # Detects the popup shown in user's screenshot
                        try:
                            # 1. Check specifically for the DIALOG element which is the most reliable indicator
                            dialog = page.query_selector('div[role="dialog"]')
                            
                            if dialog and dialog.is_visible():
                                dialog_text = dialog.text_content()
                                logger.debug(f"   🔎 Dialog detected with text: {dialog_text[:50]}...")
                                
                                # Check for keywords in the dialog text
                                if "não está no WhatsApp" in dialog_text or \
                                   "não tem o WhatsApp" in dialog_text or \
                                   "inválido" in dialog_text or \
                                   "invalid" in dialog_text:
                                    
                                    error_detected = True
                                    error_reason = "Número não está no WhatsApp (Popup)"
                                    logger.warning(f"   ⚠️ Popup detected: {error_reason}")
                                    
                                    # Try to click OK to close it
                                    ok_btn = dialog.query_selector('button:has-text("OK")')
                                    if not ok_btn:
                                        ok_btn = dialog.query_selector('[data-testid="popup-controls-ok"]')
                                    if not ok_btn:
                                        ok_btn = page.query_selector('div[role="button"]:has-text("OK")')
                                        
                                    if ok_btn:
                                        logger.info(f"      🔘 Clicking OK to dismiss...")
                                        ok_btn.click()
                                        time.sleep(1)
                                    else:
                                        # Fallback click on the dialog itself + Escape?
                                        logger.info(f"      🔘 Could not find OK button, trying Escape...")
                                        page.keyboard.press("Escape")
                                
                            # 2. As fallback, check page text if dialog check failed/missed
                            elif page.is_visible("text=não está no WhatsApp") or \
                                 page.is_visible("text=não tem o WhatsApp"):
                                error_detected = True
                                error_reason = "Número não está no WhatsApp (Text Check)"
                                logger.warning(f"   ⚠️ Text warning detected: {error_reason}")
                                page.keyboard.press("Escape")
                                
                        except Exception as e_popup:
                             logger.debug(f"   Error checking popup: {e_popup}")

                        # Fallback to legacy/strict pattern check if not yet detected
                        if not error_detected:
                            error_patterns = [
                                ('text=não está no WhatsApp', 'Número não está no WhatsApp'),
                                ('text=não tem o WhatsApp', 'Número não tem WhatsApp'),
                                ('text=O número de telefone compartilhado por url é inválido', 'Número inválido'),
                                ('text=número invalido', 'Número inválido'),
                                ('[role="alert"]', 'Alerta geral'),
                            ]
                            
                            try:
                                for selector, reason in error_patterns:
                                    error_elem = page.query_selector(selector)
                                    if error_elem and error_elem.is_visible():
                                        error_text = error_elem.text_content() if hasattr(error_elem, 'text_content') else str(error_elem)
                                        logger.warning(f"   ⚠️ WhatsApp error detected for {phone}")
                                        logger.info(f"      Reason: {reason}")
                                        error_detected = True
                                        error_reason = reason
                                        break
                            except Exception as e:
                                logger.debug(f"   🔍 Error checking patterns: {e}")

                        
                        # If error detected, skip this number and save with status
                        if error_detected:
                            logger.info(f"      → Pulando para próximo número ({error_reason})")
                            metrics.record_not_found()
                            StructuredLogger.log_message_attempt(
                                contact_name=raw_name,
                                phone=phone,
                                message_number=msg_num,
                                total_messages=3,
                                status="invalid",
                                error=error_reason
                            )
                            # Invalid phone - will be counted in contact save
                            break  # Exit message loop (skip to next phone)
                        
                        # VALIDATION 2: Try to find message field
                        input_box = None
                        
                        try:
                            input_box = page.wait_for_selector(input_selector, timeout=10000)
                        except:
                            pass
                        
                        if not input_box:
                            try:
                                input_box = page.wait_for_selector(input_selector_alt, timeout=10000)
                            except:
                                pass
                        
                        if not input_box:
                            try:
                                input_box = page.wait_for_selector(input_selector_fallback, timeout=25000)
                            except:
                                pass
                        
                        # If message field not found, possible reasons:
                        # 1. Number doesn't have WhatsApp
                        # 2. Number is blocked
                        # 3. Page timeout
                        if not input_box:
                            logger.warning(f"   ⚠️ Não foi possível enviar para {phone}")
                            logger.info(f"      Possíveis motivos:")
                            logger.info(f"      • Número não tem WhatsApp ativo")
                            logger.info(f"      • Número está bloqueado")
                            logger.info(f"      • Timeout na página")
                            
                            metrics.record_not_found()
                            StructuredLogger.log_message_attempt(
                                contact_name=raw_name,
                                phone=phone,
                                message_number=msg_num,
                                total_messages=3,
                                status="not_found",
                                error="Message field not found"
                            )
                            
                            # Not found - will be counted in contact save
                            continue  # Skip to next phone
                        
                        if input_box:
                            # Verify correct element (conversation, not search)
                            aria_label = input_box.get_attribute("aria-label") or ""
                            logger.debug(f"   🔎 Element found - aria-label: '{aria_label}'")
                            
                            # VALIDATION: Ensure it's NOT the search field
                            is_message_field = "digitar" in aria_label.lower()
                            is_search_field = "pesquisar" in aria_label.lower() or "search" in aria_label.lower()
                            
                            if is_search_field:
                                logger.warning(f"   ⚠️ Found SEARCH FIELD, not message field! Skipping...")
                                raise Exception("Search field detected, trying another selector")
                            
                            logger.debug(f"   ✅ Validated: It's a message field")
                            
                            # If found the field, ensure text is there
                            logger.debug("   ⏳ Waiting for text processing...")
                            time.sleep(8)
                            
                            # Check if field has text (from URL)
                            text_content = input_box.text_content()
                            logger.debug(f"   📝 Field content (URL): '{text_content}'")
                            
                            # If field is empty, type manually
                            if not text_content or text_content.strip() == "":
                                logger.info(f"   ⌨️ Empty field - typing message manually...")
                                
                                try:
                                    # Ensure field is focused and click multiple times
                                    input_box.click()
                                    time.sleep(0.3)
                                    input_box.click()
                                    time.sleep(0.3)
                                    input_box.focus()
                                    time.sleep(0.5)
                                    
                                    # Clear field before typing (in case there's something)
                                    input_box.fill("")
                                    time.sleep(0.3)
                                    
                                    # Type message using fill() which is more reliable than keyboard.type()
                                    input_box.fill(message)
                                    time.sleep(5)
                                    
                                    logger.debug(f"   ✍️ Message typed via fill()")
                                except Exception as type_error:
                                    logger.error(f"   ❌ Error typing message: {type_error}")
                                    logger.info(f"      Skipping message...")
                                    continue
                            else:
                                logger.debug(f"   ✅ Text already in field (via URL)")
                            
                            # Now send by pressing Enter
                            try:
                                logger.debug("   🔍 Sending message...")
                                input_box.focus()
                                time.sleep(1)
                                page.keyboard.press("Enter")
                                logger.debug(f"   ⏸️ Waiting for send confirmation...")
                                time.sleep(5)
                                
                                # Check if field is empty (indicates message was sent)
                                text_after = input_box.text_content()
                                if text_after is None:
                                    text_after = ""
                                    
                                if text_after == "" or text_after.strip() == "":
                                    logger.success(f"   ✅ Message {msg_num} sent to {phone}")
                                    total_sent += 1
                                    messages_sent_for_phone += 1
                                    metrics.record_success()
                                    StructuredLogger.log_message_attempt(
                                        contact_name=raw_name,
                                        phone=phone,
                                        message_number=msg_num,
                                        total_messages=3,
                                        status="success"
                                    )
                                else:
                                    logger.warning(f"   ⚠️ Field still has text: '{text_after}' - Trying again...")
                                    # Select all and delete
                                    try:
                                        page.keyboard.press("Control+A")
                                        time.sleep(0.2)
                                        page.keyboard.press("Delete")
                                        time.sleep(1)
                                    except Exception as clear_error:
                                        logger.debug(f"      Error clearing field: {clear_error}")
                            except Exception as send_error:
                                logger.error(f"   ❌ Error sending message: {send_error}")
                                logger.info(f"      Will retry with next message...")
                                metrics.record_failure("send_error")
                                StructuredLogger.log_message_attempt(
                                    contact_name=raw_name,
                                    phone=phone,
                                    message_number=msg_num,
                                    total_messages=3,
                                    status="failed",
                                    error=str(send_error)
                                )
                                continue

                        else:
                            logger.error(f"   ❌ Message field not found")
                        
                        # --- DELAY BETWEEN MESSAGES ---
                        if msg_num < 3:  # If not last message, wait before next
                            wait_time = DELAY_BETWEEN_MESSAGES
                            logger.info(f"   💤 Waiting {wait_time}s before message {msg_num + 1}...")
                            time.sleep(wait_time)
                        else:  # If last message, do long delay before next contact
                            wait_time = random.randint(DELAY_MIN, DELAY_MAX)
                            logger.info(f"   💤 Waiting {wait_time}s before next phone...")
                            
                            # --- RETURN TO BASE NUMBER (COOL DOWN) ---
                            # Avoids staying on the contact's chat while waiting
                            try:
                                logger.info(f"      🏠 Returning to base number ({BASE_NUMBER}) for safety...")
                                base_link = f"https://web.whatsapp.com/send?phone={BASE_NUMBER}"
                                page.goto(base_link)
                                
                                # Wait a bit to ensure it loaded the base chat
                                time.sleep(5)
                                
                                # Now wait the rest of the random delay
                                remaining_wait = max(0, wait_time - 5)
                                if remaining_wait > 0:
                                    logger.info(f"      ⏳ Holding at base number for {remaining_wait}s...")
                                    time.sleep(remaining_wait)
                                    
                            except Exception as e_base:
                                logger.error(f"      ❌ Error returning to base number: {e_base}")
                                # If failed, just wait the normal time
                                time.sleep(wait_time)
                        
                        # Track successful messages for this phone
                        pass # Moved append outside the message loop
                
                    except Exception as e_wait:
                        logger.error(f"   ❌ Error processing chat: {type(e_wait).__name__}: {e_wait}")
                        logger.debug(f"      Details: {str(e_wait)}")
                        metrics.record_failure(type(e_wait).__name__)
                        StructuredLogger.log_message_attempt(
                            contact_name=raw_name,
                            phone=phone,
                            message_number=msg_num,
                            total_messages=3,
                            status="error",
                            error=str(e_wait)
                        )
                        
                        # Save as ERROR if some messages were sent
                        pass # Moved append outside the message loop
            
                # After trying all 3 messages for this phone, add to list if at least one was sent
                if messages_sent_for_phone > 0:
                    phones_sent.append(phone)

            # --- SAVE CONTACT TO MONGODB (OUTSIDE PHONE LOOP) ---
            # Calculate funnel metrics once per contact line
            phones_total_raw = 0
            phones_valid_count = 0
            valid_mobile_phones = []
            
            for col in PHONE_COLUMNS:
                raw = row.get(col)
                if raw and not pd.isna(raw) and str(raw).strip() and raw != 0:
                    phones_total_raw += 1
                    cleaned = clean_phone_number(raw)
                    if cleaned:
                        phones_valid_count += 1
                        if is_mobile_phone(cleaned):
                            valid_mobile_phones.append(cleaned)
            
            phones_found = len(valid_mobile_phones)
            phones_with_msg = len(phones_sent)
            
            # Determine overall contact status
            if phones_found == 0:
                contact_status = "NO_MOBILE"  # No valid mobile phones
            elif phones_with_msg == 0:
                contact_status = "ERROR"
            elif phones_with_msg == phones_found:
                contact_status = "SUCCESS"
            else:
                contact_status = "PARTIAL"
            
            if db_connected:
                try:
                    mongo_repo.save_contact(
                        name=raw_name,
                        status=contact_status,
                        phones_found=phones_found,
                        phones_sent=phones_with_msg,
                        phones=phones_sent,
                        condominio=CONDOMINIO,
                        phones_total=phones_total_raw,
                        phones_valid=phones_valid_count
                    )
                    logger.info(f"   💾 MongoDB: {raw_name} | {contact_status} | {phones_with_msg}/{phones_found} phones")
                except Exception as e:
                    logger.debug(f"   ⚠️ Could not save to MongoDB: {e}")
            
            # Increment successful contacts counter if messages were sent
            if phones_with_msg > 0:
                contacts_successfully_processed += 1
                logger.info(f"   ✅ Successful contacts count: {contacts_successfully_processed}/{MAX_CONTACTS_PER_SESSION}")



        logger.success(f"🎉 Processing complete. Total sent: {total_sent}")
        
        # Finalize metrics and log summary
        metrics.finalize()
        summary = metrics.get_summary()
        
        logger.info("=" * 60)
        logger.info("📊 SESSION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Duration: {summary['duration_minutes']:.1f} minutes")
        logger.info(f"Contacts processed: {summary['total_contacts']}")
        logger.info(f"Phones processed: {summary['total_phones_processed']}")
        logger.info(f"Messages sent: {summary['messages_sent']}")
        logger.info(f"Messages failed: {summary['messages_failed']}")
        logger.info(f"Invalid phones: {summary['invalid_phones']}")
        logger.info(f"Not found on WhatsApp: {summary['not_found_phones']}")
        logger.info(f"Success rate: {summary['success_rate_percent']:.1f}%")
        logger.info(f"Messages per minute: {summary['messages_per_minute']:.1f}")
        if summary['errors_by_type']:
            logger.info(f"Errors by type: {summary['errors_by_type']}")
        logger.info("=" * 60)
        
        # Log structured summary for analysis
        StructuredLogger.log_session_summary(
            total_contacts=summary['total_contacts'],
            total_phones_processed=summary['total_phones_processed'],
            total_messages_sent=summary['messages_sent'],
            total_failures=summary['messages_failed'],
            invalid_phones=summary['invalid_phones'],
            not_found_phones=summary['not_found_phones'],
            duration_seconds=summary['duration_seconds'],
            errors_by_type=summary['errors_by_type']
        )
        
        # Save session BEFORE closing
        logger.info("💾 Saving session...")
        try:
            _context.storage_state(path=STATE_FILE)
            time.sleep(1)  # Wait for disk write
            
            # Verify if saved
            if os.path.exists(STATE_FILE) and os.path.getsize(STATE_FILE) > 100:
                logger.success(f"✅ Session saved successfully!")
            else:
                logger.warning("⚠️ File may not have been saved correctly")
        except Exception as e:
            logger.error(f"❌ Error saving session: {e}")
        finally:
            # Close context and browser
            _save_session_and_cleanup()
            
            # MongoDB connection closes automatically


if __name__ == "__main__":
    send_messages()
