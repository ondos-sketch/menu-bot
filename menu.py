import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Pôvodná verzia - NEMEŇ) ---
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

    # --- 2. SENTAMI (Nová logika: Odstránenie textu nad "Polievka") ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        
        # Získame čistý text
        raw_text = soup_s.get_text(separator="\n", strip=True)
        
        # OPRAVA: Odstránenie všetkého pred prvým výskytom slova "Polievka"
        if "Polievka" in raw_text:
            raw_text = raw_text[raw_text.find("Polievka"):]

        # Oprava rozbitých cien
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        vycistene_menu = []
        
        # Premenné pre formátovanie
        aktualny_den = ""
        
        for r in lines:
            # Preskočenie zjavného balastu pod menu
            if any(x in r.upper() for x in ["DOMOV", "RESERVÁCIA", "KONTAKT", "Hlboká cesta"]): break
            
            # Detekcia dňa (ak riadok je názov dňa)
            if any(den == r for den in dni_tyzdna + ["Týždenná ponuka"]):
                vycistene_menu.append(f"\n🔹 *{r}*")
                continue
            
            # Spracovanie riadku s jedlom/cenou
            if "€" in r:
                match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                cena = match_cena.group() if match_cena else ""
                
                # Orezanie názvu pred zátvorkou alebo hviezdičkou
                nazov = re.split(r'\(|\*', r)[0].strip()
                # Vyčistenie prefixov typu "MENU 1.:"
                nazov = re.sub(r'^MENU\s+\d+\.:\s*', '', nazov, flags=re.IGNORECASE)
                
                # Ak riadok obsahuje slovo Polievka, sformátujeme ho špeciálne
                if "Polievka" in r:
                    nazov_p = nazov.replace("Polievka", "").strip(": ").strip()
                    vycistene_menu.append(f"🍜 *Polievka:* {nazov_p}")
                else:
                    vycistene_menu.append(f"{nazov} {cena}")
            
            # Ak riadok nemá cenu, ale je to "Polievka" (napr. nadpis)
            elif "Polievka" in r:
                nazov_p = r.replace("Polievka", "").strip(": ").strip()
                if nazov_p:
                    vycistene_menu.append(f"🍜 *Polievka:* {nazov_p}")
                else:
                    # Ak je slovo "Polievka" v riadku samo, skúsime vziať ďalší riadok v ďalšom cykle
                    pass

        result_s = "\n".join(vycistene_menu)
        # Odstránenie duplicitných cien
        result_s = re.sub(r'(\d+[,.]\d+\s*€)\s+\1', r'\1', result_s)

        requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{result_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
