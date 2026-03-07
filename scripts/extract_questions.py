from __future__ import annotations

import io
import json
import logging
import os
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz
import pytesseract
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
OCR_DEBUG_DIR = DATA_DIR / "ocr_debug"
LOG_DIR = ROOT_DIR / "logs"
QUESTIONS_PATH = DATA_DIR / "questions.json"
ANSWER_TEMPLATE_PATH = DATA_DIR / "answer_key.template.json"

QUESTION_RANGE = range(31, 71)
SECTION_END_PATTERNS = (
    r"III\.\s*Leseverst[aä]ndnis",
    r"IIl\.\s*Leseverst[aä]ndnis",
    r"III\.\s*Leseverst[aä]ndnis",
    r"Ill\.\s*Leseverst[aä]ndnis",
    r"Leseverst[aä]ndnis",
)

COMMON_REPLACEMENTS = {
    "StraBen": "Straßen",
    "StraBenbahn": "Straßenbahn",
    "StraBenkünstlerin": "Straßenkünstlerin",
    "StraBenkinstlerin": "Straßenkünstlerin",
    "StraBe": "Straße",
    "MaBnahmen": "Maßnahmen",
    "MaB8nahmen": "Maßnahmen",
    "Ma&nahmen": "Maßnahmen",
    "Verfigung": "Verfügung",
    "Verfiigung": "Verfügung",
    "Flichtlings": "Flüchtlings",
    "Burgerkrieg": "Bürgerkrieg",
    "Biirgerkrieg": "Bürgerkrieg",
    "Krafte": "Kräfte",
    "tiberschreiten": "überschreiten",
    "tiberlaufen": "überlaufen",
    "GroBmutter": "Großmutter",
    "muB": "muss",
    "daB": "dass",
    "fur": "für",
    "uber": "über",
}

@dataclass(frozen=True)
class GroupConfig:
    group_id: str
    subsection: str
    label: str
    instruction: str
    start: int
    end: int
    ui_type: str
    context_anchor: str | None = None


