import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Bez zmeny) ---
    try:
        res_e = requests.get("https://www.eltoro.sk/index.php", headers=headers, timeout=15)
        soup_e = BeautifulSoup(res_e.content.decode('utf-8', 'ignore'), 'html.parser')
        text_e = soup_e.get_text(separator="\n", strip=True)
        start = re.search(r"Pondelok", text_e)
        end = re.search(r"Ponuka jedál\s*–\s*Nepretržité menu", text_e)
        if start and end:
            raw_menu = text_e[start.start():end.start()].strip()
            raw_menu = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', raw_menu)
            raw_menu = re.sub(r'\|\s*', '', raw_menu)
            raw_menu = re.sub(r'\s\d+(,\s*\d+)*', '', raw_menu)
            final_menu_e = ""
            bloky_dni = re.split(r'(Pondelok|Utorok|Streda|Štvrtok|Piatok)', raw_menu)
            for i in range(1, len(bloky_dni), 2):
                den_nazov = bloky_dni[i]
                den_text = bloky_dni[i+1].strip()
                riadky = [r.strip() for r in den_text.split('\n') if r.strip()]
                formátovaný_deň = f"\n\n🔹 *{den_nazov}*"
                if riadky:
                    formátovaný_deň += f"\n🍜 *Polievka:* {riadky[0]}"
                    for idx, jedlo in enumerate(riadky[1:], 1):
                        formátovaný_deň += f"\n{idx}. {jedlo}"
                final_menu_e += formátovaný_deň
            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*{final_menu_e}"})
    except: pass

    # --- 2. SENTAMI (Zjednotený formát s El Toro) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content.decode('utf-8', 'ignore'), 'html.parser')
        raw_text = soup_s.get_text(separator="\n", strip=True)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        if "Pondelok" in raw_text:
            start_s = raw_text.find("Pondelok")
            if "Späť" in raw_text:
                raw_text = raw_text.split("Späť")[0]
            menu_s = raw_text[start_s:].strip()

            vycistene_riadky = []
            prefix = "" 
            prvy_riadok_po_dni = False
            
            for r in menu_s.split('\n'):
                r = r.strip()
                if not r: continue
                
                # Názov dňa
                if any(den == r for den in dni_tyzdna + ["Týždenná ponuka:"]):
                    vycistene_riadky.append(f"\n🔹 *{r}*")
                    prefix = "" 
                    prvy_riadok_po_dni = True # Budúci riadok bude polievka
                    continue

                # Kategória/Číslo
                if re.match(r'^(\d+\.|Špeciál:|Šalát:)$', r):
                    prefix = r
                    prvy_riadok_po_dni = False
                    continue

                # Spracovanie jedla/polievky
                if "€" in r:
                    match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                    cena = match_cena.group() if match_cena else ""
                    nazov = re.split(r'\(|\*', r)[0].strip()
                    vycistene_riadky.append(f"{prefix} {nazov} {cena}".strip())
                    prefix = ""
                    prvy_riadok_po_dni = False
                else:
                    # Ak je to prvý text po dni a nemá cenu, je to polievka
                    if prvy_riadok_po_dni:
                        nazov_polievky = re.split(r'\(|\*', r)[0].strip()
                        vycistene_riadky.append(f"🍜 *Polievka:* {nazov_polievky}")
                        prvy_riadok_po_dni = False
                    elif prefix:
                        r = re.split(r'\(|\*', r)[0].strip()
                        prefix = f"{prefix} {r}"
                    else:
                        vycistene_riadky.append(r)

            final_menu_s = "\n".join(vycistene_riadky)
            final_menu_s = re.sub(r'(\d+[,.]\d+\s*€)\s+\1', r'\1', final_menu_s)
            
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{final_menu_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
