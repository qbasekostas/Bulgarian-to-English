# translate_epg.py (v2 - with LibreTranslate)
import requests
import xml.etree.ElementTree as ET
import time # Θα το χρειαστούμε για να είμαστε "ευγενικοί" προς το API

# --- Configuration ---
SOURCE_URL = "https://iptv-epg.org/files/epg-bg.xml"
OUTPUT_FILE = "epg-en.xml"
# Χρησιμοποιούμε ένα δημόσιο instance του LibreTranslate. Δεν χρειάζεται κλειδί!
TRANSLATE_API_URL = "https://libretranslate.de/translate"

# --- Functions ---
def translate_text(text, target_lang='en', source_lang='bg'):
    """Στέλνει κείμενο στο LibreTranslate API για μετάφραση."""
    if not text or not text.strip():
        return text  # Επιστρέφει το αρχικό αν είναι κενό

    try:
        # Το payload είναι διαφορετικό για το LibreTranslate
        payload = {
            'q': text,
            'source': source_lang,
            'target': target_lang,
            'format': 'text'
        }
        # Το LibreTranslate περιμένει JSON payload
        response = requests.post(TRANSLATE_API_URL, json=payload)
        response.raise_for_status() # Check for HTTP errors
        
        # Η δομή της απάντησης είναι επίσης διαφορετική
        translated_text = response.json().get('translatedText', text)
        print(f"Translated '{text[:30]}...' to '{translated_text[:30]}...'")
        return translated_text
    except Exception as e:
        print(f"Error translating text: {text}. Error: {e}")
        return text # Σε περίπτωση σφάλματος, επιστρέφει το αρχικό κείμενο

# --- Main Logic ---
def main():
    print(f"Downloading EPG from {SOURCE_URL}...")
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        xml_content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Failed to download EPG file: {e}")
        return

    print("Parsing XML content...")
    parser = ET.XMLParser(encoding="utf-8")
    root = ET.fromstring(xml_content, parser=parser)

    programmes = root.findall('programme')
    total_programmes = len(programmes)
    print(f"Found {total_programmes} programmes to translate.")

    for i, prog in enumerate(programmes):
        # Βάζουμε μια μικρή καθυστέρηση για να μην "βομβαρδίζουμε" τον δωρεάν server
        time.sleep(0.5) 
        
        title_element = prog.find('title')
        desc_element = prog.find('desc')

        # Μετάφραση τίτλου
        if title_element is not None and title_element.text:
            title_element.text = translate_text(title_element.text)

        # Μετάφραση περιγραφής
        if desc_element is not None and desc_element.text:
            desc_element.text = translate_text(desc_element.text)

        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{total_programmes} programmes...")

    print(f"Saving translated EPG to {OUTPUT_FILE}...")
    tree = ET.ElementTree(root)
    tree.write(OUTPUT_FILE, encoding='UTF-8', xml_declaration=True)
    print("Translation complete!")

if __name__ == "__main__":
    main()
