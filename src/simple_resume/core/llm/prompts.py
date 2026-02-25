"""Prompt templates for LLM-powered features.

All prompts are stored as pure data (template strings) with named
placeholders for format() substitution. No I/O or side effects.
"""

from __future__ import annotations

TAILOR_RESUME_PROMPT = """\
You are a professional resume writer. Rewrite the resume below to better \
align with the target job posting. Preserve all factual information but \
adjust wording, bullet points, and emphasis to highlight relevant skills \
and experience.

## Resume
{resume}

## Job Posting
{job_posting}

## Instructions
- Keep all dates, company names, and job titles accurate
- Rewrite bullet points to use keywords from the job posting where truthful
- Reorder skills to prioritize those mentioned in the job posting
- Maintain professional tone and concise formatting
- Output valid YAML in simple-resume format\
"""

EXTRACT_JOB_REQUIREMENTS_PROMPT = """\
Extract structured requirements from the following job posting. \
Return a JSON object with these fields:

- title: job title
- company: company name
- required_skills: list of required technical skills
- preferred_skills: list of preferred/nice-to-have skills
- experience_years: minimum years of experience (integer or null)
- education: required education level or null
- keywords: list of important keywords and phrases

## Job Posting
{job_posting}\
"""

LINKEDIN_ENHANCE_PROMPT = """\
Enhance and categorize the following LinkedIn profile data for use in \
a professional resume. Organize skills into categories, improve \
descriptions, and ensure consistent formatting.

## Profile Data
{profile_data}

## Instructions
- Categorize skills into technical, soft, and domain-specific groups
- Improve bullet point descriptions for clarity and impact
- Standardize date formats
- Output as a valid simple-resume YAML structure\
"""

GENERATE_COLOR_SCHEME_PROMPT = """\
Suggest a professional color scheme for a resume based on the following \
company URL. The colors should be appropriate for a printed/PDF resume \
and reflect the company's brand while remaining professional.

## Company URL
{company_url}

## Instructions
- Return exactly 5 hex color codes
- Include: primary, secondary, accent, text, and background colors
- Ensure sufficient contrast for readability
- Keep it professional and print-friendly
- Output as JSON: {{"primary": "#hex", "secondary": "#hex", \
"accent": "#hex", "text": "#hex", "background": "#hex"}}\
"""

__all__ = [
    "EXTRACT_JOB_REQUIREMENTS_PROMPT",
    "GENERATE_COLOR_SCHEME_PROMPT",
    "LINKEDIN_ENHANCE_PROMPT",
    "TAILOR_RESUME_PROMPT",
]
