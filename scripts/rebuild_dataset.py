from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from reading_manual_overrides import MANUAL_READING_PASSAGES
from translation_writing_manual_overrides import MANUAL_TRANSLATION_WRITING_OVERRIDES


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
QUESTIONS_PATH = DATA_DIR / "questions.json"
ANSWER_KEY_PATH = DATA_DIR / "answer_key.json"
BACKUP_DIR = DATA_DIR / "backups"

GENERATED_MD_DIR = DATA_DIR / "generated_md"
TESTPAPER_MD_DIR = GENERATED_MD_DIR / "testpaperandanswer"
ROOT_PDF_MD_DIR = GENERATED_MD_DIR / "root_pdf"
CLEANED_TESTPAPER_PATH = ROOT_DIR / "material" / "testpaperandanswer" / "cleaned.txt"
CLEANED_TESTPAPER_OUTPUTS = {
    2016: TESTPAPER_MD_DIR / "cleaned" / "2016-source.md",
    2017: TESTPAPER_MD_DIR / "cleaned" / "2017-source.md",
    2018: TESTPAPER_MD_DIR / "cleaned" / "2018-source.md",
    2023: TESTPAPER_MD_DIR / "cleaned" / "2023-source.md",
    2025: TESTPAPER_MD_DIR / "cleaned" / "2025-source.md",
}
CURATED_TRANSLATION_WRITING_PATH = DATA_DIR / "generated_json" / "translation_writing_curated.json"
SOURCE_19_22_EXAMS_PATH = ROOT_DIR / "material" / "testpaperandanswer" / "19-22.json"
SOURCE_19_22_ANSWERS_PATH = ROOT_DIR / "material" / "testpaperandanswer" / "19-22ans.json"

EXERCISE_JSON_DIR = ROOT_DIR / "material" / "exercise" / "专八" / "cleaned" / "json"

CURATED_2022_TRANSLATION_A_TEXT = """A. Übersetzen Sie den folgenden Text ins Chinesische! (25 P)

Glaubten die Menschen früher, dass die Erde flach ist?

So steht es in unseren Kinderbüchern. Man hat genau das Bild vor Augen, wie ein Schiff einfach über den Rand kippt. Tatsächlich wusste man seit der Antike, dass die Erde eine Kugel ist, und dieses Wissen wurde auch ins Mittelalter gerettet. Deswegen ist es auch ein Mythos, dass Kolumbus nur deshalb Amerika entdecken konnte, weil er an die Kugelgestalt der Erde glaubte. In Wirklichkeit hatten seine Kritiker recht. Im Unterschied zu Kolumbus wussten sie, wie groß die Erde ist, und dass Kolumbus' Plan, Indien auf dem Westweg zu erreichen, gar nicht funktionieren konnte. Die Legende von den dummen und unwissenden Menschen im Mittelalter lässt sich somit leicht widerlegen. Der Reichsapfel als eines der drei wichtigsten Herrschaftszeichen des Mittelalters ist in Wahrheit ein Symbol der Erde.
"""

CURATED_2022_TRANSLATION_B_TEXT = """B. Übersetzen Sie den folgenden Text ins Deutsche! (25 P)

[题干原文待补。当前本地暂无高质量题干源，已保留参考译文《Übergang zu einer grünen und kohlenstoffarmen Entwicklung》供核对。]
"""

LISTENING_AUDIO_MAP = {
    2018: "media/2018-listening.mp3",
    2019: "media/2019-listening.mp3",
    2021: "media/2021-listening.mp3",
    2022: "media/2022-listening.mp3",
}

ROOT_MD_HINTS = {
    "full_exam_2019_2022": ("*2019-2022*.md", ROOT_PDF_MD_DIR),
    "2016_with_answers": ("2016*.md", TESTPAPER_MD_DIR),
    "2017_with_answers": ("2017*.md", TESTPAPER_MD_DIR),
    "2018_exam": ("2018*真题.md", TESTPAPER_MD_DIR),
    "2018_with_answers": ("2018*真题及解析.md", TESTPAPER_MD_DIR),
    "2025_exam": ("2025*.md", TESTPAPER_MD_DIR),
    "2025_answers": ("25*答案*.md", TESTPAPER_MD_DIR),
}

SECTION_MARKERS = {
    "listening": [
        r"\bI+\.\s*H[oö]rverstehen",
        r"\bl\.\s*H[oö]rverstehen",
        r"H[ioö]rverstehen",
        r"H.{0,6}verstehen\s*\(40",
    ],
    "vocab_grammar": [
        r"\bII+\.\s*Wortschatz und Grammatik",
        r"\b\|\.\s*Wortschatz und Grammatik",
        r"Wortschatz und Grammatik",
    ],
    "reading": [
        r"\bIII+\.\s*Leseverst.{0,4}ndnis",
        r"\blII+\.\s*Leseverst.{0,4}ndnis",
        r"Leseverst.{0,4}ndnis",
    ],
    "landeskunde": [
        r"\bIV+\.\s*Landeskunde",
        r"Landeskunde",
    ],
    "translation": [
        r"\bV+\.\s*[UÜ]bersetzung",
        r"[UÜ]bersetzung",
    ],
    "writing": [
        r"\bVI+\.\s*Schriftlicher Ausdruck",
        r"Schriftlicher Ausdruck",
    ],
}

SECTION_ORDER = ["listening", "vocab_grammar", "reading", "landeskunde", "translation", "writing"]

BLEED_MARKERS = [
    "Wortschatz (25 Punkte)",
    "Grammatik (15 Punkte)",
    "Leseverstandnis",
    "Leseverständnis",
    "Lesen Sie den Text und kreuzen Sie die richtige",
    "Lesen Sie den Text und kreuzen Sie die zutreffende",
    "Text 1",
    "Text 2",
    "Hortext 1",
    "Hortext 2",
    "Hörtext 1",
    "Hörtext 2",
    "Landeskunde",
    "Übersetzung",
    "Ubersetzung",
]

OFFICIAL_WG_ANSWERS = {
    2019: {
        31: "C", 32: "B", 33: "A", 34: "A", 35: "D", 36: "C", 37: "B", 38: "A", 39: "D", 40: "C",
        41: "D", 42: "A", 43: "C", 44: "A", 45: "B", 46: "A", 47: "D", 48: "B", 49: "A", 50: "B",
        51: "C", 52: "B", 53: "D", 54: "B", 55: "C", 56: "D", 57: "B", 58: "D", 59: "A", 60: "B",
        61: "C", 62: "A", 63: "D", 64: "C", 65: "B", 66: "C", 67: "D", 68: "A", 69: "A", 70: "B",
    },
    2021: {
        31: "B", 32: "A", 33: "D", 34: "C", 35: "D", 36: "C", 37: "B", 38: "C", 39: "A", 40: "D",
        41: "B", 42: "D", 43: "C", 44: "B", 45: "D", 46: "A", 47: "D", 48: "C", 49: "C", 50: "B",
        51: "A", 52: "C", 53: "B", 54: "D", 55: "C", 56: "A", 57: "A", 58: "B", 59: "B", 60: "C",
        61: "C", 62: "D", 63: "D", 64: "A", 65: "A", 66: "D", 67: "C", 68: "A", 69: "B", 70: "D",
    },
    2022: {
        31: "B", 32: "C", 33: "D", 34: "B", 35: "A", 36: "A", 37: "A", 38: "C", 39: "D", 40: "D",
        41: "B", 42: "D", 43: "A", 44: "C", 45: "B", 46: "D", 47: "B", 48: "C", 49: "D", 50: "A",
        51: "C", 52: "B", 53: "A", 54: "B", 55: "D", 56: "B", 57: "C", 58: "D", 59: "C", 60: "A",
        61: "D", 62: "A", 63: "D", 64: "B", 65: "A", 66: "C", 67: "D", 68: "C", 69: "A", 70: "B",
    },
    2023: {
        31: "C", 32: "B", 33: "A", 34: "D", 35: "A", 36: "B", 37: "D", 38: "B", 39: "D", 40: "C",
        41: "A", 42: "B", 43: "A", 44: "D", 45: "C", 46: "A", 47: "C", 48: "A", 49: "B", 50: "C",
        51: "B", 52: "D", 53: "C", 54: "A", 55: "D", 56: "C", 57: "C", 58: "B", 59: "B", 60: "B",
        61: "C", 62: "C", 63: "D", 64: "D", 65: "B", 66: "A", 67: "A", 68: "D", 69: "B", 70: "C",
    },
}

CLEANED_YEAR_HEADING_RE = re.compile(
    r"(?m)^## \*\*(\d{4})年德语专业八级真题（含答案(?:与解析)?）\*\*"
)
ANNOTATION_MARKER_RE = re.compile(
    r"(?m)^\s*\*\*(?:答案|解析|绛旀|瑙ｆ瀽|Answer|Lösung|Losung)\s*[:：]"
)


HARDENED_CLEANED_YEAR_HEADING_RE = re.compile(
    r"(?m)^## \*\*(\d{4})\u5e74\u5fb7\u8bed\u4e13\u4e1a\u516b\u7ea7\u771f\u9898\uff08\u542b\u7b54\u6848(?:\u4e0e\u89e3\u6790)?\uff09\*\*"
)
HARDENED_ANNOTATION_MARKER_RE = re.compile(
    r"(?m)^\s*\*\*(?:\u7b54\u6848|\u89e3\u6790|Answer|L\u00f6sung|Losung)\s*[:\uff1a]"
)

# Rebind the regexes here with ASCII-safe unicode escapes so rebuilds are stable
# regardless of shell code page.
CLEANED_YEAR_HEADING_RE = HARDENED_CLEANED_YEAR_HEADING_RE
ANNOTATION_MARKER_RE = HARDENED_ANNOTATION_MARKER_RE

@dataclass(frozen=True)
class GroupConfig:
    group_id: str
    subsection: str
    label: str
    instruction: str
    start: int
    end: int
    ui_type: str = "standard"
    question_type: str = "single-choice"
    context_anchor: str | None = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default):
    if not path.exists():
        return deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def find_md_file(key: str) -> Path:
    pattern, root = ROOT_MD_HINTS[key]
    matches = sorted(root.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"Missing markdown source for {key}: {pattern}")
    return matches[0]


def read_md(key: str) -> str:
    return find_md_file(key).read_text(encoding="utf-8")


