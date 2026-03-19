from __future__ import annotations

import json
import re
import shutil
from copy import deepcopy
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DIST_DATA_DIR = ROOT_DIR / "dist" / "data"
QUESTIONS_PATH = DATA_DIR / "questions.json"
ANSWER_KEY_PATH = DATA_DIR / "answer_key.json"
SOURCE_EXAMS_PATH = ROOT_DIR / "material" / "testpaperandanswer" / "19-22.json"
SOURCE_ANSWERS_PATH = ROOT_DIR / "material" / "testpaperandanswer" / "19-22ans.json"
BACKUP_ROOT = DATA_DIR / "backups"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def backup_current_files() -> Path:
    backup_dir = BACKUP_ROOT / f"pre-19-22-json-import-{now_stamp()}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(QUESTIONS_PATH, backup_dir / "questions.json")
    shutil.copy2(ANSWER_KEY_PATH, backup_dir / "answer_key.json")
    return backup_dir


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


def normalize_option_list(options: list[str] | None, tf: bool = False) -> dict[str, str]:
    if tf:
        return {"R": "Richtig", "F": "Falsch"}
    result: dict[str, str] = {}
    for raw in options or []:
        text = str(raw).strip()
        match = re.match(r"^([A-D])\.\s*(.+)$", text)
        if match:
            result[match.group(1)] = match.group(2).strip()
    return result


def first_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "")


def build_answer_qid(year: int, number: int) -> str | None:
    if 1 <= number <= 30:
        return f"{year}-listening-{number}"
    if 31 <= number <= 70:
        return f"{year}-{number}"
    if 71 <= number <= 85:
        return f"{year}-reading-{number}"
    if 86 <= number <= 105:
        return f"{year}-landeskunde-{number}"
    return None


def flatten_answer_json(answer_doc: dict, year: int) -> dict[int, str]:
    flattened: dict[int, str] = {}
    content = answer_doc["content"][str(year)]
    for page_value in content.values():
        if not isinstance(page_value, dict):
            continue
        sections = page_value.get("sections", {})
        for section_value in sections.values():
            if isinstance(section_value, dict):
                for sub_key, sub_value in section_value.items():
                    if isinstance(sub_value, dict):
                        for qno, token in sub_value.items():
                            if str(qno).isdigit() and isinstance(token, str) and len(token.strip()) <= 5:
                                flattened[int(qno)] = token.strip().upper()
                    elif str(sub_key).isdigit() and isinstance(sub_value, str) and len(sub_value.strip()) <= 5:
                        flattened[int(sub_key)] = sub_value.strip().upper()
    return flattened


def collect_translation_references(answer_doc: dict, year: int) -> dict[int, str]:
    content = answer_doc["content"][str(year)]
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
            zh_text2 = section_value.get("德译汉参考译文_text_continued", "").strip()
            de_title = section_value.get("汉译德参考译文_title", "").strip()
            de_text = section_value.get("汉译德参考译文_text", "").strip()

            if zh_title or zh_text or zh_text2:
                pieces = []
                if zh_title:
                    pieces.append(zh_title)
                if zh_text:
                    pieces.append(zh_text)
                if zh_text2:
                    pieces.append(zh_text2)
                refs[1] = "\n\n".join(piece for piece in pieces if piece).strip()
            if de_title or de_text:
                pieces = []
                if de_title:
                    pieces.append(de_title)
                if de_text:
                    pieces.append(de_text)
                refs[2] = "\n\n".join(piece for piece in pieces if piece).strip()
    return refs


def find_year_entry(dataset: dict, year: int) -> dict:
    return next(entry for entry in dataset["years"] if entry["year"] == year)


def find_library_entry(dataset: dict, year: int, section: str) -> dict:
    return next(entry for entry in dataset["library"] if entry["year"] == year and entry["section"] == section)


def question_map(questions: list[dict]) -> dict[int, dict]:
    return {question["number"]: question for question in questions}


def group_map(groups: list[dict]) -> dict[str, dict]:
    return {group["label"]: group for group in groups}


def apply_question_text_update(target_question: dict, source_question: dict, tf: bool = False) -> None:
    text = source_question.get("text")
    if text:
        target_question["stem"] = text.strip()
    options = normalize_option_list(source_question.get("options"), tf=tf)
    if options:
        target_question["options"] = options


