import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Stabilné) ---
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

    # --- 2. SENTAMI (Oprava detekcie Piatka) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        content = soup_s.find('div', class_='entry-content')
        raw_text = content.get_text(separator="\n", strip=True) if content else soup_s.get_text(separator="\n", strip=True)
        
        # Oprava rozbitých cien
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(\d+)\n+(€)', r'\1\2 \3', raw_text)
        raw_text = re.sub(r'(\d+[,.]\d+)\n+(€)', r'\1 \2', raw_text)

        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        vycistene_menu = []
        spracovane_dni = set()
        posledny_text_bez_ceny = ""

        for r in lines:
            if any(x in r.upper() for x in ["DOMOV", "RESERVÁCIA", "KONTAKT", "GALÉRIA"]): break
            
            # IDENTIFIKÁCIA DŇA: Presne tak ako u Štvrtka
            aktualny_den = None
            for d in dni_tyzdna:
                if d.upper() in r.upper() and d not in spracovane_dni:
                    aktualny_den = d
                    break
            
            if aktualny_den:
                vycistene_menu.append(f"\n🔹 *{aktualny_den}*")
                spracovane_dni.add(aktualny_den)
                continue

            if "€" in r:
                match_cena = re.search(r'\d+[,.]\d+\s*€', r)
                cena = match_cena.group() if match_cena else ""
                nazov_v_riadku = re.split(r'\(|\*|\d+[,.]\d+', r)[0].strip()
                finalny_nazov = nazov_v_riadku if len(nazov_v_riadku) > 3 else posledny_text_bez_ceny
                
                if "Polievka" in r or "Polievka" in posledny_text_bez_ceny:
                    # Ak na webe chýbal nadpis dňa, ale našli sme polievku, vložíme ďalší deň v poradí
                    if not spracovane_dni or (len(spracovane_dni) < 5 and "Polievka" in r):
                        for d in dni_tyzdna:
                            if d not in spracovane_dni:
                                vycistene_menu.append(f"\n🔹 *{d}*")
                                spracovane_dni.add(d)
                                break
                    
                    cista_p = finalny_nazov.replace('Polievka', '').strip(': ').strip()
                    vycistene_menu.append(f"🍜 *Polievka:* {cista_p}")
                else:
                    is_special = any(x in finalny_nazov.upper() for x in ["TÝŽDENNÉ", "ŠPECIÁL", "ŠALÁT"])
                    prefix = "\n🔹 " if is_special else ""
                    vycistene_menu.append(f"{prefix}{finalny_nazov} {cena}".strip())
                posledny_text_bez_ceny = ""
            else:
                posledny_text_bez_ceny = re.split(r'\(|\*', r)[0].strip()

        result_s = "\n".join(vycistene_menu).replace('\n\n\n', '\n\n')
        requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{result_s}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
