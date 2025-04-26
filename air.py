import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Para mostrar caracteres como ñ y tildes correctamente
sys.stdout.reconfigure(encoding='utf-8')

# Configurar opciones de Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# Iniciar WebDriver con las opciones configuradas
driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, 15)

try:
    # URL con los filtros deseados
    url = ("https://www.airbnb.com.co/s/Bucaramanga--Santander/homes"
           "?adults=2&children=2&infants=2&pets=2&check_in=2025-04-12&check_out=2025-04-13")
    driver.get(url)

    # Esperar a que la página cargue y hacer scroll para cargar más resultados
    print("Cargando resultados...")
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    # Esperar y obtener todas las tarjetas de alojamiento
    cards = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='card-container']")))
    print(f"\n🔎 Se encontraron {len(cards)} alojamientos\n")

    # Procesar cada tarjeta
    for index, card in enumerate(cards, 1):
        try:
            # Título
            title = wait.until(lambda d: card.find_element(By.CSS_SELECTOR, "[data-testid='listing-card-name']")).text.strip()
            if not title:
                continue

            # Descripción
            try:
                description = card.find_element(By.CSS_SELECTOR, "[data-testid='listing-card-title']").text.strip()
            except NoSuchElementException:
                description = "N/A"

            # Precio
            try:
                price_elem = card.find_element(By.XPATH, ".//span[contains(text(), ' por noche')]")
                price_text = price_elem.text.strip()
                if "precio original" in price_text:
                    parts = price_text.split("precio original")
                    discounted_price = parts[0].split(" por noche")[0].strip()
                    normal_price = parts[1].strip()
                else:
                    discounted_price = None
                    normal_price = price_text.split(" por noche")[0].strip()
            except NoSuchElementException:
                continue

            # Tiempo de estadía
            try:
                link_elem = card.find_element(By.XPATH, ".//a[contains(@href, '/rooms/')]")
                listing_url = link_elem.get_attribute('href')
                params = parse_qs(urlparse(listing_url).query)
                check_in = params.get('check_in', [None])[0]
                check_out = params.get('check_out', [None])[0]
                if check_in and check_out:
                    d1 = datetime.strptime(check_in, "%Y-%m-%d")
                    d2 = datetime.strptime(check_out, "%Y-%m-%d")
                    nights = (d2 - d1).days
                    stay_duration = f"{nights} noche{'s' if nights > 1 else ''}"
            except Exception:
                stay_duration = "N/A"

            # Camas y habitaciones
            try:
                beds_elem = card.find_element(By.XPATH, ".//span[contains(text(), 'cama')]")
                beds = beds_elem.text.strip()
            except NoSuchElementException:
                beds = "N/A"

            # Calificación
            try:
                rating_elem = card.find_element(By.XPATH, ".//span[contains(text(), 'Calificación promedio')]")
                rating = rating_elem.text.replace("Calificación promedio: ", "").strip()
            except NoSuchElementException:
                rating = "Sin calificación"

            # Imprimir resultados
            print(f"Alojamiento #{index}")
            print("-" * 60)
            print(f"Título: {title}")
            print(f"Descripción: {description}")
            if discounted_price:
                print(f"Precio con descuento: {discounted_price}")
                print(f"Precio normal: {normal_price}")
            else:
                print(f"Precio: {normal_price}")
            print(f"Tiempo de estadía: {stay_duration}")
            print(f"Número de camas: {beds}")
            print(f"Calificación: {rating}")
            print("-" * 60 + "\n")

        except Exception as e:
            print(f"Error procesando alojamiento: {str(e)}\n")
            continue

except Exception as e:
    print(f"Error general: {str(e)}")

finally:
    driver.quit()
