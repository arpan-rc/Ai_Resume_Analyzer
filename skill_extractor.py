import os
import re
import pandas as pd
from text_cleaner import clean_resume_text

try:
    from text_cleaner import clean_skill_name
except ImportError:
    # Backward compatibility with older text_cleaner.py versions.
    clean_skill_name = clean_resume_text

SYNONYM_MAP = {
    "sklearn": "scikit-learn",
    "powerbi": "power bi",
    "ml": "machine learning",
}

ACRONYMS = {"sql", "llm", "rag", "nlp", "cnn", "yolo", "ml", "api", "apis", "aws", "gcp", "html", "css", "mlflow", "git", "github"}


def load_skill_dictionary(csv_path="data/skill_dictionary.csv") -> pd.DataFrame:
    """Load and validate the controlled skill dictionary."""
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_path)
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Skill dictionary not found: {csv_path}")

    df = pd.read_csv(csv_path)
    required = {"Skill", "Category"}
    if not required.issubset(df.columns):
        raise ValueError("Skill dictionary must contain 'Skill' and 'Category' columns.")
    return df.dropna(subset=["Skill"]).copy()


def _pattern_for(skill: str) -> re.Pattern:
    """Match whole skills while supporting names such as C++, C#, .NET and Node.js."""
    escaped = re.escape(skill.strip())
    # For names made only of word characters, require whole-word boundaries.
    # For technical names containing punctuation, use boundaries that allow tokens like C++ and .NET.
    return re.compile(r"(?<![a-z0-9])" + escaped + r"(?![a-z0-9])", re.IGNORECASE)


def _display_name(skill: str) -> str:
    lower = skill.lower().strip()
    if lower in ACRONYMS:
        return lower.upper()
    return skill.strip()


def extract_skills(cleaned_text: str, skill_df: pd.DataFrame = None):
    """Return (sorted_skills, skills_grouped_by_category)."""
    if not isinstance(cleaned_text, str) or not cleaned_text.strip():
        return [], {}

    text = clean_resume_text(cleaned_text)
    skill_df = load_skill_dictionary() if skill_df is None else skill_df.copy()
    if not {"Skill", "Category"}.issubset(skill_df.columns):
        raise ValueError("Skill dictionary must contain 'Skill' and 'Category' columns.")

    found, categorized = set(), {}
    skill_lookup = {}

    for _, row in skill_df.dropna(subset=["Skill"]).iterrows():
        display = str(row["Skill"]).strip()
        category = str(row.get("Category", "Other")).strip() or "Other"
        normalized = clean_skill_name(display)
        if normalized:
            skill_lookup[normalized] = (display, category)

    # Add aliases only when their canonical skill exists in the dictionary.
    for alias, canonical in SYNONYM_MAP.items():
        canonical_key = clean_skill_name(canonical)
        if canonical_key in skill_lookup:
            skill_lookup[clean_skill_name(alias)] = skill_lookup[canonical_key]

    for key, (display, category) in skill_lookup.items():
        if _pattern_for(key).search(text):
            name = _display_name(display)
            found.add(name)
            categorized.setdefault(category, set()).add(name)

    return sorted(found), {cat: sorted(names) for cat, names in sorted(categorized.items())}
