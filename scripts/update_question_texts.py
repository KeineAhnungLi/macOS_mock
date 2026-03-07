import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "questions.json"


GROUP_UPDATES = {
    2019: {
        "2019-w-a": {
            "instruction": "Ergänzen Sie das passende Wort im Funktionsverbgefüge!",
        },
        "2019-w-b": {
            "instruction": "Was ist richtig?",
        },
        "2019-w-c": {
            "instruction": "Bilden Sie die jeweils richtige Redewendung!",
        },
        "2019-w-d": {
            "instruction": "Entscheiden Sie, welches Wort in die jeweilige Lücke passt!",
            "shared_context": """Im kleinen Staat Bhutan, eingeklemmt im Himalaya zwischen China und Indien, (46) _____ der König das Glück der Bewohner schon vor langer Zeit zum Staatsziel und ordnete (47) _____, weniger nach Wachstum und mehr nach Lebensqualität zu (48) _____. So weit ist man in Deutschland noch nicht, doch auch hierzulande sollen Lebensqualität und Fortschritt künftig nicht mehr, wie weltweit bisher üblich, (49) _____ von Wirtschaftsdaten wie dem Bruttoinlandsprodukt (BIP) gemessen werden. Denn was keinen Marktwert hat, (50) _____ dabei außen vor, wie beispielsweise Umweltschäden oder das subjektive Wohlbefinden der Menschen. Bei Wissenschaftlern sowie Politikern (51) _____ mittlerweile weitgehend Einigkeit, dass ein unbegrenzt (52) _____ Wachstum von Wirtschaft und Wohlstand nach den heute (53) _____ Maßstäben in absehbarer Zeit die Lebensgrundlagen der Menschheit gefährden wird. Es geht also um die existentielle Frage, wie Wohlstand weltweit (54) _____ kann, ohne dass dabei die Ressourcen und die (55) _____ des Lebensraums unserer Erde überstrapaziert werden. Glück und Lebensqualität als Maßstab für gutes Wachstum gilt dabei als zukunftsweisend.""",
        },
        "2019-g-a": {
            "instruction": "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?",
        },
        "2019-g-b": {
            "instruction": "Formen Sie bitte die markierten Linksattribute in Relativsätze um!",
        },
        "2019-g-c": {
            "instruction": "Verbinden Sie bitte die folgenden zwei Sätze!",
        },
        "2019-g-d": {
            "instruction": "Formulieren Sie bitte den jeweils unterstrichenen Satzteil zu einem Nebensatz um!",
        },
        "2019-g-e": {
            "instruction": "Wählen Sie die jeweils passende Umformung!",
        },
        "2019-g-f": {
            "instruction": "Formen Sie bitte den Satz ins Passiv um!",
        },
        "2019-g-g": {
            "instruction": "Welche Lösung enthält eine korrekte Form für die indirekte Rede?",
        },
        "2019-g-h": {
            "instruction": "Füllen Sie bitte die Lücken aus!",
        },
    },
    2021: {
        "2021-w-a": {
            "instruction": "Was ist richtig?",
        },
        "2021-w-b": {
            "instruction": "Ergänzen Sie das passende Verb!",
        },
        "2021-w-c": {
            "instruction": "Ergänzen Sie den fehlenden Ausdruck in den Redewendungen!",
        },
        "2021-w-d": {
            "instruction": "Setzen Sie die angegebenen Wörter sinnvoll in den Text ein!",
            "shared_context": """Goethe und Schiller (46) _____ ihre Freundschaft als ein seltenes, wunderliches Gewächs an, als ein Glück, als ein Geschenk. Es kam ihnen (47) _____ vor, was ihnen da gelungen oder zugestoßen war, und sie gerieten in dankbares (48) _____ darüber. Als Schiller starb, wusste Goethe, dass für ihn eine (49) _____ seines Lebens zu Ende ging. So (50) _____ war das Verhältnis der beiden geworden, dass Goethe nach Schillers Tod bekannte: „Ich dachte, mich selbst zu verlieren, und verliere nun einen Freund und in demselben die Hälfte meines (51) _____.“ Goethe nannte die Freundschaft ein „glückliches Ereignis“. Ein solches (52) _____ es für uns auch heute noch, denn man wird in der Geschichte des Geistes lange suchen müssen, um etwas (53) _____ zu finden - dass zwei (54) _____ Menschen höchsten Ranges sich über Gegensätze hinweg verbinden zu wechselseitiger (55) _____ und sogar zu gemeinsamem Werk.""",
        },
        "2021-g-a": {
            "instruction": "Welche Lösung enthält die passende Ersatzform des unterstrichenen Satzteils?",
        },
        "2021-g-b": {
            "instruction": "Formen Sie bitte die markierten Linksattribute in Relativsätze um!",
        },
        "2021-g-c": {
            "instruction": "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?",
        },
        "2021-g-d": {
            "instruction": "Welche Umwandlung trifft zu?",
        },
        "2021-g-e": {
            "instruction": "Bilden Sie Sätze mit Konjunktionen!",
        },
        "2021-g-f": {
            "instruction": "Formen Sie den folgenden Satz ins Passiv um!",
        },
        "2021-g-g": {
            "instruction": "Welche Lösung enthält eine korrekte Form für die indirekte Rede?",
        },
        "2021-g-h": {
            "instruction": "Füllen Sie die Lücken!",
        },
    },
    2022: {
        "2022-w-a": {
            "instruction": "Ergänzen Sie das passende Nomen!",
        },
        "2022-w-b": {
            "instruction": "Ergänzen Sie das passende Verb!",
        },
        "2022-w-c": {
            "instruction": "Ergänzen Sie das Fehlende in den Redewendungen!",
        },
        "2022-w-d": {
            "instruction": "Setzen Sie die angegebenen Wörter sinnvoll in den Text ein!",
            "shared_context": """Um die (46) _____ befand sich das Römische Reich noch auf dem Gipfel seiner Macht. Seine Grenzen waren durch die Überwältigung vieler Völker zu einem Weltreich (47) _____ worden, aber Germanien stand nicht vollständig unter römischer Kontrolle. Auch die Eroberung des sog. freien Germaniens schien nur noch eine (48) _____ der Zeit zu sein. Denn die militärisch bestens (49) _____ Armeen der Römer waren nach erfolgreichen Feldzügen im heutigen Süddeutschland bis zur Elbe weit ins Innere Germaniens (50) _____. Der Kommandeur des römischen Heeres in Germanien, Publius Quinctilius Varus, (51) _____ so, als wären die Gebiete zwischen Rhein und Elbe schon eine römische Provinz. Im Jahre 9 n. Chr. gab es (52) _____ Streitigkeiten zwischen germanischen Stämmen westlich des Rheins, weshalb Varus zu einer militärischen Strafexpedition ins Quellgebiet der Flüsse Lippe und Ems, Siedlungsgebiet des germanischen Stammes der Cherusker, marschierte. Dort schlug Varus sein Lager (53) _____, (54) _____ zunächst die verfeindeten Germanen, gründete neue Siedlungen, zog Steuern ein und hielt Gerichtstage ab; er verhielt sich also so, als ob er der Herr im (55) _____ wäre.""",
        },
        "2022-g-a": {
            "instruction": "Welche Präposition passt?",
        },
        "2022-g-b": {
            "instruction": "Welche Umformulierung passt?",
        },
        "2022-g-c": {
            "instruction": "Setzen Sie passende Pronominaladverbien mit wo- ein!",
        },
        "2022-g-d": {
            "instruction": "Ergänzen Sie das richtige Partizip II!",
        },
        "2022-g-e": {
            "instruction": "Setzen Sie die passenden Endungen ein!",
        },
        "2022-g-f": {
            "instruction": "Welcher Nebensatz entspricht der Bedeutung der unterstrichenen Nominalisierung?",
        },
        "2022-g-g": {
            "instruction": "Direkte Rede in indirekte Rede umwandeln: Welche Form ist richtig?",
        },
        "2022-g-h": {
            "instruction": "Welche Umschreibung gibt den Inhalt des dass-Satzes wieder?",
        },
    },
}