YEAR_CONFIGS: dict[int, dict[str, Any]] = {
    2019: {
        "pages": list(range(6, 14)),
        "groups": [
            GroupConfig("2019-w-a", "Wortschatz", "A", "Ergänzen Sie das passende Wort im Funktionsverbgefüge!", 31, 35, "standard"),
            GroupConfig("2019-w-b", "Wortschatz", "B", "Was ist richtig?", 36, 40, "standard"),
            GroupConfig("2019-w-c", "Wortschatz", "C", "Bilden Sie die jeweils richtige Redewendung!", 41, 45, "standard"),
            GroupConfig("2019-w-d", "Wortschatz", "D", "Entscheiden Sie, welches Wort in die jeweilige Lücke passt!", 46, 55, "shared-passage", "Im kleinen Staat Bhutan"),
            GroupConfig("2019-g-a", "Grammatik", "A", "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?", 56, 58, "sentence-task"),
            GroupConfig("2019-g-b", "Grammatik", "B", "Formen Sie bitte die markierten Linksattribute in Relativsätze um!", 59, 60, "sentence-task"),
            GroupConfig("2019-g-c", "Grammatik", "C", "Verbinden Sie bitte die folgenden zwei Sätze!", 61, 61, "sentence-task"),
            GroupConfig("2019-g-d", "Grammatik", "D", "Formulieren Sie bitte den jeweils unterstrichenen Satzteil zu einem Nebensatz um!", 62, 63, "sentence-task"),
            GroupConfig("2019-g-e", "Grammatik", "E", "Wählen Sie die jeweils passende Umformung!", 64, 65, "sentence-task"),
            GroupConfig("2019-g-f", "Grammatik", "F", "Formen Sie bitte den Satz ins Passiv um!", 66, 66, "sentence-task"),
            GroupConfig("2019-g-g", "Grammatik", "G", "Welche Lösung enthält eine korrekte Form für die indirekte Rede?", 67, 67, "sentence-task"),
            GroupConfig("2019-g-h", "Grammatik", "H", "Füllen Sie bitte die Lücken aus!", 68, 70, "sentence-task"),
        ],
    },
    2021: {
        "pages": list(range(32, 40)),
        "groups": [
            GroupConfig("2021-w-a", "Wortschatz", "A", "Was ist richtig?", 31, 35, "standard"),
            GroupConfig("2021-w-b", "Wortschatz", "B", "Ergänzen Sie das passende Verb!", 36, 40, "standard"),
            GroupConfig("2021-w-c", "Wortschatz", "C", "Ergänzen Sie den fehlenden Ausdruck in den Redewendungen!", 41, 45, "standard"),
            GroupConfig("2021-w-d", "Wortschatz", "D", "Setzen Sie die angegebenen Wörter sinnvoll in den Text ein!", 46, 55, "shared-passage", "Die Freundschaft zwischen Goethe und Schiller"),
            GroupConfig("2021-g-a", "Grammatik", "A", "Welche Lösung enthält die passende Ersatzform des unterstrichenen Satzteils?", 56, 57, "sentence-task"),
            GroupConfig("2021-g-b", "Grammatik", "B", "Formen Sie bitte die markierten Linksattribute in Relativsätze um!", 58, 59, "sentence-task"),
            GroupConfig("2021-g-c", "Grammatik", "C", "Welche Lösung entspricht dem Inhalt des Aufgabensatzes?", 60, 60, "sentence-task"),
            GroupConfig("2021-g-d", "Grammatik", "D", "Welche Umwandlung trifft zu?", 61, 63, "sentence-task"),
            GroupConfig("2021-g-e", "Grammatik", "E", "Bilden Sie Sätze mit Konjunktionen!", 64, 65, "sentence-task"),
            GroupConfig("2021-g-f", "Grammatik", "F", "Formen Sie den folgenden Satz ins Passiv um!", 66, 66, "sentence-task"),
            GroupConfig("2021-g-g", "Grammatik", "G", "Welche Lösung enthält eine korrekte Form für die indirekte Rede?", 67, 67, "sentence-task"),
            GroupConfig("2021-g-h", "Grammatik", "H", "Füllen Sie die Lücken!", 68, 70, "sentence-task"),
        ],
    },
    2022: {
        "pages": list(range(59, 66)),
        "groups": [
            GroupConfig("2022-w-a", "Wortschatz", "A", "Ergänzen Sie das passende Nomen!", 31, 35, "standard"),
            GroupConfig("2022-w-b", "Wortschatz", "B", "Ergänzen Sie das passende Verb!", 36, 40, "standard"),
            GroupConfig("2022-w-c", "Wortschatz", "C", "Ergänzen Sie das Fehlende in den Redewendungen!", 41, 45, "standard"),
            GroupConfig("2022-w-d", "Wortschatz", "D", "Setzen Sie die angegebenen Wörter sinnvoll in den Text ein!", 46, 55, "shared-passage", "Die Romer in Germanien"),
            GroupConfig("2022-g-a", "Grammatik", "A", "Welche Präposition passt?", 56, 57, "sentence-task"),
            GroupConfig("2022-g-b", "Grammatik", "B", "Welche Umformulierung passt?", 58, 59, "sentence-task"),
            GroupConfig("2022-g-c", "Grammatik", "C", "Setzen Sie passende Pronominaladverbien mit wo- ein!", 60, 61, "sentence-task"),
            GroupConfig("2022-g-d", "Grammatik", "D", "Ergänzen Sie das richtige Partizip II!", 62, 62, "sentence-task"),
            GroupConfig("2022-g-e", "Grammatik", "E", "Setzen Sie die passenden Endungen ein!", 63, 64, "sentence-task"),
            GroupConfig("2022-g-f", "Grammatik", "F", "Welcher Nebensatz entspricht der Bedeutung der unterstrichenen Nominalisierung?", 65, 67, "sentence-task"),
            GroupConfig("2022-g-g", "Grammatik", "G", "Direkte Rede in indirekte Rede umwandeln: Welche Form ist richtig?", 68, 69, "sentence-task"),
            GroupConfig("2022-g-h", "Grammatik", "H", "Welche Umschreibung gibt den Inhalt des dass-Satzes wieder?", 70, 70, "sentence-task"),
        ],
    },
}

