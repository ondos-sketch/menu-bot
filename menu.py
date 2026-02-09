import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- 1. EL TORO (Overená verzia) ---
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
                final_menu_e += f"\n\n🔹 *{den_nazov}*"
                if riadky:
                    final_menu_e += f"\n🍜 *Polievka:* {riadky[0]}"
                    for idx, jedlo in enumerate(riadky[1:], 1):
                        final_menu_e += f"\n{idx}. {jedlo}"
            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*{final_menu_e}"})
    except: pass

    # --- 2. SENTAMI (Maximálna odolnosť) ---
    try:
        res_s = requests.get("https://sentami.sk/obedove-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content, 'html.parser')
        
        # Sťahujeme čistý text bez ohľadu na HTML tagy
        lines = [l.strip() for l in soup_s.get_text(separator="\n", strip=True).split('\n') if l.strip()]
        
        vycistene_menu = []
        index_dna = 0
        pripraveny_nazov = ""

        for r in lines:
            # Ak sme v pätičke, končíme
            if any(x in r.upper() for x in ["KONTAKT", "RESERVÁCIA", "HLBOKÁ CESTA"]): break
            
            # Detekcia ceny (ak riadok obsahuje sumu a znak €)
            match_cena = re.search(r'\d+[,.]\d+\s*€', r)
            
            if match_cena:
                cena = match_cena.group()
                nazov = r.split(cena)[0].strip().replace('*', '')
                # Ak je názov v riadku prázdny, použijeme predošlý riadok
                final_nazov = nazov if len(nazov) > 4 else pripraveny_nazov
                
                if "Polievka" in final_nazov or "Polievka" in r:
                    if index_dna < 5:
                        vycistene_menu.append(f"\n🔹 *{dni_tyzdna[index_dna]}*")
                        index_dna += 1
                    cista_p = final_nazov.replace("Polievka", "").strip(": ").strip()
                    vycistene_menu.append(f"🍜 *Polievka:* {cista_p}")
                else:
                    is_special = any(x in final_nazov.upper() for x in ["TÝŽDENNÉ", "ŠPECIÁL", "ŠALÁT"])
                    prefix = "\n🔹 " if is_special else ""
                    vycistene_menu.append(f"{prefix}{final_nazov} {cena}")
                pripraveny_nazov = ""
            else:
                # Ukladáme riadky bez ceny ako potenciálne názvy jedál
                if len(r) > 3: pripraveny_nazov = r

        if vycistene_menu:
            result_s = "\n".join(vycistene_menu).replace('\n\n\n', '\n\n')
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{result_s}"})
    except Exception as e:
        print(f"DEBUG: Chyba pri Sentami: {e}")

if __name__ == "__main__":
    ziskaj_a_posli_menu()
