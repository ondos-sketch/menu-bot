import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO ---
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
            
            vycistene_riadky = []
            for riadok in menu_s.split('\n'):
                r = riadok.strip()
                if not r: continue
                
                # Ak riadok obsahuje cenu (napr. 8,90 €), vymaž všetko medzi textom a cenou
                if "€" in r:
                    # Nájde pozíciu ceny (napr. 10,50 €)
                    match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                    if match_cena:
                        cena = match_cena.group()
                        # Zoberie text pred prvou zátvorkou alebo pred prvým číslom gramáže
                        # Ak tam nie je zátvorka, proste usekne všetko pred cenou
                        text_jedla = re.split(r'\(|\d+\s*(g|l|ml|dcl)', r)[0].strip()
                        # Ak je riadok dňa (Pondelok atď), neupravuj ho tak agresívne
                        if any(den in r for den in dni_tyzdna + ["Týždenná ponuka"]):
                             vycistene_riadky.append(r)
                        else:
                             vycistene_riadky.append(f"{text_jedla} {cena}")
                    else:
                        vycistene_riadky.append(r)
                else:
                    vycistene_riadky.append(r)

            final_menu_s = "\n".join(vycistene_riadky)
            
            # Formátovanie dní modrými odrážkami
            for den in dni_tyzdna + ["Týždenná ponuka"]:
                final_menu_s = final_menu_s.replace(den, f"\n\n🔹 *{den}*")
            
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{final_menu_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
