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

    # --- 2. SENTAMI (Oprava formátovania cien a odstraňovanie po * alebo () ---
    try:
        res_s = requests.get("https://sentami.sk/kategoria/denne-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content.decode('utf-8', 'ignore'), 'html.parser')
        
        # Získame text tak, aby sme zachovali štruktúru, ale odstránime nadbytočné medzery
        lines = [line.strip() for line in soup_s.get_text(separator="\n").splitlines() if line.strip()]
        full_text = "\n".join(lines)

        if "Pondelok" in full_text:
            start_s = full_text.find("Pondelok")
            if "Späť" in full_text:
                full_text = full_text.split("Späť")[0]
            menu_s = full_text[start_s:].strip()

            # OPRAVA ROZBITÝCH CIEN: spojí "8,1" + "0" + "€" do "8,10 €"
            menu_s = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', menu_s)
            menu_s = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', menu_s)

            vycistene_riadky = []
            for r in menu_s.split('\n'):
                r = r.strip()
                if not r or r in ["1.", "2.", "3.", "Špeciál:", "Šalát:"]: 
                    if r: vycistene_riadky.append(r)
                    continue
                
                # Ak riadok obsahuje cenu (napr. 8,10 €)
                if "€" in r:
                    match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                    cena = match_cena.group() if match_cena else ""
                    
                    # Odstránime všetko od znaku ( alebo *
                    r_clean = re.split(r'\(|\*', r)[0].strip()
                    
                    # Ak je to názov dňa, necháme tak, inak spojíme názov a cenu
                    if any(den in r for den in dni_tyzdna + ["Týždenná ponuka"]):
                        vycistene_riadky.append(f"🔹 *{r}*")
                    else:
                        vycistene_riadky.append(f"{r_clean} {cena}")
                else:
                    vycistene_riadky.append(r)

            final_menu_s = "\n".join(vycistene_riadky)
            # Vyčistíme duplicitné odrážky ak by vznikli
            final_menu_s = final_menu_s.replace("🔹 🔹", "🔹")
            
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{final_menu_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
