import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Pôvodná overená verzia) ---
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
                        formát_e += f"\n{idx}. {jedlo}"
                final_menu_e += formát_e
            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*{final_menu_e}"})
    except: pass

    # --- 2. SENTAMI (Inteligentná detekcia: Pon-Štv = 3 jedlá, Pia = 4 jedlá + fix na MENU 1.) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        content = soup_s.find('div', class_='entry-content')
        raw_text = content.get_text(separator="\n", strip=True) if content else soup_s.get_text(separator="\n", strip=True)
        
        if "Polievka" in raw_text:
            raw_text = raw_text[raw_text.find("Polievka"):]

        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        vycistene_menu = []
        
        index_dna = 0
        hlavne_jedla_v_dni = 0
        posledny_text_bez_ceny = ""
        novy_den_pripraveny = True

        for r in lines:
            if any(x in r.upper() for x in ["DOMOV", "RESERVÁCIA", "KONTAKT", "GALÉRIA"]): break
            
            if "€" in r:
                match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                cena = match_cena.group() if match_cena else ""
                
                nazov_v_riadku = re.split(r'\(|\*|\d+[,.]\d+', r)[0].strip()
                finalny_nazov = nazov_v_riadku if len(nazov_v_riadku) > 5 else posledny_text_bez_ceny
                
                # Zisťujeme, či ide o doplnkovú polievku za 2 eurá, ktorú nechceme počítať ako hlavný chod
                je_doplnkova_polievka = "2.00" in cena or "2,00" in cena
                
                # POISTKA 1: Ak v texte vyslovene svieti "MENU 1." a už sme v daný deň niečo zapísali,
                # znamená to, že reštaurácia prešla na nový deň (otočené piatkové poradie)
                if "MENU 1." in finalny_nazov.upper() and hlavne_jedla_v_dni > 0:
                    novy_den_pripraveny = True

                # Vloženie nadpisu dňa na začiatok bloku
                if novy_den_pripraveny and not je_doplnkova_polievka:
                    if index_dna < len(dni_tyzdna):
                        vycistene_menu.append(f"\n🔹 *{dni_tyzdna[index_dna]}*")
                        index_dna += 1
                    novy_den_pripraveny = False
                    hlavne_jedla_v_dni = 0

                if "Polievka" in r or "Polievka" in posledny_text_bez_ceny:
                    cista_p = finalny_nazov.replace('Polievka', '').strip(': ').strip()
                    vycistene_menu.append(f"🍜 *Polievka:* {cista_p}")
                else:
                    is_special_item = any(x in finalny_nazov.upper() for x in ["TÝŽDENNÉ", "ŠPECIÁL", "ŠALÁT"])
                    
                    if is_special_item:
                        vycistene_menu.append(f"\n🔹 {finalny_nazov} {cena}")
                    else:
                        if finalny_nazov:
                            vycistene_menu.append(f"{finalny_nazov} {cena}".strip())
                            if not je_doplnkova_polievka:
                                hlavne_jedla_v_dni += 1
                
                # POISTKA 2: Dynamický limit jedál podľa aktuálneho dňa. 
                # Ak spracovávame Pondelok až Štvrtok (index_dna 1 až 4), limit sú 3 jedlá.
                # Ak sme v Piatok (index_dna == 5), limit sú 4 jedlá.
                limit_jediel = 4 if index_dna == 5 else 3
                
                if hlavne_jedla_v_dni >= limit_jediel:
                    novy_den_pripraveny = True
                
                posledny_text_bez_ceny = ""
            else:
                posledny_text_bez_ceny = re.split(r'\(|\*', r)[0].strip()

        result_s = "\n".join(vycistene_menu)
        result_s = re.sub(r'(\d+[,.]\d+\s*€)\s+\1', r'\1', result_s)
        
        requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{result_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
