import pandas as pd
import numpy as np

# Zufalls-Seed für Reproduzierbarkeit
np.random.seed(42)

# Einlesen der Basisdatei mit bereits zugeordneten Modalitäten
df = pd.read_csv("plausibilitaetsanalyse_basis.csv")

# Leere Liste für Stichproben-Einträge
stichprobe = []

# Kombinationen aus Szenario und Modalität extrahieren
kombis = df[["Szenario", "Modalitaet"]].drop_duplicates()

# Set zur Vermeidung von Duplikaten
bereits_gewaehlt = set()

# Iteration über jede Kombination
for _, row in kombis.iterrows():
    szenario = row["Szenario"]
    modalitaet = row["Modalitaet"]

    # Filtere alle Einträge zur aktuellen Kombination
    teil_df = df[(df["Szenario"] == szenario) & (df["Modalitaet"] == modalitaet)]

    # Teilnehmer dieser Kombination
    teilnehmer = teil_df["Teilnehmer"].unique()
    np.random.shuffle(teilnehmer)

    # Bestimme, wie viele gezogen werden können
    max_tn = 2 if len(teilnehmer) >= 2 else 1

    # Ziehe bis zu 2 Teilnehmer mit je einem zufälligen Eintrag
    count = 0
    for tn in teilnehmer:
        kombi_key = (szenario, modalitaet, tn)
        if kombi_key in bereits_gewaehlt:
            continue

        auswahl = teil_df[teil_df["Teilnehmer"] == tn].sample(n=1)
        stichprobe.append(auswahl)
        bereits_gewaehlt.add(kombi_key)
        count += 1

        if count >= max_tn:
            break

# Ergebnis zusammenführen
df_stichprobe = pd.concat(stichprobe).reset_index(drop=True)
df_stichprobe = df_stichprobe[["Teilnehmer", "Szenario", "Zeitpunkt", "Modalitaet", "Text"]]



# Speichern
df_stichprobe.to_csv("plausibilitaetsanalyse_stichprobe.csv", index=False)
print("✅ Bereinigt gespeichert unter: plausibilitaetsanalyse_stichprobe.csv")
