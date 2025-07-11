import matplotlib.pyplot as plt

# Werte (hardcoded)
kriterien = ["Konsistenz", "Nachvollziehbarkeit", "Logik"]
ja_werte = [18, 17, 13]
nein_werte = [6, 7, 11]

# Farben (Pastell)
farben = {"Ja": "#A2D8B0", "Nein": "#F59791"}

x = range(len(kriterien))
bar_width = 0.5

fig, ax = plt.subplots(figsize=(8, 5))

# Balken
p1 = ax.bar(x, ja_werte, bar_width, label="Ja", color=farben["Ja"])
p2 = ax.bar(x, nein_werte, bar_width, bottom=ja_werte, label="Nein", color=farben["Nein"])

# Balkenbeschriftung
for bars in [p1, p2]:
    for bar in bars:
        hoehe = bar.get_height()
        if hoehe > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_y() + hoehe / 2,
                str(int(hoehe)),
                ha="center",
                va="center",
                color="black",
                fontsize=9
            )

# Achsenbeschriftung & Layout
ax.set_xticks(x)
ax.set_xticklabels(kriterien)
ax.set_ylabel("Anzahl")
ax.set_xlabel("Kriterien", labelpad=15)
ax.set_ylim(0, 30)
ax.legend(title="Bewertung", loc="upper right")

plt.tight_layout()
plt.savefig("plausibilitaetsanalyse.png", dpi=300)
plt.show()
