import pandas as pd
import matplotlib.pyplot as plt

# CSV laden
df = pd.read_csv("frequenzverteilungen_modell.csv")

# Farben (Pastell)
farben = {"niedrig": "#A8D5BA", "mittel": "#FFE291", "hoch": "#F5A490"}

# Gruppierung: Plot 1 = Musikintervention + Szenario 1, Plot 2 = Szenario 2 + Szenario 3
gruppe1 = df[df["Szenario"].str.startswith(("Musikintervention", "szenario_1"))]
gruppe2 = df[df["Szenario"].str.startswith(("szenario_2", "szenario_3"))]

def plot_gruppe(df_subset, dateiname):
    x_labels = [f"{row['Szenario']}\n{row['Kategorie']}" for _, row in df_subset.iterrows()]
    x = range(len(x_labels))
    bottom = [0] * len(x)

    fig, ax = plt.subplots(figsize=(10, 6))

    for ausprägung in ["niedrig", "mittel", "hoch"]:
        werte = df_subset[ausprägung].values
        bars = ax.bar(x, werte, bottom=bottom, color=farben[ausprägung], edgecolor="none", label=ausprägung)

        for i, bar in enumerate(bars):
            if werte[i] > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bottom[i] + werte[i] / 2,
                    str(werte[i]),
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=9
                )
        bottom = [bottom[i] + werte[i] for i in range(len(werte))]

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, rotation=0, ha="center")
    ax.set_ylabel("Anzahl")
    ax.set_xlabel("Szenarien", labelpad=15)

    ax.legend(title="Legende", loc="upper right", bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.savefig(dateiname, dpi=300)
    plt.show()

# Plots
plot_gruppe(gruppe1, "Plots/frequenz_gruppe1.png")
plot_gruppe(gruppe2, "Plots/frequenz_gruppe2.png")
