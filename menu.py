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
                formát_e = f"\n\n🔹 *{den_nazov}*"
                if riadky:
                    formát_e += f"\n🍜 *Polievka:* {riadky[0]}"
                    for idx, jedlo in enumerate(riadky[1:], 1):
                        final_menu_e += f"\n{idx}. {jedlo}"
                final_menu_e += formát_e
            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*{final_menu_e}"})
    except: pass

    # --- 2. SENTAMI (Inteligentné rozdelenie dní podľa textu na webe) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        content = soup_s.find('div', class_='entry-content')
        raw_text = content.get_text(separator="\n", strip=True) if content else soup_s.get_text(separator="\n", strip=True)
        
        # Oprava spojených cien na konci riadkov
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        vycistene_menu = []
        
        # Extrahujeme čisté bloky textu pre jednotlivé dni priamo podľa slov Pondelok-Piatok na webe
        # Rozdelíme text podľa reálnych nadpisov dní
        dni_regex = r'(Pondelok|Utorok|Streda|Štvrtok|Piatok)'
        bloky_sentami = re.split(dni_regex, raw_text, flags=re.IGNORECASE)
        
        # Ak sa podarilo text úspešne rozrezať podľa dní
        if len(bloky_sentami) > 1:
            for i in range(1, len(bloky_sentami), 2):
                den_nazov = bloky_sentami[i].capitalize()
                den_text = bloky_sentami[i+1]
                
                # Zastavíme sa, ak v texte dňa preblikne pätička webu
                if any(x in den_text.upper() for x in ["DOMOV", "RESERVÁCIA", "KONTAKT", "GALÉRIA", "TÝŽDENNÉ MENU"]):
                    # Ostrihneme len po stop-slovo
                    for stop_word in ["DOMOV", "RESERVÁCIA", "KONTAKT", "GALÉRIA", "TÝŽDENNÉ MENU"]:
                        if stop_word in den_text.upper():
                            den_text = den_text[:den_text.upper().find(stop_word)]
                
                vycistene_menu.append(f"\n🔹 *{den_nazov}*")
                
                # Spracujeme jedlá prislúchajúce LEN tomuto dňu
                riadky_dna = [r.strip() for r in den_text.split('\n') if r.strip()]
                posledna_polievka = ""
                
                for r in riadky_dna:
                    if "€" in r:
                        match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                        cena = match_cena.group() if match_cena else ""
                        nazov_jedla = re.split(r'\(|\*|\d+[,.]\d+', r)[0].strip()
                        
                        if not nazov_jedla and posledna_polievka:
                            nazov_jedla = posledna_polievka
                        
                        if "Polievka" in r or "Polievka" in posledna_polievka or "Vývar" in r:
                            # Ak je to doplnková polievka za 2€, zapíšeme ju ako bežné jedlo, nie ako hlavnú dennú polievku
                            if "2.00" in cena or "2,00" in cena:
                                vycistene_menu.append(f"{nazov_jedla} {cena}")
                            else:
                                cista_p = nazov_jedla.replace('Polievka', '').replace(':', '').strip()
                                vycistene_menu.append(f"🍜 *Polievka:* {cista_p}")
                        else:
                            if nazov_jedla:
                                vycistene_menu.append(f"{nazov_jedla} {cena}")
                        posledna_polievka = ""
                    else:
                        if len(r) > 3 and not any(x in r.upper() for x in dni_tyzdna):
                            posledna_polievka = r
        
        # Ak by regex zlyhal, použijeme starú metódu ako fall-back (ale upravenú o ignorovanie 2€ polievok)
        else:
            index_dna = 0
            posledny_text_bez_ceny = ""
            for r in lines:
                if any(x in r.upper() for x in ["DOMOV", "RESERVÁCIA", "KONTAKT"]): break
                if "€" in r:
                    match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                    cena = match_cena.group() if match_cena else ""
                    nazov_v_riadku = re.split(r'\(|\*|\d+[,.]\d+', r)[0].strip()
                    finálny_názov = nazov_v_riadku if len(nazov_v_riadku) > 5 else posledny_text_bez_ceny
                    
                    if ("Polievka" in r or "Polievka" in posledny_text_bez_ceny) and not ("2.00" in cena or "2,00" in cena):
                        if index_dna < len(dni_tyzdna):
                            vycistene_menu.append(f"\n🔹 *{dni_tyzdna[index_dna]}*")
                            index_dna += 1
                        čistá_p = finálny_názov.replace('Polievka', '').strip(': ').strip()
                        vycistene_menu.append(f"🍜 *Polievka:* {čistá_p}")
                    else:
                        is_special_item = any(x in finálny_názov.upper() for x in ["TÝŽDENNÉ", "ŠPECIÁL", "ŠALÁT"])
                        prefix = "\n🔹 " if is_special_item else ""
                        if finálny_názov:
                            vycistene_menu.append(f"{prefix}{finálny_názov} {cena}".strip())
                    posledny_text_bez_ceny = ""
                else:
                    posledny_text_bez_ceny = re.split(r'\(|\*', r)[0].strip()

        result_s = "\n".join(vycistene_menu)
        result_s = re.sub(r'(\d+[,.]\d+\s*€)\s+\1', r'\1', result_s)
        
        requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{result_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
