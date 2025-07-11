import os
import json
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Funktionen
def runde_start(t):
    return t.replace(second=0, microsecond=0)

def runde_ende(t):
    basis = t.replace(second=0, microsecond=0)
    if t.second >= 40:
        return basis + timedelta(minutes=1)
    else:
        return basis

def lade_und_filter(csv_path, zeitspalte, wertspalte, start_utc, end_utc):
    df = pd.read_csv(csv_path)
    df = df[df[wertspalte].notna()]
    df[zeitspalte] = pd.to_datetime(df[zeitspalte], utc=True, errors='coerce')
    df = df[(df[zeitspalte] >= start_utc) & (df[zeitspalte] <= end_utc)]
    df = df[[zeitspalte, wertspalte]].dropna()
    df[zeitspalte] = df[zeitspalte].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df

def verarbeite_teilnehmer(teilnehmer_id):
    basis = f"../{teilnehmer_id}"
    empatica = os.path.join(basis, "empatica")
    output_dir = f"../vorverarbeitet/{teilnehmer_id}"
    os.makedirs(output_dir, exist_ok=True)

    szenarien = ["szenario_1", "szenario_2", "szenario_3", "Musikintervention"]

    for szenario in szenarien:
        try:
            pfad = os.path.join(basis, szenario)
            with open(os.path.join(pfad, "timestamps.txt"), "r") as f:
                zeilen = f.readlines()

            start_str = zeilen[0].split("start:")[1].strip()
            end_str = zeilen[1].split("end:")[1].strip()

            # -2h Korrektur und auf UTC setzen
            start_local = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            end_local = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
            start_utc = runde_start(start_local - timedelta(hours=2)).replace(tzinfo=pytz.utc)
            end_utc = runde_ende(end_local - timedelta(hours=2)).replace(tzinfo=pytz.utc)

            eda = lade_und_filter(os.path.join(empatica, [f for f in os.listdir(empatica) if "eda" in f][0]), "timestamp_iso", "eda_scl_usiemens", start_utc, end_utc)
            pulse = lade_und_filter(os.path.join(empatica, [f for f in os.listdir(empatica) if "pulse-rate" in f][0]), "timestamp_iso", "pulse_rate_bpm", start_utc, end_utc)
            prv = lade_und_filter(os.path.join(empatica, [f for f in os.listdir(empatica) if "prv" in f][0]), "timestamp_iso", "prv_rmssd_ms", start_utc, end_utc)
            acc = lade_und_filter(os.path.join(empatica, [f for f in os.listdir(empatica) if "accelerometers-std" in f][0]), "timestamp_iso", "accelerometers_std_g", start_utc, end_utc)

            bildordner = os.path.join(pfad, "screenshots")
            bilder = sorted([
                os.path.join(teilnehmer_id, szenario, "screenshots", f)
                for f in os.listdir(bildordner) if f.endswith(".jpg")
            ])

            result = {
                "teilnehmer": teilnehmer_id,
                "szenario": szenario,
                "start": start_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "end": end_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "pulse_rate": pulse.to_dict(orient="records"),
                "eda": eda.to_dict(orient="records"),
                "prv_rmssd_ms": prv.to_dict(orient="records"),
                "accelerometer_std_g": acc.to_dict(orient="records"),
                "screenshots": bilder
            }

            json_path = os.path.join(output_dir, f"{szenario}.json")
            with open(json_path, "w") as f:
                json.dump(result, f, indent=2)

            print(f"✅ {teilnehmer_id} - {szenario} verarbeitet ({len(bilder)} Bilder, {len(pulse)} Pulse-Werte)")
            for eintrag in pulse.to_dict(orient="records")[:3]:
                print(f"{eintrag['timestamp_iso']} → {eintrag['pulse_rate_bpm']} bpm")

        except Exception as e:
            print(f"❌ Fehler bei {teilnehmer_id} - {szenario}: {e}")

# Starte für teilnehmer_01 bis teilnehmer_11
for i in range(1, 12):
    teilnehmer_id = f"teilnehmer_{i:02d}"
    verarbeite_teilnehmer(teilnehmer_id)
