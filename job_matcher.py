import os
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from text_cleaner import clean_resume_text, clean_skill_name


# Normalize common aliases to one canonical representation.
SKILL_ALIASES = {
    "ml": "machine learning",
    "sklearn": "scikit-learn",
    "powerbi": "power bi",
    "nodejs": "node.js",
    "postgres": "postgresql",
}

def _normalize_skill(skill):
    """Normalize a skill name and resolve known aliases."""
    normalized = clean_skill_name(str(skill or "")).strip().lower()
    return SKILL_ALIASES.get(normalized, normalized)


def _split_skills(value):
    """Split a CSV skill cell into a list of non-empty skill names."""
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def _tfidf_text(text):
    """Prepare text for TF-IDF while preserving symbol-heavy technical terms."""
    text = clean_resume_text(str(text or "")).lower()
    # Add searchable aliases for terms whose punctuation is poorly handled by
    # default tokenizers. Original cleaned text remains available for matching.
    replacements = [
        (r"(?<!\w)c\+\+(?!\w)", " cpp cplusplus "),
        (r"(?<!\w)c#(?!\w)", " csharp "),
        (r"(?<!\w)\.net(?!\w)", " dotnet "),
        (r"(?<!\w)node\.js(?!\w)", " nodejs "),
        (r"(?<!\w)ci/cd(?!\w)", " cicd "),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def load_job_roles(csv_path="data/job_roles.csv"):
    """Load and validate the job-role dataset; return (dataframe, skill column)."""
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), csv_path)

    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Job-role dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df.columns = [str(column).strip() for column in df.columns]
    skill_col = next(
        (column for column in ("Required Skills", "Example Required Skills")
         if column in df.columns),
        None,
    )

    if "Job Role" not in df.columns or skill_col is None:
        raise ValueError(
            "Job-role CSV must contain 'Job Role' and either "
            "'Required Skills' or 'Example Required Skills' columns."
        )

    df = df.dropna(subset=["Job Role"]).copy()
    df["Job Role"] = df["Job Role"].astype(str).str.strip()
    df = df[df["Job Role"] != ""].reset_index(drop=True)

    if df.empty:
        raise ValueError("Job-role dataset contains no valid job roles.")

    if df["Job Role"].duplicated().any():
        duplicates = sorted(df.loc[df["Job Role"].duplicated(), "Job Role"].unique())
        raise ValueError(f"Duplicate job roles found in CSV: {', '.join(duplicates)}")

    return df, skill_col



def match_resume_to_roles(
    cleaned_resume_text,
    extracted_skills,
    csv_path="data/job_roles.csv",
):
    """Return job roles sorted by match score, highest first."""
    if not isinstance(cleaned_resume_text, str) or not cleaned_resume_text.strip():
        return []

    jobs, skill_col = load_job_roles(csv_path)

    resume_skills = {
        _normalize_skill(skill)
        for skill in (extracted_skills or [])
        if str(skill).strip()
    }

    cleaned_resume = clean_resume_text(cleaned_resume_text)

    role_skills = [_split_skills(value) for value in jobs[skill_col]]
    role_texts = [" ".join(skills) for skills in role_skills]

    # A custom token pattern retains punctuation-bearing terms such as C++,
    # C#, .NET and Node.js. Extra aliases are also added for robust similarity.
    documents = [_tfidf_text(cleaned_resume)] + [_tfidf_text(text) for text in role_texts]
    try:
        vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b[\w+#./-]+\b",
            lowercase=True,
            ngram_range=(1, 2),
        )
        matrix = vectorizer.fit_transform(documents)
        similarities = cosine_similarity(matrix[0:1], matrix[1:])[0]
    except ValueError:
        similarities = [0.0] * len(jobs)

    results = []
    for index, (_, job) in enumerate(jobs.iterrows()):
        required = role_skills[index]
        # Keep original display labels in the report, but compare canonical names.
        canonical_required = [_normalize_skill(skill) for skill in required]
        matched_indices = [
            i for i, skill in enumerate(canonical_required)
            if skill and skill in resume_skills
        ]
        missing_indices = [
            i for i, skill in enumerate(canonical_required)
            if not skill or skill not in resume_skills
        ]

        matched = [required[i] for i in matched_indices]
        missing = [required[i] for i in missing_indices]
        # Avoid over-counting duplicate/alias requirements in the coverage score.
        unique_required = set(skill for skill in canonical_required if skill)
        unique_matched = set(canonical_required[i] for i in matched_indices if canonical_required[i])
        coverage = len(unique_matched) / len(unique_required) if unique_required else 0.0
        similarity = float(similarities[index])

        score = max(0.0, min(100.0, (0.7 * coverage + 0.3 * similarity) * 100))
        results.append({
            "Job Role": job["Job Role"],
            "Match Score": round(score, 1),
            "Required Skills": required,
            "Skills Found": list(dict.fromkeys(matched)),
            "Missing Skills": list(dict.fromkeys(missing)),
            "Cosine Similarity": round(similarity * 100, 1),
            "Skill Coverage": round(coverage * 100, 1),
        })

    return sorted(results, key=lambda result: result["Match Score"], reverse=True)
