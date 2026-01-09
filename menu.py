import requests
from bs4 import BeautifulSoup
import re

def ziskaj_a_posli_menu():
    webhook_url = "https://chat.googleapis.com/v1/spaces/AAQAF14T8YI/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=Boziy19yv5w-4lpdFD2Mz0u6HSByFWMCznQTl6QxZTU"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    dni_tyzdna = ["Pondelok", "Utorok", "Streda", "Štvrtok", "Piatok"]

    # --- EL TORO ---
    try:
        res_e = requests.get("https://www.eltoro.sk/index.php", headers=headers, timeout=15)
        soup_e = BeautifulSoup(res_e.content.decode('utf-8', 'ignore'), 'html.parser')
        text_e = soup_e.get_text(separator="\n", strip=True)
        start = re.search(r"Pondelok", text_e)
        end = re.search(r"Ponuka jedál\s*–\s*Nepretržité menu", text_e)
        if start and end:
            menu_e = text_e[start.start():end.start()].strip()
            menu_e = re.sub(r'\d{2}\.\d{2}\.\d{4}', '', menu_e)
            menu_e = re.sub(r'\|\s*', '', menu_e)
            menu_e = re.sub(r'\s\d+(,\s*\d+)*', '', menu_e)
            for den in dni_tyzdna:
                menu_e = menu_e.replace(den, f"\n\n🔹 *{den}*")
            requests.post(webhook_url, json={"text": f"🥩 *EL TORO – TÝŽDENNÉ MENU*\n{menu_e.strip()}"})
    except: pass

    # --- SENTAMI ---
    try:
        res_s = requests.get("https://sentami.sk/kategoria/denne-menu/", headers=headers, timeout=15)
        soup_s = BeautifulSoup(res_s.content.decode('utf-8', 'ignore'), 'html.parser')
        text_s = soup_s.get_text(separator="\n", strip=True)
        if "Pondelok" in text_s:
            start_s = text_s.find("Pondelok")
            if "Späť" in text_s:
                text_s = text_s.split("Späť")[0]
            menu_s = text_s[start_s:].strip()
            for den in dni_tyzdna + ["Týždenná ponuka"]:
                menu_s = menu_s.replace(den, f"\n\n🔹 *{den}*")
            requests.post(webhook_url, json={"text": f"🥗 *SENTAMI – TÝŽDENNÉ MENU*\n{menu_s.strip()}"})
    except: pass

if __name__ == "__main__":
    ziskaj_a_posli_menu()
