import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Ponechané bez zmeny) ---
    try:
        res_e = requests.get("https://www.eltoro.sk/index.php", headers=headers, timeout=15)
        soup_e = BeautifulSoup(res_e.content.decode('utf-8', 'ignore'), 'html.parser')
        text_e = soup_e.get_text(separator="\n", strip=True)
        start = re.search(r"Pondelok", text_e)
        end = re.search(r"Ponuka jedál\s*–\s*Nepretržité menu", text_e)
        if start and end:
            raw_menu = text_e[start.start():end.start()].strip()
            final_menu_e = ""
            bloky_dni = re.split(r'(Pondelok|Utorok|Streda|Štvrtok|Piatok)', raw_menu)
            for i in range(1, len(bloky_dni), 2):
                den_nazov = bloky_dni[i]
                riadky = [r.strip() for r in bloky_dni[i+1].split('\n') if r.strip()]
                formát = f"\n\n🔹 *{den_nazov}*\n🍜 *Polievka:* {riadky[0]}"
                for idx, j in enumerate(riadky[1:], 1): formát += f"\n{idx}. {j}"
                final_menu_e += formát
            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*{final_menu_e}"})
    except: pass

    # --- 2. SENTAMI (Opravené pre novú štruktúru) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        
        # Zameriame sa len na hlavný obsah, ignorujeme menu a navigáciu
        content = soup_s.find('div', class_='entry-content')
        if not content: content = soup_s # Backup ak by nenašiel div
            
        raw_text = content.get_text(separator="\n", strip=True)
        
        # Oprava rozbitých cien (spojenie 8,1 + 0 + €)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        vycistene_menu = []
        
        je_polievka_nasledovny = False
        
        for r in lines:
            # Preskočenie navigačného balastu, ak ostal
            if any(x in r.upper() for x in ["DOMOV", "GALÉRIA", "RESERVÁCIA", "KONTAKT", "Hlboká cesta"]): continue
            
            # Detekcia dňa
            if any(den == r for den in dni_tyzdna + ["Týždenná ponuka"]):
                vycistene_menu.append(f"\n🔹 *{r}*")
                je_polievka_nasledovny = True
                continue
            
            # Spracovanie riadku s jedlom/cenou
            if "€" in r:
                # Extrakcia ceny
                match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                cena = match_cena.group() if match_cena else ""
                
                # Orezanie názvu pred zátvorkou alebo hviezdičkou
                názov = re.split(r'\(|\*', r)[0].strip()
                # Odstránenie "MENU 1.:" a podobne
                názov = re.sub(r'^MENU\s+\d+\.:\s*', '', názov, flags=re.IGNORECASE)
                
                if je_polievka_nasledovny:
                    vycistene_menu.append(f"🍜 *Polievka:* {názov}")
                    je_polievka_nasledovny = False
                else:
                    # Ak riadok začína číslom, ponecháme ho, inak pridáme poradie
                    vycistene_menu.append(f"{názov} {cena}")
            elif je_polievka_nasledovny and len(r) > 3:
                # Ak riadok nemá cenu ale je pod dňom, je to polievka
                názov = re.split(r'\(|\*', r)[0].strip()
                vycistene_menu.append(f"🍜 *Polievka:* {názov}")
                je_polievka_nasledovny = False

        result_s = "\n".join(vycistene_menu)
        # Finálne prečistenie od dvojitých cien
        result_s = re.sub(r'(\d+[,.]\d+\s*€)\s+\1', r'\1', result_s)

        requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{result_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
