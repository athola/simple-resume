"""Business logic tests following extreme programming practices.

These tests implement TDD principles for business rules and user stories:
- User story validation
- Business rule enforcement
- Domain model testing
- Acceptance criteria verification
- Real-world scenario testing
"""

from pathlib import Path
from typing import Any, TypedDict

import yaml

from simple_resume.core.palettes.registry import PaletteRegistry
from simple_resume.core.paths import Paths
from simple_resume.core.render.manage import get_template_environment
from simple_resume.core.render.plan import prepare_render_data
from simple_resume.shell.runtime.content import get_content


class ContactScenario(TypedDict):
    """Contact validation scenario definition."""

    name: str
    data: dict[str, Any]
    should_be_valid: bool


class TemplateScenario(TypedDict):
    """Template validation scenario definition."""

    name: str
    data: dict[str, Any]
    appropriate: bool


class TestResumeBusinessRules:
    """Business logic tests for Resume domain rules and constraints."""

    def test_user_story_professional_resume_creation(self, temp_dir: Path) -> None:
        """User Story: As a professional, I want to create a polished Resume.

        that highlights my experience.
        """
        # Business Rule: Professional Resume must have complete contact information
        professional_resume_data = {
            "template": "resume_no_bars",
            "full_name": "Dr. Sarah Chen",
            "email": "sarah.chen@techcorp.com",
            "phone": "+1 (555) 123-4567",
            "web": "https://sarahchen.dev",
            "linkedin": "in/sarahchen",
            "description": """
# Senior Software Engineer with 8+ years experience

Specialized in **distributed systems** and **cloud architecture**.
Led teams of 5-10 engineers in enterprise-scale projects.

## Key Achievements
- Reduced system latency by 40% through optimization
- Led migration to microservices architecture
- Mentored 15+ junior developers
            """.strip(),
            "expertise": [
                "Distributed Systems",
                "Cloud Architecture (AWS/GCP)",
                "Python/Go/Rust",
                "System Design",
                "Team Leadership",
            ],
            "body": {
                "Experience": [
                    {
                        "start": "01/2020",
                        "end": "Present",
                        "title": "Senior Software Engineer",
                        "company": "TechCorp",
                        "title_link": "https://techcorp.com",
                        "description": """
## Leadership & Architecture
- Lead architect for **microservices migration** affecting 2M+ users
- Manage team of 8 engineers, conducting code reviews and mentoring
- Design and implement **scalable cloud solutions** using AWS

## Technical Impact
- Developed **real-time data pipeline** processing 1TB+ daily
- Implemented **CI/CD pipeline** reducing deployment time by 60%
- Created **monitoring framework** improving system reliability by 45%

## Business Results
- **Cost reduction**: $2M annually through infrastructure optimization
- **Performance improvement**: 40% reduction in API response times
- **Team productivity**: 3x increase in deployment frequency
                        """.strip(),
                    },
                    {
                        "start": "06/2017",
                        "end": "12/2019",
                        "title": "Software Engineer",
                        "company": "StartupXYZ",
                        "description": "Built core platform features from scratch",
                    },
                ]
            },
            "config": {"theme_color": "#2563eb", "sidebar_color": "#f8fafc"},
        }

        # Acceptance Criteria 1: Resume must have complete professional information
        self._validate_professional_resume_business_rules(professional_resume_data)

        # Acceptance Criteria 2: Resume must render correctly with markdown processing
        processed_resume = self._process_resume_with_business_logic(
            professional_resume_data, temp_dir
        )

        # Acceptance Criteria 3: Business rules for professional Resumes
        self._validate_professional_resume_business_rules(processed_resume)

    def test_user_story_student_resume_creation(self, temp_dir: Path) -> None:
        """User Story: As a student, I want to create a Resume that emphasizes my.

        education and projects.
        """
        # Business Rule: Student Resume should highlight education and potential
        # over experience
        student_resume_data = {
            "template": "resume_no_bars",
            "full_name": "Alex Johnson",
            "email": "alex.johnson@university.edu",
            "phone": "(555) 987-6543",
            "web": "https://alexjohnson.github.io",
            "github": "github.com/alexjohnson",
            "description": """
## Computer Science Student with Passion for AI/ML

**Third-year undergraduate** at Technical University with **3.8 GPA**.
Passionate about machine learning, competitive programming, and open source.

### Quick Facts
- **Dean's List**: 5/6 semesters
- **Hackathons**: 3 wins, 5 participations
- **Open Source**: Active contributor to 4 projects
- **Languages**: Python, Java, C++, JavaScript
            """.strip(),
            "body": {
                "Education": [
                    {
                        "start": "09/2021",
                        "end": "05/2025 (Expected)",
                        "title": "Bachelor of Science in Computer Science",
                        "company": "Technical University",
                        "description": """
## Relevant Coursework
- **Machine Learning** (A+)
- **Algorithms & Data Structures** (A)
- **Database Systems** (A-)
- **Software Engineering** (A)
- **Artificial Intelligence** (A)

## Academic Achievements
- **GPA**: 3.8/4.0
- **Dean's List**: Fall 2021, Spring 2022, Fall 2022, Spring 2023, Fall 2023
- **Scholarship**: Merit-based scholarship recipient
- **Research**: Undergraduate research assistant in ML lab
                        """.strip(),
                    }
                ],
                "Projects": [
                    {
                        "start": "01/2024",
                        "end": "03/2024",
                        "title": "AI-Powered Study Assistant",
                        "company": "Capstone Project",
                        "description": """
## Project Overview
Developed **machine learning application** that helps students create
personalized study plans.

### Technical Implementation
- **Backend**: Python with FastAPI, PostgreSQL database
- **ML Models**: Natural Language Processing for content analysis
- **Frontend**: React with responsive design
- **Deployment**: Docker container on AWS

### Results & Impact
- **100+ beta users** during testing phase
- **85% satisfaction rate** in user feedback
- **Featured** in university tech showcase
- **Open source**: 50+ stars on GitHub
                        """.strip(),
                    },
                    {
                        "start": "09/2023",
                        "end": "12/2023",
                        "title": "Competitive Programming Platform",
                        "company": "Course Project",
                        "description": (
                            "Built platform for coding contests with 500+ problems"
                        ),
                    },
                ],
            },
        }

        # Business Rule Validation for Student Resumes
        processed_resume = self._process_resume_with_business_logic(
            student_resume_data, temp_dir
        )
        self._validate_student_resume_business_rules(processed_resume)

    def test_user_story_career_change_resume(self, temp_dir: Path) -> None:
        """User Story: As a career changer, I want to highlight transferable.

        skills and new certifications.
        """
        # Business Rule: Career change Resume must bridge past experience with new goals
        career_change_resume_data = {
            "template": "resume_with_bars",
            "full_name": "Michael Rodriguez",
            "email": "michael.rodriguez@email.com",
            "phone": "(555) 456-7890",
            "linkedin": "in/michaelrodriguez",
            "description": """
## Career Transition: Finance → Software Engineering

**Finance professional** with 7 years experience transitioning to
**software engineering**.
Combining analytical expertise with modern programming skills for
**FinTech** opportunities.

### Career Change Narrative
After successful career in **financial analysis**, discovered passion for
**technology** through automation projects.
Completed **intensive coding bootcamp** and built portfolio of
**real-world applications**.

**Goal**: Leverage **domain expertise** in finance with **technical skills**
in software development.
            """.strip(),
            "body": {
                "Experience": [
                    {
                        "start": "03/2024",
                        "end": "Present",
                        "title": "Software Engineering Fellow",
                        "company": "Tech Bootcamp",
                        "description": """
## Intensive Training Program
- **Full-stack development** with Python, JavaScript, React
- **Database design** and **API development**
- **Version control** with Git and collaborative workflows
- **Agile methodologies** and **project management**

## Projects Completed
- **FinTech Dashboard**: Real-time financial data visualization
- **Trading Bot**: Algorithmic trading with Python
- **Budget App**: Personal finance tracking application
                        """.strip(),
                    },
                    {
                        "start": "06/2017",
                        "end": "02/2024",
                        "title": "Senior Financial Analyst",
                        "company": "Investment Firm",
                        "description": """
## Financial Expertise (Transferable Skills)
- **Data Analysis**: Python, Excel, SQL for financial modeling
- **Risk Assessment**: Quantitative analysis and reporting
- **Process Automation**: Streamlined workflows using VBA and Python
- **Stakeholder Communication**: Presentations to executive team

## Technical Bridge to Software Engineering
- **Python Programming**: Automated financial reports and analysis
- **Database Skills**: SQL queries for financial data extraction
- **API Integration**: Connected financial systems via REST APIs
- **Problem Solving**: Analytical mindset applied to technical challenges
                        """.strip(),
                    },
                ],
                "Certification": [
                    {
                        "start": "01/2024",
                        "end": "03/2024",
                        "title": "Full Stack Web Development",
                        "company": "Tech Bootcamp Certificate",
                        "description": "480-hour intensive program",
                    },
                    {
                        "start": "11/2023",
                        "end": "12/2023",
                        "title": "AWS Cloud Practitioner",
                        "company": "Amazon Web Services",
                        "description": "Cloud computing fundamentals certification",
                    },
                ],
            },
        }

        processed_resume = self._process_resume_with_business_logic(
            career_change_resume_data, temp_dir
        )
        self._validate_career_change_resume_business_rules(processed_resume)

    def test_business_rule_resume_length_constraints(self, temp_dir: Path) -> None:
        """Business Rule: Resumes should maintain appropriate length for readability."""
        # Test Case 1: Resume too short (insufficient content)
        short_resume = {
            "template": "resume_no_bars",
            "full_name": "Minimal User",
            # Missing essential content
        }

        # Test Case 2: Resume appropriate length
        appropriate_resume = {
            "template": "resume_no_bars",
            "full_name": "Balanced User",
            "description": "Experienced professional with a diverse background",
            "expertise": ["Skill 1", "Skill 2", "Skill 3"],
            "body": {
                "Experience": [
                    {
                        "title": "Senior Developer",
                        "company": "TechCorp",
                        "description": "Detailed experience description",
                    }
                ]
            },
        }

        # Test Case 3: Resume too long (excessive content)
        long_resume = {
            "template": "resume_no_bars",
            "full_name": "Verbose User",
            "description": "A" * 2000,  # Very long description
            "expertise": [f"Skill {i}" for i in range(50)],  # Too many skills
            "body": {
                "Experience": [
                    {
                        "title": f"Job {i}",
                        "company": f"Company {i}",
                        "description": "B" * 500,  # Long descriptions
                    }
                    for i in range(20)  # Too many jobs
                ]
            },
        }

        # Business Rule Validation
        processed_short = self._process_resume_with_business_logic(
            short_resume, temp_dir
        )
        processed_appropriate = self._process_resume_with_business_logic(
            appropriate_resume, temp_dir
        )
        processed_long = self._process_resume_with_business_logic(long_resume, temp_dir)

        # Assert business rules about Resume length
        assert self._get_resume_content_length(processed_short) < 100, (
            "Short Resume should be flagged as insufficient"
        )
        assert 100 <= self._get_resume_content_length(processed_appropriate) <= 5000, (
            "Appropriate Resume should pass length validation"
        )
        assert self._get_resume_content_length(processed_long) > 5000, (
            "Long Resume should be flagged as excessive"
        )

    def test_business_rule_contact_information_validation(self, temp_dir: Path) -> None:
        """Business Rule: Contact information must be valid and complete."""
        # Test Cases for contact information validation
        test_cases: list[ContactScenario] = [
            {
                "name": "valid_contact",
                "data": {
                    "template": "resume_no_bars",
                    "full_name": "Valid User",
                    "email": "valid@example.com",
                    "phone": "+1 (555) 123-4567",
                },
                "should_be_valid": True,
            },
            {
                "name": "invalid_email",
                "data": {
                    "template": "resume_no_bars",
                    "full_name": "Invalid Email User",
                    "email": "invalid-email",
                    "phone": "+1 (555) 123-4567",
                },
                "should_be_valid": False,
            },
            {
                "name": "invalid_phone",
                "data": {
                    "template": "resume_no_bars",
                    "full_name": "Invalid Phone User",
                    "email": "valid@example.com",
                    "phone": "not-a-phone-number",
                },
                "should_be_valid": False,
            },
            {
                "name": "missing_contact",
                "data": {"template": "resume_no_bars", "full_name": "No Contact User"},
                "should_be_valid": False,
            },
        ]

        for test_case in test_cases:
            processed_resume = self._process_resume_with_business_logic(
                test_case["data"], temp_dir
            )

            if test_case["should_be_valid"]:
                assert self._validate_contact_information(processed_resume), (
                    f"Contact validation failed for {test_case['name']}"
                )
            else:
                assert not self._validate_contact_information(processed_resume), (
                    f"Contact validation should fail for {test_case['name']}"
                )

    def test_business_rule_template_appropriateness(self, temp_dir: Path) -> None:
        """Business Rule: Template choice should match content type and profession."""
        # Test Cases for template appropriateness
        test_scenarios: list[TemplateScenario] = [
            {
                "name": "technical_with_no_bars",
                "data": {
                    "template": "resume_no_bars",
                    "full_name": "Technical User",
                    "expertise": ["Python", "Docker", "Kubernetes"],
                    "body": {"Experience": [{"title": "Software Engineer"}]},
                },
                "appropriate": True,
            },
            {
                "name": "executive_with_bars",
                "data": {
                    "template": "resume_with_bars",
                    "full_name": "Executive User",
                    "expertise": ["Leadership", "Strategy", "Management"],
                    "body": {"Experience": [{"title": "CEO"}, {"title": "CTO"}]},
                },
                "appropriate": True,
            },
            {
                "name": "student_with_cover",
                "data": {
                    "template": "cover",
                    "full_name": "Student User",
                    "description": (
                        "This is a detailed description of my qualifications and "
                        "experience that makes me suitable for this position. I have "
                        "knowledge in various technologies and I'm "
                        "passionate about learning new things and contributing to the "
                        "team's success with my skills and dedication."
                    ),
                    "body": {"Education": [{"title": "Student"}]},
                },
                "appropriate": True,
            },
        ]

        for scenario in test_scenarios:
            processed_resume = self._process_resume_with_business_logic(
                scenario["data"], temp_dir
            )
            template_appropriate = self._validate_template_choice(processed_resume)

            assert template_appropriate == scenario["appropriate"], (
                f"Template validation mismatch for {scenario['name']}"
            )

    # Helper methods for business logic validation
    def _validate_professional_resume_business_rules(
        self, resume_data: dict[str, Any]
    ) -> None:
        """Validate professional Resume business rules."""
        required_fields = ["full_name", "email", "phone", "description", "body"]
        for field in required_fields:
            assert field in resume_data, f"Professional Resume must have {field}"
            assert resume_data[field], f"Professional Resume {field} cannot be empty"

        # Email validation
        assert "@" in resume_data["email"], "Email must contain '@'"
        assert "." in resume_data["email"], "Email must contain '.'"

        # Phone validation
        phone = (
            resume_data["phone"]
            .replace(" ", "")
            .replace("-", "")
            .replace("(", "")
            .replace(")", "")
        )
        assert phone.replace("+", "").isdigit(), (
            "Phone must contain only digits and standard characters"
        )

        # Experience validation
        assert "Experience" in resume_data["body"], (
            "Professional Resume must have experience section"
        )
        assert len(resume_data["body"]["Experience"]) > 0, (
            "Professional Resume must have at least one experience entry"
        )

    def _validate_student_resume_business_rules(
        self, resume_data: dict[str, Any]
    ) -> None:
        """Validate student Resume business rules."""
        # Student Resumes should emphasize education
        if "Education" in resume_data.get("body", {}):
            education_entries = resume_data["body"]["Education"]
            assert len(education_entries) > 0, (
                "Student Resume should have education entries"
            )

        # Should have projects or extracurricular activities
        body_sections = resume_data.get("body", {})
        has_projects = (
            "Projects" in body_sections and len(body_sections["Projects"]) > 0
        )
        has_experience = (
            "Experience" in body_sections and len(body_sections["Experience"]) > 0
        )

        assert has_projects or has_experience, (
            "Student Resume should have projects or relevant experience"
        )

    def _validate_career_change_resume_business_rules(
        self, resume_data: dict[str, Any]
    ) -> None:
        """Validate career change Resume business rules."""
        # Should have both past and new career elements
        body = resume_data.get("body", {})

        # Should show narrative of career transition
        description = resume_data.get("description", "")
        transition_keywords = [
            "transition",
            "career",
            "change",
            "pivot",
            "new",
            "learning",
        ]
        has_transition_narrative = any(
            keyword.lower() in description.lower() for keyword in transition_keywords
        )

        assert has_transition_narrative, (
            "Career change Resume should explain the transition"
        )

        # Should have certifications or education in new field
        has_certifications = "Certification" in body and len(body["Certification"]) > 0
        has_education = "Education" in body and len(body["Education"]) > 0

        assert has_certifications or has_education, (
            "Career change Resume should show new qualifications"
        )

    def _validate_contact_information(self, resume_data: dict[str, Any]) -> bool:
        """Validate contact information format and completeness."""
        contact_methods = 0

        if resume_data.get("email"):
            email = resume_data["email"]
            if "@" in email and "." in email.split("@")[1]:
                contact_methods += 1

        if resume_data.get("phone"):
            phone = resume_data["phone"]
            clean_phone = (
                phone.replace(" ", "")
                .replace("-", "")
                .replace("(", "")
                .replace(")", "")
            )
            if clean_phone.replace("+", "").isdigit() and len(clean_phone) >= 10:
                contact_methods += 1

        if resume_data.get("web") and resume_data["web"].startswith(
            ("http://", "https://")
        ):
            contact_methods += 1

        if resume_data.get("linkedin") and (
            "linkedin.com" in resume_data["linkedin"]
            or resume_data["linkedin"].startswith("in/")
        ):
            contact_methods += 1

        # Business Rule: Must have at least 2 valid contact methods
        return contact_methods >= 2

    def _validate_template_choice(self, resume_data: dict[str, Any]) -> bool:
        """Validate template appropriateness for content type."""
        template = resume_data.get("template", "")
        body = resume_data.get("body", {})

        if template == "resume_no_bars":
            # Good for technical roles, minimal design
            return "Experience" in body or "Projects" in body
        elif template == "resume_with_bars":
            # Good for executive/management roles
            return "Experience" in body and len(body["Experience"]) >= 2
        elif template == "cover":
            # Good for applications/cover letters
            return len(resume_data.get("description", "")) > 100

        return True  # Default to valid for unknown templates

    def _get_resume_content_length(self, resume_data: dict[str, object]) -> int:
        """Calculate total content length of Resume."""
        content_parts = [
            resume_data.get("description", ""),
            resume_data.get("full_name", ""),
            " ".join(resume_data.get("expertise", [])),  # type: ignore[arg-type]
        ]

        # Add body content
        body = resume_data.get("body", {})
        for section in body.values():  # type: ignore[attr-defined]
            for item in section:
                content_parts.extend(
                    [
                        item.get("title", ""),
                        item.get("company", ""),
                        item.get("description", ""),
                    ]
                )

        return len(" ".join(str(part) for part in content_parts))

    def _process_resume_with_business_logic(
        self, resume_data: dict[str, Any], temp_dir: Path
    ) -> dict[str, Any]:
        """Process Resume through the actual business logic."""
        # Create Resume file
        resume_file = temp_dir / "test_resume.yaml"
        with open(resume_file, "w", encoding="utf-8") as f:
            yaml.dump(resume_data, f)

        # Test input directory
        test_input_dir = temp_dir / "input"
        test_input_dir.mkdir(exist_ok=True)
        test_output_dir = temp_dir / "output"
        test_output_dir.mkdir(exist_ok=True)
        (test_input_dir / "test_resume.yaml").write_text(resume_file.read_text())

        # Create Paths object for testing
        paths = Paths(
            data=temp_dir,
            input=test_input_dir,
            output=test_output_dir,
            content=temp_dir / "content",
            templates=temp_dir / "templates",
            static=temp_dir / "static",
        )

        # Process through business logic
        processed_resume = get_content("test_resume", paths=paths)
        return processed_resume


