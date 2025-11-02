# translate_epg.py (v5 - Google Translate Edition)
import requests
import xml.etree.ElementTree as ET
import time
from googletrans import Translator, LANGUAGES

# --- Configuration ---
SOURCE_URL = "https://iptv-epg.org/files/epg-bg.xml"
OUTPUT_FILE = "epg-en.xml"

# --- Caching & Translator Initialization ---
translation_cache = {}
api_calls_made = 0
# Δημιουργούμε ένα αντικείμενο Translator
translator = Translator()

# --- Functions ---
def translate_text(text, target_lang='en', source_lang='bg'):
    """
    Μεταφράζει κείμενο χρησιμοποιώντας τη βιβλιοθήκη googletrans.
    Χρησιμοποιεί cache για να αποφύγει τις επαναλαμβανόμενες κλήσεις.
    """
    global api_calls_made
    if not text or not text.strip():
        return text

    if text in translation_cache:
        return translation_cache[text]

    # Δίνουμε 3 προσπάθειες σε περίπτωση προσωρινού σφάλματος δικτύου
    for attempt in range(3):
        try:
            # Κάνουμε την κλήση μετάφρασης
            translated_result = translator.translate(text, dest=target_lang, src=source_lang)
            translated_text = translated_result.text
            api_calls_made += 1
            
            print(f"API Call #{api_calls_made}: Translated '{text[:30]}...' to '{translated_text[:30]}...'")
            
            translation_cache[text] = translated_text
            # Προσθέτουμε μια σημαντική καθυστέρηση ΜΟΝΟ όταν κάνουμε πραγματική κλήση
            time.sleep(1) 
            return translated_text
        except Exception as e:
            print(f"Attempt {attempt + 1}/3 failed for text '{text[:30]}...'. Error: {e}")
            time.sleep(2) # Περιμένουμε λίγο περισσότερο πριν ξαναπροσπαθήσουμε

    # Αν όλες οι προσπάθειες αποτύχουν, επιστρέφουμε το αρχικό κείμενο
    print(f"Warning: All translation attempts failed for text: '{text[:30]}...'. Returning original text.")
    return text

# --- Main Logic ( παραμένει το ίδιο ) ---
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
    print(f"Found {total_programmes} programmes to process.")

    for i, prog in enumerate(programmes):
        # Δεν χρειαζόμαστε sleep εδώ, αφού το βάλαμε μέσα στη συνάρτηση μετάφρασης
        title_element = prog.find('title')
        desc_element = prog.find('desc')

        if title_element is not None and title_element.text:
            title_element.text = translate_text(title_element.text)

        if desc_element is not None and desc_element.text:
            desc_element.text = translate_text(desc_element.text)

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{total_programmes} programmes... (Google API calls made: {api_calls_made})")

    print("\n--- Translation Summary ---")
    print(f"Total programmes processed: {total_programmes}")
    print(f"Total unique phrases translated (API calls): {api_calls_made}")
    print(f"Cache size: {len(translation_cache)}")
    print("--------------------------\n")
    
    print(f"Saving translated EPG to {OUTPUT_FILE}...")
    tree = ET.ElementTree(root)
    tree.write(OUTPUT_FILE, encoding='UTF-8', xml_declaration=True)
    print("Translation complete!")

if __name__ == "__main__":
    main()
