import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Ponechané, funguje dobre) ---
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
                riadky = [r.strip() for r in bloky_dni[i+1].split('\n') if r.strip()]
                final_menu_e += f"\n\n🔹 *{den_nazov}*"
                if riadky:
                    final_menu_e += f"\n🍜 *Polievka:* {riadky[0]}"
                    for idx, jedlo in enumerate(riadky[1:], 1):
                        final_menu_e += f"\n{idx}. {jedlo}"
            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*{final_menu_e}"})
    except: pass

    # --- 2. SENTAMI (Nová ultra-robustná logika) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        
        # Extrahujeme úplne všetok text zo stránky (ignorujeme HTML štruktúru)
        raw_text = soup_s.get_text(separator="\n", strip=True)
        
        # Vyčistíme text od cien, ktoré sú rozdelené do viacerých riadkov (častý problém Sentami)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        vycistene_menu = []
        index_dna = 0
        posledny_text_bez_ceny = ""

        # Prechádzame riadok po riadku
        for r in lines:
            # Stop slová - ak narazíme na pätičku, končíme
            if any(x in r.upper() for x in ["DOMOV", "RESERVÁCIA", "KONTAKT", "GALÉRIA", "OBCHODNÉ PODMIENKY"]):
                break
            
            # Detekcia ceny (jedlo končí cenou s €)
            if "€" in r:
                match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                cena = match_cena.group() if match_cena else ""
                
                # Získame názov jedla
                nazov_raw = re.split(r'\(|\*|\d+[,.]\d+', r)[0].strip()
                # Ak je názov v riadku krátky, pripojíme text z predošlého riadku
                final_nazov = nazov_raw if len(nazov_raw) > 5 else posledny_text_bez_ceny
                
                # Ak riadok obsahuje slovo Polievka (alebo bol predošlý riadok o polievke)
                if "Polievka" in r or "Polievka" in posledny_text_bez_ceny:
                    if index_dna < 5:
                        vycistene_menu.append(f"\n🔹 *{dni_tyzdna[index_dna]}*")
                        index_dna += 1
                    
                    p_nazov = final_nazov.replace("Polievka", "").replace(":", "").strip()
                    vycistene_menu.append(f"🍜 *Polievka:* {p_nazov}")
                else:
                    # Rozlíšenie denného menu a špeciálov
                    is_special = bool(re.match(r'^(Týždenné|Špeciál|Šalát)', final_nazov, re.I))
                    if is_special:
                        vycistene_menu.append(f"\n🔹 {final_nazov} {cena}")
                    else:
                        vycistene_menu.append(f"{final_nazov} {cena}")
                
                posledny_text_bez_ceny = "" # Reset po spracovaní jedla
            else:
                # Ak riadok nemá cenu, uložíme si ho pre prípad, že je to názov jedla
                if len(r) > 3: posledny_text_bez_ceny = r

        # Finálne spojenie
        if vycistene_menu:
            final_output_s = "\n".join(vycistene_menu)
            final_output_s = re.sub(r'\n{3,}', '\n\n', final_output_s) # Upratanie medzier
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n\n{final_output_s.strip()}"})
    except Exception as e:
        print(f"Chyba: {e}")

if __name__ == "__main__":
    ziskaj_a_posli_menu()
