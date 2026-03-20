import re
import json
from seleniumwire.utils import decode as sw_decode

def decode(body):
    """
    Decodifica o corpo da resposta tratando compressão (gzip/brotli) automaticamente.
    """
    try:
        # Usa o utilitário do selenium-wire para descompactar os bytes
        decompressed_body = sw_decode(body, 'gzip') # O selenium-wire tenta detectar o encoding
        
        # Converte os bytes resultantes em string UTF-8 e depois em dicionário JSON
        return json.loads(decompressed_body.decode('utf-8'))
    except Exception as e:
        print(f"❌ Erro na decodificação dos dados: {e}")
        return None


def parse_stat_value(value):
    """
    Converte uma string de estatística para tipo numérico apropriado.

    Exemplos de conversão:
    - "45%" → 0.45
    - "1.23" → 1.23 (float)
    - "15" → 15 (int)
    - "8/17 (47%)" → {'success': 8, 'total': 17, 'rate': 0.47}
    - "8/10" → {'success': 8, 'total': 10}

    Retorna o valor original caso não consiga interpretar.
    """
    if isinstance(value, str):
        value = value.strip()

        if value.endswith("%"):
            try:
                return int(value.replace("%", "")) / 100
            except ValueError:
                return value

        elif re.match(r"^\d+\.\d+$", value):
            return float(value)

        elif re.match(r"^\d+$", value):
            return int(value)

        elif "/" in value and "(" in value and ")" in value:
            match = re.match(r"(\d+)/(\d+) \((\d+)%\)", value)
            if match:
                return {
                    "success": int(match.group(1)),
                    "total": int(match.group(2)),
                    "rate": int(match.group(3)) / 100
                }

        elif "/" in value:
            try:
                parts = value.split("/")
                return {
                    "success": int(parts[0]),
                    "total": int(parts[1])
                }
            except (ValueError, IndexError):
                return value

    return value
