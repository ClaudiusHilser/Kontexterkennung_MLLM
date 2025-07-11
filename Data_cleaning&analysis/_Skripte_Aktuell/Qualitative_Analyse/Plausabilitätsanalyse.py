"""
_Skript: _Plausibilitaetsanalyse_Vorbereitung.py_

Ziel:
Dieses Skript erzeugt eine strukturierte CSV-Datei mit allen vom MLLM generierten Einzelinterpretationen
zur Vorbereitung der qualitativen Plausibilitätsanalyse.

Funktion:
- Liest alle JSON-Dateien aus den Teilnehmerordnern (teilnehmer_02 bis teilnehmer_11) ein
- Extrahiert pro Eintrag den Teilnehmer, das Szenario, den Zeitpunkt und den generierten Text
- Ergänzt zu jedem Eintrag die passende dominante Modalität durch Abgleich mit einer externen CSV-Datei
- Erstellt eine strukturierte CSV-Datei mit den Spalten:
  Teilnehmer, Szenario, Zeitpunkt, Text, Modalitaet

Output:
- plausibilitaetsanalyse_basis.csv (Grundlage für Stichprobenziehung und manuelle Bewertung)
"""



import os
import json
import pandas as pd

# === Pfade ===
base_path = os.path.join("..", "..", "interpretationen")  # JSON-Ordner
csv_output = "plausibilitaetsanalyse_basis.csv"           # Ziel-Datei
modalitaet_csv = "../Quantitative_Analyse/modalitaetsgewichtung_gesamt.csv"        # << HIER Pfad anpassen

# === Modalitäten laden ===
df_modalitaet = pd.read_csv(modalitaet_csv)
df_modalitaet["Teilnehmer"] = df_modalitaet["teilnehmer"].astype(str).str.zfill(2)
df_modalitaet["Zeitpunkt"] = df_modalitaet["zeitpunkt"]
df_modalitaet["Szenario"] = df_modalitaet["szenario"]

# === Ergebnisse-Container ===
eintraege = []

# === JSONs einlesen ===
for tn in range(2, 12):
    teilnehmer_ordner = os.path.join(base_path, f"teilnehmer_{tn:02d}")
    if not os.path.isdir(teilnehmer_ordner):
        continue

    for file_name in os.listdir(teilnehmer_ordner):
        if not file_name.endswith(".json"):
            continue

        szenario = file_name.replace(".json", "")
        file_path = os.path.join(teilnehmer_ordner, file_name)

        with open(file_path, "r", encoding="utf-8") as f:
            daten = json.load(f)

        for eintrag in daten:
            zeitpunkt = eintrag.get("zeitpunkt", "")
            text = eintrag.get("text", "").strip()

            # Modalität aus externer CSV suchen
            match = df_modalitaet[
                (df_modalitaet["Teilnehmer"] == f"{tn:02d}") &
                (df_modalitaet["Szenario"] == szenario) &
                (df_modalitaet["Zeitpunkt"] == zeitpunkt)
            ]

            if not match.empty:
                modalitaet = match.iloc[0]["modalitaet"]
            else:
                modalitaet = "Unbekannt"

            eintraege.append({
                "Teilnehmer": f"{tn:02d}",
                "Szenario": szenario,
                "Zeitpunkt": zeitpunkt,
                "Text": text,
                "Modalitaet": modalitaet
            })

# === DataFrame erzeugen und speichern ===
df_plausibilitaet = pd.DataFrame(eintraege)
df_plausibilitaet.to_csv(csv_output, index=False)

print("✅ Bewertungsbasis für Plausibilitätsanalyse gespeichert unter:", csv_output)
