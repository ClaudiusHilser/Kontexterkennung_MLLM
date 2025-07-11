import os
import pandas as pd

# Verzeichnis mit den Fragebogendateien
fragebogen_ordner = "../../fragebogen"

# Leeres DataFrame zur Sammlung aller Einträge
fragebogen_df = pd.DataFrame()

# Bewertungsskala definieren
def skala_umrechnen(wert):
    try:
        w = int(wert)
        if w in [1, 2]:
            return "niedrig"
        elif w == 3:
            return "mittel"
        elif w in [4, 5]:
            return "hoch"
    except:
        return "n/a"

# Alle CSV-Dateien im Ordner durchgehen
for datei in os.listdir(fragebogen_ordner):
    if not datei.endswith(".csv"):
        continue

    pfad = os.path.join(fragebogen_ordner, datei)
    df = pd.read_csv(pfad).set_index("step")["value"]

    teilnehmer = datei.replace("fra_teilnehmer", "").replace(".csv", "").zfill(2)
    teilnehmer_id = f"teilnehmer_{teilnehmer}"

    # Stresslevel-Einträge extrahieren
    stresslevel_werte = df[df.index == "Stresslevel"].values
    szenario_1_stress = skala_umrechnen(stresslevel_werte[0]) if len(stresslevel_werte) >= 1 else "n/a"
    szenario_3_stress = skala_umrechnen(stresslevel_werte[-1]) if len(stresslevel_werte) >= 2 else "n/a"

    # Weitere Werte zuordnen
    musik_entspannung = skala_umrechnen(df.get("Entspannung1", "n/a"))
    szenario_2_ablenkung = skala_umrechnen(df.get("Ablenkung", "n/a"))

    fragebogen_df = pd.concat([fragebogen_df, pd.DataFrame([{
        "teilnehmer": teilnehmer_id,
        "szenario_1_stress": szenario_1_stress,
        "Musikintervention_entspannung": musik_entspannung,
        "szenario_2_ablenkung": szenario_2_ablenkung,
        "szenario_3_stress": szenario_3_stress
    }])], ignore_index=True)

# Ausgabe anzeigen
print(fragebogen_df)

# Ausgabe speichern
fragebogen_df.to_csv("fragebogen_kategorisiert.csv", index=False)

