from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

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

def convertir_a_am_pm(hora, periodo):
    """
    Convierte la hora en formato de 12 horas con "am" o "pm" según el periodo.
    """
    if periodo == "Madrugada":
        sufijo = "am"
    elif periodo == "Mañana":
        sufijo = "am"
    elif periodo == "Tarde":
        sufijo = "pm"
    elif periodo == "Noche":
        sufijo = "pm"
    else:
        sufijo = ""  # Por si no se encuentra el periodo

    return f"{hora} {sufijo}"

def obtener_info_viajes(url):
    """
    Obtiene la información de los viajes usando Selenium y BeautifulSoup
    """
    driver = configurar_selenium()
    try:
        driver.get(url)
        time.sleep(10)  # Espera para que cargue el contenido dinámico

        # Obtener el HTML después de que JavaScript haya cargado todo el contenido
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Lista para almacenar todos los viajes
        viajes = []

        # Encontrar todos los contenedores de viajes
        contenedores = soup.find_all("div", class_="container-lg border-bottom resultContainer d-flex flex-column justify-content-center")

        for contenedor in contenedores:
            # Extraer horario de salida
            salida = contenedor.find("div", class_="time_and_city col d-flex flex-column justify-content-center align-items-center")
            if salida:
                hora_salida = salida.find("div").text.strip()  # Ejemplo: "01:30"
                icono_salida = salida.find("svg", {"title": True})  # Buscar el ícono con el atributo title
                periodo_salida = icono_salida["title"] if icono_salida else "No disponible"
                hora_salida_am_pm = convertir_a_am_pm(hora_salida, periodo_salida)
            else:
                hora_salida_am_pm = "No disponible"

            # Extraer terminal de salida
            terminal_salida = salida.find("div", class_="font_12 text-secondary").text.strip() if salida else "No disponible"

            # Extraer horario de llegada
            llegada = contenedor.find_all("div", class_="time_and_city col d-flex flex-column justify-content-center align-items-center")[-1]
            if llegada:
                hora_llegada = llegada.find("div").text.strip()  # Ejemplo: "10:40"
                icono_llegada = llegada.find("svg", {"title": True})  # Buscar el ícono con el atributo title
                periodo_llegada = icono_llegada["title"] if icono_llegada else "No disponible"
                hora_llegada_am_pm = convertir_a_am_pm(hora_llegada, periodo_llegada)
                terminal_llegada = llegada.find("div", class_="font_12 text-secondary").text.strip()
            else:
                hora_llegada_am_pm = "No disponible"
                terminal_llegada = "No disponible"

            # Extraer tipo de servicio
            tipo_servicio = contenedor.find("div", class_="col time_and_city text-center d-flex flex-column justify-content-center")
            tipo_servicio = tipo_servicio.text.strip() if tipo_servicio else "No disponible"

            # Extraer asientos disponibles
            asientos = contenedor.find("div", class_="col time_and_city d-flex flex-column justify-content-center align-items-center max_width_150")
            asientos = asientos.text.strip() if asientos else "No disponible"

            # Extraer precio
            precio = contenedor.find("div", class_="view_seats_button text-center")
            precio = precio.text.strip() if precio else "No disponible"

            # Crear diccionario con la información del viaje
            viaje = {
                'hora_salida_am_pm': hora_salida_am_pm,
                'terminal_salida': terminal_salida,
                'hora_llegada_am_pm': hora_llegada_am_pm,
                'terminal_llegada': terminal_llegada,
                'tipo_servicio': tipo_servicio,
                'asientos': asientos,
                'precio': precio
            }
            viajes.append(viaje)

        return viajes

    finally:
        driver.quit()

def main():
    # URL proporcionada
    url = "https://omega.redbus.co/searchbus?fromcityID=195236&tocityID=195201&fromcity=Term.%20BUCARAMANGA&tocity=Term.%20BOGOTA%20SALITRE&datePicker=2025-03-13"

    print("Buscando viajes disponibles...")
    viajes = obtener_info_viajes(url)

    if viajes:
        print(f"\nSe encontraron {len(viajes)} viajes:")
        for i, viaje in enumerate(viajes, 1):
            print(f"\nViaje #{i}")
            print("=" * 50)
            print(f"Hora de salida: {viaje['hora_salida_am_pm']}")
            print(f"Terminal de salida: {viaje['terminal_salida']}")
            print(f"Hora de llegada: {viaje['hora_llegada_am_pm']}")
            print(f"Terminal de llegada: {viaje['terminal_llegada']}")
            print(f"Tipo de servicio: {viaje['tipo_servicio']}")
            print(f"Asientos disponibles: {viaje['asientos']}")
            print(f"Precio: {viaje['precio']}")
    else:
        print("No se encontraron viajes disponibles")

if __name__ == "__main__":
    main()
