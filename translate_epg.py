# translate_epg.py (v4 - Resilient Edition with Multiple Endpoints)
import requests
import xml.etree.ElementTree as ET
import time
import json

# --- Configuration ---
SOURCE_URL = "https://iptv-epg.org/files/epg-bg.xml"
OUTPUT_FILE = "epg-en.xml"

# --- List of Public LibreTranslate Servers ---
# Το script θα τα δοκιμάσει με τη σειρά μέχρι να βρει έναν που λειτουργεί.
API_ENDPOINTS = [
    "https://libretranslate.de/translate",
    "https://translate.astian.org/translate",
    "https://translation.pirate-party.ch/translate",
    "https://trans.zillyhuhn.com/translate",
]

# --- Caching Dictionary ---
translation_cache = {}
api_calls_made = 0

# --- Functions ---
def translate_text(text, target_lang='en', source_lang='bg'):
    """
    Προσπαθεί να μεταφράσει κείμενο δοκιμάζοντας μια λίστα από API endpoints.
    Χρησιμοποιεί cache για να αποφύγει διπλές κλήσεις.
    """
    global api_calls_made
    if not text or not text.strip():
        return text

    if text in translation_cache:
        return translation_cache[text]

    payload = {'q': text, 'source': source_lang, 'target': target_lang}

    # Κάνουμε loop σε κάθε διαθέσιμο server
    for endpoint in API_ENDPOINTS:
        try:
            # Κάνουμε την κλήση στο API
            response = requests.post(endpoint, json=payload, timeout=15)
            api_calls_made += 1

            # Αν ο server απαντήσει με σφάλμα (π.χ. rate limit), δοκιμάζουμε τον επόμενο
            if response.status_code != 200:
                print(f"Endpoint {endpoint} returned status {response.status_code}. Trying next...")
                continue # Πάμε στον επόμενο server της λίστας

            translated_text = response.json().get('translatedText', text)
            
            print(f"Success on {endpoint.split('/')[2]}! API Call #{api_calls_made}: Translated '{text[:30]}...'")
            
            translation_cache[text] = translated_text
            return translated_text

        except requests.exceptions.RequestException as e:
            # Αν υπάρχει σφάλμα δικτύου (DNS, timeout κλπ), δοκιμάζουμε τον επόμενο
            print(f"Endpoint {endpoint} failed: {e}. Trying next...")
            continue # Πάμε στον επόμενο server της λίστας
        except json.JSONDecodeError:
            print(f"Endpoint {endpoint} did not return valid JSON. Trying next...")
            continue

    # Αν κανένας server από τη λίστα δεν λειτούργησε, επιστρέφουμε το αρχικό κείμενο
    print(f"Warning: All API endpoints failed for text: '{text[:30]}...'. Returning original text.")
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
        time.sleep(0.3) # Αφήνουμε μια μικρή καθυστέρηση για να είμαστε ευγενικοί

        title_element = prog.find('title')
        desc_element = prog.find('desc')

        if title_element is not None and title_element.text:
            title_element.text = translate_text(title_element.text)

        if desc_element is not None and desc_element.text:
            desc_element.text = translate_text(desc_element.text)

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{total_programmes} programmes... (API calls made: {api_calls_made})")

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
