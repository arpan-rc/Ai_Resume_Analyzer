import re
import unicodedata


def clean_resume_text(text: str) -> str:
    """
    Normalize resume text while preserving meaningful technical symbols.

    Args:
        text: Raw text extracted from a PDF or DOCX resume.

    Returns:
        Cleaned lowercase text suitable for skill extraction and matching.
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # Normalize Unicode characters and remove control characters.
    text = unicodedata.normalize("NFKC", text)

    # Normalize common Unicode dash variants.
    text = re.sub(r"[\u2010-\u2015\u2212]", "-", text)

    # Convert to lowercase for consistent keyword matching.
    text = text.lower()

    # Replace line breaks and tabs with spaces.
    text = re.sub(r"[\r\n\t]+", " ", text)

    # Preserve letters, digits, whitespace, and technical symbols.
    # This keeps C++, C#, .NET, Node.js, CI/CD, and similar terms.
    text = re.sub(r"[^a-z0-9\s+#./-]", " ", text)

    # Remove standalone periods, but retain periods used in technical
    # names such as .NET, Node.js, and ASP.NET.
    text = re.sub(r"(?<!\w)\.(?!net\b)", " ", text)

    # Remove repeated separators at the beginning or end of text.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def clean_skill_name(skill: str) -> str:
    """
    Normalize a skill name using the same cleaning rules as resume text.

    Useful when normalizing skill-dictionary entries before comparison.
    """
    return clean_resume_text(skill)
