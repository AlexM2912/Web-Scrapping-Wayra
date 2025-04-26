import torch
from transformers import DistilBertTokenizer, DistilBertModel
from typing import Dict, List, Optional
import re

class BaseBERTExtractor:
    def __init__(self):
        try:
            model_name = 'distilbert-base-multilingual-cased'
            self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
            self.model = DistilBertModel.from_pretrained(model_name)
            if torch.cuda.is_available():
                self.model = self.model.cuda()
            self.model.eval()
            torch.cuda.empty_cache()
        except Exception as e:
            print(f"Error initializing BERT model: {str(e)}")
            try:
                # Fallback to CPU
                self.model = DistilBertModel.from_pretrained(model_name)
                self.model.eval()
            except Exception as e2:
                print(f"Fallback initialization failed: {str(e2)}")
                raise RuntimeError(f"Failed to initialize BERT model: {str(e)}")

    def preprocess_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text.strip())
        return text

    def extract_entities(self, text: str) -> Dict[str, str]:
        text = self.preprocess_text(text)
        inputs = self.tokenizer(text, return_tensors='pt', padding=True, truncation=True)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        return outputs.last_hidden_state

class AviancaBERTExtractor(BaseBERTExtractor):
    def extract_flight_info(self, text: str) -> Dict[str, str]:
        entities = super().extract_entities(text)
        return {
            'schedule': self._extract_schedule(text),
            'price': self._extract_price(text),
            'flight_type': self._extract_flight_type(text)
        }
    
    def _extract_schedule(self, text: str) -> Dict[str, str]:
        schedule_pattern = r'(\d{1,2}:\d{2})\s*(?:AM|PM)?'
        matches = re.finditer(schedule_pattern, text)
        times = [match.group() for match in matches]
        return {
            'departure': times[0] if len(times) > 0 else '',
            'arrival': times[1] if len(times) > 1 else ''
        }

    def _extract_price(self, text: str) -> str:
        price_pattern = r'\$\s*[\d.,]+(?:\s*(?:COP|USD))?'
        match = re.search(price_pattern, text)
        return match.group() if match else ''
    
    def _extract_flight_type(self, text: str) -> str:
        type_patterns = ['directo', 'escala', 'primera clase', 'económico']
        for pattern in type_patterns:
            if pattern in text.lower():
                return pattern
        return ''

class AirBERTExtractor(BaseBERTExtractor):
    def extract_accommodation_info(self, text: str) -> Dict[str, str]:
        entities = super().extract_entities(text)
        return {
            'title': self._extract_title(text),
            'description': self._extract_description(text),
            'price': self._extract_price(text),
            'rating': self._extract_rating(text)
        }
    
    def _extract_title(self, text: str) -> str:
        title_pattern = r'^([^\n]+)'
        match = re.search(title_pattern, text)
        return match.group(1).strip() if match else ''

    def _extract_description(self, text: str) -> str:
        desc_pattern = r'(?:descripción|about|sobre)\s*:?\s*([^\n]+)'
        match = re.search(desc_pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ''

    def _extract_price(self, text: str) -> str:
        price_pattern = r'\$\s*[\d.,]+(?:\s*(?:COP|USD))?(?:\s*por noche)?'
        match = re.search(price_pattern, text)
        return match.group() if match else ''

    def _extract_rating(self, text: str) -> str:
        rating_pattern = r'([0-9.]+)\s*(?:estrellas|stars|★)'
        match = re.search(rating_pattern, text, re.IGNORECASE)
        return match.group(1) if match else ''

class CoopetranBERTExtractor(BaseBERTExtractor):
    def extract_bus_info(self, text: str) -> Dict[str, str]:
        entities = super().extract_entities(text)
        return {
            'schedule': self._extract_schedule(text),
            'terminal': self._extract_terminal(text),
            'seats': self._extract_seats(text),
            'bus_type': self._extract_bus_type(text)
        }
    
    def _extract_schedule(self, text: str) -> Dict[str, str]:
        schedule_pattern = r'(\d{1,2}:\d{2})\s*(?:AM|PM)?'
        matches = re.finditer(schedule_pattern, text)
        times = [match.group() for match in matches]
        return {
            'departure': times[0] if len(times) > 0 else '',
            'arrival': times[1] if len(times) > 1 else ''
        }

    def _extract_terminal(self, text: str) -> str:
        terminal_pattern = r'Terminal\s+(?:de\s+)?(\w+)'
        match = re.search(terminal_pattern, text)
        return match.group(1) if match else ''

    def _extract_service_type(self, text: str) -> str:
        type_patterns = ['ejecutivo', 'premium', 'vip', 'estándar']
        for pattern in type_patterns:
            if pattern in text.lower():
                return pattern
        return ''

    def _extract_seats(self, text: str) -> str:
        seats_pattern = r'(\d+)\s*(?:sillas|asientos)\s*disponibles'
        match = re.search(seats_pattern, text)
        return match.group(1) if match else ''

    def _extract_bus_type(self, text: str) -> str:
        type_pattern = r'(?:Bus|Autobus)\s+([^\n]+)'
        match = re.search(type_pattern, text)
        return match.group(1).strip() if match else ''

class OmegaBERTExtractor(BaseBERTExtractor):
    def extract_bus_info(self, text: str) -> Dict[str, str]:
        entities = super().extract_entities(text)
        return {
            'schedule': self._extract_schedule(text),
            'terminal': self._extract_terminal(text),
            'service_type': self._extract_service_type(text),
            'seats': self._extract_seats(text)
        }
    
    def _extract_schedule(self, text: str) -> Dict[str, str]:
        schedule_pattern = r'(\d{1,2}:\d{2})\s*(?:AM|PM)?'
        matches = re.finditer(schedule_pattern, text)
        times = [match.group() for match in matches]
        return {
            'departure': times[0] if len(times) > 0 else '',
            'arrival': times[1] if len(times) > 1 else ''
        }

    def _extract_terminal(self, text: str) -> str:
        terminal_pattern = r'Terminal\s+(?:de\s+)?(\w+)'
        match = re.search(terminal_pattern, text)
        return match.group(1) if match else ''

    def _extract_service_type(self, text: str) -> str:
        type_patterns = ['ejecutivo', 'premium', 'vip', 'estándar']
        for pattern in type_patterns:
            if pattern in text.lower():
                return pattern
        return ''

    def _extract_seats(self, text: str) -> str:
        seats_pattern = r'(\d+)\s*(?:sillas|asientos)\s*disponibles'
        match = re.search(seats_pattern, text)
        return match.group(1) if match else ''