def update_year_from_exam(dataset: dict, exam: dict) -> dict[str, int]:
    year = exam["year"]
    stats = {"questions_updated": 0, "groups_updated": 0}
    year_entry = find_year_entry(dataset, year)
    year_questions = question_map(year_entry["questions"])
    year_groups = {group["id"]: group for group in year_entry["groups"]}
    library_listening = question_map(find_library_entry(dataset, year, "listening")["questions"])
    library_reading_entry = find_library_entry(dataset, year, "reading")
    library_reading = question_map(library_reading_entry["questions"])
    library_landeskunde = question_map(find_library_entry(dataset, year, "landeskunde")["questions"])
    library_translation_entry = find_library_entry(dataset, year, "translation")
    library_writing_entry = find_library_entry(dataset, year, "writing")

    for part in exam["parts"]:
        part_name = part["name"]
        if "Hörverstehen" in part_name or "H枚rverstehen" in part_name:
            for section in part.get("sections", []):
                tf = section.get("type") == "Richtig/Falsch"
                for source_question in section.get("questions", []):
                    target = library_listening.get(source_question["number"])
                    if not target:
                        continue
                    apply_question_text_update(target, source_question, tf=tf)
                    stats["questions_updated"] += 1
        elif "Wortschatz und Grammatik" in part_name:
            for section in part.get("sections", []):
                section_name = section["name"]
                if section_name == "Wortschatz D":
                    group = next((g for g in year_entry["groups"] if g["question_numbers"][0] == 46), None)
                    if group and section.get("passage"):
                        group["shared_context"] = section["passage"].strip()
                        stats["groups_updated"] += 1
                    for source_question in section.get("questions", []):
                        target = year_questions.get(source_question["number"])
                        if not target:
                            continue
                        options = normalize_option_list(source_question.get("options"))
                        if options:
                            target["options"] = options
                            target["stem"] = f"Lücke ({source_question['number']})"
                            stats["questions_updated"] += 1
                else:
                    for source_question in section.get("questions", []):
                        target = year_questions.get(source_question["number"])
                        if not target:
                            continue
                        apply_question_text_update(target, source_question)
                        stats["questions_updated"] += 1
        elif "Leseverständnis" in part_name or "Leseverst" in part_name:
            for section in part.get("sections", []):
                label = section["name"]
                target_group = next((g for g in library_reading_entry["groups"] if g["label"] == label), None)
                if target_group and section.get("passage"):
                    target_group["shared_context"] = section["passage"].strip()
                    stats["groups_updated"] += 1
                for source_question in section.get("questions", []):
                    target = library_reading.get(source_question["number"])
                    if not target:
                        continue
                    apply_question_text_update(target, source_question)
                    stats["questions_updated"] += 1
        elif "Landeskunde" in part_name:
            for section in part.get("sections", []):
                tf = section["name"] == "A"
                for source_question in section.get("questions", []):
                    target = library_landeskunde.get(source_question["number"])
                    if not target:
                        continue
                    apply_question_text_update(target, source_question, tf=tf)
                    stats["questions_updated"] += 1
        elif "Übersetzung" in part_name or "脺bersetzung" in part_name:
            sections = part.get("sections", [])
            for index, section in enumerate(sections, start=1):
                if index > len(library_translation_entry["questions"]):
                    continue
                library_translation_entry["questions"][index - 1]["prompt_text"] = section.get("text", "").strip()
                prompt_title = first_line(section.get("text", ""))
                if prompt_title:
                    library_translation_entry["questions"][index - 1]["stem"] = prompt_title
                    stats["questions_updated"] += 1
        elif "Schriftlicher Ausdruck" in part_name:
            prompt_text = part.get("text", "").strip()
            if prompt_text:
                question = library_writing_entry["questions"][0]
                question["prompt_text"] = prompt_text
                prompt_title = first_line(prompt_text)
                if prompt_title:
                    question["stem"] = prompt_title
                subprompts = re.findall(r"(?m)^(?:[0-9]+[.)]|[-•])\s*(.+)$", prompt_text)
                if subprompts:
                    question["subprompts"] = subprompts
                stats["questions_updated"] += 1

    return stats


def main() -> None:
    backup_dir = backup_current_files()
    dataset = load_json(QUESTIONS_PATH)
    answer_key = load_json(ANSWER_KEY_PATH)
    answer_before = deepcopy(answer_key)
    answer_doc = load_json(SOURCE_ANSWERS_PATH)
    complete_exams = parse_complete_exam_objects(SOURCE_EXAMS_PATH)
    complete_exam_map = {exam["year"]: exam for exam in complete_exams}

    changed_answers: list[tuple[str, str, str]] = []
    added_answers: list[tuple[str, str]] = []
    translation_refs_added = 0
    question_update_stats: dict[int, dict[str, int]] = {}

    for year in (2019, 2021, 2022):
        flattened = flatten_answer_json(answer_doc, year)
        for number, token in sorted(flattened.items()):
            qid = build_answer_qid(year, number)
            if not qid:
                continue
            entry = answer_key.setdefault(qid, {})
            old = entry.get("correct_option")
            if old is None:
                added_answers.append((qid, token))
            elif old != token:
                changed_answers.append((qid, old, token))
            entry["correct_option"] = token

        refs = collect_translation_references(answer_doc, year)
        for idx in (1, 2):
            ref_text = refs.get(idx, "").strip()
            if not ref_text:
                continue
            qid = f"{year}-translation-{idx}"
            entry = answer_key.setdefault(qid, {})
            entry["display_answer"] = "见参考译文"
            entry["explanation"] = ref_text
            translation_refs_added += 1

    for year in (2019, 2021):
        exam = complete_exam_map.get(year)
        if exam:
            question_update_stats[year] = update_year_from_exam(dataset, exam)

    write_json(QUESTIONS_PATH, dataset)
    write_json(ANSWER_KEY_PATH, answer_key)
    write_json(DIST_DATA_DIR / "questions.json", dataset)
    write_json(DIST_DATA_DIR / "answer_key.json", answer_key)

    print(f"[OK] backup: {backup_dir}")
    print(f"[OK] parsed complete exam objects: {[exam['year'] for exam in complete_exams]}")
    print(f"[OK] changed answers: {len(changed_answers)}")
    print(f"[OK] added missing answers: {len(added_answers)}")
    print(f"[OK] translation refs updated: {translation_refs_added}")
    for year, stats in sorted(question_update_stats.items()):
        print(f"[OK] question refresh {year}: questions={stats['questions_updated']} groups={stats['groups_updated']}")
    if changed_answers:
        for qid, old, new in changed_answers[:20]:
            print(f"[DIFF] {qid}: {old} -> {new}")


if __name__ == "__main__":
    main()
