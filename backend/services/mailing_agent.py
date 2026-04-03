import os
import json
from huggingface_hub import InferenceClient
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Reload env to ensure we pick up changes without restarting Uvicorn
load_dotenv(override=True)

HF_TOKEN = os.getenv("HF_TOKEN")
# Using Qwen2.5 as it's open, powerful, and usually accessible without gated approval
MODEL_ID = "Qwen/Qwen2.5-72B-Instruct"

client = None
if HF_TOKEN:
    try:
        client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)
    except Exception as e:
        logger.error(f"Failed to init InferenceClient: {e}")

def get_email_creds():
    load_dotenv(override=True)
    addr = os.getenv("EMAIL_ADDRESS")
    pwd = os.getenv("EMAIL_APP_PASSWORD")
    if pwd:
        pwd = pwd.replace(" ", "")  # Usually safer to strip spaces in app passwords
    return addr, pwd

def send_real_email(supplier_name: str, supplier_email: str, component_name: str, requirement_details: dict):
    subject = f"Request for Quote: {component_name}"
    body = (
        f"Hello {supplier_name} Team,\n\n"
        f"We are looking to source {requirement_details.get('quantity', 0)} units of {component_name}.\n"
        f"Please reply to this email with your unit price and estimated lead time in days.\n\n"
        f"Thank you,\n"
        f"Procurement Bot"
    )

    addr, pwd = get_email_creds()
    msg = MIMEMultipart()
    if addr:
        msg['From'] = addr
    msg['To'] = supplier_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    pwd_clean = pwd or ""
    try:
        server = smtplib.SMTP(os.getenv("EMAIL_HOST", "smtp.gmail.com"), int(os.getenv("EMAIL_PORT", 587)))
        server.starttls()
        server.login(addr or "", pwd_clean)
        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent RFQ email to {supplier_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send real email: {e}")
        return False

def fetch_real_inbox_replies(component_name: str):
    """
    Connects to the inbox via IMAP and searches for emails 
    whose subject or body mentions the component name.
    """
    replies = []
    
    addr, pwd = get_email_creds()
    
    # Return empty if creds not configured
    if not addr or not pwd:
        logger.warning("No email credentials found. Cannot fetch real emails.")
        return replies
        
    pwd_clean = pwd or ""
    try:
        mail = imaplib.IMAP4_SSL(os.getenv("IMAP_HOST", "imap.gmail.com"))
        mail.login(addr or "", pwd_clean)
        mail.select("inbox")

        # Search for emails mentioning the component name
        status, messages = mail.search(None, f'BODY "{component_name}"')
        
        if status == "OK" and messages[0]:
            email_ids = messages[0].split()
            for e_id in email_ids:
                res, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Get sender info
                        from_header = decode_header(msg.get("From", ""))[0]
                        sender = from_header[0]
                        if isinstance(sender, bytes):
                            sender = sender.decode(from_header[1] or 'utf-8')
                        
                        # Extract only the name part from "Name <email@domain.com>"
                        real_name, email_addr = parseaddr(sender)
                        display_name = real_name if real_name else email_addr

                        # Extract text payload
                        content_list = []
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if isinstance(payload, bytes):
                                        content_list.append(payload.decode('utf-8', errors='ignore'))
                        else:
                            payload = msg.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                content_list.append(payload.decode('utf-8', errors='ignore'))

                        content = "".join(content_list)
                        replies.append({
                            "supplier_name": display_name,
                            "email_content": content.strip()
                        })

        mail.logout()
    except Exception as e:
        logger.error(f"Failed to fetch emails via IMAP: {e}")
        
    return replies

def analyze_supplier_replies(component_name: str, replies: list):
    """
    Analyzes an array of replies for a given component and extracts price, lead time.
    Also determines the best supplier.
    `replies` should be a list of dicts: {"supplier_name": str, "email_content": str}
    """
    if not client:
        logger.warning("No Hugging Face token provided or client failed to init. Returning mock insights.")
        return {
            "insights": [{"supplier_name": r["supplier_name"], "price": 0.0, "lead_time_days": 0} for r in replies],
            "recommended_supplier": replies[0]["supplier_name"] if replies else "None",
            "reason": "Mocked reason due to missing HF client."
        }

    # Prepare chat messages
    system_prompt = (
        "You are an expert procurement AI assistant. You read supplier email replies, "
        "extract quoted 'price' (as a number) and 'lead_time_days' (as an integer representing days), "
        "and determine the best supplier by considering the lowest price and shortest lead time."
    )
    
    user_prompt = f"Component required: {component_name}\n\nHere are the supplier replies:\n"
    for idx, r in enumerate(replies):
        user_prompt += f"--- ID {idx + 1} ---\nSupplier Name: {r['supplier_name']}\nEmail Content: \"{r['email_content']}\"\n\n"
        
    user_prompt += (
        "Analyze the emails and output pure JSON and nothing else. Output format must exactly match:\n"
        "{\n"
        "  \"insights\": [\n"
        "    {\"supplier_name\": \"Use the exact supplier name from the 'Supplier Name' field above\", \"price\": 1.23, \"lead_time_days\": 5},\n"
        "    ...\n"
        "  ],\n"
        "  \"recommended_supplier\": \"Exact best supplier name as provided in the input\",\n"
        "  \"reason\": \"Short explanation of why they are the best.\"\n"
        "}"
    )

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = client.chat_completion(messages=messages, max_tokens=1024, temperature=0.1)
        response_text = response.choices[0].message.content.strip()
        
        # Clean up markdown if the model wrapped output in ```json ... ```
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        return json.loads(response_text)
    except Exception as e:
        logger.error(f"Error calling HF InferenceClient for supplier analysis: {e}")
        return {"error": str(e)}
