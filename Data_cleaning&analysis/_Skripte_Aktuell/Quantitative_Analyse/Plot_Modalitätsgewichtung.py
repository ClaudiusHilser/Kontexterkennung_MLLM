import pandas as pd
import matplotlib.pyplot as plt

# CSV laden
df = pd.read_csv("modalitaets_verteilung_pro_szenario.csv")

# Pivotieren für gestapelten Balken
pivot_df = df.pivot(index="szenario", columns="modalitaet", values="anzahl").fillna(0)

# Gewünschte Reihenfolge: Beides ganz oben
pivot_df = pivot_df[["Physiologie", "Bild", "Beides"]]

# Farben automatisch
colors = {
    "Physiologie": "#89B4F8",
    "Bild": "#FFBC8B",
    "Beides": "#88DFC5",
}

# Plot
ax = pivot_df.plot(
    kind="bar",
    stacked=True,
    figsize=(10, 6),
    color=[colors[col] for col in pivot_df.columns]
)


# Werte in Balken schreiben
for i, szenario in enumerate(pivot_df.index):
    bottom = 0
    for modalitaet in ["Physiologie", "Bild", "Beides"]:
        value = pivot_df.loc[szenario, modalitaet]
        if value > 0:
            ax.text(
                i,
                bottom + value / 2,
                int(value),
                ha="center", va="center",
                fontsize=9,
                color="white"
            )
            bottom += value

# Achsen & Titel
plt.ylabel("Anzahl")
plt.xlabel("Szenarien")
plt.xticks(rotation=0)
ax.legend(title="Legende", loc="upper right", bbox_to_anchor=(1, 1))

plt.tight_layout()
plt.savefig("Plots/modalitaetsverteilung_szenario_balken_beschriftet.png")
plt.show()
