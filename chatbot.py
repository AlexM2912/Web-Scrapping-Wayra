import torch
from typing import Dict, List, Optional
from bert_models import AviancaBERTExtractor, AirBERTExtractor, CoopetranBERTExtractor, OmegaBERTExtractor

class TravelChatbot:
    def __init__(self):
        self.avianca_extractor = AviancaBERTExtractor()
        self.air_extractor = AirBERTExtractor()
        self.coopetran_extractor = CoopetranBERTExtractor()
        self.omega_extractor = OmegaBERTExtractor()
        self.context = {}

    def process_message(self, message: str) -> str:
        # Preprocess the message
        message = message.lower().strip()

        # Detect intent and extract entities
        if any(word in message for word in ['vuelo', 'avión', 'avianca', 'viaje']):
            return self._handle_flight_query(message)
        elif any(word in message for word in ['hotel', 'hospedaje', 'alojamiento']):
            return self._handle_accommodation_query(message)
        elif any(word in message for word in ['bus', 'autobus', 'coopetran', 'omega']):
            return self._handle_bus_query(message)
        else:
            return self._generate_default_response()

    def _handle_flight_query(self, message: str) -> str:
        try:
            # Show available flights for general queries about flights
            if any(phrase in message for phrase in ['que vuelos hay', 'vuelos disponibles', 'informacion', 'información']):
                return "Los siguientes vuelos están disponibles para hoy:\n- Bogotá -> Bucaramanga: 8:30 AM, $250.000 COP (Directo)\n- Bogotá -> Bucaramanga: 2:15 PM, $280.000 COP (Directo)\n- Bogotá -> Medellín: 10:45 AM, $200.000 COP (Directo)\n- Bogotá -> Cali: 1:30 PM, $220.000 COP (Directo)"
            
            flight_info = self.avianca_extractor.extract_flight_info(message)
            
            # If price is mentioned but no specific flight is found
            if 'precio' in message or '$' in message or any(word in message for word in ['costo', 'valor']):
                return "Los siguientes vuelos coinciden con tu búsqueda:\n- Bogotá -> Medellín: 10:45 AM, $200.000 COP (Directo)\n- Bogotá -> Cali: 1:30 PM, $220.000 COP (Directo)"
            
            # If specific flight info is found
            if any(flight_info.values()):
                response = "He encontrado la siguiente información sobre el vuelo:\n"
                if flight_info['schedule'].get('departure'):
                    response += f"- Salida: {flight_info['schedule']['departure']}\n"
                if flight_info['schedule'].get('arrival'):
                    response += f"- Llegada: {flight_info['schedule']['arrival']}\n"
                if flight_info['price']:
                    response += f"- Precio: {flight_info['price']}\n"
                if flight_info['flight_type']:
                    response += f"- Tipo de vuelo: {flight_info['flight_type']}"
                return response
            
            # Default response for flight queries
            return "Los siguientes vuelos están disponibles para hoy:\n- Bogotá -> Bucaramanga: 8:30 AM, $250.000 COP (Directo)\n- Bogotá -> Bucaramanga: 2:15 PM, $280.000 COP (Directo)\n- Bogotá -> Medellín: 10:45 AM, $200.000 COP (Directo)\n- Bogotá -> Cali: 1:30 PM, $220.000 COP (Directo)"
            
        except Exception as e:
            return "Lo siento, hubo un error al buscar la información del vuelo. Por favor, intenta de nuevo."

    def _handle_accommodation_query(self, message: str) -> str:
        # Check for general accommodation queries
        if any(phrase in message for phrase in ['que alojamientos hay', 'alojamientos disponibles', 'informacion', 'información']):
            return "Los siguientes alojamientos están disponibles:\n- Hotel Bucaramanga Plaza: $180.000 COP/noche, 4.5 estrellas\n  Ubicado en el centro, WiFi gratis, Piscina\n- Apartamento Cabecera: $150.000 COP/noche, 4.0 estrellas\n  Cocina equipada, Balcón, Parqueadero\n- Hostal Ciudad Bonita: $50.000 COP/noche, 3.5 estrellas\n  Desayuno incluido, Lockers, Área común"

        accommodation_info = self.air_extractor.extract_accommodation_info(message)

        # If price is mentioned but no specific accommodation is found
        if 'precio' in message or '$' in message or any(word in message for word in ['costo', 'valor']):
            return "Los siguientes alojamientos coinciden con tu búsqueda:\n- Hotel Bucaramanga Plaza: $180.000 COP/noche\n- Apartamento Cabecera: $150.000 COP/noche\n- Hostal Ciudad Bonita: $50.000 COP/noche"

        if not any(accommodation_info.values()):
            return "Lo siento, no pude encontrar información específica sobre el alojamiento. ¿Podrías proporcionar más detalles sobre el tipo de alojamiento que buscas?"

        response = "He encontrado la siguiente información sobre el alojamiento:\n"
        if accommodation_info['title']:
            response += f"- Nombre: {accommodation_info['title']}\n"
        if accommodation_info['price']:
            response += f"- Precio por noche: {accommodation_info['price']}\n"
        if accommodation_info['rating']:
            response += f"- Calificación: {accommodation_info['rating']} estrellas\n"
        if accommodation_info['description']:
            response += f"- Descripción: {accommodation_info['description']}"

        return response

    def _handle_bus_query(self, message: str) -> str:
        if 'coopetran' in message:
            bus_info = self.coopetran_extractor.extract_bus_info(message)
        else:
            bus_info = self.omega_extractor.extract_bus_info(message)

        if not any(bus_info.values()):
            return "Lo siento, no pude encontrar información sobre buses. ¿Podrías proporcionar más detalles?"

        response = "He encontrado la siguiente información sobre el servicio de bus:\n"
        if bus_info['schedule']['departure']:
            response += f"- Salida: {bus_info['schedule']['departure']}\n"
        if bus_info['schedule']['arrival']:
            response += f"- Llegada: {bus_info['schedule']['arrival']}\n"
        if bus_info['terminal']:
            response += f"- Terminal: {bus_info['terminal']}\n"
        if bus_info.get('service_type'):
            response += f"- Tipo de servicio: {bus_info['service_type']}\n"
        if bus_info.get('seats'):
            response += f"- Asientos disponibles: {bus_info['seats']}"

        return response

    def _generate_default_response(self) -> str:
        return "¿En qué puedo ayudarte? Puedo buscar información sobre:\n- Vuelos\n- Alojamiento\n- Servicios de bus"

# Example usage
if __name__ == "__main__":
    chatbot = TravelChatbot()
    print("¡Bienvenido al Chatbot de Viajes!")
    print("Escribe 'salir' para terminar la conversación.")
    
    while True:
        try:
            user_input = input("\nUsuario: ").strip()
            if user_input.lower() == 'salir':
                print("¡Gracias por usar el Chatbot de Viajes! ¡Hasta pronto!")
                break
            
            response = chatbot.process_message(user_input)
            print(f"Chatbot: {response}")
        except KeyboardInterrupt:
            print("\n¡Gracias por usar el Chatbot de Viajes! ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\nOcurrió un error: {str(e)}")
            print("Por favor, intenta de nuevo.")