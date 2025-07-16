import os
import pandas as pd
import matplotlib.pyplot as plt

# Pfade und Teilnehmer
basis_pfad = os.path.join("..", "..", "fragebogen")
teilnehmer_ids = [f"fra_teilnehmer{i}.csv" for i in range(2, 12)]

# Initialisierung: Werte von 1 bis 5 zählen
kontroll_counts = {str(i): 0 for i in range(1, 6)}

# Daten einlesen
for datei in teilnehmer_ids:
    pfad = os.path.join(basis_pfad, datei)
    if not os.path.exists(pfad):
        continue
    df = pd.read_csv(pfad)
    df = df.set_index("step")

    if "Kontrollgefühl" in df.index:
        wert = str(df.loc["Kontrollgefühl", "value"]).strip()
        if wert in kontroll_counts:
            kontroll_counts[wert] += 1



import matplotlib.pyplot as plt

# Kontrollgefühl-Werte
werte = [0, 1, 2, 5, 2]

# Bedeutung der Skalenwerte
labels = [
    "1 – sehr unsicher",
    "2 – unsicher",
    "3 – neutral",
    "4 – sicher",
    "5 – sehr sicher"
]

# Farbstufen
farben = ["#F1948A", "#F8C471", "#F9E79F", "#7DCEA0", "#45B39D"]

fig, ax = plt.subplots(figsize=(6, 6))

wedges, _, autotexts = ax.pie(
    werte,
    labels=[""] * len(werte),
    colors=farben,
    startangle=90,
    autopct=lambda pct: f"{int(round(pct * sum(werte) / 100.0))}" if pct > 0 else "",
    textprops={'fontsize': 10, 'color': 'black'}
)

ax.legend(wedges, labels, title="Legende", loc="upper right", bbox_to_anchor=(1, 1))

plt.tight_layout()
plt.savefig("kontrollgefuehl_kreisdiagramm_lesbar.png", dpi=300)
plt.show()
