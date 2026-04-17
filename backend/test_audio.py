import sys, os, asyncio
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv('../.env')

import pyaudio, pyttsx3, traceback

print('=== Testing Audio Stack ===')

# 1. Test pyttsx3
print('[1] pyttsx3 init...')
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 155)
    engine.setProperty('volume', 0.92)
    voices = engine.getProperty('voices')
    print(f'    Voices: {len(voices)}')
    for v in voices:
        es = any('es' in str(l).lower() for l in (v.languages or []))
        print(f'    - {v.name} (es: {es})')
    # Select Spanish
    for v in voices:
        if any('spanish' in str(l).lower() or 'es' in str(l).lower() for l in (v.languages or [])):
            engine.setProperty('voice', v.id)
            print(f'    Selected Spanish: {v.name}')
            break
    # Test speak
    engine.say('Hola, soy Ada. Puedo hablar.')
    engine.runAndWait()
    print('    TTS speak: OK')
except Exception as e:
    print(f'    TTS FAIL: {e}')
    traceback.print_exc()

# 2. Test pyaudio input
print('[2] pyaudio input devices...')
try:
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f'    IN [{i}]: {info["name"]}')
    p.terminate()
except Exception as e:
    print(f'    pyaudio FAIL: {e}')

# 3. Test pyaudio output
print('[3] pyaudio output devices...')
try:
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxOutputChannels'] > 0:
            print(f'    OUT [{i}]: {info["name"]}')
    p.terminate()
except Exception as e:
    print(f'    pyaudio FAIL: {e}')

print('=== Done ===')