STEM_UPDATES = {
    2019: {
        31: "Der Facharbeiter nahm die Maschine nach der Reparatur wieder in _____.",
        32: "Die Regierung _____ Maßnahmen, um die Inflation zu stoppen.",
        33: "Der Mitarbeiter sagt: „Ich stehe Ihnen jederzeit gerne zur _____.“",
        34: "Die Straßenkünstlerin _____ mit ihrer Vorstellung alle Aufmerksamkeit der Passanten auf sich.",
        35: "Man muss die Theorie in die Tat _____.",
        36: "In der frisch umgegrabenen Erde _____ es von Insekten.",
        37: "Unter _____ aller Kräfte gelang es ihm, das Kind zu retten.",
        38: "Viele Syrer _____ illegal die Grenze, um vor der Kriegskatastrophe nach Europa zu fliehen.",
        39: "Im Bürgerkrieg seines Heimatlandes wurde die gesamte Familie des Flüchtlings _____.",
        40: "Viele _____ ihn um seinen Reichtum.",
        41: "Von _____ an lernte Mozart bereits Klavier spielen.",
        42: "Viele Jugendliche haben heutzutage keinen _____ auf die Politik.",
        43: "Die alte Frau hatte sich von einem Betrüger übers _____ hauen lassen.",
        44: "Der Bewerber war mit Pauken und _____ in der Prüfung durchgefallen.",
        45: "Sie ist schon dreißig und hat es eilig, unter die _____ zu kommen.",
        46: "Lücke (46)",
        47: "Lücke (47)",
        48: "Lücke (48)",
        49: "Lücke (49)",
        50: "Lücke (50)",
        51: "Lücke (51)",
        52: "Lücke (52)",
        53: "Lücke (53)",
        54: "Lücke (54)",
        55: "Lücke (55)",
        56: "Er kann bereits einen Ausweg gefunden haben.",
        57: "Die Polizei musste eingesetzt werden, sonst hätte es Tote gegeben.",
        58: "Zu meinem Erstaunen wurden die Bilder von Monet nicht ausgestellt.",
        59: "Die von dem Vorstandsvorsitzenden signalisierte Gesprächsbereitschaft wurde leider nicht ernst genommen.",
        60: "Unterdessen wurde der bei Fulda mit einer Schafherde zusammengeprallte ICE aus dem Tunnel geborgen.",
        61: "Ich konnte deine Gedanken nicht lesen. Deshalb habe ich dich nicht gut verstanden.",
        62: "Im Falle einer humanitären Katastrophe ist Deutschland bereit, sein Engagement zu verstärken.",
        63: "Erst nach dem Erledigen der Hausaufgaben darf das Kind mit seinen Freunden draußen spielen.",
        64: "Zu einer Großoffensive könnte es kommen. Die Folge dieser Offensive würde alles bisher Geschehene in Syrien in den Schatten stellen.",
        65: "Vor zehn Jahren ging die Investmentbank Lehman Brothers bankrott. Infolgedessen brach weltweit die Kreditversorgung zusammen.",
        66: "Es besteht kein Zweifel, dass ein Gefängnisausbruch unter Strafe steht.",
        67: "Der Mitarbeiter sagt: „Wegen des schlechten Wetters konnte ich nicht kommen.“\nDer Mitarbeiter sagt, _____.",
        68: "Vieles von dem, was _____ begegnet, ist eine Resonanz auf das, was man aussendet.",
        69: "Die Kindergärtnerin sagt zu den Kindern: „_____ euch die Hände!“",
        70: "Der Erfolg dieser Maßnahme _____.",
    },
    2021: {
        31: "Der Vortrag des Gastprofessors war sehr _____, die Studierenden haben viel Neues gelernt.",
        32: "Er sitzt im Gefängnis, weil er _____ hinterzogen hat.",
        33: "Ob er kommt, ist _____.",
        34: "„Es war sehr _____ von dir, mich zu begleiten.“",
        35: "Die Sorge der Verwandten um die kranke Großmutter war _____.",
        36: "Die Verletzung _____ sehr weh.",
        37: "Man muss den Plan _____.",
        38: "Darüber ist kein Wort zu _____.",
        39: "Der Zug _____ sich in Bewegung.",
        40: "„Darf ich dir eine Tasse Tee _____?“",
        41: "Kommt Zeit, kommt _____.",
        42: "Bauern müssen auch bei _____ und Wetter aufs Feld.",
        43: "Wer gerne reist, will _____ und Leute kennenlernen.",
        44: "Nach der misslungenen Prüfung stand er mit dem Rücken zur _____.",
        45: "In der Kürze liegt die _____.",
        46: "Lücke (46)",
        47: "Lücke (47)",
        48: "Lücke (48)",
        49: "Lücke (49)",
        50: "Lücke (50)",
        51: "Lücke (51)",
        52: "Lücke (52)",
        53: "Lücke (53)",
        54: "Lücke (54)",
        55: "Lücke (55)",
        56: "Aufgrund ihres fleißigen Lernens erhöhte sich Sarahs Sprachniveau stetig.",
        57: "Zehn Jahre nachdem Familie Schneider das Unternehmen übernommen hat, ist die Geduld der Familie zu Ende.",
        58: "Was steht bei dem gefürchteten und von dem Premier angesteuerten No-Deal-Brexit für die beiderseitigen Beziehungen auf dem Spiel?",
        59: "Hinter diesem Problem stand eine schweigende Mehrheit.",
        60: "Das Baby kann jeden Moment auf die Welt kommen.",
        61: "DHV-Präsident Bernhard Kempen zufolge verändert sich das Klima an Hochschulen.",
        62: "Sie können ein einzelnes Objekt in einem Bild hervorheben, indem Sie seine Ränder schärfen.",
        63: "Im Konflikt mit dem Iran verlegen die USA nach den Angriffen auf saudische Ölanlagen weitere Truppen in den Nahen Osten.",
        64: "Die Bundesregierung hat sich auf ein Klimapaket geeinigt. Wir sind damit zufrieden.",
        65: "Mit PayPal habe ich auch oft Probleme. Aus diesem Grund nutze ich den Anbieter so gut wie kaum noch.",
        66: "Man plant, am Stadtrand einen öffentlichen Freizeitpark zu errichten.",
        67: "Der Politiker stellte fest: „Die CO₂-Preise sind lächerlich gering und werden niemanden veranlassen, seine Konsumgewohnheiten zu verändern.“\nDer Politiker stellte fest, _____.",
        68: "Sie tut so, _____.",
        69: "Ohne Hilfe der Polizei _____ der Rettungsdienst auf dem Weg zur Unfallstelle im Stau _____.",
        70: "_____ sind Fahrräder in überfüllten Waggons unzulässig.",
    },
    2022: {
        31: "Der junge Mann machte in der Straßenbahn einer alten Frau _____.",
        32: "Der Chef bat den Auszubildenden, eine _____ für ihn zu machen.",
        33: "Die _____ der zweitägigen Tagung verlangte von den Organisatoren viel Einsatz.",
        34: "Der Arzt leistete dem Verunglückten nach dem Unfall erste _____.",
        35: "Es ist eine der wichtigsten Aufgaben eines Richters, _____ zu sprechen.",
        36: "Die Bedeutung von Goethes Drama „Faust“ lässt sich an der Vielzahl der Interpretationen _____.",
        37: "Das Theaterstück wurde für die Freilichtbühne neu _____.",
        38: "Der Verlag will die Biographie von Goethe 2021 neu _____.",
        39: "Das Unternehmen musste wegen Insolvenz alle Gehaltszahlungen an die Mitarbeiter _____.",
        40: "Mit der Erfindung des Computers ist ein neues Zeitalter _____.",
        41: "Als er wieder einmal zu spät kam, hat ihm seine Freundin ordentlich _____ gewaschen.",
        42: "Ihr Charakter ist einfach so. Immer findet sie ein Haar in der _____.",
        43: "Wieder einmal hatte er sich durch seine voreilige Antwort _____ verbrannt.",
        44: "Der neue Mitarbeiter zeigte seinem unfreundlichen Vorgesetzten nach vielen Monaten endlich einmal _____.",
        45: "Der Ehemann fiel aus allen _____, als sich seine Frau von ihm scheiden lassen wollte.",
        46: "Lücke (46)",
        47: "Lücke (47)",
        48: "Lücke (48)",
        49: "Lücke (49)",
        50: "Lücke (50)",
        51: "Lücke (51)",
        52: "Lücke (52)",
        53: "Lücke (53)",
        54: "Lücke (54)",
        55: "Lücke (55)",
        56: "Der Radfahrer hatte Glück, denn der Polizist sah _____ einer Strafe ab.",
        57: "Mit ihrer Bemerkung wollte sie _____ den Vorfall vor drei Jahren anspielen.",
        58: "Du bist noch zu klein. Du kannst nicht alleine mit der U-Bahn fahren.\nEntscheiden Sie zwischen „zwar..., aber...“ oder „zu..., als dass...“.",
        59: "Die beiden Schwestern ähneln sich sehr. Die eine hat längere Haare.\nEntscheiden Sie zwischen „nur dass...“ oder „es sei denn...“.",
        60: "Er ist nicht so schwer verletzt, _____ es anfänglich aussah.",
        61: "Die Nachbarn haben während der Nacht laute Musik gehört, _____ wir uns belästigt gefühlt haben.",
        62: "Sie hatte diese Information aus dem Zeitungsartikel _____. (schlussfolgern)",
        63: "Über einig__ alt__ Kulturen berichten.",
        64: "Von unser__ freundlich__ Nachbarin erzählen.",
        65: "Ungeachtet der heftigen Regenfälle waren viele Autos auf den Straßen unterwegs.\nViele Autos waren auf den Straßen unterwegs, _____.",
        66: "Bei weiterhin steigenden Infektionszahlen werden umgehend Beschränkungen verhängt.\nEs werden umgehend Beschränkungen verhängt, _____.",
        67: "Anlässlich der Veröffentlichung von Martin Walsers neuem Roman wurden landesweit viele Lesungen veranstaltet.\nLandesweit wurden viele Lesungen veranstaltet, _____.",
        68: "„Stefanie musste sich einen Anwalt nehmen.“\nDer Freund erzählte, _____.",
        69: "„Die Verhandlungen wurden erfolgreich abgeschlossen.“\nDer Politiker berichtete, _____.",
        70: "Es war inzwischen allen klar geworden, dass sich diese Katastrophe nie hatte ereignen dürfen.\nEs war inzwischen allen klar geworden, _____.",
    },
}


