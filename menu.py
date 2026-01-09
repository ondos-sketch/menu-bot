import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    # AKTUALIZOVANÝ WEBHOOK
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAEcGOcC4/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=dAQZOZvcdeC7pYOTXTbCMUDVhJfrqSO8gmy1cbocUxQ"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (S polievkou a číslovaním) ---
    try:
        res_e = requests.get("https://www.eltoro.sk/index.php", headers=headers, timeout=15)
        soup_e = BeautifulSoup(res_e.content.decode('utf-8', 'ignore'), 'html.parser')
        text_e = soup_e.get_text(separator="\n", strip=True)
        
        start = re.search(r"Pondelok", text_e)
        end = re.search(r"Ponuka jedál\s*–\s*Nepretržité menu", text_e)
        
        if start and end:
            raw_menu = text_e[start.start():end.start()].strip()
            # Základné čistenie
            raw_menu = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', raw_menu)
            raw_menu = re.sub(r'\|\s*', '', raw_menu)
            raw_menu = re.sub(r'\s\d+(,\s*\d+)*', '', raw_menu)
            
            final_menu_e = ""
            # Rozdelenie na dni
            bloky_dni = re.split(r'(Pondelok|Utorok|Streda|Štvrtok|Piatok)', raw_menu)
            
            for i in range(1, len(bloky_dni), 2):
                den_nazov = bloky_dni[i]
                den_text = bloky_dni[i+1].strip()
                riadky = [r.strip() for r in den_text.split('\n') if r.strip()]
                
                formátovaný_deň = f"\n\n🔹 *{den_nazov}*"
                if riadky:
                    # Označenie polievky (predpokladáme, že je v prvom riadku)
                    formátovaný_deň += f"\n🍜 *Polievka:* {riadky[0]}"
                    # Číslovanie ostatných jedál od 1
                    for idx, jedlo in enumerate(riadky[1:], 1):
                        formátovaný_deň += f"\n{idx}. {jedlo}"
                final_menu_e += formátovaný_deň

            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*{final_menu_e}"})
    except Exception as e:
        print(f"Chyba El Toro: {e}")

    # --- 2. SENTAMI ---
    try:
        res_s = requests.get("https://sentami.sk/kategoria/denne-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content.decode('utf-8', 'ignore'), 'html.parser')
        text_s = soup_s.get_text(separator="\n", strip=True)
        
        if "Pondelok" in text_s:
            start_s = text_s.find("Pondelok")
            if "Späť" in text_s:
                text_s = text_s.split("Späť")[0]
            
            menu_s = text_s[start_s:].strip()
            for den in dni_tyzdna + ["Týždenná ponuka"]:
                menu_s = menu_s.replace(den, f"\n\n🔹 *{den}*")
            
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{menu_s.strip()}"})
    except Exception as e:
        print(f"Chyba Sentami: {e}")

if __name__ == "__main__":
    ziskaj_a_posli_menu()