BLEED_MARKERS = sorted(
    {
        "Wortschatz (25 Punkte)",
        "Grammatik (15 Punkte)",
        "Leseverständnis",
        "Leseverstandnis",
        *(group.instruction for config in YEAR_CONFIGS.values() for group in config["groups"]),
    },
    key=len,
    reverse=True,
)


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("extract_questions")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(LOG_DIR / "extract.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


LOGGER = setup_logging()


def find_pdf() -> Path:
    pdfs = sorted(ROOT_DIR.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError("工作区内没有 PDF 文件。")
    return pdfs[0]


def resolve_tesseract_cmd() -> str:
    candidates = [
        os.environ.get("TESSERACT_CMD"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise FileNotFoundError("未找到 Tesseract，可通过环境变量 TESSERACT_CMD 指定路径。")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\n")
    text = text.replace("“", '"').replace("”", '"').replace("„", '"')
    text = text.replace("’", "'").replace("‘", "'").replace("—", "-")
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\b[O0]([ABCD])[.,]", r"\1.", text)
    text = re.sub(r"\b([ABCD])\1[.,]", r"\1.", text)
    text = re.sub(r"\b([ABCD])[«»“”\"'`´]+[.,]", r"\1.", text)
    for source, target in COMMON_REPLACEMENTS.items():
        text = text.replace(source, target)
    return text.strip()


def strip_heading_bleed(text: str) -> str:
    trimmed = text
    for marker in BLEED_MARKERS:
        index = trimmed.find(marker)
        if index > 0:
            trimmed = trimmed[:index]
    return trimmed


def clean_inline(text: str) -> str:
    text = normalize_text(text)
    text = strip_heading_bleed(text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\bQ[lI]?$", "", text).strip()
    text = re.sub(r"\bP$", "", text).strip()
    return text.strip(" _-+=|,.;:")


def clean_block(text: str) -> str:
    text = normalize_text(text)
    text = strip_heading_bleed(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line for line in text.splitlines() if not re.fullmatch(r"[\W_]+", line.strip()))
    text = re.sub(r"\bQ[lI]?$", "", text).strip()
    text = re.sub(r"\bP$", "", text).strip()
    return text.strip(" _-+=|")


def question_start_pattern(question_number: int) -> re.Pattern[str]:
    return re.compile(rf"(?<!\d){question_number}[.,]\s*", re.MULTILINE)


def find_question_start(text: str, question_number: int) -> int:
    match = question_start_pattern(question_number).search(text)
    if not match:
        raise ValueError(f"未找到题号 {question_number}。")
    return match.start()


def locate_section_body(year_text: str) -> str:
    start = find_question_start(year_text, 31)
    end_positions = [m.start() for pattern in SECTION_END_PATTERNS for m in [re.search(pattern, year_text, re.IGNORECASE)] if m]
    end = min(end_positions) if end_positions else len(year_text)
    return year_text[start:end].strip()


def extract_question_block(section_text: str, question_number: int) -> str:
    start = find_question_start(section_text, question_number)
    if question_number < 70:
        end = find_question_start(section_text, question_number + 1)
    else:
        end = len(section_text)
    return section_text[start:end].strip()


def parse_question_block(block: str, question_number: int) -> dict[str, Any]:
    start_match = question_start_pattern(question_number).search(block)
    if not start_match:
        raise ValueError(f"题块缺少起始题号 {question_number}。")

    body = block[start_match.end():].strip()
    option_matches = list(re.finditer(r"(^|[\s\-_}\]{(])([ABCD])[.,]\s*", body, re.MULTILINE))
    if len(option_matches) < 4:
        raise ValueError(f"题号 {question_number} 选项数量异常：{len(option_matches)}")
    if len(option_matches) > 4:
        option_matches = option_matches[:4]

    stem = clean_block(body[: option_matches[0].start(2)])
    options: dict[str, str] = {}
    for index, match in enumerate(option_matches):
        option_label = match.group(2)
        option_start = match.end()
        option_end = option_matches[index + 1].start(2) if index + 1 < len(option_matches) else len(body)
        options[option_label] = clean_inline(body[option_start:option_end])

    return {
        "number": question_number,
        "stem": stem,
        "options": options,
    }


def question_page_lookup(page_texts: dict[int, str], question_number: int) -> int:
    pattern = question_start_pattern(question_number)
    matched_page = None
    for page_number, page_text in page_texts.items():
        if pattern.search(page_text):
            matched_page = page_number
            break
    if matched_page is None:
        fallback_pages = [page_number for page_number, page_text in page_texts.items() if find_question_candidates(page_text)]
        matched_page = fallback_pages[-1] if fallback_pages else min(page_texts)
    return matched_page


def find_question_candidates(text: str) -> list[int]:
    return [int(value) for value in re.findall(r"(?<!\d)([3-6]\d|70)[.,]", text)]


def extract_shared_context(section_text: str, group: GroupConfig) -> str | None:
    if not group.context_anchor:
        return None

    lower_section = section_text.lower()
    lower_anchor = group.context_anchor.lower()
    anchor_index = lower_section.find(lower_anchor)
    question_index = find_question_start(section_text, group.start)
    if anchor_index != -1:
        context = section_text[anchor_index:question_index]
        return clean_block(context)

    fallback_start = lower_section.find(group.instruction.lower())
    if fallback_start == -1:
        fallback_start = max(0, lower_section.rfind(f"{group.label.lower()}.", 0, question_index))
    context = section_text[fallback_start:question_index]
    context = clean_block(context)
    if context:
        LOGGER.warning("题组 %s 的共享材料使用了回退截取。", group.group_id)
        return context

    LOGGER.warning("未在题组 %s 中找到共享材料锚点：%s", group.group_id, group.context_anchor)
    return None


def ocr_page(document: fitz.Document, page_number: int) -> str:
    page = document.load_page(page_number - 1)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2.1, 2.1), alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
    text = pytesseract.image_to_string(image, lang="eng", config="--oem 1 --psm 6")
    return normalize_text(text)


def build_year_payload(year: int, document: fitz.Document) -> dict[str, Any]:
    config = YEAR_CONFIGS[year]
    page_texts: dict[int, str] = {}
    for page_number in config["pages"]:
        LOGGER.info("OCR 年份 %s 第 %s 页", year, page_number)
        page_texts[page_number] = ocr_page(document, page_number)

    OCR_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    for page_number, text in page_texts.items():
        (OCR_DEBUG_DIR / f"{year}_page_{page_number:02d}.txt").write_text(text, encoding="utf-8")

    year_text = "\n\n".join(page_texts[page_number] for page_number in config["pages"])
    section_text = locate_section_body(year_text)
    (OCR_DEBUG_DIR / f"{year}_section_ii.txt").write_text(section_text, encoding="utf-8")

    groups = []
    questions = []
    group_by_question: dict[int, GroupConfig] = {}
    for group in config["groups"]:
        for question_number in range(group.start, group.end + 1):
            group_by_question[question_number] = group

    for question_number in QUESTION_RANGE:
        group = group_by_question[question_number]
        block = extract_question_block(section_text, question_number)
        parsed = parse_question_block(block, question_number)
        question_id = f"{year}-{question_number}"
        questions.append(
            {
                "id": question_id,
                "year": year,
                "number": question_number,
                "page": question_page_lookup(page_texts, question_number),
                "subsection": group.subsection,
                "group_id": group.group_id,
                "group_label": group.label,
                "ui_type": group.ui_type,
                "instruction": group.instruction,
                "stem": parsed["stem"] or f"Lücke ({question_number})",
                "options": parsed["options"],
            }
        )

    for group in config["groups"]:
        groups.append(
            {
                "id": group.group_id,
                "subsection": group.subsection,
                "label": group.label,
                "instruction": group.instruction,
                "ui_type": group.ui_type,
                "question_numbers": list(range(group.start, group.end + 1)),
                "shared_context": extract_shared_context(section_text, group),
            }
        )

    return {
        "year": year,
        "pages": config["pages"],
        "question_count": len(questions),
        "groups": groups,
        "questions": questions,
    }


def build_answer_template(payload: dict[str, Any]) -> dict[str, Any]:
    template: dict[str, Any] = {}
    for year_entry in payload["years"]:
        for question in year_entry["questions"]:
            template[question["id"]] = {
                "correct_option": None,
                "explanation": "",
            }
    return template


def build_dataset(pdf_path: Path | None = None) -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pytesseract.pytesseract.tesseract_cmd = resolve_tesseract_cmd()
    selected_pdf = pdf_path or find_pdf()
    LOGGER.info("开始处理 PDF：%s", selected_pdf.name)

    with fitz.open(selected_pdf) as document:
        years = [build_year_payload(year, document) for year in sorted(YEAR_CONFIGS)]

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_pdf": selected_pdf.name,
            "section": "Wortschatz und Grammatik",
            "available_years": [entry["year"] for entry in years],
            "notes": [
                "当前 PDF 中可识别到 2019、2021、2022 三套题。",
                "答案与解析暂未录入，可后续通过 data/answer_key.json 补充。",
            ],
        },
        "years": years,
    }

    QUESTIONS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ANSWER_TEMPLATE_PATH.write_text(
        json.dumps(build_answer_template(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    LOGGER.info("题库已写入：%s", QUESTIONS_PATH)
    return payload


def main() -> None:
    build_dataset()


if __name__ == "__main__":
    main()