BLEED_MARKERS = [
    "Ergänzen Sie",
    "Entscheiden Sie",
    "Was ist richtig",
    "Bilden Sie",
    "Setzen Sie",
    "Welche Lösung",
    "Formen Sie",
    "Verbinden Sie",
    "Formulieren Sie",
    "Wählen Sie",
    "Füllen Sie",
    "Welcher Nebensatz",
    "Welche Präposition",
    "Welche Umformulierung",
    "Welche Umschreibung",
    "Direkte Rede",
]


def clean_option(text: str) -> str:
    value = re.sub(r"\s+", " ", str(text)).strip()
    for marker in BLEED_MARKERS:
        index = value.find(marker)
        if index > 0:
            value = value[:index].rstrip(" ,.;:-")
    value = re.sub(r"\s+[A-H][,.;:]?$", "", value)
    value = re.sub(r"\s+\d+$", "", value)
    value = re.sub(r"\s*[~*]+$", "", value)
    value = re.sub(r"\bQ[lI]\b", "", value).strip()
    return value


def main() -> None:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    years = {entry["year"]: entry for entry in data["years"]}

    for year, entry in years.items():
        group_index = {group["id"]: group for group in entry["groups"]}
        for group_id, payload in GROUP_UPDATES.get(year, {}).items():
            group = group_index[group_id]
            group["instruction"] = payload["instruction"]
            if "shared_context" in payload:
                group["shared_context"] = payload["shared_context"]

        for question in entry["questions"]:
            stem = STEM_UPDATES.get(year, {}).get(question["number"])
            if stem:
                question["stem"] = stem
            question["instruction"] = group_index[question["group_id"]]["instruction"]
            question["options"] = {key: clean_option(value) for key, value in question["options"].items()}

    with DATA_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
