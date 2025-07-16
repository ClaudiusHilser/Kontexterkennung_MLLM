import pandas as pd

# Datei laden
df = pd.read_csv("gesamtinterpretation_übersicht.csv")

# Teilnehmer 1 ausschließen
df = df[df["Teilnehmer"] != "teilnehmer_01"]

# In langes Format transformieren
df_melted = pd.melt(
    df,
    id_vars=["Teilnehmer", "Szenario"],
    value_vars=["Stress", "Entspannung", "Ablenkung"],
    var_name="Kategorie",
    value_name="Ausprägung"
)

# Nur gültige Werte verwenden
df_melted = df_melted[df_melted["Ausprägung"].isin(["niedrig", "mittel", "hoch"])]

# Häufigkeit pro Szenario und Kategorie zählen
frequenzen = (
    df_melted
    .groupby(["Szenario", "Kategorie"])["Ausprägung"]
    .value_counts()
    .unstack(fill_value=0)
    .reset_index()
)

# Ergebnis anzeigen
print(frequenzen)

# als CSV speichern
frequenzen.to_csv("frequenzverteilungen_modell.csv", index=False, encoding="utf-8")
