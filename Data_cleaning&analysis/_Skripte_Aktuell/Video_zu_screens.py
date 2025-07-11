import os
import subprocess

# Teilnehmer-Ordner angeben (nur Ordnername)
teilnehmer_ordner = "teilnehmer_11"

# Szenariennamen (Ordner und Dateinamen müssen exakt so heißen)
szenarien = ["szenario_1", "musikintervention", "szenario_2", "szenario_3"]

# Intervall für Screenshots (Sekunden)
intervall = 10
qualitaet = "3"  # ffmpeg-Qualität (5 = ca. 30–50 KB)

# Basisverzeichnis (z. B. dort wo du das Skript speicherst)
basis_pfad = os.path.abspath(teilnehmer_ordner)
video_ordner = os.path.join(basis_pfad, "videos")

for szenario in szenarien:
    video_datei = f"{teilnehmer_ordner}_{szenario}.mov"
    video_pfad = os.path.join(video_ordner, video_datei)

    screenshots_ordner = os.path.join(basis_pfad, szenario, "screenshots")
    os.makedirs(screenshots_ordner, exist_ok=True)

    # Vorhandene Screenshots löschen mit Rückmeldung
    bilder_vorher = [f for f in os.listdir(screenshots_ordner) if f.endswith(".jpg") or f.endswith(".png")]
    if bilder_vorher:
        for file in bilder_vorher:
            os.remove(os.path.join(screenshots_ordner, file))
        print(f"🗑️  {len(bilder_vorher)} alte Screenshots in '{szenario}' gelöscht.")
    else:
        print(f"📂 Ordner '{szenario}' war bereits leer.")

    print(f"🎞️  Verarbeite Video: {video_pfad}")

    # Screenshot-Basename
    basename = f"{teilnehmer_ordner}_{szenario}"

    # ffmpeg-Befehl
    ffmpeg_command = [
        "ffmpeg",
        "-i", video_pfad,
        "-vf", f"fps=1/{intervall},scale=iw/2:-1",
        "-qscale:v", qualitaet,
        os.path.join(screenshots_ordner, f"{basename}_%04d.jpg")
    ]

    result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print(f"❌ Fehler bei {szenario}:")
        print(result.stderr[:500])
    else:
        print(f"✅ {szenario} abgeschlossen.")

print("\n📷 Fertig! Alle Screenshots wurden erzeugt.")
