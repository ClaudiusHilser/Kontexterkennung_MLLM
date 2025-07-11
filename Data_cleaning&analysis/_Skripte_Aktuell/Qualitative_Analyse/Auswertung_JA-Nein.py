import os
import pandas as pd
import matplotlib.pyplot as plt

# Pfade
basis_pfad = os.path.join("..", "..", "fragebogen")
teilnehmer_ids = [f"fra_teilnehmer{i}.csv" for i in range(2, 12)]

# Ziel-Fragen
fragen = [
    "Popup5_Entspannung2",
    "Popup7_Warnungswunsch",
    "Popup8_StehendesFahrzeug",
    "Vorbereitung"
]

# Initialisierung
antworten = {frage: {"Ja": 0, "Nein": 0} for frage in fragen}

# Daten einlesen und zählen
for datei in teilnehmer_ids:
    pfad = os.path.join(basis_pfad, datei)
    if not os.path.exists(pfad):
        continue
    df = pd.read_csv(pfad)
    df = df.set_index("step")  # Schritt als Index

    for frage in fragen:
        if frage in df.index:
            wert = str(df.loc[frage, "value"]).strip()
            if wert in antworten[frage]:
                antworten[frage][wert] += 1

# Diagrammdaten vorbereiten
labels = ["Musik = Entspannung", "Warnung bei Ablenkung", "Pannenfahrzeug erkannt", "Vorbereitung ausreichend"]
ja_werte = [antworten[f]["Ja"] for f in fragen]
nein_werte = [antworten[f]["Nein"] for f in fragen]

x = range(len(fragen))
bar_width = 0.5

# Farben
farben = {"Ja": "#A2D8B0", "Nein": "#F59791"}

# Plot
fig, ax = plt.subplots(figsize=(10, 6))

p1 = ax.bar(x, ja_werte, bar_width, label='Ja', color=farben["Ja"])
p2 = ax.bar(x, nein_werte, bar_width, bottom=ja_werte, label='Nein', color=farben["Nein"])

# Balkenbeschriftung
for bars in [p1, p2]:
    for bar in bars:
        hoehe = bar.get_height()
        if hoehe > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_y() + hoehe / 2,
                str(int(hoehe)),
                ha='center',
                va='center',
                color='black',
                fontsize=9
            )

# Achsen und Layout
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=0, ha="center")
ax.set_ylabel("Anzahl")
ax.set_xlabel("Fragen")
ax.set_ylim(0, 11)
ax.legend(title="Antworten", loc="upper right")  # Legende oben rechts
# Kein Titel

plt.tight_layout()
plt.savefig("fragebogen_auswertung.png", dpi=300)
plt.show()

