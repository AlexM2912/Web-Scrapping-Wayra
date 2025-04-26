from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re

def configurar_selenium():
    """
    Configura el navegador Chrome para Selenium
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service()
    return webdriver.Chrome(service=service, options=options)

def esperar_y_obtener_elementos(driver, selector, by=By.CSS_SELECTOR, timeout=20):
    """
    Espera y obtiene elementos con manejo de errores
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        return True
    except TimeoutException:
        print(f"Timeout esperando por elementos con selector: {selector}")
        return False

def extraer_texto_limpio(texto):
    """
    Limpia y formatea el texto extraído
    """
    if not texto:
        return "No disponible"
    texto = texto.strip()
    texto = re.sub(r'\s+', ' ', texto)  # Reemplaza múltiples espacios con uno solo
    return texto

def extraer_horario(texto):
    """
    Extrae el horario del texto usando expresiones regulares
    """
    if not texto:
        return "No disponible"
    # Busca patrones de hora como "11:30 PM" o "09:30 AM"
    horario = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM)', texto)
    if horario:
        return horario.group()
    return "No disponible"

def extraer_terminal(texto):
    """
    Extrae el nombre de la terminal del texto, eliminando números
    """
    if not texto:
        return "No disponible"
    # Busca texto que contenga "Terminal" seguido por cualquier texto, excluyendo "Llegada Aprox"
    texto = texto.replace("Llegada Aprox", "").strip()
    terminal = re.search(r'Terminal\s+(?:de\s+)?(\w+)(?:\d+h)?', texto)
    if terminal:
        return f"Terminal de {terminal.group(1)}"
    return "No disponible"

def calcular_duracion(hora_salida, hora_llegada):
    """
    Calcula la duración aproximada del viaje
    """
    if hora_salida == "No disponible" or hora_llegada == "No disponible":
        return "No disponible"
    
    try:
        from datetime import datetime
        formato = "%I:%M %p"
        salida = datetime.strptime(hora_salida, formato)
        llegada = datetime.strptime(hora_llegada, formato)
        
        # Ajustar si el viaje cruza la medianoche
        if llegada < salida:
            llegada = llegada.replace(day=salida.day + 1)
        
        duracion = llegada - salida
        horas = duracion.seconds // 3600
        minutos = (duracion.seconds % 3600) // 60
        
        if minutos == 0:
            return f"{horas} horas"
        return f"{horas} horas y {minutos} minutos"
    except:
        return "No disponible"

def extraer_precio(texto):
    """
    Extrae el precio del texto
    """
    if not texto:
        return "No disponible"
    # Busca valores monetarios como "$120.000"
    precio = re.search(r'\$\s*[\d.,]+(?:\s*(?:COP|USD))?', texto)
    if precio:
        return precio.group()
    return "No disponible"

def extraer_sillas(texto):
    """
    Extrae el número de sillas disponibles
    """
    if not texto:
        return "No disponible"
    # Busca números seguidos por "sillas disponibles"
    sillas = re.search(r'(\d+)\s*sillas\s*disponibles', texto)
    if sillas:
        return f"{sillas.group(1)} sillas disponibles"
    return "No disponible"

def extraer_tipo_bus(texto):
    """
    Extrae el tipo de bus del texto
    """
    if not texto:
        return "No disponible"
    # Busca el tipo de bus después de "Tipo de bus -"
    tipo = re.search(r'Tipo\s+de\s+bus\s*-\s*([\w\s]+)', texto)
    if tipo:
        return tipo.group(1).strip()
    return "No disponible"

def obtener_info_viajes(url):
    """
    Obtiene la información de los viajes usando Selenium y BeautifulSoup
    """
    driver = configurar_selenium()
    try:
        print("Accediendo a la página...")
        driver.get(url)
        time.sleep(5)  # Espera inicial para carga de JavaScript

        # Intentar diferentes selectores para los contenedores de viajes
        selectors_to_try = [
            ".ticket-card-container",
            ".travel-card",
            "div[class*='ticket']",
            "div[class*='travel']",
            "div[class*='journey']"
        ]

        found = False
        for selector in selectors_to_try:
            if esperar_y_obtener_elementos(driver, selector):
                found = True
                print(f"Elementos encontrados con selector: {selector}")
                break

        if not found:
            print("No se pudieron encontrar los elementos de viajes")
            return []

        # Obtener el HTML después de que JavaScript haya cargado todo el contenido
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Lista para almacenar todos los viajes
        viajes = []

        # Intentar encontrar los contenedores con diferentes selectores
        contenedores = []
        for selector in selectors_to_try:
            contenedores = soup.select(selector)
            if contenedores:
                break

        if not contenedores:
            print("No se encontraron contenedores de viajes en la página")
            return []

        for contenedor in contenedores:
            try:
                texto_completo = extraer_texto_limpio(contenedor.get_text())
                
                # Crear diccionario con la información extraída usando las funciones especializadas
                viaje = {
                    'horario_salida': extraer_horario(texto_completo),
                    'horario_llegada': extraer_horario(texto_completo.split('Llegada Aprox')[-1] if 'Llegada Aprox' in texto_completo else ''),
                    'terminal_salida': extraer_terminal(texto_completo),
                    'terminal_llegada': extraer_terminal(texto_completo.split('Llegada Aprox')[-1] if 'Llegada Aprox' in texto_completo else ''),
                    'duracion': calcular_duracion(extraer_horario(texto_completo), 
                              extraer_horario(texto_completo.split('Llegada Aprox')[-1] if 'Llegada Aprox' in texto_completo else '')),
                    'precio': extraer_precio(texto_completo),
                    'sillas_disponibles': extraer_sillas(texto_completo),
                    'tipo_bus': extraer_tipo_bus(texto_completo)
                }
                
                viajes.append(viaje)
            except Exception as e:
                print(f"Error al procesar un contenedor de viaje: {str(e)}")
                continue

        return viajes

    except Exception as e:
        print(f"Error durante la extracción de datos: {str(e)}")
        return []
    finally:
        driver.quit()

def main():
    # URL exacta proporcionada por el usuario
    url = "https://tiquetes.copetran.com/busqueda?origen=Bogota,+DC+(Todas)&origen_id=15&destino=Bucaramanga,+SAN+(Todas)&destino_id=34&salida=2025-04-12"

    print("Buscando viajes disponibles...")
    viajes = obtener_info_viajes(url)

    if viajes:
        print(f"\nSe encontraron {len(viajes)} viajes:")
        for i, viaje in enumerate(viajes, 1):
            duracion = calcular_duracion(viaje['horario_salida'], viaje['horario_llegada'])
            print(f"\nViaje #{i}")
            print("=" * 50)
            print(f"Horario de salida: {viaje['horario_salida']}")
            print(f"Horario de llegada: {viaje['horario_llegada']}")
            print(f"Duración aproximada: {duracion}")
            print(f"Terminal de salida: {viaje['terminal_salida']}")
            print(f"Terminal de llegada: {viaje['terminal_llegada']}")
            print(f"Precio: {viaje['precio']}")
            print(f"Sillas disponibles: {viaje['sillas_disponibles']}")
            print(f"Tipo de bus: {viaje['tipo_bus']}")
    else:
        print("No se encontraron viajes disponibles")

if __name__ == "__main__":
    main()
