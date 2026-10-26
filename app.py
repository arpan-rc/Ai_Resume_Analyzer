
import os
import pandas as pd
import plotly.express as px
import streamlit as st

from resume_parser import parse_resume
from text_cleaner import clean_resume_text
from skill_extractor import load_skill_dictionary, extract_skills
from job_matcher import load_job_roles, match_resume_to_roles
from roadmap_generator import generate_roadmap

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
JOB_CSV = os.path.join(DATA_DIR, "job_roles.csv")
SKILL_CSV = os.path.join(DATA_DIR, "skill_dictionary.csv")
MAX_FILE_SIZE = 5 * 1024 * 1024

st.set_page_config(
    page_title="AI Resume Analyzer & Job Recommendation System",
    page_icon="📄",
    layout="wide",
)


def main():
    st.title("📄 AI Resume Analyzer and Job Recommendation System")
    st.caption(
        "Educational tool for comparing job-related skills with role requirements. "
        "Scores are estimates, not hiring decisions."
    )

    try:
        loaded = load_job_roles(JOB_CSV)
        jobs_df = loaded[0] if isinstance(loaded, tuple) else loaded
        skill_df = load_skill_dictionary(SKILL_CSV)

        if jobs_df.empty or "Job Role" not in jobs_df.columns:
            st.error("The job dataset must contain at least one job role.")
            return

        roles = jobs_df["Job Role"].dropna().astype(str).str.strip().drop_duplicates().tolist()
        roles = [role for role in roles if role]
        if not roles:
            st.error("No valid job roles were found in the dataset.")
            return

    except Exception as exc:
        st.error(f"Could not load project datasets: {exc}")
        return

    with st.expander("📋 View Job Role Requirements"):
        st.dataframe(jobs_df, use_container_width=True, hide_index=True)

    upload_col, role_col = st.columns(2)

    with upload_col:
        uploaded_file = st.file_uploader(
            "Upload Resume (PDF or DOCX, maximum 5 MB)",
            type=["pdf", "docx"],
        )

    with role_col:
        target_role = st.selectbox(
            "Select Target Job Role",
            roles,
            index=min(1, len(roles) - 1),
        )

    if uploaded_file is None:
        st.info("Upload a PDF or DOCX resume to begin.")
        return

    if uploaded_file.size <= 0:
        st.error("The uploaded file is empty.")
        return

    if uploaded_file.size > MAX_FILE_SIZE:
        st.error("File exceeds the maximum allowed size of 5 MB.")
        return

    try:
        with st.spinner("Analyzing your resume..."):
            raw_text = parse_resume(uploaded_file)
            cleaned_text = clean_resume_text(raw_text)

            if not cleaned_text:
                st.error("No readable text was found in the resume.")
                return

            found_skills, categorized_skills = extract_skills(
                cleaned_text, skill_df
            )

            ranked_roles = match_resume_to_roles(
                cleaned_text, found_skills, JOB_CSV
            )

            if not ranked_roles:
                st.error(
                    "No job matches could be calculated. "
                    "Check the resume text and job-role dataset."
                )
                return

            selected = next(
                (
                    result for result in ranked_roles
                    if result["Job Role"] == target_role
                ),
                ranked_roles[0],
            )

            roadmap = generate_roadmap(
                selected["Job Role"],
                selected["Missing Skills"],
            )

    except Exception as exc:
        st.error(f"Resume analysis failed: {exc}")
        return

    st.success(f"Successfully analyzed: {uploaded_file.name}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Target Role", selected["Job Role"])
    col2.metric("Match Score", f'{selected["Match Score"]}%')
    col3.metric("Skills Identified", len(found_skills))

    st.divider()

    left, right = st.columns([1.1, 1])

    with left:
        st.subheader(f'🎯 Skill Gap: {selected["Job Role"]}')
        found_col, missing_col = st.columns(2)

        with found_col:
            st.markdown("**✅ Skills Found**")
            if selected["Skills Found"]:
                for skill in selected["Skills Found"]:
                    st.markdown(f"- `{skill}`")
            else:
                st.write("No required skills matched.")

        with missing_col:
            st.markdown("**⚠️ Missing Skills**")
            if selected["Missing Skills"]:
                for skill in selected["Missing Skills"]:
                    st.markdown(f"- `{skill}`")
            else:
                st.success("All listed required skills were found.")

        st.subheader("🗺️ Learning Roadmap")
        for step in roadmap:
            st.markdown(f"- {step}")

    with right:
        st.subheader("🏆 Top 3 Recommended Roles")

        for index, result in enumerate(ranked_roles[:3], start=1):
            st.markdown(
                f'**{index}. {result["Job Role"]}** — '
                f'`{result["Match Score"]}%` '
                f'*(Skills matched: {len(result["Skills Found"])}/'
                f'{len(result["Required Skills"])})*'
            )

        st.subheader("📊 Match Score Distribution")

        chart_df = pd.DataFrame(ranked_roles)[
            ["Job Role", "Match Score"]
        ]

        fig = px.bar(
            chart_df,
            x="Match Score",
            y="Job Role",
            orientation="h",
            text="Match Score",
            range_x=[0, 100],
            labels={
                "Match Score": "Match Score (%)",
                "Job Role": "Job Role",
            },
        )
        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    skills_col, report_col = st.columns([1.2, 1])

    with skills_col:
        st.subheader("🧩 Extracted Skills by Category")
        if categorized_skills:
            for category, skills in categorized_skills.items():
                st.markdown(
                    f"**{category}:** "
                    + ", ".join(f"`{skill}`" for skill in skills)
                )
        else:
            st.write("No dictionary skills were detected.")

    with report_col:
        st.subheader("📥 Download Analysis Report")

        report_lines = [
            "AI RESUME ANALYZER & JOB RECOMMENDATION REPORT",
            "=" * 55,
            f"Resume: {uploaded_file.name}",
            f"Target Role: {selected['Job Role']}",
            f"Match Score: {selected['Match Score']}%",
            "",
            "SKILLS FOUND:",
            ", ".join(selected["Skills Found"]) or "None",
            "",
            "MISSING SKILLS:",
            ", ".join(selected["Missing Skills"]) or "None",
            "",
            "TOP RECOMMENDED ROLES:",
        ]

        report_lines.extend(
            f"{i}. {result['Job Role']} ({result['Match Score']}%)"
            for i, result in enumerate(ranked_roles[:3], start=1)
        )

        report_lines.extend(["", "LEARNING ROADMAP:"])
        report_lines.extend(f"- {step}" for step in roadmap)
        report_lines.extend([
            "",
            "Scores are educational estimates based on skill overlap and TF-IDF similarity, not hiring decisions.",
            "Required skills are based on the project job-role dataset.",
        ])

        st.download_button(
            "Download Report (.txt)",
            data="\n".join(report_lines),
            file_name="resume_analysis_report.txt",
            mime="text/plain",
        )

    with st.expander("🔍 View Cleaned Resume Text"):
        st.text_area(
            "Cleaned Resume Text",
            cleaned_text,
            height=180,
        )


if __name__ == "__main__":
    main()
