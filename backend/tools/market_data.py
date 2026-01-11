"""Mock market salary data for various companies and roles.

This data is used by the check_market_rate tool to validate candidate claims
and inform Marcus's offer decisions.

Also includes mock candidate resumes for testing scripts.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class SalaryRange:
    """Represents a salary range for a specific role/company/level."""

    min: int
    max: int
    typical: int
    company: str
    role: str
    level: str

    def __str__(self):
        return f"${self.min:,} - ${self.max:,} (typical: ${self.typical:,})"


# Mock market data - organized by company, then role, then level
# Based on realistic 2024/2025 tech compensation data
MARKET_DATA: Dict[str, Dict[str, Dict[str, SalaryRange]]] = {
    "Google": {
        "Software Engineer": {
            "new_grad": SalaryRange(
                min=120000,
                max=150000,
                typical=135000,
                company="Google",
                role="Software Engineer",
                level="new_grad",
            ),
            "mid": SalaryRange(
                min=150000,
                max=220000,
                typical=185000,
                company="Google",
                role="Software Engineer",
                level="mid",
            ),
            "senior": SalaryRange(
                min=200000,
                max=350000,
                typical=275000,
                company="Google",
                role="Software Engineer",
                level="senior",
            ),
        },
        "Product Manager": {
            "new_grad": SalaryRange(
                min=110000,
                max=140000,
                typical=125000,
                company="Google",
                role="Product Manager",
                level="new_grad",
            ),
            "mid": SalaryRange(
                min=160000,
                max=230000,
                typical=195000,
                company="Google",
                role="Product Manager",
                level="mid",
            ),
            "senior": SalaryRange(
                min=220000,
                max=380000,
                typical=300000,
                company="Google",
                role="Product Manager",
                level="senior",
            ),
        },
    },
    "Meta": {
        "Software Engineer": {
            "new_grad": SalaryRange(
                min=115000,
                max=155000,
                typical=140000,
                company="Meta",
                role="Software Engineer",
                level="new_grad",
            ),
            "mid": SalaryRange(
                min=155000,
                max=240000,
                typical=195000,
                company="Meta",
                role="Software Engineer",
                level="mid",
            ),
            "senior": SalaryRange(
                min=210000,
                max=380000,
                typical=295000,
                company="Meta",
                role="Software Engineer",
                level="senior",
            ),
        },
    },
    "Amazon": {
        "Software Engineer": {
            "new_grad": SalaryRange(
                min=100000,
                max=130000,
                typical=115000,
                company="Amazon",
                role="Software Engineer",
                level="new_grad",
            ),
            "mid": SalaryRange(
                min=130000,
                max=200000,
                typical=165000,
                company="Amazon",
                role="Software Engineer",
                level="mid",
            ),
            "senior": SalaryRange(
                min=180000,
                max=320000,
                typical=250000,
                company="Amazon",
                role="Software Engineer",
                level="senior",
            ),
        },
    },
    "Netflix": {
        "Software Engineer": {
            "new_grad": SalaryRange(
                min=130000,
                max=180000,
                typical=155000,
                company="Netflix",
                role="Software Engineer",
                level="new_grad",
            ),
            "mid": SalaryRange(
                min=200000,
                max=320000,
                typical=260000,
                company="Netflix",
                role="Software Engineer",
                level="mid",
            ),
            "senior": SalaryRange(
                min=300000,
                max=500000,
                typical=400000,
                company="Netflix",
                role="Software Engineer",
                level="senior",
            ),
        },
    },
    "Microsoft": {
        "Software Engineer": {
            "new_grad": SalaryRange(
                min=105000,
                max=135000,
                typical=120000,
                company="Microsoft",
                role="Software Engineer",
                level="new_grad",
            ),
            "mid": SalaryRange(
                min=140000,
                max=210000,
                typical=175000,
                company="Microsoft",
                role="Software Engineer",
                level="mid",
            ),
            "senior": SalaryRange(
                min=190000,
                max=330000,
                typical=260000,
                company="Microsoft",
                role="Software Engineer",
                level="senior",
            ),
        },
    },
    "Startup": {
        "Software Engineer": {
            "new_grad": SalaryRange(
                min=80000,
                max=120000,
                typical=100000,
                company="Startup",
                role="Software Engineer",
                level="new_grad",
            ),
            "mid": SalaryRange(
                min=110000,
                max=160000,
                typical=135000,
                company="Startup",
                role="Software Engineer",
                level="mid",
            ),
            "senior": SalaryRange(
                min=140000,
                max=220000,
                typical=180000,
                company="Startup",
                role="Software Engineer",
                level="senior",
            ),
        },
    },
}


def get_market_rate(
    role: str, company: str, level: str = "new_grad"
) -> Optional[SalaryRange]:
    """Look up market rate for a specific role/company/level.

    Args:
        role: Job role (e.g. 'Software Engineer')
        company: Company name (e.g. 'Google', 'Meta')
        level: Seniority level ('new_grad', 'mid', 'senior')

    Returns:
        SalaryRange if found, None otherwise
    """
    # Normalize inputs
    company = company.strip()
    role = role.strip()
    level = level.strip().lower()

    # Try exact match first
    if company in MARKET_DATA:
        if role in MARKET_DATA[company]:
            if level in MARKET_DATA[company][role]:
                return MARKET_DATA[company][role][level]

    # Try case-insensitive match for company
    company_lower = company.lower()
    for comp_key in MARKET_DATA:
        if comp_key.lower() == company_lower:
            if role in MARKET_DATA[comp_key]:
                if level in MARKET_DATA[comp_key][role]:
                    return MARKET_DATA[comp_key][role][level]

    # If no match, return None
    return None


def format_market_rate_response(salary_range: Optional[SalaryRange]) -> str:
    """Format a market rate lookup result as a human-readable string.

    Args:
        salary_range: The salary range from get_market_rate, or None

    Returns:
        Formatted string describing the market rate
    """
    if salary_range is None:
        return "No market data available for that role/company combination."

    return (
        f"Market data for {salary_range.role} at {salary_range.company} "
        f"({salary_range.level}): {salary_range}. "
        f"This includes base salary, bonus, and equity value."
    )


# Mock candidate resumes for testing scripts
@dataclass
class CandidateResume:
    """Mock candidate background information."""

    name: str
    role: str
    level: str
    education: str
    experience: List[str]
    skills: List[str]
    competing_offers: List[Dict[str, any]]
    strengths: List[str]
    weaknesses: List[str]


MOCK_RESUMES: Dict[str, CandidateResume] = {
    "professional": CandidateResume(
        name="Alex Chen (The Professional)",
        role="Software Engineer",
        level="new_grad",
        education="BS Computer Science, Top 20 University, GPA 3.7",
        experience=[
            "Google internship - distributed systems team (Summer 2024)",
            "Built internal monitoring tool used by 500+ engineers",
            "Open source contributor to popular Python framework",
        ],
        skills=[
            "Python",
            "Go",
            "Distributed Systems",
            "Docker",
            "Kubernetes",
            "System Design",
        ],
        competing_offers=[
            {
                "company": "Google",
                "role": "Software Engineer",
                "level": "new_grad",
                "amount": 135000,
                "verified": True,
            }
        ],
        strengths=[
            "Well-prepared with market research",
            "Has legitimate competing offer",
            "Professional communication style",
            "Shows clear value proposition",
            "Concise and respectful",
        ],
        weaknesses=[],
    ),
    "overconfident": CandidateResume(
        name="Jordan Smith (The Overconfident)",
        role="Software Engineer",
        level="new_grad",
        education="BS Computer Science, Mid-tier University, GPA 3.2",
        experience=[
            "Built a personal app with 'lots of users' (unverified)",
            "Completed online coding bootcamp",
            "Some freelance web development",
        ],
        skills=[
            "Python",
            "JavaScript",
            "Started learning Rust (tutorial incomplete)",
        ],
        competing_offers=[
            {
                "company": "Meta",
                "role": "Software Engineer",
                "level": "new_grad",
                "amount": 200000,
                "verified": False,  # UNREALISTIC
            },
            {
                "company": "Google",
                "role": "Software Engineer",
                "level": "new_grad",
                "amount": 200000,
                "verified": False,  # UNREALISTIC
            },
            {
                "company": "Netflix",
                "role": "Software Engineer",
                "level": "new_grad",
                "amount": 200000,
                "verified": False,  # UNREALISTIC - Netflix pays more but not this much for new grad
            },
        ],
        strengths=[],
        weaknesses=[
            "Inflated/unverified claims about offers",
            "Rambles excessively",
            "Aggressive and dismissive",
            "No clear evidence of technical depth",
            "Unrealistic salary expectations ($180k floor)",
            "Disrespectful communication",
        ],
    ),
    "nervous_rambler": CandidateResume(
        name="Sam Johnson (The Nervous Rambler)",
        role="Software Engineer",
        level="new_grad",
        education="BS Computer Science + Math Minor, Good University, GPA 3.5",
        experience=[
            "University research assistant - ML project",
            "Built a few class projects",
            "Participated in hackathons",
        ],
        skills=["Python", "Java", "Basic ML", "Web Development"],
        competing_offers=[],
        strengths=[
            "Polite and well-meaning",
            "Decent technical background",
            "Honest about inexperience",
        ],
        weaknesses=[
            "Overly nervous",
            "Rambles and over-explains",
            "Indecisive and repetitive",
            "Lacks confidence in negotiation",
            "Asks too many clarifying questions",
            "Wastes time with circular conversation",
        ],
    ),
}


def get_candidate_resume(candidate_type: str) -> Optional[CandidateResume]:
    """Get mock resume for a test candidate.

    Args:
        candidate_type: Type of candidate ('professional', 'overconfident', 'nervous_rambler')

    Returns:
        CandidateResume if found, None otherwise
    """
    return MOCK_RESUMES.get(candidate_type.lower())
