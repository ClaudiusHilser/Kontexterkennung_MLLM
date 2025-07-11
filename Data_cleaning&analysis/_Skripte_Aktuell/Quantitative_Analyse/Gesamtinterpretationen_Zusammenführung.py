import os
import json
import pandas as pd
import re

# Basisordner mit allen Gesamtinterpretationen
basisordner = "../../Gesamtinterpretationen"

# Leere Liste für alle Daten
eintraege = []

# Alle Teilnehmerordner durchgehen
for teilnehmer in os.listdir(basisordner):
    teilnehmer_pfad = os.path.join(basisordner, teilnehmer)
    if not os.path.isdir(teilnehmer_pfad):
        continue

    for datei in os.listdir(teilnehmer_pfad):
        if not datei.endswith(".json"):
            continue

        szenario = datei.replace(".json", "")
        pfad = os.path.join(teilnehmer_pfad, datei)

        with open(pfad, "r", encoding="utf-8") as f:
            data = json.load(f)

        interpretation = data.get("gesamtinterpretation", "")

        # Werte mit regex extrahieren
        def extrahiere_kategorie(text, kategorie):
            match = re.search(rf"{kategorie}:\s*(niedrig|mittel|hoch)", text, re.IGNORECASE)
            return match.group(1).lower() if match else "n/a"

        stress = extrahiere_kategorie(interpretation, "Stress")
        entspannung = extrahiere_kategorie(interpretation, "Entspannung")
        ablenkung = extrahiere_kategorie(interpretation, "Ablenkung")

        eintraege.append({
            "Teilnehmer": teilnehmer,
            "Szenario": szenario,
            "Stress": stress,
            "Entspannung": entspannung,
            "Ablenkung": ablenkung
        })

# In DataFrame speichern
df = pd.DataFrame(eintraege)
df.sort_values(by=["Teilnehmer", "Szenario"], inplace=True)

# Als Übersicht speichern
df.to_csv("gesamtinterpretation_übersicht.csv", index=False, encoding="utf-8")
print("✅ Übersicht gespeichert als 'gesamtinterpretation_übersicht.csv'")