class TestMinimalConfigRendering:
    """Integration tests for template rendering with minimal configuration.

    Issue #26: Ensure templates render correctly when using minimal config,
    relying on defaults from both the config normalization and template
    defensive .get() patterns.
    """

    def test_template_renders_with_minimal_config(self) -> None:
        """Verify templates render without KeyError using only required fields.

        This test validates that Issue #25 (defensive .get() in templates) and
        Issue #27 (consolidated plan.py) work together to allow minimal config.
        """
        # Minimal data with only required fields - rely on defaults
        minimal_data = {
            "full_name": "Test User",
            "config": {"output_mode": "html"},  # Minimal non-empty config
        }

        # Should not raise KeyError
        result = prepare_render_data(minimal_data, registry=PaletteRegistry())

        # Verify render plan was created
        assert result is not None
        assert result.context is not None

        # Verify color keys that are always defaulted are present
        # Note: page_width/height/sidebar_width may be None - templates use .get()
        always_present_keys = [
            "theme_color",
            "sidebar_color",
            "sidebar_text_color",
            "bar_background_color",
            "date2_color",
            "frame_color",
        ]
        for key in always_present_keys:
            assert key in result.context, f"Missing required key: {key}"

    def test_resume_config_dict_has_color_keys(self) -> None:
        """Verify resume_config dict in context has color keys templates access."""
        minimal_data = {
            "full_name": "Test User",
            "config": {"output_mode": "html"},
        }

        result = prepare_render_data(minimal_data, registry=PaletteRegistry())

        # The resume_config dict is what templates access via resume_config.get()
        resume_config = result.context.get("resume_config", {})

        # Keys that are always present after normalization (colors and computed values)
        # Note: page_width/height/sidebar_width may NOT be in resume_config when not
        # specified - templates use defensive .get() with defaults for these
        always_normalized_keys = [
            "sidebar_color",
            "theme_color",
            "sidebar_padding_left",
            "sidebar_padding_right",
            "sidebar_padding_top",
            "sidebar_padding_bottom",
            "sidebar_text_color",
            "sidebar_bold_color",
            "bold_font_weight",
            "bar_background_color",
            "date2_color",
            "frame_color",
            "heading_icon_color",
            "h2_padding_top",
            "h3_padding_top",
            "section_heading_margin_top",
            "section_heading_margin_bottom",
        ]

        for key in always_normalized_keys:
            assert key in resume_config, (
                f"Missing key '{key}' in resume_config - templates may fail"
            )

    def test_template_rendering_with_jinja2(self) -> None:
        """Integration test: render base template with minimal config.

        This tests that Issue #25's defensive .get() patterns in resume_base.html
        work correctly - the CSS variables should be rendered with defaults even
        when config values are missing.

        Note: Extended templates (resume_no_bars, resume_with_bars) require
        additional context like 'titles' dict which is outside Issue #25's scope.
        """
        minimal_data = {
            "full_name": "Test User",
            "description": "A test description",
            "config": {"output_mode": "html"},
            "body": {},  # Empty body sections
        }

        result = prepare_render_data(minimal_data, registry=PaletteRegistry())

        # Set up Jinja2 environment with actual templates using production setup
        templates_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "simple_resume"
            / "shell"
            / "assets"
            / "templates"
        )
        env = get_template_environment(str(templates_path))

        # Test resume_base.html - this contains the CSS variable .get() patterns
        template = env.get_template("html/resume_base.html")

        # Should render without KeyError due to defensive .get() patterns
        # This is the key test - any KeyError here means Issue #25 regressed
        rendered = template.render(**result.context)
        assert rendered, "Template produced empty output"

        # Verify CSS variables from resume_config.get() are rendered with defaults
        assert "--sidebar-color:" in rendered, "Missing sidebar-color CSS variable"
        assert "--theme-color:" in rendered, "Missing theme-color CSS variable"
        assert "--page-width:" in rendered, "Missing page-width CSS variable"
        assert "--page-height:" in rendered, "Missing page-height CSS variable"
        assert "--sidebar-width:" in rendered, "Missing sidebar-width CSS variable"

        # Verify default values are used (from Issue #25's .get() defaults)
        assert "#F6F6F6" in rendered, "Default sidebar-color not applied"
        assert "#0395DE" in rendered, "Default theme-color not applied"
        assert "210mm" in rendered, "Default page-width not applied"
        assert "297mm" in rendered, "Default page-height not applied"
        assert "65mm" in rendered, "Default sidebar-width not applied"

    def test_cover_template_renders_with_minimal_config(self) -> None:
        """Verify cover.html template works with minimal config.

        Issue #25 added defensive .get() patterns to cover.html.
        This test ensures cover letters render correctly when
        optional config values (cover_padding_top, etc.) are missing.
        """
        minimal_data = {
            "full_name": "Test User",
            "template": "cover",
            "description": "Cover letter content here.",
            "config": {"output_mode": "html"},
            "body": {},
        }

        result = prepare_render_data(minimal_data, registry=PaletteRegistry())

        # Verify resume_config exists
        assert result.context is not None
        resume_config = result.context.get("resume_config", {})
        assert isinstance(resume_config, dict)

        # Set up Jinja2 environment with actual templates
        templates_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "simple_resume"
            / "shell"
            / "assets"
            / "templates"
        )
        env = get_template_environment(str(templates_path))
        template = env.get_template("html/cover.html")

        # Should render without KeyError due to defensive .get() patterns
        rendered = template.render(**result.context)
        assert rendered, "Cover template produced empty output"

        # Verify no invalid CSS from None values
        assert "Nonemm" not in rendered, "Invalid CSS from None+mm concatenation"
        assert "Nonepx" not in rendered, "Invalid CSS from None+px concatenation"
        assert "None}" not in rendered, "Invalid CSS value from None"

        # Verify cover-specific CSS variables are present
        assert "padding-top:" in rendered, "Missing cover padding-top"
        assert "padding-bottom:" in rendered, "Missing cover padding-bottom"
