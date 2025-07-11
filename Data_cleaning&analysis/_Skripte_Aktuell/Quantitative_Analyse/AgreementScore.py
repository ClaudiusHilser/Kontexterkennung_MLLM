import pandas as pd

# Dateien laden
fragebogen = pd.read_csv("fragebogen_kategorisiert.csv")
modell = pd.read_csv("gesamtinterpretation_übersicht.csv")

modell = modell[modell["Teilnehmer"] != "teilnehmer_01"]
fragebogen = fragebogen[fragebogen["teilnehmer"] != "teilnehmer_01"]


# Fragebogendaten auf langes Format bringen
fragebogen_melted = pd.melt(
    fragebogen,
    id_vars=["teilnehmer"],
    var_name="szenario",
    value_name="Fragebogen"
)

# Szenarionamen vereinheitlichen
fragebogen_melted["szenario"] = (
    fragebogen_melted["szenario"]
    .str.replace("szenario_1_stress", "szenario_1")
    .str.replace("szenario_2_ablenkung", "szenario_2")
    .str.replace("szenario_3_stress", "szenario_3")
    .str.replace("Musikintervention_entspannung", "Musikintervention")
)

# Kategorie zuordnen
fragebogen_melted["Kategorie"] = fragebogen_melted["szenario"].apply(lambda x: (
    "Stress" if "szenario_1" in x or "szenario_3" in x else
    "Entspannung" if "Musikintervention" in x else
    "Ablenkung"
))

fragebogen_melted["Szenario"] = fragebogen_melted["szenario"].str.replace("_stress|_ablenkung|_entspannung", "")
fragebogen_melted.rename(columns={"teilnehmer": "Teilnehmer"}, inplace=True)

# Modell auch auf langes Format bringen
modell_melted = pd.melt(
    modell,
    id_vars=["Teilnehmer", "Szenario"],
    var_name="Kategorie",
    value_name="Modell"
)

# Merge
merged = pd.merge(modell_melted, fragebogen_melted, on=["Teilnehmer", "Szenario", "Kategorie"], how="inner")

# Agreement berechnen
merged["Treffer"] = merged["Modell"] == merged["Fragebogen"]

# Ergebnis aggregieren
agreement_summary = merged.groupby(["Szenario", "Kategorie"])["Treffer"].agg(["sum", "count"])
agreement_summary["Agreement_Score"] = (agreement_summary["sum"] / agreement_summary["count"]).round(2)

# Ergebnis anzeigen
print(agreement_summary)

# als CSV speichern
agreement_summary.to_csv("agreement_score_auswertung.csv", encoding="utf-8")
merged.to_csv("agreement_merged_daten.csv", index=False)


