# AI Resume Analyzer and Job Recommendation System

An NLP-based application built with Python and Streamlit that evaluates how well a candidate's resume matches target technical job roles, highlights missing skills, recommends top suitable roles, and generates a structured learning roadmap.

## Project Structure

```text
ai_resume_analyzer/
|-- app.py
|-- resume_parser.py
|-- text_cleaner.py
|-- skill_extractor.py
|-- job_matcher.py
|-- roadmap_generator.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- data/
|   |-- job_roles.csv
|   |-- skill_dictionary.csv
|-- sample_resumes/
|   |-- Resume_A_Data_Analyst.docx
|   |-- Resume_B_ML_Engineer.docx
|   |-- Resume_C_NLP_Engineer.docx
|-- reports/
|   |-- sample_analysis_report.txt
|-- tests/
    |-- test_cases.csv
```

## Features
1. **Resume Upload (`resume_parser.py`)**: Accepts `.pdf` and `.docx` resumes with file type and size validation.
2. **Text Extraction & Cleaning (`text_cleaner.py`)**: Normalizes unstructured resume text while preserving technical tokens like `C++`, `C#`, and `.NET`.
3. **Categorized Skill Extraction (`skill_extractor.py`)**: Matches against 40+ technical skills grouped into Programming, Databases, Data & Analytics, Machine Learning & AI, Cloud & DevOps, and Tools.
4. **Job Role Matching (`job_matcher.py`)**: Ranks the technical job roles listed in `data/job_roles.csv` (the current dataset shown in the project contains 5 roles) using TF-IDF vectorization, cosine similarity, and skill overlap.
5. **Skill-Gap & Learning Roadmap (`roadmap_generator.py`)**: Identifies missing skills for any selected target role and produces a week-by-week study plan plus a downloadable `.txt` report.
6. **Interactive Dashboard (`app.py`)**: Built with Streamlit and Plotly.

## Setup & Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```


## Dataset format

- `data/job_roles.csv` must contain `Job Role` and `Required Skills` columns. Required skills are comma-separated. The application recommends only roles loaded from this file.
- `data/skill_dictionary.csv` must contain `Skill` and `Category` columns. Add or remove skills here to change dictionary-based extraction.
- The Machine Learning Engineer role's required skills should be kept in sync with the intended skill-gap analysis. For example, if MLflow is meant to be required, add it to that role's `Required Skills` value; the skill dictionary alone does not make it a role requirement.

## Matching score

The displayed score is an educational ranking estimate composed of 70% required-skill coverage and 30% TF-IDF cosine similarity. It is not a probability of being hired and should not be used as an employment decision.

## Limitations

- Scanned/image-only PDFs are not OCR-processed; upload a text-based PDF or DOCX.
- Skill extraction is dictionary/keyword-based and may miss synonyms not defined in the code or CSV.
- Results depend on the completeness and accuracy of the job-role and skill-dictionary CSV files.
