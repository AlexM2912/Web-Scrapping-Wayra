from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, ElementClickInterceptedException
import logging
import time
import random

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración del navegador
chrome_options = Options()
chrome_options.add_argument('--headless')  # Sin interfaz gráfica
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

# Agregar cabeceras de navegador realistas
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
chrome_options.add_argument('--accept-language=es-ES,es;q=0.9,en;q=0.8')

MAX_RETRIES = 5  # Número máximo de reintentos
BASE_WAIT_TIME = 45
MAX_WAIT_TIME = 120

def get_exponential_backoff(attempt):
    """Calcular el tiempo de retroceso exponencial con jitter"""
    base_delay = min(MAX_WAIT_TIME, BASE_WAIT_TIME * (2 ** attempt))
    jitter = random.uniform(0, 0.1 * base_delay)  # 10% de jitter
    return base_delay + jitter

def setup_driver():
    """Configuración y lanzamiento del navegador"""
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(BASE_WAIT_TIME)
        return driver
    except Exception as e:
        logging.error(f'Error al configurar el navegador: {e}')
        raise

def handle_cookie_consent(driver):
    """Manejar el banner de consentimiento de cookies"""
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))
        )
        cookie_button.click()
        logging.info('Consentimiento de cookies manejado')
        time.sleep(2)  # Esperar a que el banner desaparezca
    except TimeoutException:
        logging.info('No se encontró banner de cookies')
    except Exception as e:
        logging.warning(f'Error al manejar el consentimiento de cookies: {e}')

def wait_for_elements(driver, selector, timeout=BASE_WAIT_TIME):
    """Esperar que los elementos estén presentes en la página"""
    try:
        wait = WebDriverWait(driver, timeout)
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
        return elements
    except TimeoutException:
        logging.warning(f'Tiempo de espera agotado para el selector: {selector}')
        return None
    except Exception as e:
        logging.error(f'Error esperando los elementos: {e}')
        return None

def scroll_to_element(driver, element):
    """Desplazar la página hasta un elemento con JavaScript"""
    try:
        driver.execute_script('arguments[0].scrollIntoView({block: "center"});', element)
        time.sleep(1)  # Esperar a que el desplazamiento se complete
    except Exception as e:
        logging.warning(f'Error al desplazar hacia el elemento: {e}')

def click_show_more_button(driver):
    """Hacer clic en el botón 'Mostrar más vuelos' hasta que todos los vuelos estén cargados"""
    max_attempts = 3
    retry_delay = 2

    try:
        while True:
            try:
                # Esperar a que el botón esté presente
                button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'FB566-MoreFlightsBtn'))
                )

                # Desplazar el botón a la vista
                scroll_to_element(driver, button)

                # Intentar hacer clic en el botón
                for attempt in range(max_attempts):
                    try:
                        # Esperar a que el botón sea clickeable
                        button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, 'FB566-MoreFlightsBtn'))
                        )
                        button.click()
                        break
                    except ElementClickInterceptedException:
                        # Si no se puede hacer clic normalmente, intentar hacer clic con JavaScript
                        driver.execute_script('arguments[0].click();', button)
                        break
                    except Exception as e:
                        if attempt == max_attempts - 1:
                            raise
                        time.sleep(retry_delay)

                logging.info('Hizo clic en el botón "Mostrar más vuelos"')
                time.sleep(5)  # Esperar a que se carguen los nuevos vuelos

            except TimeoutException:
                logging.info('No se encontró más el botón "Mostrar más vuelos". Todos los vuelos están cargados.')
                break

    except Exception as e:
        logging.error(f'Error en click_show_more_button: {e}')

def extract_flight_info(vuelo):
    """Extraer la información del vuelo"""
    try:
        info = {
            'hora_salida': vuelo.find_element(By.CSS_SELECTOR, 'div.journey-schedule_time.journey-schedule_time-departure').text,
            'hora_llegada': vuelo.find_element(By.CSS_SELECTOR, 'div.journey-schedule_time.journey-schedule_time-return').text,
            'duracion': vuelo.find_element(By.CSS_SELECTOR, 'div.journey-schedule_duration_time').text,
            'tipo_vuelo': vuelo.find_element(By.CSS_SELECTOR, 'span.button_label.ng-star-inserted').text,
            'precio': vuelo.find_element(By.CSS_SELECTOR, 'span.price.text-space-gap').text
        }
        return info
    except NoSuchElementException as e:
        logging.error(f'Elemento no encontrado: {e}')
        return None
    except Exception as e:
        logging.error(f'Error al extraer la información del vuelo: {e}')
        return None

def scrape_flights(url):
    """Scraping de vuelos"""
    driver = None
    try:
        for attempt in range(MAX_RETRIES):
            try:
                if driver is None:
                    driver = setup_driver()

                wait_time = get_exponential_backoff(attempt)
                logging.info(f'Intento {attempt + 1} de {MAX_RETRIES} (tiempo de espera: {wait_time:.2f}s)')

                driver.get(url)
                time.sleep(2)  # Pausa breve después de cargar la página

                # Manejar el consentimiento de cookies
                handle_cookie_consent(driver)

                # Hacer clic en el botón "Mostrar más vuelos" hasta que todos los vuelos estén cargados
                click_show_more_button(driver)

                # Esperar a que los elementos de vuelo se carguen
                vuelos = wait_for_elements(driver, 'div.journey_inner.target-conections-reviewer', timeout=wait_time)
                if not vuelos:
                    if attempt < MAX_RETRIES - 1:
                        logging.warning('No se encontraron elementos de vuelo, reintentando con una nueva sesión...')
                        if driver:
                            driver.quit()
                        driver = None
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.error('Se alcanzó el número máximo de reintentos, no se encontraron vuelos')
                        break

                # Extraer la información de los vuelos
                logging.info('Vuelos encontrados:')
                for vuelo in vuelos:
                    info = extract_flight_info(vuelo)
                    if info:
                        logging.info(f'Detalles del vuelo: {info}')
                        print('-' * 40)

                break  # Si todo salió bien, salir del bucle de reintentos

            except (TimeoutException, WebDriverException) as e:
                if attempt < MAX_RETRIES - 1:
                    logging.warning(f'Error en el intento {attempt + 1}: {str(e)}')
                    if driver:
                        driver.quit()
                    driver = None
                    time.sleep(wait_time)
                else:
                    logging.error(f'Se alcanzó el número máximo de reintentos: {str(e)}')
                    raise

    except Exception as e:
        logging.error(f'Error durante el scraping: {e}')
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    # URL proporcionada directamente (sin automatizar la construcción)
    url = "https://www.avianca.com/es/booking/select/?origin1=BOG&destination1=BGA&departure1=2025-04-14&adt1=2&tng1=2&chd1=2&inf1=2&origin2=BGA&destination2=BOG&departure2=2025-04-20&adt2=2&tng2=2&chd2=2&inf2=2&currency=COP&posCode=CO"

    # Ejecutar búsqueda de vuelos
    scrape_flights(url)
