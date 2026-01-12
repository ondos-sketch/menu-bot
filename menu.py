import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Bez zmeny, funguje správne) ---
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

    # --- 2. SENTAMI (Opravené ceny a vrátené oddelovače dní) ---
    try:
        res_s = requests.get("https://sentami.sk/kategoria/denne-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content.decode('utf-8', 'ignore'), 'html.parser')
        
        # Získame riadky a najskôr opravíme rozbité ceny v celom texte
        raw_text = soup_s.get_text(separator="\n", strip=True)
        # Oprava cien rozdelených do riadkov: "8,1" + "0" + "€" -> "8,10 €"
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        if "Pondelok" in raw_text:
            start_s = raw_text.find("Pondelok")
            if "Späť" in raw_text:
                raw_text = raw_text.split("Späť")[0]
            menu_s = raw_text[start_s:].strip()

            vycistene_riadky = []
            for r in menu_s.split('\n'):
                r = r.strip()
                if not r: continue
                
                # Identifikácia dňa - pridáme oddelovač 🔹
                if any(den == r for den in dni_tyzdna + ["Týždenná ponuka:"]):
                    vycistene_riadky.append(f"\n🔹 *{r}*")
                    continue

                # Čistenie riadku s jedlom a cenou
                if "€" in r:
                    match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                    cena = match_cena.group() if match_cena else ""
                    
                    # Odstránenie všetkého od znaku ( alebo * (podľa vašej požiadavky)
                    názov_jedla = re.split(r'\(|\*', r)[0].strip()
                    
                    # Ak po odrezaní niečo ostalo, spojíme to s jednou cenou
                    if názov_jedla and názov_jedla not in ["1.", "2.", "Špeciál:", "Šalát:"]:
                        vycistene_riadky.append(f"{názov_jedla} {cena}")
                    else:
                        vycistene_riadky.append(r)
                else:
                    vycistene_riadky.append(r)

            final_menu_s = "\n".join(vycistene_riadky)
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{final_menu_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
