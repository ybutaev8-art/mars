import os, sys, re
sys.path.insert(0, r"C:\Users\YASHNARBEK\.gemini\antigravity\scratch\mars_pos_bot")
from ai_service import ai_service

def split_multi_queries(text):
    pattern = r"(?:\n+|\?+\s+|;\s*|,\s*(?:yana|keyin|qolaversa|shuningdek|hamda)\s+|\b(?:va\s+yana|va\s+keyin|yana\s+bitta\s+savol|yana\s+bir\s+savol|ikkinchi\s+savol(?:im)?)\b)"
    parts = re.split(pattern, text, flags=re.IGNORECASE)
    return [p.strip(' ?!,.\t\r\n') for p in parts if len(p.strip(' ?!,.\t\r\n')) >= 4]

tests = [
    "Oylik qarzimni tekshiring, yana z-otchyot qanday olinadi?",
    "Shotdan tolasa boladimi? Apparat soati notogri bolib qoldi",
    "Oylik rekvizitni bering va yana ofisingiz qayerda?",
    "Oylik qarzim bormi?\nApparatga lenta qanday qoyiladi?"
]

for t in tests:
    parts = split_multi_queries(t)
    print("TEST:", t)
    for i, p in enumerate(parts, 1):
        res = ai_service.detect_semantic_intent(p)
        print(f"  Part {i}: '{p}' -> Intent: {res.get('intent') if res else None}")
    print()
