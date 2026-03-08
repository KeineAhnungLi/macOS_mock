from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
QUESTIONS_PATH = DATA_DIR / "questions.json"
ANSWER_KEY_PATH = DATA_DIR / "answer_key.json"
BACKUP_DIR = DATA_DIR / "backups"

GENERATED_MD_DIR = DATA_DIR / "generated_md"
TESTPAPER_MD_DIR = GENERATED_MD_DIR / "testpaperandanswer"
ROOT_PDF_MD_DIR = GENERATED_MD_DIR / "root_pdf"

EXERCISE_JSON_DIR = ROOT_DIR / "material" / "exercise" / "专八" / "cleaned" / "json"

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
}


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


def clean_inline(text: str) -> str:
    value = normalize_text(text)
    for marker in BLEED_MARKERS:
        index = value.find(marker)
        if index > 0:
            value = value[:index]
    value = value.replace("___—", "_____")
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s*[~*|]+\s*$", "", value)
    return value.strip(" ,.;:-")


def clean_block(text: str) -> str:
    value = normalize_text(text)
    for marker in BLEED_MARKERS:
        index = value.find(marker)
        if index > 0:
            value = value[:index]
    value = value.replace("___—", "_____")
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


def parse_choice_block(block: str, number: int) -> tuple[str, dict[str, str]]:
    start_match = question_start_re(number).search(block)
    if not start_match:
        raise ValueError(f"Missing choice question {number}")

    body = block[start_match.end() :].strip()
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
    return clean_block(block[start_match.end() :])


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
        "stem": clean_block(stem),
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


def build_2018_or_2025_wg_year(year: int, exam_text: str, source_pdf: str) -> tuple[dict, dict]:
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
    q71 = question_start_re(71).search(section)
    q79 = question_start_re(79).search(section)
    shared1 = clean_block(section[text1_start:q71.start()]) if text1_start != -1 and q71 else None
    shared2 = clean_block(section[text2_start:q79.start()]) if text2_start != -1 and q79 else None

    groups.append(build_set_group(f"{year}-reading-a", "Text 1", "Lesen Sie den Text und kreuzen Sie die richtige Lösung an!", 71, 78, "shared-passage", shared1))
    groups.append(build_set_group(f"{year}-reading-b", "Text 2", "Lesen Sie den Text und kreuzen Sie die richtige Lösung an!", 79, 85, "shared-passage", shared2))

    for number in range(71, 86):
        block = question_block(section, 71, 85, number)
        stem, options = parse_choice_block(block, number)
        group_id = f"{year}-reading-a" if number <= 78 else f"{year}-reading-b"
        group_label = "Text 1" if number <= 78 else "Text 2"
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
    groups = [
        build_set_group(f"{year}-country-a", "A", "Welche der folgenden Aussagen sind richtig, welche falsch?", 86, 91, "standard"),
        build_set_group(f"{year}-country-b", "B", "Kreuzen Sie die richtige Lösung an!", 92, 105, "standard"),
    ]
    questions = []

    for number in range(86, 92):
        try:
            block = question_block(section, 86, 105, number)
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

    for number in range(92, 106):
        block = question_block(section, 86, 105, number)
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
    part_a = re.search(r"A\.\s*Ubersetzen.*?(?=\nB\.)", section, re.IGNORECASE | re.DOTALL)
    part_b = re.search(r"B\.\s*Ubersetzen.*", section, re.IGNORECASE | re.DOTALL)

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


def normalize_exercise_options(raw_options: dict | None) -> dict[str, str]:
    if not raw_options:
        return {}

    options: dict[str, str] = {}
    for raw_key, raw_value in raw_options.items():
        key = clean_inline(str(raw_key)).upper()
        value = str(raw_value or "")
        if key in {"A", "B", "C", "D"} and value:
            options[key] = clean_inline(value)
            continue

        combined = f"{raw_key} {raw_value}"
        matches = list(re.finditer(r"([A-D])[.:]?\s*(.+?)(?=(?:\s+[A-D][.:]?\s)|$)", combined, re.IGNORECASE))
        for match in matches:
            options[match.group(1).upper()] = clean_inline(match.group(2))

    return {key: value for key, value in options.items() if value}


