import os
import base64
import json
import csv
import logging
from datetime import datetime, timedelta
from openai import AzureOpenAI

# -------------------------------------------------------------
# Logging konfigurieren
# -------------------------------------------------------------

logging.basicConfig(
    filename="auswertungslog.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)
# Logging auch in die Konsole ausgeben
logging.getLogger().addHandler(logging.StreamHandler())


# -------------------------------------------------------------
# Azure OpenAI-Client:
# -------------------------------------------------------------
client = AzureOpenAI(
    api_key="",
    api_version="2024-06-01",
    base_url="https://fhgenie-api-iao-vehicleint.openai.azure.com/openai/deployments/gpt-4o-2024-08-06"
)

# -------------------------------------------------------------
# Funktion für Auswertung:
# -------------------------------------------------------------
def auswertung(teilnehmer_id, szenario):
    print(f"\n==== Starte Auswertung für {teilnehmer_id}, {szenario} ====")
    logging.info(f"Starte Auswertung für {teilnehmer_id}, {szenario}")

    json_path = f"../vorverarbeitet/{teilnehmer_id}/{szenario}.json"
    ausgabe_pfad = f"../auswertung/{teilnehmer_id}_{szenario}.csv"
    json_output_path = f"../interpretationen/{teilnehmer_id}/{szenario}.json"
    gesamt_json_path = f"../Gesamtinterpretationen/{teilnehmer_id}/{szenario}.json"
    os.makedirs(os.path.dirname(ausgabe_pfad), exist_ok=True)
    os.makedirs(os.path.dirname(json_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(gesamt_json_path), exist_ok=True)

    try:
        with open(json_path, "r") as f:
            daten = json.load(f)
    except FileNotFoundError:
        print(f"[Übersprungen] Keine Datei gefunden für {teilnehmer_id}, {szenario}")
        logging.warning(f"Datei fehlt: {json_path}")
        return

    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def get_wert_zur_minute(datenliste, zielzeit):
        for eintrag in datenliste:
            if eintrag["timestamp_iso"][:16] == zielzeit.strftime("%Y-%m-%d %H:%M"):
                return eintrag
        return {}

    prompt_einleitung = (
        "Hinweis: Die folgenden Daten stammen aus einem experimentellen Fahrsimulator („Fahrkiste“). "
        "Die Versuchsperson sitzt in einem fest installierten Fahrersitz mit Lenkrad und führt simulierte Fahrszenarien durch. "
        "Die Kamera zeigt das Gesicht, den Oberkörper und das Blickverhalten der Person. "
        "Die Fahrt erfolgt im Modus SAE Level 3 (hochautomatisiert). "
        "Die Fahrzeugführung übernimmt das System, die Person darf sich temporär anderen Tätigkeiten widmen, muss jedoch jederzeit übernahmebereit bleiben, da der Mensch weiterhin die übergeordnete Verantwortung trägt."
    )
    if szenario == "szenario_3":
        prompt_einleitung += " In diesem Abschnitt erfolgt eine manuelle Fahrzeugübernahme durch die Person."

    gesamt_prompt_tokens = 0
    gesamt_completion_tokens = 0
    gesamt_total_tokens = 0
    interpretationen = []

    with open(ausgabe_pfad, mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Sekunde", "Frage", "Antwort"])
        startzeit = datetime.strptime(daten["start"], "%Y-%m-%d %H:%M:%S")

        for i, bildname in enumerate(daten["screenshots"]):
            sekunde = i * 10
            bildzeit = startzeit + timedelta(seconds=sekunde)
            minute = bildzeit.replace(second=0)
            zeitpunkt_str = str(timedelta(seconds=sekunde)).rjust(8, "0")

            bildpfad = os.path.join("..", bildname)
            base64_image = encode_image(bildpfad)

            pulse = get_wert_zur_minute(daten["pulse_rate"], minute)
            eda = get_wert_zur_minute(daten["eda"], minute)
            prv = get_wert_zur_minute(daten["prv_rmssd_ms"], minute)
            acc = get_wert_zur_minute(daten["accelerometer_std_g"], minute)

            frage = f"""
            {prompt_einleitung}

            Bildzeitpunkt: {bildzeit.strftime('%Y-%m-%d %H:%M:%S')}
            Physiologische Werte:
            - Puls: {pulse.get('pulse_rate_bpm', 'n/a')} bpm
            - EDA: {eda.get('eda_scl_usiemens', 'n/a')} µS
            - RMSSD: {prv.get('prv_rmssd_ms', 'n/a')} ms
            - Bewegung: {acc.get('accelerometers_std_g', 'n/a')} g

            Du erhältst ein Bild und physiologische Daten (Puls, EDA, RMSSD, Bewegung) und sollst den Zustand der Person bewerten – ausschließlich in Bezug auf:

            - Stress
            - Entspannung
            - Ablenkung

            Für jede Kategorie gib bitte eine von drei Stufen an: **niedrig**, **mittel** oder **hoch**. Gib zusätzlich je einen Satz Begründung auf Basis des Bildes und
            der physiologischen Werte.

            Wichtig:
            - Falls eine Datenquelle (Bild oder Physiologie) die Einschätzung besonders beeinflusst hat, gib dies am Ende explizit an.

            Beispielhafte Antwortstruktur:

            Stress: mittel – Der Puls ist leicht erhöht, die Mimik angespannt.  
            Entspannung: niedrig – Körperhaltung wirkt angespannt.  
            Ablenkung: hoch – Der Blick richtet sich deutlich auf das Infotainmentsystem.  
            Dominierende Datenquelle: Die Einschätzung basiert hauptsächlich auf der Pulsrate, da diese deutlich erhöht ist.
            """

            response = client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": frage.strip()},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ],
                    }
                ],
                max_tokens=600
            )

            antwort = response.choices[0].message.content
            writer.writerow([sekunde, frage.strip(), antwort])
            interpretationen.append({"zeitpunkt": zeitpunkt_str, "text": antwort.strip()})

            usage = response.usage
            if usage:
                gesamt_prompt_tokens += usage.prompt_tokens
                gesamt_completion_tokens += usage.completion_tokens
                gesamt_total_tokens += usage.total_tokens

    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(interpretationen, f, indent=2, ensure_ascii=False)

    zusammenfassung_prompt = """Die folgenden Einschätzungen stammen aus einem experimentellen Fahrsimulator („Fahrkiste“)...\n"""
    for eintrag in interpretationen:
        zusammenfassung_prompt += f"{eintrag['zeitpunkt']}: {eintrag['text']}\n"
    zusammenfassung_prompt += """
    Bitte fasse den Gesamtzustand der Person über das gesamte Szenario hinweg zusammen.

    Gehe dabei strukturiert auf jede der drei Kategorien ein:
    - Gib für jede Kategorie eine Einschätzung: **niedrig**, **mittel** oder **hoch**
    - Begründe die Einschätzung jeweils mit einem kurzen Satz basierend auf typischen Mustern aus den Einzelbewertungen

    Verwende diese Antwortstruktur:

    Stress: [niedrig/mittel/hoch] – z.\u200bB. „Die meisten Bewertungen zeigten eine erhöhte Pulsrate und angespannte Mimik.“  
    Entspannung: [niedrig/mittel/hoch] – z.\u200bB. „Die Körperhaltung wirkte überwiegend angespannt.“  
    Ablenkung: [niedrig/mittel/hoch] – z.\u200bB. „In mehreren Momenten war der Blick nicht auf den Fahrkontext gerichtet.“

    Formuliere zum Abschluss **einen Satz**, der den erkannten Gesamtkontext des Fahrers beschreibt.
    """

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[{"role": "user", "content": zusammenfassung_prompt.strip()}],
        max_tokens=800
    )

    antwort = response.choices[0].message.content
    with open(ausgabe_pfad, mode="a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["GESAMT", zusammenfassung_prompt.strip(), antwort])

    with open(gesamt_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "teilnehmer": teilnehmer_id,
            "szenario": szenario,
            "gesamtinterpretation": antwort.strip()
        }, f, indent=2, ensure_ascii=False)

    usage = response.usage
    if usage:
        gesamt_prompt_tokens += usage.prompt_tokens
        gesamt_completion_tokens += usage.completion_tokens
        gesamt_total_tokens += usage.total_tokens

    logging.info(f"Fertig: {teilnehmer_id}, {szenario} – Tokens total: {gesamt_total_tokens}")

# -------------------------------------------------------------
# Schleife für alle Teilnehmer und Szenarien
# -------------------------------------------------------------
szenarien = ["szenario_1", "Musikintervention", "szenario_2", "szenario_3"]
teilnehmer_ids = [f"teilnehmer_{str(i).zfill(2)}" for i in range(1, 2)]

for teilnehmer_id in teilnehmer_ids:
    for szenario in szenarien:
        auswertung(teilnehmer_id, szenario)
