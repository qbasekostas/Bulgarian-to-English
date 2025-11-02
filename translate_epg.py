# translate_epg.py (v3 - with Caching and Robust Error Handling)
import requests
import xml.etree.ElementTree as ET
import time
import json # Χρησιμοποιείται για να ελέγξουμε το JSON error

# --- Configuration ---
SOURCE_URL = "https://iptv-epg.org/files/epg-bg.xml"
OUTPUT_FILE = "epg-en.xml"
# Αλλάζουμε σε ένα άλλο δημόσιο instance για δοκιμή, μπορεί να είναι λιγότερο φορτωμένο
TRANSLATE_API_URL = "https://translate.argosopentech.com/translate"

# --- Caching Dictionary ---
# Η "μνήμη" του script. Θα αποθηκεύει τις μεταφράσεις που ήδη έχει κάνει.
translation_cache = {}
api_calls_made = 0

# --- Functions ---
def translate_text(text, target_lang='en', source_lang='bg'):
    """
    Στέλνει κείμενο στο API για μετάφραση, χρησιμοποιώντας πρώτα το cache.
    """
    global api_calls_made
    if not text or not text.strip():
        return text

    # 1. Έλεγχος αν η μετάφραση υπάρχει ήδη στο cache
    if text in translation_cache:
        return translation_cache[text]

    # Αν δεν υπάρχει, κάνουμε την κλήση στο API
    try:
        payload = {'q': text, 'source': source_lang, 'target': target_lang}
        
        # Κάνουμε την κλήση στο API
        response = requests.post(TRANSLATE_API_URL, json=payload, timeout=10)
        api_calls_made += 1

        # 2. Καλύτερος έλεγχος σφαλμάτων
        # Ελέγχουμε αν η απάντηση ήταν επιτυχής (status code 200)
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code} for text: '{text[:30]}...'. Response: {response.text}")
            return text # Επιστρέφουμε το αρχικό κείμενο

        # Προσπαθούμε να πάρουμε το JSON. Αν αποτύχει, το πιάνουμε.
        translated_text = response.json().get('translatedText', text)
        
        print(f"API Call #{api_calls_made}: Translated '{text[:30]}...' to '{translated_text[:30]}...'")

        # 3. Αποθηκεύουμε τη νέα μετάφραση στο cache
        translation_cache[text] = translated_text
        
        return translated_text

    except requests.exceptions.RequestException as e:
        print(f"Network error translating text: {text}. Error: {e}")
        return text
    except json.JSONDecodeError:
        # Αυτό είναι το σφάλμα που είχες! Τώρα το τυπώνουμε όμορφα.
        print(f"JSON Decode Error: The server did not return valid JSON. Response: {response.text}")
        return text

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
    print(f"Found {total_programmes} programmes to process.")

    for i, prog in enumerate(programmes):
        # 3. Αυξάνουμε λίγο την καθυστέρηση για ασφάλεια
        time.sleep(0.2) # Μικρότερη καθυστέρηση τώρα, αφού θα κάνουμε λιγότερες κλήσεις

        title_element = prog.find('title')
        desc_element = prog.find('desc')

        if title_element is not None and title_element.text:
            title_element.text = translate_text(title_element.text)

        if desc_element is not None and desc_element.text:
            desc_element.text = translate_text(desc_element.text)

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{total_programmes} programmes... (API calls made so far: {api_calls_made})")

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