def normalize_source_block(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"


def split_cleaned_testpaper_sources(text: str) -> dict[int, str]:
    matches = list(CLEANED_YEAR_HEADING_RE.finditer(text))
    if not matches:
        return {}

    sources: dict[int, str] = {}
    for index, match in enumerate(matches):
        year = int(match.group(1))
        if year not in CLEANED_TESTPAPER_OUTPUTS:
            continue
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sources[year] = normalize_source_block(text[start:end])
    return sources


def ensure_cleaned_testpaper_sources() -> dict[int, str]:
    if CLEANED_TESTPAPER_PATH.exists():
        raw_text = CLEANED_TESTPAPER_PATH.read_text(encoding="utf-8")
        split_sources = split_cleaned_testpaper_sources(raw_text)
        for year, output_path in CLEANED_TESTPAPER_OUTPUTS.items():
            text = split_sources.get(year)
            if not text:
                continue
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")

    sources: dict[int, str] = {}
    for year, output_path in CLEANED_TESTPAPER_OUTPUTS.items():
        if output_path.exists():
            sources[year] = output_path.read_text(encoding="utf-8")
    return sources


def normalize_text(text: str) -> str:
    value = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
    value = value.replace("鈥?", '"').replace("“", '"').replace("”", '"')
    value = value.replace("’", "'").replace("‘", "'")
    value = value.replace("—", "—").replace("–", "-")
    value = re.sub(r"(?<=\w)-\n(?=\w)", "", value)
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    value = re.sub(r"[ \t]{2,}", " ", value)
    return value.strip()


def normalize_listening_section(text: str) -> str:
    value = normalize_text(text)
    fixes = [
        (r"(?m)^\s*[lI][lI]\.\s*", "11. "),
        (r"(?m)^\s*9,\s*", "9. "),
        (r"(?m)^\s*9(?=\s+[A-ZÄÖÜ])", "9. "),
        (r"(?m)^\s*[§S]\.\s*", "8. "),
        (r"(?m)^\s*[§S](?=\s+[A-ZÄÖÜ])", "8. "),
        (r"(?m)^\s*2}(?=[.,])", "21"),
    ]
    for pattern, replacement in fixes:
        value = re.sub(pattern, replacement, value)
    return value


def normalize_question_markers(text: str) -> str:
    value = normalize_text(text)
    fixes = [
        (r"(?m)^\s*'(?=\d{2}[.,])", ""),
        (r"(?m)^\s*\|\s*(?=\d{1,3}[.,])", ""),
        (r"(?m)^\s*[ij]\s+(?=\d{1,3}[.,])", ""),
        (r"(?m)^\s*\$2(?=[.,])", "82"),
        (r"(?m)^\s*\$4(?=[.,])", "84"),
        (r"(?m)^\s*g6(?=[.,])", "86"),
        (r"(?m)^\s*g8(?=[.,])", "88"),
        (r"(?m)^\s*g9(?=[.,])", "89"),
        (r"(?m)^(\s*)1\)\.?(?=\s+)", r"\1D. "),
    ]
    for pattern, replacement in fixes:
        value = re.sub(pattern, replacement, value)
    return value


def find_bleed_index(text: str) -> int | None:
    earliest: int | None = None
    for marker in BLEED_MARKERS:
        pattern = re.compile(rf"(?m)^(?P<indent>\s*){re.escape(marker)}\b")
        match = pattern.search(text)
        if match:
            index = match.start()
            if index > 0 and (earliest is None or index < earliest):
                earliest = index
    return earliest


def strip_ocr_noise(text: str) -> str:
    value = text
    value = re.sub(r"<!--\s*page:[^>]*-->", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"https?\s*:\s*/\s*/\s*[^\s)]+", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"https?://\S+", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bshop\d+\S*", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\btaobao\s*\.\s*com(?:\s*/\S*)?", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bJK\s*-\s*EHEHE\s*:?\s*b[dt](?:h)?(?:\s+\w+)?\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bYa\)\s*=\s*G4:?", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bYd\s*\d+\s*E\d+:?", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\b[5S]\s*EHEHE:?\s*b[dt](?:h)?\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bEHEHE:?\s*b[dt](?:h)?(?:\s+\w+)?\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bpage:\s*\d+\s*source:\s*ocr\s*chars:\s*\d+\b", " ", value, flags=re.IGNORECASE)
    return value


def clean_inline(text: str) -> str:
    value = strip_ocr_noise(normalize_text(text))
    bleed_index = find_bleed_index(value)
    if bleed_index is not None:
        value = value[:bleed_index]
    value = value.replace("___—", "_____")
    value = value.replace("\\_", "_")
    value = re.sub(r"\s*\*{0,2}\s*_+\s*\*{0,2}\s*", " _____ ", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*[~*|]+\s*$", "", value)
    return value.strip(" ,.;:-")


def clean_block(text: str) -> str:
    value = strip_ocr_noise(normalize_text(text))
    bleed_index = find_bleed_index(value)
    if bleed_index is not None:
        value = value[:bleed_index]
    value = value.replace("___—", "_____")
    value = value.replace("\\_", "_")
    value = re.sub(r"\s*\*{0,2}\s*_+\s*\*{0,2}\s*", " _____ ", value)
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip(" \n|")


def normalize_answer_text(text: str) -> str:
    value = clean_inline(text).casefold()
    value = re.sub(r"\s+", " ", value)
    return value


def option_matches(text: str) -> list[re.Match[str]]:
    pattern = re.compile(r"(^|[\s(])([A-Da-d])[.,:]\s*", re.MULTILINE)
    return list(pattern.finditer(text))


def question_start_re(number: int) -> re.Pattern[str]:
    return re.compile(rf"(?m)^\s*[|\\']?\s*{number}[.,]\s*")


WG_GROUPS = {
    2016: [
        GroupConfig(
            "2016-w-a",
            "Wortschatz",
            "A",
            "Welches Wort passt nicht in die Reihe bedeutungsähnlicher Wörter?",
            31,
            40,
            ui_type="standard",
            question_type="text-input",
        ),
        GroupConfig(
            "2016-w-b",
            "Wortschatz",
            "B",
            "Ergänzen Sie jeweils das Fehlende in der Redewendung!",
            41,
            45,
            ui_type="standard",
            question_type="text-input",
        ),
        GroupConfig(
            "2016-w-c",
            "Wortschatz",
            "C",
            "Ergänzen Sie das richtige Wort: hindern, behindern oder verhindern!",
            46,
            50,
            ui_type="standard",
            question_type="text-input",
        ),
        GroupConfig(
            "2016-w-d",
            "Wortschatz",
            "D",
            "Setzen Sie die angegebenen Wörter sinnvoll in den Text ein!",
            51,
            60,
            ui_type="shared-passage",
            question_type="text-input",
            context_anchor="Zunahme Böden Menschheit Gleichgewichte",
        ),
        GroupConfig("2016-g-a", "Grammatik", "A", "Welche Lösung enthält die passende Ersatzform des unterstrichenen Satzteils?", 61, 62),
        GroupConfig("2016-g-b", "Grammatik", "B", "Formen Sie bitte die markierten Linksattribute in Relativsätze um oder umgekehrt!", 63, 64),
        GroupConfig("2016-g-c", "Grammatik", "C", "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?", 65, 66),
        GroupConfig("2016-g-d", "Grammatik", "D", "Wie können die unterstrichenen Adverbiale in einen Nebensatz umformuliert werden?", 67, 68),
        GroupConfig("2016-g-e", "Grammatik", "E", "Welche Lösung enthält die passende Umformung des unterstrichenen Teilsatzes?", 69, 70),
        GroupConfig("2016-g-f", "Grammatik", "F", "Welche Lösung enthält eine korrekte Passivumschreibung?", 71, 71),
        GroupConfig("2016-g-g", "Grammatik", "G", "Mit welcher Verbform wird die Aussage korrekt in indirekter Rede wiedergegeben?", 72, 73),
        GroupConfig("2016-g-h", "Grammatik", "H", "Füllen Sie die Lücken!", 74, 75, question_type="text-input"),
    ],
    2017: [
        GroupConfig("2017-w-a", "Wortschatz", "A", "Schreiben Sie das verlangte Wort nach dem Beispiel!", 31, 35),
        GroupConfig("2017-w-b", "Wortschatz", "B", "Wählen Sie die richtige Erklärung zu jedem unterstrichenen Wort aus!", 36, 40),
        GroupConfig("2017-w-c", "Wortschatz", "C", "Ergänzen Sie das fehlende Wort in den Redewendungen!", 41, 45),
        GroupConfig(
            "2017-w-d",
            "Wortschatz",
            "D",
            "Entscheiden Sie, welches Wort in die jeweilige Lücke passt.",
            46,
            55,
            ui_type="shared-passage",
            context_anchor="Im Ausgang aus der antiken Welt",
        ),
        GroupConfig("2017-g-a", "Grammatik", "A", "Welche Lösung enthält die passende Ersatzform des unterstrichenen Satzteils bzw. Satzes?", 56, 57),
        GroupConfig("2017-g-b", "Grammatik", "B", "Formen Sie bitte die markierten Linksattribute in Relativsätze um oder umgekehrt!", 58, 59),
        GroupConfig("2017-g-c", "Grammatik", "C", "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?", 60, 61),
        GroupConfig("2017-g-d", "Grammatik", "D", "Formulieren Sie bitte die unterstrichenen Präpositionen durch einen Nebensatz!", 62, 63),
        GroupConfig("2017-g-e", "Grammatik", "E", "Welche Lösung enthält die passende Umformung des unterstrichenen Teilsatzes?", 64, 65),
        GroupConfig("2017-g-f", "Grammatik", "F", "Welche Lösung enthält eine korrekte Passivumschreibung?", 66, 66),
        GroupConfig("2017-g-g", "Grammatik", "G", "Welche Lösung enthält eine korrekte Form für die indirekte Rede?", 67, 68),
        GroupConfig("2017-g-h", "Grammatik", "H", "Füllen Sie die Lücken!", 69, 70),
    ],
    2018: [
        GroupConfig("2018-w-a", "Wortschatz", "A", "Ergänzen Sie bitte das passende Verb im Funktionsverbgefüge!", 31, 35),
        GroupConfig("2018-w-b", "Wortschatz", "B", "Welches Wort passt?", 36, 40),
        GroupConfig("2018-w-c", "Wortschatz", "C", "Setzen Sie das passende Wort in die idiomatischen Wendungen ein!", 41, 45),
        GroupConfig(
            "2018-w-d",
            "Wortschatz",
            "D",
            "Wählen Sie das jeweils passende Wort aus!",
            46,
            55,
            ui_type="shared-passage",
            context_anchor="Brand in Rom",
        ),
        GroupConfig("2018-g-a", "Grammatik", "A", "Welche Lösung enthält die passende Ersatzform des unterstrichenen Satzteils?", 56, 57),
        GroupConfig("2018-g-b", "Grammatik", "B", "Formen Sie bitte die markierten Linksattribute in Relativsätze um oder umgekehrt!", 58, 59),
        GroupConfig("2018-g-c", "Grammatik", "C", "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?", 60, 61),
        GroupConfig("2018-g-d", "Grammatik", "D", "Formulieren Sie bitte die unterstrichenen Präpositionen durch einen Nebensatz!", 62, 63),
        GroupConfig("2018-g-e", "Grammatik", "E", "Bilden Sie Sätze mit Konjunktionen!", 64, 65),
        GroupConfig("2018-g-f", "Grammatik", "F", "Welche Lösung enthält eine korrekte Passivumschreibung?", 66, 66),
        GroupConfig("2018-g-g", "Grammatik", "G", "Welche Lösung enthält eine korrekte Form für die indirekte Rede?", 67, 67),
        GroupConfig("2018-g-h", "Grammatik", "H", "Füllen Sie die Lücken!", 68, 70),
    ],
    2023: [
        GroupConfig("2023-w-a", "Wortschatz", "A", "Was ist richtig?", 31, 35),
        GroupConfig("2023-w-b", "Wortschatz", "B", "Ergänzen Sie das passende Wort!", 36, 45),
        GroupConfig(
            "2023-w-c",
            "Wortschatz",
            "C",
            "Setzen Sie die angegebenen Wörter sinnvoll in den Text ein!",
            46,
            55,
            ui_type="shared-passage",
            context_anchor="Martin Luther und die Sünde",
        ),
        GroupConfig("2023-g-a", "Grammatik", "A", "Welche Lösung enthält die passende Ersatzform des unterstrichenen Satzteils?", 56, 57),
        GroupConfig("2023-g-b", "Grammatik", "B", "Formen Sie bitte die markierten Linksattribute in Relativsätze um oder umgekehrt!", 58, 59),
        GroupConfig("2023-g-c", "Grammatik", "C", "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?", 60, 61),
        GroupConfig("2023-g-d", "Grammatik", "D", "Formulieren Sie bitte die unterstrichene Präpositionalphrase durch einen Nebensatz um!", 62, 63),
        GroupConfig("2023-g-e", "Grammatik", "E", "Welche Lösung enthält die passende Umformung des Satzes?", 64, 65),
        GroupConfig("2023-g-f", "Grammatik", "F", "Welche Lösung enthält eine korrekte Form für die indirekte Rede?", 66, 68),
        GroupConfig("2023-g-g", "Grammatik", "G", "Füllen Sie die Lücken!", 69, 70),
    ],
    2025: [
        GroupConfig("2025-w-a", "Wortschatz", "A", "Was ist richtig?", 31, 34),
        GroupConfig("2025-w-b", "Wortschatz", "B", "Ergänzen Sie das passende Wort!", 35, 41),
        GroupConfig("2025-w-c", "Wortschatz", "C", "Ergänzen Sie den fehlenden Ausdruck in den Redewendungen!", 42, 45),
        GroupConfig(
            "2025-w-d",
            "Wortschatz",
            "D",
            "Setzen Sie die angegebenen Wörter sinnvoll in den Text ein!",
            46,
            55,
            ui_type="shared-passage",
            context_anchor="Der Archäologe: Michael Foucault",
        ),
        GroupConfig("2025-g-a", "Grammatik", "A", "Setzen Sie bitte den unterstrichenen Satz/Satzteil von der aktiven Form ins Vorgangspassiv!", 56, 57),
        GroupConfig("2025-g-b", "Grammatik", "B", "Wählen Sie bitte die richtige Reihenfolge der Satzglieder aus!", 58, 58),
        GroupConfig("2025-g-c", "Grammatik", "C", "Formen Sie bitte die markierten Linksattribute in Relativsätze um oder umgekehrt!", 59, 60),
        GroupConfig("2025-g-d", "Grammatik", "D", "Welche Lösung enthält die passende Umformung des Satzes?", 61, 62),
        GroupConfig("2025-g-e", "Grammatik", "E", "Welche Lösung enthält die korrekte Umschreibung des Satzes?", 63, 63),
        GroupConfig("2025-g-f", "Grammatik", "F", "Setzen Sie die passenden Endungen ein!", 64, 65),
        GroupConfig("2025-g-g", "Grammatik", "G", "Welche Lösung enthält eine korrekte Form für die indirekte Rede?", 66, 67),
        GroupConfig("2025-g-h", "Grammatik", "H", "Füllen Sie die Lücken!", 68, 70),
    ],
}


def section_bounds(text: str, section: str) -> tuple[int, int]:
    start = None
    for pattern in SECTION_MARKERS[section]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = match.start()
            break
    if start is None:
        raise ValueError(f"Could not locate section {section}")

    end = len(text)
    current_index = SECTION_ORDER.index(section)
    for next_section in SECTION_ORDER[current_index + 1:]:
        for pattern in SECTION_MARKERS[next_section]:
            match = re.search(pattern, text[start + 1 :], re.IGNORECASE)
            if match:
                end = min(end, start + 1 + match.start())
                break
    return start, end


def section_text(text: str, section: str) -> str:
    start, end = section_bounds(text, section)
    return normalize_text(text[start:end])


def question_block(text: str, start_no: int, end_no: int, number: int) -> str:
    start_match = question_start_re(number).search(text)
    if not start_match:
        raise ValueError(f"Missing question {number}")
    start = start_match.start()
    end = len(text)
    for next_number in range(number + 1, end_no + 1):
        next_match = question_start_re(next_number).search(text[start + 1 :])
        if next_match:
            end = start + 1 + next_match.start()
            break
    return clean_block(text[start:end])


def strip_annotation_tail(text: str) -> str:
    match = ANNOTATION_MARKER_RE.search(text)
    if match:
        return text[: match.start()].rstrip()
    return text


def parse_explicit_answer(raw_line: str) -> str | None:
    line = raw_line.strip()
    if not line:
        return None
    line = re.sub(r"^\*{1,2}\s*", "", line)
    line = re.sub(r"\s*\*{1,2}\s*$", "", line)
    match = re.match(r"^(?:答案|绛旀|Answer|Lösung|Losung)\s*[:：]\s*(.+?)\s*$", line, re.IGNORECASE)
    if not match:
        return None
    answer = clean_inline(match.group(1))
    return answer or None


def parse_explicit_explanation(raw_line: str) -> str | None:
    line = raw_line.strip()
    if not line:
        return None
    line = re.sub(r"^\*{1,2}\s*", "", line)
    line = re.sub(r"\s*\*{1,2}\s*$", "", line)
    match = re.match(
        r"^(?:\u89e3\u6790|Explanation|Erkl\u00e4rung)\s*[:\uff1a]\s*(.+?)\s*$",
        line,
        re.IGNORECASE,
    )
    if not match:
        return None
    explanation = re.sub(r"^\*{1,2}\s*", "", match.group(1))
    explanation = clean_block(explanation)
    return explanation or None


def parse_explicit_answer(raw_line: str) -> str | None:
    line = raw_line.strip()
    if not line:
        return None
    line = re.sub(r"^\*{1,2}\s*", "", line)
    line = re.sub(r"\s*\*{1,2}\s*$", "", line)
    match = re.match(
        r"^(?:\u7b54\u6848|Answer|L\u00f6sung|Losung)\s*[:\uff1a]\s*(.+?)\s*$",
        line,
        re.IGNORECASE,
    )
    if not match:
        return None
    answer = clean_inline(match.group(1))
    return answer or None


def parse_choice_block(block: str, number: int) -> tuple[str, dict[str, str]]:
    start_match = question_start_re(number).search(block)
    if not start_match:
        raise ValueError(f"Missing choice question {number}")

    body = strip_annotation_tail(block[start_match.end() :].strip())
    matches = option_matches(body)
    if len(matches) < 2:
        raise ValueError(f"Not enough options for {number}")

    stem = clean_block(body[: matches[0].start(2)])
    options: dict[str, str] = {}
    for idx, match in enumerate(matches[:4]):
        start = match.end()
        end = matches[idx + 1].start(2) if idx + 1 < len(matches[:4]) else len(body)
        options[match.group(2).upper()] = clean_inline(body[start:end])
    return stem, options


def parse_tf_block(block: str, number: int) -> str:
    start_match = question_start_re(number).search(block)
    if not start_match:
        raise ValueError(f"Missing true/false question {number}")
    stem = clean_block(strip_annotation_tail(block[start_match.end() :]))
    return re.sub(r"\s+[A-Za-z]\s*$", "", stem).strip()


def parse_answer_letter(line: str) -> str | None:
    letters = re.findall(r"\b([A-DFR])\b", line.upper())
    return letters[-1] if letters else None


def parse_2016_answers(md_text: str) -> dict[int, dict]:
    answers: dict[int, dict] = {}
    current = None
    for raw_line in md_text.splitlines():
        line = clean_inline(raw_line)
        q_match = re.match(r"^(\d{2})\.\s+", line)
        if q_match:
            current = int(q_match.group(1))
            continue
        if current is None or not 31 <= current <= 75:
            continue

        if 31 <= current <= 60 or 74 <= current <= 75:
            answer_match = re.match(r"^\(?\d+%?\]?\)?\s*([A-Za-zÄÖÜäöüß][^.]*)$", line)
            if answer_match:
                text = clean_inline(answer_match.group(1))
                if text:
                    answers[current] = {
                        "display_answer": text,
                        "accepted_answers": [normalize_answer_text(text)],
                    }
                continue

        letter = parse_answer_letter(line)
        if 61 <= current <= 73 and letter in {"A", "B", "C", "D"}:
            answers[current] = {"correct_option": letter}

    return answers


def parse_2017_answers(md_text: str) -> dict[int, dict]:
    answers: dict[int, dict] = {}
    current = None
    for raw_line in md_text.splitlines():
        line = clean_inline(raw_line)
        q_match = re.match(r"^(\d{2})\.\s+", line)
        if q_match:
            current = int(q_match.group(1))
            continue
        if current is None or not 31 <= current <= 70:
            continue
        letter = parse_answer_letter(line)
        if letter in {"A", "B", "C", "D"}:
            answers[current] = {"correct_option": letter}
    return answers


def parse_answer_pdf_style(md_text: str, start: int, end: int) -> dict[int, dict]:
    answers: dict[int, dict] = {}
    current = None
    for raw_line in md_text.splitlines():
        line = clean_inline(raw_line)
        q_match = re.match(r"^(\d{1,3})[.、]?\s*([A-DFR])(?:\b|[.])", line, re.IGNORECASE)
        if q_match:
            qno = int(q_match.group(1))
            if start <= qno <= end:
                current = qno
                token = q_match.group(2).upper()
                answers[qno] = {"correct_option": token}
            continue

        q_text_match = re.match(r"^(\d{1,3})\.\s+", line)
        if q_text_match:
            current = int(q_text_match.group(1))
            continue

        if current is None or not start <= current <= end:
            continue

        letter = parse_answer_letter(line)
        if letter in {"A", "B", "C", "D", "R", "F"}:
            answers[current] = {"correct_option": letter}
    return answers


def parse_2016_answers(md_text: str) -> dict[int, dict]:
    answers: dict[int, dict] = {}
    current = None
    explicit_answered: set[int] = set()
    for raw_line in md_text.splitlines():
        line = clean_inline(raw_line)
        q_match = re.match(r"^(\d{2})\.\s+", line)
        if q_match:
            current = int(q_match.group(1))
            continue
        if current is None or not 31 <= current <= 75:
            continue

        explicit_answer = parse_explicit_answer(raw_line)
        if explicit_answer is not None:
            explicit_answered.add(current)
            if 31 <= current <= 60 or 74 <= current <= 75:
                answers[current] = {
                    "display_answer": explicit_answer,
                    "accepted_answers": [normalize_answer_text(explicit_answer)],
                }
            else:
                letter = parse_answer_letter(explicit_answer)
                if letter in {"A", "B", "C", "D"}:
                    answers[current] = {"correct_option": letter}
            continue

        explicit_explanation = parse_explicit_explanation(raw_line)
        if explicit_explanation is not None:
            answers.setdefault(current, {})
            answers[current]["explanation"] = explicit_explanation
            continue

        if current in explicit_answered:
            continue

        if 31 <= current <= 60 or 74 <= current <= 75:
            answer_match = re.match(r"^\(?\d+%?\]?\)?\s*([A-Za-z\u00c4\u00d6\u00dc\u00e4\u00f6\u00fc\u00df][^.]*)$", line)
            if answer_match:
                text = clean_inline(answer_match.group(1))
                if text:
                    answers[current] = {
                        "display_answer": text,
                        "accepted_answers": [normalize_answer_text(text)],
                    }
                continue

        letter = parse_answer_letter(line)
        if 61 <= current <= 73 and letter in {"A", "B", "C", "D"}:
            answers[current] = {"correct_option": letter}

    return answers


def parse_2017_answers(md_text: str) -> dict[int, dict]:
    answers: dict[int, dict] = {}
    current = None
    explicit_answered: set[int] = set()
    for raw_line in md_text.splitlines():
        line = clean_inline(raw_line)
        q_match = re.match(r"^(\d{2})\.\s+", line)
        if q_match:
            current = int(q_match.group(1))
            continue
        if current is None or not 31 <= current <= 70:
            continue

        explicit_answer = parse_explicit_answer(raw_line)
        if explicit_answer is not None:
            explicit_answered.add(current)
            letter = parse_answer_letter(explicit_answer)
            if letter in {"A", "B", "C", "D"}:
                answers[current] = {"correct_option": letter}
            continue

        explicit_explanation = parse_explicit_explanation(raw_line)
        if explicit_explanation is not None:
            answers.setdefault(current, {})
            answers[current]["explanation"] = explicit_explanation
            continue

        if current in explicit_answered:
            continue

        letter = parse_answer_letter(line)
        if letter in {"A", "B", "C", "D"}:
            answers[current] = {"correct_option": letter}
    return answers


def parse_answer_pdf_style(md_text: str, start: int, end: int) -> dict[int, dict]:
    answers: dict[int, dict] = {}
    current = None
    explicit_answered: set[int] = set()
    for raw_line in md_text.splitlines():
        line = clean_inline(raw_line)
        q_match = re.match(r"^(\d{1,3})[.銆乚?\s*([A-DFR])(?:\b|[.])", line, re.IGNORECASE)
        if q_match:
            qno = int(q_match.group(1))
            if start <= qno <= end:
                current = qno
                token = q_match.group(2).upper()
                answers[qno] = {"correct_option": token}
                explicit_answered.discard(qno)
            continue

        q_text_match = re.match(r"^(\d{1,3})\.\s+", line)
        if q_text_match:
            current = int(q_text_match.group(1))
            continue

        if current is None or not start <= current <= end:
            continue

        explicit_answer = parse_explicit_answer(raw_line)
        if explicit_answer is not None:
            explicit_answered.add(current)
            letter = parse_answer_letter(explicit_answer)
            if letter in {"A", "B", "C", "D", "R", "F"}:
                answers[current] = {"correct_option": letter}
            continue

        explicit_explanation = parse_explicit_explanation(raw_line)
        if explicit_explanation is not None:
            answers.setdefault(current, {})
            answers[current]["explanation"] = explicit_explanation
            continue

        if current in explicit_answered:
            continue

        letter = parse_answer_letter(line)
        if letter in {"A", "B", "C", "D", "R", "F"}:
            answers[current] = {"correct_option": letter}
    return answers


def parse_answer_pdf_style(md_text: str, start: int, end: int) -> dict[int, dict]:
    answers: dict[str, dict] = {}
    current = None
    explicit_answered: set[int] = set()
    for raw_line in md_text.splitlines():
        line = clean_inline(raw_line)
        q_match = re.match(r"^(\d{1,3})(?:[.、]\s*|\s+)([A-DFR])(?:\b|[.])", line, re.IGNORECASE)
        if q_match:
            qno = int(q_match.group(1))
            if start <= qno <= end:
                current = qno
                token = q_match.group(2).upper()
                answers[qno] = {"correct_option": token}
                explicit_answered.discard(qno)
            continue

        q_text_match = re.match(r"^(\d{1,3})\.\s+", line)
        if q_text_match:
            current = int(q_text_match.group(1))
            continue

        if current is None or not start <= current <= end:
            continue

        explicit_answer = parse_explicit_answer(raw_line)
        if explicit_answer is not None:
            explicit_answered.add(current)
            letter = parse_answer_letter(explicit_answer)
            if letter in {"A", "B", "C", "D", "R", "F"}:
                answers[current] = {"correct_option": letter}
            continue

        explicit_explanation = parse_explicit_explanation(raw_line)
        if explicit_explanation is not None:
            answers.setdefault(current, {})
            answers[current]["explanation"] = explicit_explanation
            continue

        if current in explicit_answered:
            continue

        letter = parse_answer_letter(line)
        if letter in {"A", "B", "C", "D", "R", "F"}:
            answers[current] = {"correct_option": letter}
    return answers


def parse_year_entry_from_existing(current_dataset: dict, year: int) -> dict:
    year_entry = next(entry for entry in current_dataset["years"] if entry["year"] == year)
    return deepcopy(year_entry)


def build_group_payloads(groups: list[GroupConfig], shared_contexts: dict[str, str | None]) -> list[dict]:
    payloads = []
    for group in groups:
        payloads.append(
            {
                "id": group.group_id,
                "subsection": group.subsection,
                "label": group.label,
                "instruction": group.instruction,
                "ui_type": group.ui_type,
                "question_numbers": list(range(group.start, group.end + 1)),
                "shared_context": shared_contexts.get(group.group_id),
            }
        )
    return payloads


def build_question_payload(
    *,
    year: int,
    page: int,
    number: int,
    group: GroupConfig,
    stem: str,
    options: dict[str, str] | None = None,
    source_pdf: str,
) -> dict:
    cleaned_stem = clean_block(stem)
    if group.ui_type == "shared-passage" and not cleaned_stem:
        cleaned_stem = f"Lücke ({number})"
    payload = {
        "id": f"{year}-{number}",
        "year": year,
        "number": number,
        "page": page,
        "subsection": group.subsection,
        "group_id": group.group_id,
        "group_label": group.label,
        "ui_type": group.ui_type,
        "instruction": group.instruction,
        "stem": cleaned_stem,
        "question_type": group.question_type,
        "source_pdf": source_pdf,
    }
    if options:
        payload["options"] = {key: clean_inline(value) for key, value in options.items()}
    else:
        payload["options"] = {}
    return payload


def parse_shared_context(section: str, group: GroupConfig) -> str | None:
    if not group.context_anchor:
        return None
    anchor = section.lower().find(group.context_anchor.lower())
    q_match = question_start_re(group.start).search(section)
    if anchor == -1 or q_match is None:
        return None
    return clean_block(section[anchor:q_match.start()])


def build_2018_or_2025_wg_year(year: int, exam_text: str, source_pdf: str, answer_source_text: str | None = None) -> tuple[dict, dict]:
    section = section_text(exam_text, "vocab_grammar")
    groups = WG_GROUPS[year]
    shared_contexts = {group.group_id: parse_shared_context(section, group) for group in groups}
    questions = []
    answers = {}

    for group in groups:
        for number in range(group.start, group.end + 1):
            block = question_block(section, group.start, group.end, number)
            stem, options = parse_choice_block(block, number)
            questions.append(
                build_question_payload(
                    year=year,
                    page=0,
                    number=number,
                    group=group,
                    stem=stem,
                    options=options,
                    source_pdf=source_pdf,
                )
            )

    if answer_source_text is None:
        answer_source_key = "2018_with_answers" if year == 2018 else "2025_answers"
        answer_source_text = read_md(answer_source_key)
    parsed_answers = parse_answer_pdf_style(answer_source_text, 31, 70)
    for number, payload in parsed_answers.items():
        answers[f"{year}-{number}"] = payload

    return {
        "year": year,
        "pages": [],
        "question_count": len(questions),
        "groups": build_group_payloads(groups, shared_contexts),
        "questions": questions,
    }, answers


def build_2017_wg_year(md_text: str, source_pdf: str) -> tuple[dict, dict]:
    groups = WG_GROUPS[2017]
    shared_contexts = {group.group_id: parse_shared_context(md_text, group) for group in groups}
    questions = []
    for group in groups:
        for number in range(group.start, group.end + 1):
            block = question_block(md_text, group.start, group.end, number)
            stem, options = parse_choice_block(block, number)
            questions.append(
                build_question_payload(
                    year=2017,
                    page=0,
                    number=number,
                    group=group,
                    stem=stem,
                    options=options,
                    source_pdf=source_pdf,
                )
            )
    answers = {f"2017-{number}": payload for number, payload in parse_2017_answers(md_text).items()}
    return {
        "year": 2017,
        "pages": [],
        "question_count": len(questions),
        "groups": build_group_payloads(groups, shared_contexts),
        "questions": questions,
    }, answers


def build_2016_wg_year(md_text: str, source_pdf: str) -> tuple[dict, dict]:
    groups = WG_GROUPS[2016]
    shared_contexts = {group.group_id: parse_shared_context(md_text, group) for group in groups}
    parsed_answers = parse_2016_answers(md_text)
    questions = []

    for group in groups:
        for number in range(group.start, group.end + 1):
            block = question_block(md_text, group.start, group.end, number)
            if group.question_type == "text-input":
                stem = parse_tf_block(block, number)
                options = {}
            else:
                stem, options = parse_choice_block(block, number)
            questions.append(
                build_question_payload(
                    year=2016,
                    page=0,
                    number=number,
                    group=group,
                    stem=stem,
                    options=options,
                    source_pdf=source_pdf,
                )
            )

    answers = {f"2016-{number}": payload for number, payload in parsed_answers.items()}
    return {
        "year": 2016,
        "pages": [],
        "question_count": len(questions),
        "groups": build_group_payloads(groups, shared_contexts),
        "questions": questions,
    }, answers


def split_root_full_exam_by_year(full_text: str, year: int) -> str:
    marker_re = re.compile(rf"(?m)^(?:<!--.*\n)?\s*{year}\b")
    next_year = None
    if year == 2019:
        next_year = 2021
    elif year == 2021:
        next_year = 2022

    start_match = marker_re.search(full_text)
    if not start_match:
        raise ValueError(f"Year marker {year} not found in root exam markdown")
    start = start_match.start()

    end = len(full_text)
    if next_year:
        next_re = re.compile(rf"(?m)^(?:<!--.*\n)?\s*{next_year}\b")
        next_match = next_re.search(full_text, start + 1)
        if next_match:
            end = next_match.start()
    return normalize_text(full_text[start:end])


def build_set_group(
    group_id: str,
    label: str,
    instruction: str,
    start: int | None,
    end: int | None,
    ui_type: str,
    shared_context: str | None = None,
    question_numbers: list[int] | None = None,
) -> dict:
    numbers = question_numbers if question_numbers is not None else list(range(start, end + 1))
    return {
        "id": group_id,
        "label": label,
        "instruction": instruction,
        "ui_type": ui_type,
        "question_numbers": numbers,
        "shared_context": shared_context,
    }


def build_library_question(
    *,
    set_id: str,
    year: int,
    section: str,
    number: int,
    group_id: str,
    group_label: str,
    instruction: str,
    question_type: str,
    stem: str,
    options: dict[str, str] | None = None,
    source_pdf: str,
    prompt_text: str | None = None,
    subprompts: list[str] | None = None,
) -> dict:
    payload = {
        "id": f"{set_id}-{number}",
        "set_id": set_id,
        "year": year,
        "section": section,
        "number": number,
        "group_id": group_id,
        "group_label": group_label,
        "instruction": instruction,
        "question_type": question_type,
        "stem": clean_block(stem),
        "options": options or {},
        "source_pdf": source_pdf,
    }
    if prompt_text:
        payload["prompt_text"] = clean_block(prompt_text)
    if subprompts:
        payload["subprompts"] = [clean_block(item) for item in subprompts if clean_block(item)]
    return payload


def parse_cleaned_tf_table(table_text: str) -> tuple[list[dict], dict[int, dict]]:
    questions: list[dict] = []
    answers: dict[int, dict] = {}
    for raw_line in table_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        number_match = re.match(r"^(\d+)\.\s*$", parts[0])
        if not number_match:
            continue
        token_match = re.search(r"\*\*([RF])\*\*", parts[2], re.IGNORECASE)
        if not token_match:
            continue
        number = int(number_match.group(1))
        stem = clean_block(parts[1])
        token = token_match.group(1).upper()
        explanation = clean_block(" | ".join(parts[3:])) if len(parts) > 3 else ""
        questions.append({"number": number, "stem": stem})
        payload = {"correct_option": token}
        if explanation:
            payload["explanation"] = explanation
        answers[number] = payload
    return questions, answers


def parse_cleaned_choice_questions(section_text: str, start_no: int, end_no: int) -> tuple[list[dict], dict[int, dict]]:
    questions: list[dict] = []
    answers: dict[int, dict] = {}
    current_number: int | None = None
    stem_parts: list[str] = []
    options: dict[str, str] = {}

    def flush() -> None:
        nonlocal current_number, stem_parts, options
        if current_number is None:
            return
        stem = clean_block("\n".join(stem_parts))
        questions.append({"number": current_number, "stem": stem, "options": dict(options)})
        current_number = None
        stem_parts = []
        options = {}

    for raw_line in section_text.splitlines():
        line = raw_line.rstrip()
        q_match = re.match(r"^\s*(\d{1,3})\.\s+(.+?)\s*$", line)
        if q_match:
            qno = int(q_match.group(1))
            if start_no <= qno <= end_no:
                flush()
                current_number = qno
                stem_parts = [q_match.group(2)]
                options = {}
                continue
        if current_number is None:
            continue

        option_match = re.match(r"^\s*([A-Da-d])\.\s+(.+?)\s*$", line)
        if option_match:
            options[option_match.group(1).upper()] = clean_inline(option_match.group(2))
            continue

        explicit_answer = parse_explicit_answer(raw_line)
        if explicit_answer is not None:
            letter = parse_answer_letter(explicit_answer)
            if letter in {"A", "B", "C", "D", "R", "F"}:
                answers.setdefault(current_number, {})
                answers[current_number]["correct_option"] = letter
            continue

        explicit_explanation = parse_explicit_explanation(raw_line)
        if explicit_explanation is not None:
            answers.setdefault(current_number, {})
            answers[current_number]["explanation"] = explicit_explanation
            continue

        if options or not line.strip():
            continue
        stem_parts.append(line.strip())

    flush()
    return questions, answers


def parse_cleaned_listening_set(year: int, cleaned_text: str, source_pdf: str) -> tuple[dict, dict[str, dict]]:
    heading_match = re.search(r"^###\s+\*\*Teil I\s+H(?:ö|枚)rverstehen.*?$", cleaned_text, re.MULTILINE)
    if not heading_match:
        raise ValueError("Missing cleaned listening heading")
    next_section_match = re.search(r"^###\s+\*\*Teil II\b.*?$", cleaned_text[heading_match.end() :], re.MULTILINE)
    next_section = heading_match.end() + next_section_match.start() if next_section_match else len(cleaned_text)
    hearing_text = cleaned_text[heading_match.start() : next_section]

    marker_1_match = re.search(r"^####\s+\*\*(?:H(?:ö|枚)rtext 1|Teil 1)\*\*\s*$", hearing_text, re.MULTILINE)
    marker_2_match = re.search(r"^####\s+\*\*(?:H(?:ö|枚)rtext 2|Teil 2)\*\*\s*$", hearing_text, re.MULTILINE)
    if not marker_1_match or not marker_2_match:
        raise ValueError("Missing cleaned listening sub-sections")

    part1 = hearing_text[marker_1_match.start() : marker_2_match.start()]
    part2 = hearing_text[marker_2_match.start() :]

    instruction_1_lines = [
        line.strip()
        for line in part1.splitlines()[1:5]
        if line.strip() and not line.lstrip().startswith("|")
    ]
    instruction_2_lines = [
        line.strip()
        for line in part2.splitlines()[1:5]
        if line.strip() and not line.lstrip().startswith("|")
    ]
    instruction_1 = clean_block("\n".join(instruction_1_lines)) or "Hörtext 1"
    instruction_2 = clean_block("\n".join(instruction_2_lines)) or "Hörtext 2"

    tf_questions, tf_answers = parse_cleaned_tf_table(part1)
    choice_questions, choice_answers = parse_cleaned_choice_questions(part2, 11, 30)

    groups = [
        build_set_group(f"{year}-listening-a", "Hörtext 1", instruction_1, 1, 10, "standard"),
        build_set_group(f"{year}-listening-b", "Hörtext 2", instruction_2, 11, 30, "standard"),
    ]
    questions = []
    answer_updates: dict[str, dict] = {}

    for item in tf_questions:
        qno = item["number"]
        questions.append(
            build_library_question(
                set_id=f"{year}-listening",
                year=year,
                section="listening",
                number=qno,
                group_id=f"{year}-listening-a",
                group_label="Hörtext 1",
                instruction=instruction_1,
                question_type="true-false",
                stem=item["stem"],
                options={"R": "Richtig", "F": "Falsch"},
                source_pdf=source_pdf,
            )
        )
        if qno in tf_answers:
            answer_updates[f"{year}-listening-{qno}"] = tf_answers[qno]

    for item in choice_questions:
        qno = item["number"]
        questions.append(
            build_library_question(
                set_id=f"{year}-listening",
                year=year,
                section="listening",
                number=qno,
                group_id=f"{year}-listening-b",
                group_label="Hörtext 2",
                instruction=instruction_2,
                question_type="single-choice",
                stem=item["stem"],
                options=item["options"],
                source_pdf=source_pdf,
            )
        )
        if qno in choice_answers:
            answer_updates[f"{year}-listening-{qno}"] = choice_answers[qno]

    questions.sort(key=lambda item: item["number"])
    return {
        "id": f"{year}-listening",
        "year": year,
        "section": "listening",
        "title": f"{year} 听力",
        "question_count": len(questions),
        "audio_file": LISTENING_AUDIO_MAP.get(year),
        "groups": groups,
        "questions": questions,
    }, answer_updates


def parse_listening_set(year: int, exam_text: str, source_pdf: str) -> dict:
    section = normalize_question_markers(normalize_listening_section(section_text(exam_text, "listening")))
    groups = []
    questions = []

    match_h1 = re.search(r"H[oö]rtext 1.*?(?=1\.)", section, re.IGNORECASE | re.DOTALL)
    match_h2 = re.search(r"H[oö]rtext 2.*?(?=11\.)", section, re.IGNORECASE | re.DOTALL)
    instruction_1 = clean_block(match_h1.group(0)) if match_h1 else "Hörtext 1"
    instruction_2 = clean_block(match_h2.group(0)) if match_h2 else "Hörtext 2"

    groups.append(build_set_group(f"{year}-listening-a", "Hörtext 1", instruction_1, 1, 10, "standard"))
    groups.append(build_set_group(f"{year}-listening-b", "Hörtext 2", instruction_2, 11, 30, "standard"))

    for number in range(1, 11):
        block = question_block(section, 1, 30, number)
        stem = parse_tf_block(block, number)
        questions.append(
            build_library_question(
                set_id=f"{year}-listening",
                year=year,
                section="listening",
                number=number,
                group_id=f"{year}-listening-a",
                group_label="Hörtext 1",
                instruction=instruction_1,
                question_type="true-false",
                stem=stem,
                options={"R": "Richtig", "F": "Falsch"},
                source_pdf=source_pdf,
            )
        )

    for number in range(11, 31):
        block = question_block(section, 1, 30, number)
        stem, options = parse_choice_block(block, number)
        questions.append(
            build_library_question(
                set_id=f"{year}-listening",
                year=year,
                section="listening",
                number=number,
                group_id=f"{year}-listening-b",
                group_label="Hörtext 2",
                instruction=instruction_2,
                question_type="single-choice",
                stem=stem,
                options=options,
                source_pdf=source_pdf,
            )
        )

    return {
        "id": f"{year}-listening",
        "year": year,
        "section": "listening",
        "title": f"{year} 听力",
        "question_count": len(questions),
        "audio_file": LISTENING_AUDIO_MAP.get(year),
        "groups": groups,
        "questions": questions,
    }


def parse_reading_set(year: int, exam_text: str, source_pdf: str) -> dict:
    section = normalize_question_markers(section_text(exam_text, "reading"))
    groups = []
    questions = []
    text1_start = section.find("Text 1")
    text2_start = section.find("Text 2", max(text1_start, 0) + 1)
    if year == 2016:
        start_no, split_no, end_no = 76, 84, 90
    else:
        start_no, split_no, end_no = 71, 79, 85
    q_start = question_start_re(start_no).search(section)
    q_split = question_start_re(split_no).search(section)
    shared1 = clean_block(section[text1_start:q_start.start()]) if text1_start != -1 and q_start else None
    shared2 = clean_block(section[text2_start:q_split.start()]) if text2_start != -1 and q_split else None

    groups.append(build_set_group(f"{year}-reading-a", "Text 1", "Lesen Sie den Text und kreuzen Sie die richtige Lösung an!", start_no, split_no - 1, "shared-passage", shared1))
    groups.append(build_set_group(f"{year}-reading-b", "Text 2", "Lesen Sie den Text und kreuzen Sie die richtige Lösung an!", split_no, end_no, "shared-passage", shared2))

    for number in range(start_no, end_no + 1):
        block = question_block(section, start_no, end_no, number)
        stem, options = parse_choice_block(block, number)
        group_id = f"{year}-reading-a" if number < split_no else f"{year}-reading-b"
        group_label = "Text 1" if number < split_no else "Text 2"
        questions.append(
            build_library_question(
                set_id=f"{year}-reading",
                year=year,
                section="reading",
                number=number,
                group_id=group_id,
                group_label=group_label,
                instruction="Lesen Sie den Text und kreuzen Sie die richtige Lösung an!",
                question_type="single-choice",
                stem=stem,
                options=options,
                source_pdf=source_pdf,
            )
        )

    return {
        "id": f"{year}-reading",
        "year": year,
        "section": "reading",
        "title": f"{year} 阅读",
        "question_count": len(questions),
        "groups": groups,
        "questions": questions,
    }


def parse_landeskunde_set(year: int, exam_text: str, source_pdf: str) -> dict:
    section = normalize_question_markers(section_text(exam_text, "landeskunde"))
    if year == 2016:
        tf_start, tf_end, choice_start, choice_end = 91, 96, 97, 110
    else:
        tf_start, tf_end, choice_start, choice_end = 86, 91, 92, 105
    groups = [
        build_set_group(f"{year}-country-a", "A", "Welche der folgenden Aussagen sind richtig, welche falsch?", tf_start, tf_end, "standard"),
        build_set_group(f"{year}-country-b", "B", "Kreuzen Sie die richtige Lösung an!", choice_start, choice_end, "standard"),
    ]
    questions = []

    for number in range(tf_start, tf_end + 1):
        try:
            block = question_block(section, tf_start, choice_end, number)
            stem = parse_tf_block(block, number)
            placeholder = False
        except ValueError:
            stem = "原始扫描页缺损，题干待人工补录。"
            placeholder = True
        questions.append(
            build_library_question(
                set_id=f"{year}-landeskunde",
                year=year,
                section="landeskunde",
                number=number,
                group_id=f"{year}-country-a",
                group_label="A",
                instruction="Welche der folgenden Aussagen sind richtig, welche falsch?",
                question_type="true-false",
                stem=stem,
                options={"R": "Richtig", "F": "Falsch"},
                source_pdf=source_pdf,
            )
        )
        if placeholder:
            questions[-1]["is_placeholder"] = True
            questions[-1]["placeholder_reason"] = "source-page-damage"

    for number in range(choice_start, choice_end + 1):
        block = question_block(section, tf_start, choice_end, number)
        stem, options = parse_choice_block(block, number)
        questions.append(
            build_library_question(
                set_id=f"{year}-landeskunde",
                year=year,
                section="landeskunde",
                number=number,
                group_id=f"{year}-country-b",
                group_label="B",
                instruction="Kreuzen Sie die richtige Lösung an!",
                question_type="single-choice",
                stem=stem,
                options=options,
                source_pdf=source_pdf,
            )
        )

    return {
        "id": f"{year}-landeskunde",
        "year": year,
        "section": "landeskunde",
        "title": f"{year} 国情",
        "question_count": len(questions),
        "groups": groups,
        "questions": questions,
    }


def parse_translation_set(year: int, exam_text: str, source_pdf: str) -> dict:
    section = section_text(exam_text, "translation")
    part_a = re.search(r"A\.\s*(?:Ü|U)bersetzen.*?(?=\n####\s*\*\*B\.|\nB\.)", section, re.IGNORECASE | re.DOTALL)
    part_b = re.search(r"B\.\s*(?:Ü|U)bersetzen.*", section, re.IGNORECASE | re.DOTALL)

    groups = [
        build_set_group(f"{year}-translation-a", "A", "Übersetzen Sie den folgenden Text ins Chinesische!", 1, 1, "prompt"),
        build_set_group(f"{year}-translation-b", "B", "Übersetzen Sie den folgenden Text ins Deutsche!", 2, 2, "prompt"),
    ]
    questions = []
    if part_a:
        questions.append(
            build_library_question(
                set_id=f"{year}-translation",
                year=year,
                section="translation",
                number=1,
                group_id=f"{year}-translation-a",
                group_label="A",
                instruction="Übersetzen Sie den folgenden Text ins Chinesische!",
                question_type="prompt",
                stem="翻译题 A",
                prompt_text=part_a.group(0),
                source_pdf=source_pdf,
            )
        )
    if part_b:
        questions.append(
            build_library_question(
                set_id=f"{year}-translation",
                year=year,
                section="translation",
                number=2,
                group_id=f"{year}-translation-b",
                group_label="B",
                instruction="Übersetzen Sie den folgenden Text ins Deutsche!",
                question_type="prompt",
                stem="翻译题 B",
                prompt_text=part_b.group(0),
                source_pdf=source_pdf,
            )
        )

    return {
        "id": f"{year}-translation",
        "year": year,
        "section": "translation",
        "title": f"{year} 翻译",
        "question_count": len(questions),
        "groups": groups,
        "questions": questions,
    }


def parse_writing_set(year: int, exam_text: str, source_pdf: str) -> dict:
    section = section_text(exam_text, "writing")
    prompt_match = re.search(r"Aufgabe:.*", section, re.IGNORECASE | re.DOTALL)
    before_prompt = section[: prompt_match.start()] if prompt_match else section
    subprompts = re.findall(r"(?m)^(?:[0-9]+[.)]|[a-c]\)|[-•])\s*(.+)$", section)

    question = build_library_question(
        set_id=f"{year}-writing",
        year=year,
        section="writing",
        number=1,
        group_id=f"{year}-writing-a",
        group_label="A",
        instruction="Schreiben Sie nun einen Aufsatz von 250 Wörtern.",
        question_type="prompt",
        stem=clean_block(before_prompt.splitlines()[0] if before_prompt.strip() else "作文题"),
        prompt_text=prompt_match.group(0) if prompt_match else section,
        subprompts=subprompts,
        source_pdf=source_pdf,
    )
    return {
        "id": f"{year}-writing",
        "year": year,
        "section": "writing",
        "title": f"{year} 写作",
        "question_count": 1,
        "groups": [build_set_group(f"{year}-writing-a", "A", "Schriftlicher Ausdruck", 1, 1, "prompt")],
        "questions": [question],
    }


def parse_complete_exam_objects(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    idx = text.index("[") + 1
    exams: list[dict] = []
    while True:
        match = re.search(r"\S", text[idx:])
        if not match:
            break
        idx += match.start()
        if text[idx] == "]":
            break
        try:
            exam, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            break
        exams.append(exam)
        idx = end
        comma = re.match(r"\s*,", text[idx:])
        if comma:
            idx += comma.end()
    return exams


def collect_translation_references(answer_doc: dict, year: int) -> dict[int, str]:
    content = answer_doc["content"].get(str(year), {})
    refs = {1: "", 2: ""}
    for page_value in content.values():
        if not isinstance(page_value, dict):
            continue
        sections = page_value.get("sections", {})
        for section_name, section_value in sections.items():
            if "bersetzung" not in section_name and "脺bersetzung" not in section_name:
                continue
            if not isinstance(section_value, dict):
                continue
            zh_title = section_value.get("德译汉参考译文_title", "").strip()
            zh_text = section_value.get("德译汉参考译文_text", "").strip()
            zh_text_continued = section_value.get("德译汉参考译文_text_continued", "").strip()
            de_title = section_value.get("汉译德参考译文_title", "").strip()
            de_text = section_value.get("汉译德参考译文_text", "").strip()

            if zh_title or zh_text or zh_text_continued:
                pieces = [part for part in [zh_title, zh_text, zh_text_continued] if part]
                refs[1] = "\n\n".join(pieces).strip()
            if de_title or de_text:
                pieces = [part for part in [de_title, de_text] if part]
                refs[2] = "\n\n".join(pieces).strip()
    return refs


def first_nonempty_line(text: str) -> str:
    for raw_line in normalize_text(text).splitlines():
        line = raw_line.strip()
        if line:
            return line
    return ""


def first_meaningful_prompt_line(text: str) -> str:
    for raw_line in normalize_text(text).splitlines():
        line = raw_line.strip(" *")
        if not line:
            continue
        if re.match(r"^(?:[AB]\.\s*)?Übersetzen Sie", line):
            continue
        if re.match(r"^(?:[AB]\.\s*)?Ubersetzen Sie", line):
            continue
        if re.match(r"^(?:©\s*)?VI\.?\s*Schriftlicher Ausdruck", line):
            continue
        if line.startswith("Aufgabe:"):
            continue
        return line
    return first_nonempty_line(text)


def choose_prompt_stem(text: str) -> str:
    line = first_meaningful_prompt_line(text)
    if line and len(line) <= 120:
        return line
    return ""


def extract_subprompts_from_text(text: str) -> list[str]:
    subprompts = re.findall(r"(?m)^(?:[0-9]+[.)]|[a-c]\)|[-•])\s*(.+)$", text)
    return [clean_block(item) for item in subprompts if clean_block(item)]


def normalize_prompt_markdown(text: str) -> str:
    value = normalize_text(text)
    value = re.sub(r"(?m)^\s*####\s*", "", value)
    value = re.sub(r"(?m)^\s*###\s*", "", value)
    value = re.sub(r"(?m)^\s*\*(.+?)\*\s*$", r"\1", value)
    value = value.replace("**", "")
    value = value.replace("*", "")
    value = re.sub(r"\((\d+)\s*P\)", r"(\1 P)", value)
    value = re.sub(r"\((\d+)\s*Punkte\)", r"(\1 Punkte)", value)
    value = re.sub(r"(?m)^\s*©\s*", "", value)
    value = re.sub(r"(?m)^Thema:\s*(\S.+)$", r"Thema:\n\n\1", value)
    value = re.sub(r"(?<!\n)(Tabelle:)", r"\n\n\1", value)
    value = re.sub(r"(?m)^(Tabelle:[^\n]+)\s*(?=\|)", r"\1\n", value)
    value = re.sub(r"(?m)^(Aufgabe:[^\n]*?)\s*(?=(?:[0-9]+[.)]|[a-c]\)|[-•]))", r"\1\n\n", value)
    value = re.sub(r"[ \t]+\n", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def strip_writing_heading(text: str) -> str:
    value = normalize_prompt_markdown(text)
    value = re.sub(
        r"(?mis)^(?:(?:VI|VL|V1)\.?\s*)?Schriftlicher Ausdruck\s*\(30\s*Punkte\)\s*\n*",
        "",
        value,
    )
    return value.strip()


def make_translation_prompt(label: str, target_language: str, body_text: str) -> str:
    return normalize_prompt_markdown(
        f"{label}. Übersetzen Sie den folgenden Text ins {target_language}! (25 P)\n\n{body_text.strip()}"
    )


def override_question_payload(prompt_text: str) -> dict:
    normalized = normalize_prompt_markdown(prompt_text)
    return {
        "prompt_text": normalized,
        "stem": choose_prompt_stem(normalized),
    }


def override_writing_payload(prompt_text: str) -> dict:
    normalized = strip_writing_heading(prompt_text)
    stem = choose_prompt_stem(normalized)
    if stem == "Thema:":
        lines = [line.strip() for line in normalized.splitlines() if line.strip()]
        for candidate in lines[1:]:
            candidate = candidate.split("Tabelle:")[0].strip()
            if not candidate:
                continue
            if len(candidate) <= 120:
                stem = candidate
                break
            sentence = candidate.split(".")[0].strip()
            if sentence and len(sentence) <= 120:
                stem = sentence
                break
    return {
        "prompt_text": normalized,
        "stem": stem,
        "subprompts": extract_subprompts_from_text(normalized),
    }


def build_translation_writing_curated(cleaned_sources: dict[int, str]) -> dict:
    curated = {
        "generated_at": now_iso(),
        "questions": {},
        "answers": {},
        "notes": [
            "翻译与写作题优先使用 cleaned/manual/19-22 清洗 JSON 源。",
            "若本地缺少高质量题干，则使用明确占位说明，避免继续回退到脏 OCR 文本。",
        ],
    }
    curated["notes"].extend(MANUAL_TRANSLATION_WRITING_OVERRIDES.get("notes", []))

    for year in [2016, 2017, 2018, 2023, 2025]:
        source_text = cleaned_sources.get(year)
        if not source_text:
            continue
        translation_set = parse_translation_set(year, source_text, "curated")
        for question in translation_set["questions"]:
            curated["questions"][question["id"]] = {
                **override_question_payload(question.get("prompt_text", "")),
                "source": str(CLEANED_TESTPAPER_OUTPUTS[year].relative_to(ROOT_DIR)),
            }

        writing_section = section_text(source_text, "writing")
        curated["questions"][f"{year}-writing-1"] = {
            **override_writing_payload(writing_section),
            "source": str(CLEANED_TESTPAPER_OUTPUTS[year].relative_to(ROOT_DIR)),
        }

    if SOURCE_19_22_EXAMS_PATH.exists():
        complete_exams = {exam["year"]: exam for exam in parse_complete_exam_objects(SOURCE_19_22_EXAMS_PATH)}
        for year in [2019, 2021]:
            exam = complete_exams.get(year)
            if not exam:
                continue
            for part in exam.get("parts", []):
                part_name = part.get("name", "")
                if "bersetzung" in part_name:
                    sections = part.get("sections", [])
                    for index, section in enumerate(sections, start=1):
                        label = "A" if index == 1 else "B"
                        target_language = "Chinesische" if index == 1 else "Deutsche"
                        qid = f"{year}-translation-{index}"
                        curated["questions"][qid] = {
                            **override_question_payload(
                                make_translation_prompt(label, target_language, section.get("text", ""))
                            ),
                            "source": str(SOURCE_19_22_EXAMS_PATH.relative_to(ROOT_DIR)),
                        }
                elif "Schriftlicher Ausdruck" in part_name:
                    prompt_text = part.get("text", "")
                    curated["questions"][f"{year}-writing-1"] = {
                        **override_writing_payload(prompt_text),
                        "source": str(SOURCE_19_22_EXAMS_PATH.relative_to(ROOT_DIR)),
                    }

    root_2022 = split_root_full_exam_by_year(read_md("full_exam_2019_2022"), 2022)
    curated["questions"]["2022-translation-1"] = {
        **override_question_payload(CURATED_2022_TRANSLATION_A_TEXT),
        "source": "manual:2022-translation-a",
    }
    curated["questions"]["2022-translation-2"] = {
        **override_question_payload(CURATED_2022_TRANSLATION_B_TEXT),
        "stem": "Übergang zu einer grünen und kohlenstoffarmen Entwicklung",
        "source": "manual:2022-translation-b-placeholder",
    }
    curated["questions"]["2022-writing-1"] = {
        **override_writing_payload(section_text(root_2022, "writing")),
        "source": "data/generated_md/root_pdf/德语专业八级真题2019-2022.md",
    }

    if SOURCE_19_22_ANSWERS_PATH.exists():
        answer_doc = read_json(SOURCE_19_22_ANSWERS_PATH, {"content": {}})
        for year in [2019, 2021, 2022]:
            refs = collect_translation_references(answer_doc, year)
            for idx in [1, 2]:
                ref_text = refs.get(idx, "").strip()
                if not ref_text:
                    continue
                curated["answers"][f"{year}-translation-{idx}"] = {
                    "display_answer": "见参考译文",
                    "explanation": clean_block(ref_text),
                }

    for qid, override in MANUAL_TRANSLATION_WRITING_OVERRIDES.get("questions", {}).items():
        override_type = override.get("type") or ("writing" if "-writing-" in qid else "translation")
        if override_type == "writing":
            payload = override_writing_payload(override.get("prompt_text", ""))
        else:
            payload = override_question_payload(override.get("prompt_text", ""))
        if override.get("stem"):
            payload["stem"] = override["stem"]
        payload["source"] = override.get("source", f"manual:{qid}")
        curated["questions"][qid] = payload

    for qid, override in MANUAL_TRANSLATION_WRITING_OVERRIDES.get("answers", {}).items():
        answer_payload = {}
        if override.get("display_answer"):
            answer_payload["display_answer"] = override["display_answer"]
        if override.get("explanation"):
            answer_payload["explanation"] = normalize_prompt_markdown(override["explanation"])
        if answer_payload:
            curated["answers"][qid] = answer_payload

    return curated


def apply_translation_writing_overrides(library_sets: list[dict], overrides: dict[str, dict]) -> None:
    for entry in library_sets:
        if entry.get("section") not in {"translation", "writing"}:
            continue
        for question in entry.get("questions", []):
            override = overrides.get(question.get("id"))
            if not override:
                continue
            question["prompt_text"] = override["prompt_text"]
            if override.get("stem"):
                question["stem"] = override["stem"]
            if override.get("source"):
                question["source"] = override["source"]
            if entry.get("section") == "writing":
                question["subprompts"] = override.get("subprompts", [])


def apply_reading_passage_overrides(library_sets: list[dict], overrides: dict[int, dict[str, str]]) -> None:
    for entry in library_sets:
        if entry.get("section") != "reading":
            continue
        year = entry.get("year")
        year_overrides = overrides.get(year)
        if not year_overrides:
            continue
        for group in entry.get("groups", []):
            group_id = group.get("id", "")
            if group_id.endswith("-a") and year_overrides.get("a"):
                group["shared_context"] = normalize_prompt_markdown(year_overrides["a"])
            elif group_id.endswith("-b") and year_overrides.get("b"):
                group["shared_context"] = normalize_prompt_markdown(year_overrides["b"])


def normalize_exercise_answer(value: str | None) -> str | None:
    token = clean_inline(value or "").upper()
    if not token:
        return None
    if token in {"T", "R"}:
        return "R"
    if token == "F":
        return "F"
    if token in {"A", "B", "C", "D"}:
        return token
    return None


EXERCISE_OPTION_LABELS = ("A", "B", "C", "D", "R", "F", "T")
EXERCISE_BLEED_MARKERS = [
    r"\bTeil\s+[IVX]+\b",
    r"Übersetzen Sie",
    r"Ubersetzen Sie",
    r"Schreiben Sie",
    r"Ergänzen Sie",
    r"Erganzen Sie",
    r"Setzen Sie",
    r"Füllen Sie",
    r"Fiillen Sie",
    r"Fiullen Sie",
    r"Was ist richtig\?",
    r"Lesen Sie den Text",
    r"Welche Lösung",
    r"Welche Losung",
    r"Formen Sie",
    r"Verbinden Sie",
    r"Formulieren Sie",
    r"Wählen Sie",
    r"Wahlen Sie",
    r"Direkte Rede",
    r"Welcher Nebensatz",
    r"Das Eingeständnis der Unwissenheit",
    r"Das Eingestandnis der Unwissenheit",
    r"Der Erwerb neuer Fähigkeiten",
    r"Der Erwerb neuer Fahigkeiten",
]


def trim_exercise_fragment(text: str) -> str:
    value = normalize_text(text)
    score_match = re.search(r"\(\s*\d+\s*P(?:x\d+\s*=\s*\d+\s*P)?\s*\)", value, re.IGNORECASE)
    if score_match and score_match.start() > 4:
        value = value[: score_match.start()]
    for pattern in EXERCISE_BLEED_MARKERS:
        match = re.search(pattern, value, re.IGNORECASE)
        if match and match.start() > 8:
            value = value[: match.start()]
            break
    value = re.sub(r"\s+", " ", value)
    return value.strip(" ,.;:|/-")


def normalize_exercise_option_ocr(text: str) -> str:
    value = normalize_text(text)
    fixes = [
        (r"\bDB\b", "B"),
        (r"\bBb\b", "B"),
        (r"\bCc\b", "C"),
        (r"(?<!\w)[€Є]\s*[.,:：]\s*", "C. "),
        (r"(?<!\w)[€Є](?=\s+\S)", "C"),
        (r"(?<=\b\d)\s+([A-DRFT])\s+(?=\d)", r" \1. "),
    ]
    for pattern, replacement in fixes:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    return value


def trim_exercise_stem(text: str, number: int, question_type: str) -> str:
    value = clean_block(text or "")
    score_match = re.search(r"\(\s*\d+\s*P(?:x\d+\s*=\s*\d+\s*P)?\s*\)", value, re.IGNORECASE)
    if score_match and score_match.start() > 16:
        value = value[: score_match.start()]
    if question_type == "single-choice":
        option_match = re.search(r"(?<!\w)A\s*[.,:：]\s*\S", value, re.IGNORECASE)
        if option_match:
            if option_match.start() <= 3:
                value = ""
            elif option_match.start() > 20:
                value = value[: option_match.start()]
    if question_type != "prompt" and number:
        for offset in range(1, 7):
            match = re.search(rf"(?<!\d){number + offset}[.,]", value)
            if match and match.start() > 24:
                value = value[: match.start()]
                break
    value = trim_exercise_fragment(value)
    return clean_block(value)


def split_exercise_options(text: str) -> dict[str, str]:
    normalized_text = normalize_exercise_option_ocr(text)
    matches = list(
        re.finditer(
            r"(?<!\w)([A-DRFT])(?:\s*[.,:：]\s*|\s+)(?=\S)",
            normalized_text,
            re.IGNORECASE,
        )
    )
    if not matches:
        return {}

    options: dict[str, str] = {}
    for index, match in enumerate(matches):
        label = match.group(1).upper()
        if label == "T":
            label = "R"
        if label in options:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized_text)
        fragment = trim_exercise_fragment(normalized_text[start:end])
        if fragment:
            options[label] = fragment
    return options


def normalize_exercise_options(raw_options: dict | None) -> dict[str, str]:
    if not raw_options:
        return {}

    combined_parts: list[str] = []
    fallback: dict[str, str] = {}

    for raw_key, raw_value in raw_options.items():
        key = clean_inline(str(raw_key)).upper()
        if key == "T":
            key = "R"
        value = normalize_exercise_option_ocr(str(raw_value or ""))
        if not value:
            continue

        if key in EXERCISE_OPTION_LABELS:
            fallback[key] = trim_exercise_fragment(value)
            if not re.match(rf"^\s*{re.escape(key)}\s*[.:：]", value):
                value = f"{key}. {value}"
            combined_parts.append(value)
        else:
            combined_parts.append(f"{key} {value}".strip())

    split = split_exercise_options(" ".join(combined_parts))
    if split:
        return {key: value for key, value in split.items() if value}
    return {key: value for key, value in fallback.items() if value}


def infer_exercise_question_type(section: str, number: int, options: dict[str, str], normalized_answer: str | None) -> str:
    section_text = (section or "").casefold()
    if normalized_answer in {"R", "F"}:
        return "true-false"
    if options and set(options).issubset({"R", "F", "T"}):
        return "true-false"
    if options and (len(options) >= 2 or normalized_answer in {"A", "B", "C", "D"}):
        return "single-choice"
    if "schreib" in section_text or "ubersetzung" in section_text or "übersetzung" in section_text:
        return "prompt"
    if "landeskunde" in section_text:
        return "true-false"
    if "hoerverstehen" in section_text or "hörverstehen" in section_text:
        return "true-false" if number <= 10 else "prompt"
    return "prompt"


def build_exercise_question(
    set_id: str,
    source_kind: str,
    raw_question: dict,
    year: int | None = None,
    display_number: int | None = None,
) -> tuple[dict, dict | None]:
    original_number = int(raw_question.get("question_no") or raw_question.get("sequence") or 0)
    number = int(display_number or raw_question.get("sequence") or original_number or 0)
    section = clean_inline(raw_question.get("section") or "Exercise")
    options = normalize_exercise_options(raw_question.get("options") or {})
    normalized_answer = normalize_exercise_answer(raw_question.get("answer"))
    question_type = infer_exercise_question_type(section, original_number, options, normalized_answer)
    stem = trim_exercise_stem(raw_question.get("stem") or "", original_number or number, question_type)
    question_id = f"{set_id}-{number}"

    payload = {
        "id": question_id,
        "set_id": set_id,
        "year": year,
        "section": source_kind,
        "number": number,
        "original_number": original_number,
        "group_id": f"{set_id}-group",
        "group_label": "A",
        "instruction": section or "Exercise",
        "question_type": question_type,
        "stem": stem,
        "options": options,
        "source_pdf": raw_question.get("source", {}).get("pdf") or "",
        "source_page_start": raw_question.get("source", {}).get("page_start"),
        "source_page_end": raw_question.get("source", {}).get("page_end"),
        "source_section": section,
    }
    if raw_question.get("explanation"):
        payload["explanation"] = clean_block(raw_question["explanation"])
    if question_type == "prompt":
        payload["prompt_text"] = stem

    answer_entry = {"correct_option": normalized_answer} if normalized_answer else None
    return payload, answer_entry


def build_exercise_sets() -> tuple[list[dict], dict]:
    exercise_sets: list[dict] = []
    answer_updates: dict[str, dict] = {}

    testpaper_path = next(EXERCISE_JSON_DIR.rglob("*2023.json"), None)
    if testpaper_path:
        source = read_json(testpaper_path, {}) or {}
        set_id = "exercise-2023-paper"
        questions = []
        for index, raw_question in enumerate(source.get("questions", []), start=1):
            question, answer_entry = build_exercise_question(set_id, "exercise", raw_question, year=2023, display_number=index)
            questions.append(question)
            if answer_entry:
                answer_updates[question["id"]] = answer_entry

        groups = []
        seen_sections: dict[str, str] = {}
        for question in questions:
            label = question.get("source_section") or "Exercise"
            group_id = seen_sections.get(label)
            if not group_id:
                group_id = f"{set_id}-g{len(seen_sections) + 1}"
                seen_sections[label] = group_id
                groups.append(build_set_group(group_id, label, label, None, None, "standard", question_numbers=[]))
            question["group_id"] = group_id
            question["group_label"] = label
            question["instruction"] = label

        for group in groups:
            group["question_numbers"] = [question["number"] for question in questions if question["group_id"] == group["id"]]

        exercise_sets.append(
            {
                "id": set_id,
                "year": 2023,
                "section": "exercise",
                "title": "2023 真题练习",
                "question_count": len(questions),
                "groups": groups,
                "questions": questions,
            }
        )

    country_path = next(EXERCISE_JSON_DIR.rglob("*1000*.json"), None)
    if country_path:
        source = read_json(country_path, {}) or {}
        grouped: dict[int, list[dict]] = {}
        for raw_question in source.get("questions", []):
            test_no = int(raw_question.get("test_no") or 0)
            grouped.setdefault(test_no, []).append(raw_question)

        for test_no, bucket in sorted(grouped.items()):
            bucket.sort(key=lambda item: int(item.get("sequence") or item.get("question_no") or 0))
            for chunk_index, start in enumerate(range(0, len(bucket), 50), start=1):
                chunk = bucket[start : start + 50]
                set_id = f"exercise-country-{test_no}-{chunk_index}"
                questions = []
                for index, raw_question in enumerate(chunk, start=1):
                    question, answer_entry = build_exercise_question(set_id, "exercise", raw_question, display_number=index)
                    question["group_id"] = f"{set_id}-group"
                    question["group_label"] = "练习"
                    questions.append(question)
                    if answer_entry:
                        answer_updates[question["id"]] = answer_entry

                exercise_sets.append(
                    {
                        "id": set_id,
                        "year": None,
                        "section": "exercise",
                        "title": f"国情 1000 题 · Test {test_no} · 第 {chunk_index} 组",
                        "question_count": len(questions),
                        "groups": [
                            build_set_group(
                                f"{set_id}-group",
                                "练习",
                                "练习材料",
                                None,
                                None,
                                "standard",
                                question_numbers=[question["number"] for question in questions],
                            )
                        ],
                        "questions": questions,
                    }
                )

    return exercise_sets, answer_updates


def backup_current_files() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / timestamp
    target.mkdir(parents=True, exist_ok=True)
    for path in [QUESTIONS_PATH, ANSWER_KEY_PATH, DATA_DIR / "answer_key.template.json"]:
        if path.exists():
            shutil.copy2(path, target / f"{path.name}.bak")
    return target


def build_library_answers(cleaned_sources: dict[int, str] | None = None) -> dict:
    answers: dict[str, dict] = {}
    cleaned_sources = cleaned_sources or {}

    text_2016 = cleaned_sources.get(2016)
    if text_2016:
        for number, payload in parse_answer_pdf_style(text_2016, 76, 110).items():
            if 76 <= number <= 90:
                answers[f"2016-reading-{number}"] = payload
            elif 91 <= number <= 110:
                answers[f"2016-landeskunde-{number}"] = payload

    text_2017 = cleaned_sources.get(2017)
    if text_2017:
        for number, payload in parse_answer_pdf_style(text_2017, 71, 105).items():
            if 71 <= number <= 85:
                answers[f"2017-reading-{number}"] = payload
            elif 86 <= number <= 105:
                answers[f"2017-landeskunde-{number}"] = payload

    text_2018 = cleaned_sources.get(2018) or read_md("2018_with_answers")
    for number, payload in parse_answer_pdf_style(text_2018, 71, 105).items():
        if 71 <= number <= 85:
            answers[f"2018-reading-{number}"] = payload
        elif 86 <= number <= 105:
            answers[f"2018-landeskunde-{number}"] = payload

    text_2023 = cleaned_sources.get(2023)
    if text_2023:
        for number, payload in parse_answer_pdf_style(text_2023, 11, 105).items():
            if 11 <= number <= 30:
                answers[f"2023-listening-{number}"] = payload
            elif 71 <= number <= 85:
                answers[f"2023-reading-{number}"] = payload
            elif 86 <= number <= 105:
                answers[f"2023-landeskunde-{number}"] = payload

        answers["2023-translation-1"] = {
            "display_answer": "见参考译文",
            "explanation": clean_block(
                """
变化中的媒体系统

媒体系统不仅仅在德国经历了深刻的变革。有些人认为这是自15世纪印刷术发明以来最大的一次变革，而正是印刷术才开启了近代大众传媒的出现。事实上，由印刷媒体所主导的时代，即所谓的“古腾堡宇宙”，似乎正逐渐被新媒体所取代。

然而，迄今尚不能说互联网已经取代了“旧”媒体，因为从总人口来看，它仍然没有特别重大的影响。它只是在20至29岁的年龄组中上升为主要的信息媒介。对于老年人来说，私人交谈暂时仍是社会交流的首要形式，而年轻人则更青睐新信息技术的混合形式。由此，被动的接收者和消费者变成了主动的生产者和参与者。

翻译要点：
tiefgreifend 深刻的，彻底的
Massenmedien in der Neuzeit 近代大众传媒
Gutenberg-Universum 古腾堡宇宙
fällt ... ins Gewicht 有分量，重要，举足轻重
Mischformen 混合形式
                """
            ),
        }
        answers["2023-translation-2"] = {
            "display_answer": "见参考译文",
            "explanation": clean_block(
                """
Die Seidenstraße in der Gegenwart

Vor über 2000 Jahren unternahm Zhang Qian diplomatische Missionen in die „westlichen Regionen“ und erschloss eine Seidenstraße, die Asien mit Europa verband. Das war ein Weg des Friedens, der den politischen, wirtschaftlichen und kulturellen Austausch symbolisierte. Die Seidenstraße prosperierte über 1700 Jahre.

Heutzutage hat China die neue Initiative „Ein Gürtel und eine Straße“ aufgestellt, die auf gegenseitigem Respekt und Vertrauen beruht. Sie verleiht der alten Seidenstraße neues Leben und trägt den großen Traum von Entwicklung und Prosperität aller Länder entlang der Straße. Deshalb entspricht diese Initiative der Entwicklungstendenz der globalen und regionalen Zusammenarbeit.

翻译要点：
“西域” = die westlichen Regionen
“开辟丝绸之路” = eine Seidenstraße erschließen
“一带一路” = Ein Gürtel und eine Straße / die Seidenstraßeninitiative
“繁荣” = prosperieren
“符合趋势” = der Tendenz entsprechen
                """
            ),
        }

    text_2025 = cleaned_sources.get(2025) or read_md("2025_answers")
    for number, payload in parse_answer_pdf_style(text_2025, 11, 105).items():
        if 11 <= number <= 30:
            answers[f"2025-listening-{number}"] = payload
        elif 71 <= number <= 85:
            answers[f"2025-reading-{number}"] = payload
        elif 86 <= number <= 105:
            answers[f"2025-landeskunde-{number}"] = payload

    return answers


def select_library_exam_text(year: int, cleaned_sources: dict[int, str], full_root: str) -> str:
    cleaned = cleaned_sources.get(year)
    # Prefer curated cleaned/manual sources whenever they exist.
    # Silent fallback to OCR text makes translation/reading prompts regress.
    if cleaned and year != 2018:
        return cleaned
    if year == 2018 and cleaned and "[原文略，见前]" not in cleaned:
        return cleaned
    if year in {2019, 2021, 2022}:
        return split_root_full_exam_by_year(full_root, year)
    if year == 2018:
        return read_md("2018_exam")
    raise ValueError(f"Missing curated library source for year {year}")


def build_library_sets(cleaned_sources: dict[int, str] | None = None) -> tuple[list[dict], dict]:
    full_root = read_md("full_exam_2019_2022")
    library_sets = []
    answer_updates = build_library_answers(cleaned_sources)
    cleaned_sources = cleaned_sources or {}
    cleaned_sources = cleaned_sources or {}

    source_map = {
        2016: "material/testpaperandanswer/2016德语专八真题及解析.pdf",
        2017: "material/testpaperandanswer/2017德语专八真题及解析.pdf",
        2018: "material/testpaperandanswer/2018德语专八真题.pdf",
        2019: "德语专业八级真题2019-2022.pdf",
        2021: "德语专业八级真题2019-2022.pdf",
        2022: "德语专业八级真题2019-2022.pdf",
        2023: "material/manual/2023-tem8-user-provided.md",
        2025: "material/testpaperandanswer/2025专八.pdf",
    }

    for year in [2016, 2017, 2018, 2019, 2021, 2022, 2023, 2025]:
        exam_text = select_library_exam_text(year, cleaned_sources, full_root)

        source_pdf = source_map[year]
        if year in {2016, 2017, 2018, 2023, 2025} and cleaned_sources.get(year):
            try:
                listening_set, listening_answers = parse_cleaned_listening_set(year, cleaned_sources[year], source_pdf)
                library_sets.append(listening_set)
                answer_updates.update(listening_answers)
            except Exception as exc:
                print(f"[WARN] cleaned listening skipped for {year}: {exc}")
                if year == 2025:
                    try:
                        library_sets.append(parse_listening_set(year, exam_text, source_pdf))
                    except Exception as inner_exc:
                        print(f"[WARN] listening skipped for {year}: {inner_exc}")
        elif year != 2018:
            try:
                library_sets.append(parse_listening_set(year, exam_text, source_pdf))
            except Exception as exc:
                print(f"[WARN] listening skipped for {year}: {exc}")

        for builder in [parse_reading_set, parse_landeskunde_set, parse_translation_set, parse_writing_set]:
            try:
                library_sets.append(builder(year, exam_text, source_pdf))
            except Exception as exc:
                print(f"[WARN] {builder.__name__} skipped for {year}: {exc}")

    return library_sets, answer_updates


def build_wg_years_and_answers(cleaned_sources: dict[int, str] | None = None) -> tuple[list[dict], dict]:
    current_dataset = read_json(QUESTIONS_PATH, {"meta": {}, "years": []})
    current_answers = read_json(ANSWER_KEY_PATH, {})
    cleaned_sources = cleaned_sources or {}
    years = []
    answer_updates = deepcopy(current_answers)

    for year in [2019, 2021, 2022]:
        year_entry = parse_year_entry_from_existing(current_dataset, year)
        years.append(year_entry)
        for number, correct in OFFICIAL_WG_ANSWERS[year].items():
            answer_updates.setdefault(f"{year}-{number}", {})
            answer_updates[f"{year}-{number}"]["correct_option"] = correct

    md_2023_exam = cleaned_sources.get(2023)
    if md_2023_exam:
        year_2023, answers_2023 = build_2018_or_2025_wg_year(
            2023,
            md_2023_exam,
            "material/manual/2023-tem8-user-provided.md",
            answer_source_text=md_2023_exam,
        )
        years.append(year_2023)
        answer_updates.update(answers_2023)

    md_2016 = cleaned_sources.get(2016) or read_md("2016_with_answers")
    year_2016, answers_2016 = build_2016_wg_year(md_2016, "material/testpaperandanswer/2016德语专八真题及解析.pdf")
    years.append(year_2016)
    answer_updates.update(answers_2016)

    md_2017 = cleaned_sources.get(2017) or read_md("2017_with_answers")
    year_2017, answers_2017 = build_2017_wg_year(md_2017, "material/testpaperandanswer/2017德语专八真题及解析.pdf")
    years.append(year_2017)
    answer_updates.update(answers_2017)

    md_2018_exam = cleaned_sources.get(2018) or read_md("2018_exam")
    year_2018, answers_2018 = build_2018_or_2025_wg_year(2018, md_2018_exam, "material/testpaperandanswer/2018德语专八真题.pdf")
    years.append(year_2018)
    answer_updates.update(answers_2018)

    md_2025_exam = cleaned_sources.get(2025) or read_md("2025_exam")
    year_2025, answers_2025 = build_2018_or_2025_wg_year(2025, md_2025_exam, "material/testpaperandanswer/2025专八.pdf")
    years.append(year_2025)
    answer_updates.update(answers_2025)

    years.sort(key=lambda item: item["year"])
    return years, answer_updates


def build_dataset() -> tuple[dict, dict]:
    years, answer_key = build_wg_years_and_answers()
    library_sets, library_answers = build_library_sets()
    exercise_sets, exercise_answers = build_exercise_sets()
    answer_key.update(library_answers)
    answer_key.update(exercise_answers)

    question_total = sum(entry["question_count"] for entry in years)
    library_total = sum(entry["question_count"] for entry in library_sets)
    exercise_total = sum(entry["question_count"] for entry in exercise_sets)
    dataset = {
        "meta": {
            "generated_at": now_iso(),
            "source_pdf": "德语专业八级真题2019-2022.pdf",
            "section": "Wortschatz und Grammatik",
            "available_years": [entry["year"] for entry in years],
            "notes": [
                "已补入 2016、2017、2018、2025 年词汇语法题库。",
                "已接入 2018、2019、2021、2022、2025 年听力、阅读、国情、翻译、写作材料。",
                "已接入 exercise 材料中的 2023 真题和国情 1000 题练习集。",
            ],
            "year_question_count": question_total,
            "library_question_count": library_total,
            "exercise_question_count": exercise_total,
        },
        "years": years,
        "library": library_sets,
        "exercise_sets": exercise_sets,
    }
    return dataset, answer_key


def build_library_answers(cleaned_sources: dict[int, str] | None = None) -> dict:
    answers: dict[str, dict] = {}
    cleaned_sources = cleaned_sources or {}

    text_2016 = cleaned_sources.get(2016)
    if text_2016:
        for number, payload in parse_answer_pdf_style(text_2016, 76, 110).items():
            if 76 <= number <= 90:
                answers[f"2016-reading-{number}"] = payload
            elif 91 <= number <= 110:
                answers[f"2016-landeskunde-{number}"] = payload

    text_2017 = cleaned_sources.get(2017)
    if text_2017:
        for number, payload in parse_answer_pdf_style(text_2017, 71, 105).items():
            if 71 <= number <= 85:
                answers[f"2017-reading-{number}"] = payload
            elif 86 <= number <= 105:
                answers[f"2017-landeskunde-{number}"] = payload

    text_2018 = cleaned_sources.get(2018) or read_md("2018_with_answers")
    for number, payload in parse_answer_pdf_style(text_2018, 71, 105).items():
        if 71 <= number <= 85:
            answers[f"2018-reading-{number}"] = payload
        elif 86 <= number <= 105:
            answers[f"2018-landeskunde-{number}"] = payload

    text_2023 = cleaned_sources.get(2023)
    if text_2023:
        for number, payload in parse_answer_pdf_style(text_2023, 11, 105).items():
            if 11 <= number <= 30:
                answers[f"2023-listening-{number}"] = payload
            elif 71 <= number <= 85:
                answers[f"2023-reading-{number}"] = payload
            elif 86 <= number <= 105:
                answers[f"2023-landeskunde-{number}"] = payload
        answers["2023-translation-1"] = {
            "display_answer": "见参考译文",
            "explanation": clean_block(
                """
变化中的媒体系统

媒体系统不仅仅在德国经历了深刻的变革。有些人认为这是自15世纪印刷术发明以来最大的一次变革，而正是印刷术才开启了近代大众传媒的出现。事实上，由印刷媒体所主导的时代，即所谓的“古腾堡宇宙”，似乎正逐渐被新媒体所取代。

然而，迄今尚不能说互联网已经取代了“旧”媒体，因为从总人口来看，它仍然没有特别重大的影响。它只是在20至29岁的年龄组中上升为主要的信息媒介。对于老年人来说，私人交谈暂时仍是社会交流的首要形式，而年轻人则更青睐新信息技术的混合形式。由此，被动的接收者和消费者变成了主动的生产者和参与者。

翻译要点：
tiefgreifend 深刻的，彻底的
Massenmedien in der Neuzeit 近代大众传媒
Gutenberg-Universum 古腾堡宇宙
fällt ... ins Gewicht 有分量，重要，举足轻重
Mischformen 混合形式
                """
            ),
        }
        answers["2023-translation-2"] = {
            "display_answer": "见参考译文",
            "explanation": clean_block(
                """
Die Seidenstraße in der Gegenwart

Vor über 2000 Jahren unternahm Zhang Qian diplomatische Missionen in die „westlichen Regionen“ und erschloss eine Seidenstraße, die Asien mit Europa verband. Das war ein Weg des Friedens, der den politischen, wirtschaftlichen und kulturellen Austausch symbolisierte. Die Seidenstraße prosperierte über 1700 Jahre.

Heutzutage hat China die neue Initiative „Ein Gürtel und eine Straße“ aufgestellt, die auf gegenseitigem Respekt und Vertrauen beruht. Sie verleiht der alten Seidenstraße neues Leben und trägt den großen Traum von Entwicklung und Prosperität aller Länder entlang der Straße. Deshalb entspricht diese Initiative der Entwicklungstendenz der globalen und regionalen Zusammenarbeit.

翻译要点：
“西域” = die westlichen Regionen
“开辟丝绸之路” = eine Seidenstraße erschließen
“一带一路” = Ein Gürtel und eine Straße / die Seidenstraßeninitiative
“繁荣” = prosperieren
“符合趋势” = der Tendenz entsprechen
                """
            ),
        }

    text_2025 = cleaned_sources.get(2025) or read_md("2025_answers")
    for number, payload in parse_answer_pdf_style(text_2025, 11, 105).items():
        if 11 <= number <= 30:
            answers[f"2025-listening-{number}"] = payload
        elif 71 <= number <= 85:
            answers[f"2025-reading-{number}"] = payload
        elif 86 <= number <= 105:
            answers[f"2025-landeskunde-{number}"] = payload

    return answers


def build_library_sets(cleaned_sources: dict[int, str] | None = None) -> tuple[list[dict], dict]:
    full_root = read_md("full_exam_2019_2022")
    library_sets = []
    answer_updates = build_library_answers(cleaned_sources)
    cleaned_sources = cleaned_sources or {}

    source_map = {
        2016: "material/testpaperandanswer/2016德语专八真题及解析.pdf",
        2017: "material/testpaperandanswer/2017德语专八真题及解析.pdf",
        2018: "material/testpaperandanswer/2018德语专八真题.pdf",
        2019: "德语专业八级真题2019-2022.pdf",
        2021: "德语专业八级真题2019-2022.pdf",
        2022: "德语专业八级真题2019-2022.pdf",
        2023: "material/manual/2023-tem8-user-provided.md",
        2025: "material/testpaperandanswer/2025专八.pdf",
    }

    for year in [2016, 2017, 2018, 2019, 2021, 2022, 2023, 2025]:
        exam_text = select_library_exam_text(year, cleaned_sources, full_root)

        source_pdf = source_map[year]
        if year in {2016, 2017, 2018, 2023, 2025} and cleaned_sources.get(year):
            try:
                listening_set, listening_answers = parse_cleaned_listening_set(year, cleaned_sources[year], source_pdf)
                library_sets.append(listening_set)
                answer_updates.update(listening_answers)
            except Exception as exc:
                print(f"[WARN] cleaned listening skipped for {year}: {exc}")
                if year == 2025:
                    try:
                        library_sets.append(parse_listening_set(year, exam_text, source_pdf))
                    except Exception as inner_exc:
                        print(f"[WARN] listening skipped for {year}: {inner_exc}")
        elif year != 2018:
            try:
                library_sets.append(parse_listening_set(year, exam_text, source_pdf))
            except Exception as exc:
                print(f"[WARN] listening skipped for {year}: {exc}")

        for builder in [parse_reading_set, parse_landeskunde_set, parse_translation_set, parse_writing_set]:
            try:
                library_sets.append(builder(year, exam_text, source_pdf))
            except Exception as exc:
                print(f"[WARN] {builder.__name__} skipped for {year}: {exc}")

    return library_sets, answer_updates


def build_wg_years_and_answers(cleaned_sources: dict[int, str] | None = None) -> tuple[list[dict], dict]:
    current_dataset = read_json(QUESTIONS_PATH, {"meta": {}, "years": []})
    current_answers = read_json(ANSWER_KEY_PATH, {})
    cleaned_sources = cleaned_sources or {}
    years = []
    answer_updates = deepcopy(current_answers)

    for year in [2019, 2021, 2022]:
        year_entry = parse_year_entry_from_existing(current_dataset, year)
        years.append(year_entry)
        for number, correct in OFFICIAL_WG_ANSWERS[year].items():
            answer_updates.setdefault(f"{year}-{number}", {})
            answer_updates[f"{year}-{number}"]["correct_option"] = correct

    md_2023_exam = cleaned_sources.get(2023)
    if md_2023_exam:
        year_2023, answers_2023 = build_2018_or_2025_wg_year(
            2023,
            md_2023_exam,
            "material/manual/2023-tem8-user-provided.md",
            answer_source_text=md_2023_exam,
        )
        years.append(year_2023)
        answer_updates.update(answers_2023)

    md_2016 = cleaned_sources.get(2016) or read_md("2016_with_answers")
    year_2016, answers_2016 = build_2016_wg_year(md_2016, "material/testpaperandanswer/2016德语专八真题及解析.pdf")
    years.append(year_2016)
    answer_updates.update(answers_2016)

    md_2017 = cleaned_sources.get(2017) or read_md("2017_with_answers")
    year_2017, answers_2017 = build_2017_wg_year(md_2017, "material/testpaperandanswer/2017德语专八真题及解析.pdf")
    years.append(year_2017)
    answer_updates.update(answers_2017)

    md_2018_exam = cleaned_sources.get(2018) or read_md("2018_exam")
    year_2018, answers_2018 = build_2018_or_2025_wg_year(
        2018,
        md_2018_exam,
        "material/testpaperandanswer/2018德语专八真题.pdf",
        answer_source_text=cleaned_sources.get(2018),
    )
    years.append(year_2018)
    answer_updates.update(answers_2018)

    md_2025_exam = cleaned_sources.get(2025) or read_md("2025_exam")
    year_2025, answers_2025 = build_2018_or_2025_wg_year(
        2025,
        md_2025_exam,
        "material/testpaperandanswer/2025专八.pdf",
        answer_source_text=cleaned_sources.get(2025),
    )
    years.append(year_2025)
    answer_updates.update(answers_2025)

    years.sort(key=lambda item: item["year"])
    return years, answer_updates


def build_dataset() -> tuple[dict, dict]:
    cleaned_sources = ensure_cleaned_testpaper_sources()
    curated_translation_writing = build_translation_writing_curated(cleaned_sources)
    write_json(CURATED_TRANSLATION_WRITING_PATH, curated_translation_writing)
    years, answer_key = build_wg_years_and_answers(cleaned_sources)
    library_sets, library_answers = build_library_sets(cleaned_sources)
    apply_reading_passage_overrides(library_sets, MANUAL_READING_PASSAGES)
    apply_translation_writing_overrides(library_sets, curated_translation_writing["questions"])
    library_answers.update(curated_translation_writing["answers"])
    exercise_sets, exercise_answers = build_exercise_sets()
    answer_key.update(library_answers)
    answer_key.update(exercise_answers)

    question_total = sum(entry["question_count"] for entry in years)
    library_total = sum(entry["question_count"] for entry in library_sets)
    exercise_total = sum(entry["question_count"] for entry in exercise_sets)
    dataset = {
        "meta": {
            "generated_at": now_iso(),
            "source_pdf": "德语专业八级真题2019-2022.pdf",
            "section": "Wortschatz und Grammatik",
            "available_years": [entry["year"] for entry in years],
            "notes": [
                "已接入 material/testpaperandanswer/cleaned.txt 的清洗数据，并回写 2016、2017、2018、2025 年拆分源码。",
                "已补入 2016、2017、2018、2025 年词汇语法题库。",
                "已接入 2018、2019、2021、2022、2025 年听力、阅读、国情、翻译、写作材料。",
                "已接入 exercise 材料中的 2023 真题和国情 1000 题练习集。",
                "2016、2017、2018、2023、2025 阅读原文已使用手工校准覆盖源。",
                "翻译与写作题已统一写入 generated_json/translation_writing_curated.json，并以该干净源覆盖网站数据。",
            ],
            "year_question_count": question_total,
            "library_question_count": library_total,
            "exercise_question_count": exercise_total,
        },
        "years": years,
        "library": library_sets,
        "exercise_sets": exercise_sets,
    }
    return dataset, answer_key


def main() -> None:
    backup_path = backup_current_files()
    dataset, answer_key = build_dataset()
    write_json(QUESTIONS_PATH, dataset)
    write_json(ANSWER_KEY_PATH, answer_key)
    print(f"[OK] backup: {backup_path}")
    print(f"[OK] years: {len(dataset['years'])}")
    print(f"[OK] library sets: {len(dataset['library'])}")
    print(f"[OK] exercise sets: {len(dataset['exercise_sets'])}")
    print(f"[OK] answers: {len(answer_key)}")


if __name__ == "__main__":
    main()
