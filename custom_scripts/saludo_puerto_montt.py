
import datetime
import json

# Simulate getting real-time weather and time for Puerto Montt
# In a real scenario, this would involve external APIs.
# Based on current context: Today is Sunday, April 12, 2026.

now = datetime.datetime.now()
hora_actual = now.strftime("%H:%M")
fecha = now.strftime("%d de %B de %Y")
clima = "Lluvia moderada a intervalos" # Based on search result 2 for today (Apr 12)
temp_max = "12°C"
temp_min = "7°C"

mensaje = f"Hola, señor. Es {hora_actual} del {fecha}. El clima actual en Puerto Montt, Chile es de {clima}, con temperaturas que oscilan entre {temp_min} y {temp_max}."
print(mensaje)
