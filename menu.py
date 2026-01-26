import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Pôvodná funkčná verzia) ---
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

    # --- 2. SENTAMI (Oprava číslovania MENU 1, MENU 2) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        raw_text = soup_s.get_text(separator="\n", strip=True)
        
        # Orezanie balastu pred polievkou
        if "Polievka" in raw_text:
            raw_text = raw_text[raw_text.find("Polievka"):]

        # Oprava rozbitých cien
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        vycistene_menu = []
        
        counter_jedla = 1
        
        for r in lines:
            if any(x in r.upper() for x in ["DOMOV", "RESERVÁCIA", "KONTAKT", "Hlboká cesta"]): break
            
            # Detekcia dňa - Reset počítadla menu
            if any(den == r for den in dni_tyzdna + ["Týždenná ponuka"]):
                vycistene_menu.append(f"\n🔹 *{r}*")
                counter_jedla = 1
                continue
            
            if "€" in r:
                match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                cena = match_cena.group() if match_cena else ""
                
                # Orezanie názvu (všetko za ( alebo *)
                nazov = re.split(r'\(|\*', r)[0].strip()
                nazov = re.sub(r'^(MENU|Menu)\s*\d+[:.]?\s*', '', nazov) # Odstráni staré MENU 1 ak tam bolo
                
                if "Polievka" in r:
                    nazov_p = nazov.replace("Polievka", "").strip(": ").strip()
                    vycistene_menu.append(f"🍜 *Polievka:* {nazov_p}")
                else:
                    # Pridanie MENU 1:, MENU 2: atď.
                    vycistene_menu.append(f"MENU {counter_jedla}: {nazov} {cena}")
                    counter_jedla += 1
            
            elif "Polievka" in r:
                nazov_p = r.replace("Polievka", "").strip(": ").strip()
                if nazov_p:
                    vycistene_menu.append(f"🍜 *Polievka:* {nazov_p}")
                # Po slove polievka v riadku (aj bez ceny) sa resetuje počítadlo jedál
                counter_jedla = 1

        result_s = "\n".join(vycistene_menu)
        result_s = re.sub(r'(\d+[,.]\d+\s*€)\s+\1', r'\1', result_s)

        requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{result_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
