"""
_Skript: _Modalitäten_Fehlernanalyse.py

Ziel:
- Analysiert die Nennungen dominanter Modalitäten in MLLM-Interpretationen
- Erstellt:
    1. CSV mit unklaren Fällen zur manuellen Nachbesserung
    2. CSV mit gruppierter Modalitätsverteilung nach Szenario
    3. Print-Ausgabe der Gesamtverteilung

Input:
- JSON-Interpretationen in /interpretationen/teilnehmer_02 bis _11

Output:
- modalitaets_unklar.csv
- modalitaets_verteilung_pro_szenario.csv
"""

import os
import json
import pandas as pd

# Pfade
base_path = os.path.join("..", "..", "interpretationen")
csv_unklar = "modalitaets_unklar.csv"
csv_verteilung = "modalitaets_verteilung_pro_szenario.csv"
csv_gesamt = "Modalitaetsgewichtung_gesamt.csv"


# Ergebnislisten
all_entries = []
unklar_entries = []

# Teilnehmer 02–11
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
            text_raw = eintrag.get("text", "")
            zeitpunkt = eintrag.get("zeitpunkt", "")

            modal_line = next((line for line in text_raw.split("\n") if "Dominierende Datenquelle" in line), "")
            modal_line_lower = modal_line.lower()

            # Erweiterte Modalitätszuordnung
            bild_keywords = [
                "bild", "blick", "visuell", "sichtbar", "sichtbarkeit", "anzeichen",
                "orientierung", "aufmerksamkeit", "interaktion mit", "infotainmentsystem", "tablet",
                "körperhaltung", "körperliche haltung", "körpersprache", "sitzhaltung", "physischen haltung",
                "position der person", "körperlichen haltung"
            ]

            physio_keywords = [
                "puls", "eda", "physio", "bewegung", "bewegungsrate",
                "handhaltung", "position der hände"
            ]

            has_bild = any(kw in modal_line_lower for kw in bild_keywords)
            has_phys = any(kw in modal_line_lower for kw in physio_keywords)

            if has_bild and has_phys:
                modalitaet = "Beides"
            elif has_bild:
                modalitaet = "Bild"
            elif has_phys:
                modalitaet = "Physiologie"
            else:
                modalitaet = "Unklar"

            eintrag_data = {
                "teilnehmer": f"{tn:02d}",
                "szenario": szenario,
                "zeitpunkt": zeitpunkt,
                "modalitaet": modalitaet,
                "text": modal_line.strip()
            }

            all_entries.append(eintrag_data)

            if modalitaet == "Unklar":
                unklar_entries.append(eintrag_data)

# DataFrames erzeugen
df_all = pd.DataFrame(all_entries)
df_unklar = pd.DataFrame(unklar_entries)

# Speichern
df_unklar.to_csv(csv_unklar, index=False)

# Gruppierte Verteilung erstellen
df_grouped = (
    df_all
    .groupby(["szenario", "modalitaet"])
    .size()
    .reset_index(name="anzahl")
    .sort_values(by=["szenario", "modalitaet"])
)

df_grouped.to_csv(csv_verteilung, index=False)

# Gesamtgewichtung speichern
df_gesamt = df_all[["teilnehmer", "szenario", "zeitpunkt", "modalitaet"]]
df_gesamt.to_csv(csv_gesamt, index=False)
print("✅ Modalitätsgewichtung gesamt gespeichert:", csv_gesamt)


# Ausgabe
print("✅ Unklare Fälle gespeichert:", csv_unklar)
print("✅ Gruppierte Verteilung gespeichert:", csv_verteilung)

print("\n📊 Gesamtverteilung:")
print(df_all["modalitaet"].value_counts())
