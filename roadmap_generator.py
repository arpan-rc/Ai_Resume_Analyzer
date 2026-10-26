from math import ceil


def generate_roadmap(target_role: str, missing_skills: list) -> list:
    """Create a practical learning roadmap of up to four weeks."""

    skills = list(dict.fromkeys(
        str(skill).strip()
        for skill in (missing_skills or [])
        if skill is not None and str(skill).strip()
    ))

    if not skills:
        return [
            f"Congratulations! You have all listed core skills for the "
            f"{target_role} role. Keep practising through projects."
        ]

    themes = [
        "Foundations and core concepts",
        "Practical exercises and integration",
        "Hands-on project development",
        "Testing, deployment, and revision",
    ]

    week_count = min(4, len(skills))
    chunk_size = ceil(len(skills) / week_count)

    roadmap = []
    for index, start in enumerate(range(0, len(skills), chunk_size)):
        week_skills = skills[start:start + chunk_size]
        roadmap.append(
            f"Week {index + 1} — {themes[index]}: "
            f"Learn and practise {', '.join(week_skills)}."
        )

    return roadmap