def infer_exercise_question_type(section: str, number: int, options: dict[str, str], normalized_answer: str | None) -> str:
    section_text = (section or "").casefold()
    if "schreib" in section_text or "ubersetzung" in section_text or "übersetzung" in section_text:
        return "prompt"
    if options:
        return "single-choice"
    if normalized_answer in {"R", "F"}:
        return "true-false"
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
    stem = clean_block(raw_question.get("stem") or "")
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


def build_library_answers() -> dict:
    answers: dict[str, dict] = {}

    text_2018 = read_md("2018_with_answers")
    for number, payload in parse_answer_pdf_style(text_2018, 71, 105).items():
        if 71 <= number <= 85:
            answers[f"2018-reading-{number}"] = payload
        elif 86 <= number <= 105:
            answers[f"2018-landeskunde-{number}"] = payload

    text_2025 = read_md("2025_answers")
    for number, payload in parse_answer_pdf_style(text_2025, 11, 105).items():
        if 11 <= number <= 30:
            answers[f"2025-listening-{number}"] = payload
        elif 71 <= number <= 85:
            answers[f"2025-reading-{number}"] = payload
        elif 86 <= number <= 105:
            answers[f"2025-landeskunde-{number}"] = payload

    return answers


def build_library_sets() -> tuple[list[dict], dict]:
    full_root = read_md("full_exam_2019_2022")
    library_sets = []
    answer_updates = build_library_answers()

    source_map = {
        2018: "material/testpaperandanswer/2018德语专八真题.pdf",
        2019: "德语专业八级真题2019-2022.pdf",
        2021: "德语专业八级真题2019-2022.pdf",
        2022: "德语专业八级真题2019-2022.pdf",
        2025: "material/testpaperandanswer/2025专八.pdf",
    }

    for year in [2018, 2019, 2021, 2022, 2025]:
        if year in {2019, 2021, 2022}:
            exam_text = split_root_full_exam_by_year(full_root, year)
        elif year == 2018:
            exam_text = read_md("2018_exam")
        else:
            exam_text = read_md("2025_exam")

        source_pdf = source_map[year]
        if year != 2018:
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


def build_wg_years_and_answers() -> tuple[list[dict], dict]:
    current_dataset = read_json(QUESTIONS_PATH, {"meta": {}, "years": []})
    current_answers = read_json(ANSWER_KEY_PATH, {})
    years = []
    answer_updates = deepcopy(current_answers)

    for year in [2019, 2021, 2022]:
        year_entry = parse_year_entry_from_existing(current_dataset, year)
        years.append(year_entry)
        for number, correct in OFFICIAL_WG_ANSWERS[year].items():
            answer_updates.setdefault(f"{year}-{number}", {})
            answer_updates[f"{year}-{number}"]["correct_option"] = correct

    md_2016 = read_md("2016_with_answers")
    year_2016, answers_2016 = build_2016_wg_year(md_2016, "material/testpaperandanswer/2016德语专八真题及解析.pdf")
    years.append(year_2016)
    answer_updates.update(answers_2016)

    md_2017 = read_md("2017_with_answers")
    year_2017, answers_2017 = build_2017_wg_year(md_2017, "material/testpaperandanswer/2017德语专八真题及解析.pdf")
    years.append(year_2017)
    answer_updates.update(answers_2017)

    md_2018_exam = read_md("2018_exam")
    year_2018, answers_2018 = build_2018_or_2025_wg_year(2018, md_2018_exam, "material/testpaperandanswer/2018德语专八真题.pdf")
    years.append(year_2018)
    answer_updates.update(answers_2018)

    md_2025_exam = read_md("2025_exam")
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
