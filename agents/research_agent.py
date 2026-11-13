import os
import re
import time
import html
import json
import ast

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI


# ==================================================
# PROJECT CONFIGURATION
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class ResearchAgent:

    def __init__(self):

        tavily_api_key = os.getenv("TAVILY_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY is missing from .env")

        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY is missing from .env")

        self.tavily = TavilyClient(api_key=tavily_api_key)

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=google_api_key,
            timeout=60,
            max_retries=1
        )

        self.minimum_relevance = 0.70
        self.minimum_content_length = 300
        self.maximum_results = 5
        self.batch_size = 5

        print("Research Agent initialized successfully!")
        print("Tavily and Gemini are connected.")

    # ==================================================
    # DOMAIN UTILITIES
    # ==================================================

    def get_hostname(self, url):
        try:
            return (urlsplit(url).hostname or "").lower().strip(".")
        except Exception:
            return ""
    def get_domain(self, url):

        try:
            hostname = urlsplit(str(url)).hostname

            if not hostname:
                return ""

            hostname = hostname.lower().strip()

            if hostname.startswith("www."):
                hostname = hostname[4:]

            return hostname

        except Exception:
            return ""

    def domain_matches(self, hostname, trusted_domain):
        hostname = hostname.lower().strip(".")
        trusted_domain = trusted_domain.lower().strip(".")

        return (
            hostname == trusted_domain
            or hostname.endswith("." + trusted_domain)
        )

    def matches_any_domain(self, hostname, domains):
        return any(
            self.domain_matches(hostname, domain)
            for domain in domains
        )

    def normalize_url(self, url):
        try:
            parsed = urlsplit(url)

            return urlunsplit((
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",
                ""
            ))

        except Exception:
            return url

    # ==================================================
    # TEXT CLEANING
    # ==================================================

    def clean_text(self, text):
        if not text:
            return ""

        text = html.unescape(str(text))
        text = re.sub(r"<[^>]+>", " ", text)

        return re.sub(r"\s+", " ", text).strip()

    def get_best_article_content(self, result):
        """
        Select the best article content by comparing
        both Tavily content fields after cleaning.
        """

        content = str(
            result.get("content", "") or ""
        )

        raw_content = str(
            result.get("raw_content", "") or ""
        )

        # Clean both candidates before comparing.
        cleaned_content = self.clean_article_content(
            content
        )

        cleaned_raw_content = self.clean_article_content(
            raw_content
        )

        # Prefer whichever candidate contains usable text.
        if not cleaned_content:
            return raw_content

        if not cleaned_raw_content:
            return content

        # Prefer raw content only when it provides
        # meaningfully more cleaned article information.
        if (
            len(cleaned_raw_content)
            > len(cleaned_content) * 1.10
        ):
            return raw_content

        return content

    def clean_article_content(self, content):

        if not content:
            return ""

        content = html.unescape(str(content))

        # ==================================================
        # 1. REMOVE SCRIPTS, STYLES AND HTML COMMENTS
        # ==================================================

        content = re.sub(
            r"<script\b[^>]*>.*?</script>",
            " ",
            content,
            flags=re.I | re.S
        )

        content = re.sub(
            r"<style\b[^>]*>.*?</style>",
            " ",
            content,
            flags=re.I | re.S
        )

        content = re.sub(
            r"<!--.*?-->",
            " ",
            content,
            flags=re.S
        )

        # ==================================================
        # 2. REMOVE HTML TAGS
        # ==================================================

        content = re.sub(
            r"<[^>]+>",
            " ",
            content
        )

        # ==================================================
        # 3. CLEAN MARKDOWN LINKS
        # Preserve useful anchor text.
        # ==================================================

                # Handle escaped Markdown parentheses
        content = content.replace(r"\(", "(").replace(r"\)", ")")

        content = re.sub(
            r"!\[([^\]]*)\]\([^)]+\)",
            r" \1 ",
            content
        )

        content = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r" \1 ",
            content
        )
        # Remove remaining URLs.
        content = re.sub(
            r"https?://\S+",
            " ",
            content
        )

        # ==================================================
        # 4. REMOVE COMMON NAVIGATION ELEMENTS
        # ==================================================

        navigation_patterns = [
            r"\bSkip\s+to\s+content\b",
            r"\bOpen\s+navigation\b",
            r"\bClose\s+navigation\b",
            r"\bCookie\s+Settings\b",
            r"\bBack\s+to\s+top\b",
            r"\bopens\s+in\s+a\s+new\s+window\b",
            r"\bToggle\s+navigation\b",
            r"\bMenu\s+Close\b"
        ]

        for pattern in navigation_patterns:
            content = re.sub(
                pattern,
                " ",
                content,
                flags=re.I
            )

        # ==================================================
        # 5. REMOVE KNOWN WEBSITE NAVIGATION NOISE
        # ==================================================

        navigation_noise = [
            r"Explore\s+Featured\s+Categories",
            r"Explore\s+by\s+Role",
            r"Explore\s+by\s+Skill",
            r"Browse\s+Free\s+Courses\s+by\s+Category",
            r"Explore\s+Related\s+Categories",
            r"Learn\s+On\s+the\s+Go",
            r"Work\s+with\s+us",
            r"For\s+Businesses",
            r"Discover\s+For\s+Businesses",
            r"Also\s+from\s+this\s+source"
        ]

        for pattern in navigation_noise:
            content = re.sub(
                pattern,
                " ",
                content,
                flags=re.I
            )

        # ==================================================
        # 6. REMOVE CLEAR WEBSITE FOOTERS
        # Only use relatively reliable footer markers.
        # ==================================================

        footer_patterns = [

            # PR Newswire
            r"The\s+Linux\s+Foundation\s+has\s+registered\s+trademarks",
            r"Media\s+Contact\s*:",
            r"SOURCE\s*:\s*The\s+Linux\s+Foundation",

            # General website footer
            r"All\s+rights\s+reserved",
            r"Your\s+privacy\s+choices",
            r"Subscribe\s+to\s+our\s+newsletter",
            r"Get\s+the\s+latest\s+news\s+in\s+your\s+inbox",

            # Promotional and related content sections
            r"Recommended\s+Programs",
            r"Recommended\s+Resources",
            r"News\s+Releases\s+in\s+Similar\s+Topics",
            r"Request\s+a\s+Demo",
            r"Also\s+from\s+this\s+source"
        ]

        footer_positions = []

        for pattern in footer_patterns:

            match = re.search(
                pattern,
                content,
                flags=re.I
            )

            if match:
                footer_positions.append(match.start())

        if footer_positions:
            content = content[:min(footer_positions)]

        # ==================================================
        # 7. REMOVE RELATED CONTENT AT THE END
        # Avoid cutting article sections containing
        # similar words in the middle of the article.
        # ==================================================

        related_footer_patterns = [

            r"(?im)^\s*Related\s+posts\s*:?\s*$",
            r"(?im)^\s*Related\s+articles\s*:?\s*$",
            r"(?im)^\s*Related\s+stories\s*:?\s*$",
            r"(?im)^\s*More\s+related\s+articles\s*$",
            r"(?im)^\s*Recommended\s+for\s+you\s*$",
            r"(?im)^\s*You\s+may\s+also\s+like\s*$",
            r"(?im)^\s*You\s+might\s+also\s+like\s*$",
            r"(?im)^\s*Share\s+this\s+article\s*$",
            r"(?im)^\s*Latest\s+posts\s*:?\s*$"
        ]

        related_positions = []

        for pattern in related_footer_patterns:

            match = re.search(
                pattern,
                content
            )

            if match:
                related_positions.append(match.start())

        if related_positions:

            content = content[:min(related_positions)]

        # ==================================================
        # 8. REMOVE COMMON PROMOTIONAL ELEMENTS
        # ==================================================

        promotional_patterns = [
            r"\bStart\s+your\s+free\s+trial\b",
            r"\bEnroll\s+now\b",
            r"\bDownload\s+the\s+brochure\b",
            r"\bRegister\s+now\b",
            r"\bRequest\s+more\s+information\b"
        ]

        for pattern in promotional_patterns:

            content = re.sub(
                pattern,
                " ",
                content,
                flags=re.I
            )

        # ==================================================
        # 9. REMOVE EMPTY MARKDOWN AND REPEATED SYMBOLS
        # ==================================================

        content = re.sub(
            r"^\s*[-_*]{3,}\s*$",
            " ",
            content,
            flags=re.M
        )

        content = re.sub(
            r"[ \t]+",
            " ",
            content
        )

        content = re.sub(
            r"\n\s*\n+",
            "\n\n",
            content
        )

        content = content.strip()

        return content
    # ==================================================
    # KEYWORDS AND SEARCH
    # ==================================================

    def extract_keywords(self, text):

        stop_words = {
            "the", "and", "for", "with", "from", "that",
            "this", "are", "was", "were", "have", "has",
            "had", "will", "would", "could", "should",
            "into", "about", "their", "there", "what",
            "when", "where", "which", "while", "than",
            "then", "also", "been", "being", "using",
            "used", "use", "more", "most", "some", "such",
            "only", "other", "over", "under", "after",
            "before", "between", "through", "latest",
            "recent", "developments"
        }

        words = re.findall(
            r"\b[a-zA-Z0-9-]+\b",
            text.lower()
        )

        return list(dict.fromkeys(
            word for word in words
            if len(word) > 2 and word not in stop_words
        ))

    def calculate_keyword_relevance(self, topic, content):

        keywords = self.extract_keywords(topic)

        if not keywords:
            return 0.0

        content = content.lower()

        matches = sum(
            keyword in content
            for keyword in keywords
        )

        return matches / len(keywords)

    def build_search_queries(self, topic):

        return [
            topic,
            f"{topic} latest official announcements and releases",
            f"{topic} recent research papers and preprints",
            f"{topic} technical breakthroughs from AI research labs",
            f"{topic} recent developments reported by technology news"
        ]

    def is_recent_research_topic(self, topic):

        terms = [
            "latest",
            "recent",
            "new developments",
            "current developments",
            "breakthroughs",
            "this month",
            "this year",
            "2026",
            "2025"
        ]

        topic = topic.lower()

        return any(term in topic for term in terms)

    # ==================================================
    # PAGE FILTERING
    # ==================================================

    def is_blocked_page(self, content):

        patterns = [
            "verify you are human",
            "checking your browser",
            "access denied",
            "captcha",
            "enable javascript to continue",
            "temporarily blocked",
            "security verification"
        ]

        content = content.lower()

        return any(
            pattern in content
            for pattern in patterns
        )

    def is_listing_page(self, title, content):

        title = title.lower()
        content = content.lower()

        if any(pattern in title for pattern in [
            "release notes",
            "changelog",
            "archive",
            "all announcements",
            "all news",
            "news archive"
        ]):
            return True

        dates = re.findall(
            r"\b(?:20\d{2})[-/]\d{1,2}[-/]\d{1,2}\b",
            content
        )

        return (
            len(set(dates)) >= 4
            and any(
                word in content
                for word in ["release notes", "changelog", "updates"]
            )
        )

    def is_newsroom_archive(self, title, url, content):

        title = title.lower()
        url = url.lower()
        content = content.lower()

        identity = any(pattern in title for pattern in [
            "newsroom",
            "news archive",
            "press release archive",
            "press releases",
            "all announcements",
            "company news"
        ])

        newsroom_url = any(pattern in url for pattern in [
            "/news",
            "/news/",
            "/newsroom",
            "/press",
            "/press-releases",
            "/announcements"
        ])

        date_patterns = [
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"[a-z]*\s+\d{1,2},?\s+20\d{2}\b",
            r"\b20\d{2}-\d{1,2}-\d{1,2}\b",
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"[a-z]*\s+20\d{2}\b"
        ]

        date_count = sum(
            len(re.findall(pattern, content, flags=re.I))
            for pattern in date_patterns
        )

        read_more = len(re.findall(
            r"read\s+(?:the\s+)?(?:full\s+)?story|read\s+more|view\s+announcement",
            content
        ))

        headings = len(re.findall(
            r"(?:^|\s)#{1,3}\s+",
            content
        ))

        return (
            (identity and (date_count >= 2 or read_more >= 2))
            or (
                newsroom_url
                and date_count >= 4
                and read_more >= 3
            )
            or (
                date_count >= 5
                and read_more >= 4
                and headings >= 4
            )
        )

    def is_documentation_landing_page(self, title, url, content):

        url = url.lower()
        title = title.lower()
        content = content.lower()

        doc_url = any(pattern in url for pattern in [
            "/docs",
            "/documentation",
            "/developers/docs",
            "/developer/documentation"
        ])

        nav_terms = [
            "get started",
            "getting started",
            "learn about models",
            "developer tools",
            "api keys",
            "sdk",
            "sdks and the cli",
            "support",
            "tutorials",
            "quick start",
            "quickstart",
            "build agents",
            "deploy agents",
            "import models",
            "documentation",
            "api reference",
            "code examples",
            "resources"
        ]

        nav_count = sum(
            term in content
            for term in nav_terms
        )

        links = len(re.findall(
            r"\[[^\]]+\]\((?:/|[a-zA-Z0-9_-]+\.html)",
            content
        ))

        generic_titles = {
            "generative ai",
            "documentation",
            "developer documentation",
            "api documentation",
            "developer guide",
            "product documentation"
        }

        return (
            doc_url
            and nav_count >= 5
            and (
                title.strip() in generic_titles
                or links >= 12
                or (nav_count >= 7 and links >= 15)
            )
        )

    def is_ai_company_directory(self, title, url, content):

        title = title.lower()
        url = url.lower()
        content = content.lower()

        categories = [
            "agent models",
            "image, video and interactive worlds",
            "image and video",
            "video generation",
            "voice, speech and music",
            "speech and music",
            "world models",
            "robotics and physical ai",
            "physical ai",
            "science, biology and materials",
            "biology and materials",
            "open, efficient and new-architecture models",
            "open and efficient models",
            "model architectures",
            "ai infrastructure",
            "ai applications",
            "ai agents",
            "generative ai companies",
            "ai startups"
        ]

        category_count = sum(
            term in content
            for term in categories
        )

        directory_titles = [
            "ai startup directory",
            "ai companies directory",
            "ai company directory",
            "ai startup landscape",
            "ai landscape",
            "ai company landscape",
            "ai ecosystem map",
            "map of ai companies",
            "ai companies to watch",
            "ai startups to watch",
            "ai startup database",
            "directory of ai companies",
            "ai company database",
            "the ai landscape"
        ]

        has_title = any(
            term in title
            for term in directory_titles
        )

        directory_url = any(pattern in url for pattern in [
            "/directory",
            "/directories",
            "/landscape",
            "/ecosystem",
            "/companies",
            "/startups",
            "/startup-map",
            "/company-map"
        ])

        logos = {
            name.strip().lower()
            for name in re.findall(
                r"!\[([^\]]+)\]\s*\\?\(",
                content
            )
            if len(name.strip()) >= 2
        }

        entries = sum(
            len(re.findall(pattern, content))
            for pattern in [
                r"!\[[^\]]+\]\s*\\?\(",
                r"\[[A-Z][A-Za-z0-9& .'-]{1,40}\]\(",
                r"(?m)^\s*[-*]\s+[A-Z][A-Za-z0-9& .'-]{1,40}\s*$"
            ]
        )

        directory_language = sum(
            term in content
            for term in [
                "companies in this category",
                "ai companies",
                "ai startups",
                "startup landscape",
                "company landscape",
                "explore companies",
                "browse companies",
                "meet the companies",
                "companies building",
                "companies working on",
                "ai ecosystem",
                "company directory"
            ]
        )

        heading_count = len(re.findall(
            r"(?m)^\s*#{1,3}\s+.+",
            content
        ))

        return (
            (len(logos) >= 5 and category_count >= 3)
            or (entries >= 8 and category_count >= 3)
            or (
                has_title
                and (
                    len(logos) >= 3
                    or entries >= 5
                    or category_count >= 2
                )
            )
            or (
                directory_url
                and (
                    len(logos) >= 5
                    or (
                        category_count >= 3
                        and directory_language >= 2
                    )
                )
            )
            or (
                category_count >= 5
                and entries >= 6
                and heading_count >= 5
            )
        )

    def is_research_landing_page(self, title, url, content):
        """
        Reject generic research hubs and topic landing pages.
        Preserve individual research articles.
        """

        title_l = title.lower().strip()
        url_l = url.lower()
        text = content.lower()

        generic_titles = {
            "artificial intelligence",
            "ai research",
            "research",
            "generative ai",
            "artificial intelligence research",
            "machine learning research"
        }

        path = urlsplit(url).path.strip("/").lower()

        generic_path = path in {
            "artificial-intelligence",
            "ai",
            "research",
            "artificial-intelligence-research",
            "machine-learning"
        }

        hub_signals = [
            "areas of research",
            "research areas",
            "explore our research",
            "research topics",
            "our research",
            "research projects",
            "featured research",
            "all research",
            "research teams",
            "research publications",
            "research initiatives",
            "featured topics",
            "explore our work",
            "research news",
            "latest research"
        ]

        hub_count = sum(
            signal in text
            for signal in hub_signals
        )

        link_count = len(re.findall(
            r"\[[^\]]+\]\((?:https?://|/)",
            content
        ))

        article_signals = [
            "abstract",
            "doi.org",
            "published in",
            "we propose",
            "we introduce",
            "we demonstrate",
            "our results show",
            "methodology",
            "experimental results",
            "conclusion"
        ]

        article_count = sum(
            signal in text
            for signal in article_signals
        )

        if (
            "research.ibm.com" in url_l
            and path == "artificial-intelligence"
        ):
            return True

        if (
            title_l in generic_titles
            and (generic_path or hub_count >= 2)
        ):
            return article_count < 2

        return (
            generic_path
            and hub_count >= 3
            and link_count >= 8
            and article_count < 2
        )

    def is_whitepaper_landing_page(self, title, url, content):

        text = (
            title + " " + url + " " + content[:5000]
        ).lower()

        identity = any(pattern in text for pattern in [
            "whitepaper",
            "white paper",
            "ebook",
            "e-book",
            "downloadable report"
        ])

        cta = any(pattern in text for pattern in [
            "download now",
            "download the whitepaper",
            "download whitepaper",
            "download our report",
            "download the ebook",
            "download the e-book",
            "get your copy",
            "access the whitepaper"
        ])

        other_signals = sum(
            pattern in text
            for pattern in [
                "what you'll learn",
                "what you will learn",
                "related blog posts",
                "related resources",
                "request a demo",
                "fill out the form",
                "get the report"
            ]
        )

        return identity and cta and other_signals >= 1

    def is_market_report_page(self, title, url, content):
        """
        Filter generic market-size, market-share and forecast pages.
        Do not reject substantive technical research merely because
        it mentions market trends.
        """

        title_l = title.lower()
        url_l = url.lower()
        text = (title + " " + content[:5000]).lower()

        market_signals = [
            "market size",
            "market share",
            "market forecast",
            "market growth",
            "market trends",
            "industry analysis",
            "competitive landscape",
            "market segmentation",
            "regional outlook",
            "key players",
            "market opportunity",
            "cagr",
            "revenue forecast",
            "industry forecast",
            "market outlook"
        ]

        market_count = sum(
            signal in text
            for signal in market_signals
        )

        forecast_title = any(signal in title_l for signal in [
            "market size",
            "market share",
            "market forecast",
            "market trends",
            "market outlook",
            "market analysis",
            "industry report"
        ])

        report_domain = any(domain in url_l for domain in [
            "imarcgroup.com",
            "grandviewresearch.com",
            "marketsandmarkets.com",
            "fortunebusinessinsights.com",
            "precedenceresearch.com",
            "mordorintelligence.com"
        ])

        report_language = sum(
            signal in text
            for signal in [
                "buy now",
                "request a sample",
                "download sample",
                "report description",
                "scope of the report",
                "table of contents",
                "key market segments",
                "competitive analysis"
            ]
        )

        technical_evidence = sum(
            signal in text
            for signal in [
                "we introduce",
                "we propose",
                "we demonstrate",
                "experimental results",
                "benchmark results",
                "research paper",
                "arxiv.org",
                "doi.org",
                "open-source model",
                "new architecture"
            ]
        )

        return (
            market_count >= 5
            and (
                forecast_title
                or report_domain
                or report_language >= 2
            )
            and technical_evidence < 2
        )

    def is_category_page(self, url, title):

        url = url.lower()
        title = title.lower()

        blocked_paths = [
            "/category/",
            "/categories/",
            "/tag/",
            "/tags/",
            "/topics/",
            "/topic/",
            "/archive/",
            "/author/",
            "/search/",
            "/directory/"
        ]

        if any(path in url for path in blocked_paths):
            return True

        return any(pattern in title for pattern in [
            "all articles",
            "all posts",
            "browse topics",
            "latest articles",
            "latest posts",
            "news and updates",
            "search results"
        ])
            # ==================================================
    # SOURCE FILTERING
    # ==================================================

    def is_video_or_social_source(self, url, title):

        url = url.lower()
        title = title.lower()

        blocked_domains = [
            "youtube.com",
            "youtu.be",
            "vimeo.com",
            "tiktok.com",
            "instagram.com",
            "facebook.com",
            "linkedin.com",
            "x.com",
            "twitter.com",
            "reddit.com"
        ]

        if any(domain in url for domain in blocked_domains):
            return True

        blocked_title_patterns = [
            "watch video",
            "youtube video",
            "podcast episode",
            "listen to podcast",
            "follow us on"
        ]

        return any(pattern in title for pattern in blocked_title_patterns)

    def is_course_or_tutorial_source(self, url, title):

        url = url.lower()
        title = title.lower()

        blocked_domains = [
            "coursera.org",
            "udemy.com",
            "edx.org",
            "udacity.com",
            "skillshare.com",
            "codecademy.com",
            "freecodecamp.org"
        ]

        if any(domain in url for domain in blocked_domains):
            return True

        blocked_patterns = [
            "complete course",
            "full course",
            "beginner tutorial",
            "step by step tutorial",
            "learn generative ai",
            "learn artificial intelligence",
            "certification course",
            "online course",
            "training course",
            "how to learn"
        ]

        return any(pattern in title for pattern in blocked_patterns)

    def is_promotional_content(self, title, content):

        text = f"{title} {content}".lower()

        promotional_patterns = [
            "sign up for free",
            "register today",
            "start your free trial",
            "get started today",
            "limited time offer",
            "buy now",
            "download our app",
            "contact our sales team",
            "book a demo",
            "request a demo",
            "subscribe today",
            "join our community",
            "sponsored content",
            "paid partnership",
            "advertisement"
        ]

        matches = sum(
            1 for pattern in promotional_patterns
            if pattern in text
        )

        return matches >= 3

    def is_general_educational_content(self, title, content):

        title = title.lower()
        content = content.lower()

        educational_patterns = [
            "what is artificial intelligence",
            "what is generative ai",
            "introduction to artificial intelligence",
            "introduction to generative ai",
            "beginners guide",
            "beginner's guide",
            "complete guide to",
            "ultimate guide to",
            "basics of artificial intelligence",
            "basics of generative ai",
            "how does artificial intelligence work",
            "how does generative ai work",
            "explained for beginners"
        ]

        if any(pattern in title for pattern in educational_patterns):
            return True

        generic_content_patterns = [
            "in this tutorial",
            "in this lesson",
            "you will learn",
            "learning objectives",
            "course curriculum",
            "step-by-step guide"
        ]

        matches = sum(
            1 for pattern in generic_content_patterns
            if pattern in content
        )

        return matches >= 3

    def is_book_or_product_page(self, url, title):

        url = url.lower()
        title = title.lower()

        blocked_url_patterns = [
            "/books/",
            "/book/",
            "/products/",
            "/product/",
            "/store/",
            "/shop/",
            "/pricing/",
            "/plans/",
            "/marketplace/"
        ]

        if any(pattern in url for pattern in blocked_url_patterns):
            return True

        blocked_title_patterns = [
            "buy the book",
            "order the book",
            "best books on",
            "top books about",
            "product review",
            "pricing plans",
            "subscription plans",
            "buy now"
        ]

        return any(
            pattern in title
            for pattern in blocked_title_patterns
        )

    def is_low_quality_source(self, result):

        url = str(result.get("url", "") or "")
        title = str(result.get("title", "") or "")
        content = self.get_best_article_content(result)

        if not url or not title:
            return True

        if self.is_category_page(url, title):
            return True

        if self.is_video_or_social_source(url, title):
            return True

        if self.is_course_or_tutorial_source(url, title):
            return True

        if self.is_book_or_product_page(url, title):
            return True

        if self.is_promotional_content(title, content):
            return True

        if self.is_general_educational_content(title, content):
            return True

        if len(content.strip()) < self.minimum_content_length:
            return True

        return False

    # ==================================================
    # DATE EXTRACTION
    # ==================================================

    def extract_publication_date(self, result):

        possible_date_fields = [
            "published_date",
            "published",
            "date",
            "published_at",
            "created_at",
            "updated_at"
        ]

        for field in possible_date_fields:

            value = result.get(field)

            if not value:
                continue

            try:

                if isinstance(value, datetime):
                    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

                date_string = str(value).strip()

                date_string = date_string.replace("Z", "+00:00")

                try:
                    parsed_date = datetime.fromisoformat(date_string)

                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(
                            tzinfo=timezone.utc
                        )

                    return parsed_date

                except ValueError:
                    pass

                date_formats = [
                    "%Y-%m-%d",
                    "%Y/%m/%d",
                    "%d-%m-%Y",
                    "%B %d, %Y",
                    "%b %d, %Y",
                    "%d %B %Y",
                    "%d %b %Y"
                ]

                for date_format in date_formats:

                    try:

                        parsed_date = datetime.strptime(
                            date_string,
                            date_format
                        )

                        return parsed_date.replace(
                            tzinfo=timezone.utc
                        )

                    except ValueError:
                        continue

            except (TypeError, ValueError, OverflowError):
                continue

        return None

    # ==================================================
    # FRESHNESS SCORING
    # ==================================================

    def calculate_freshness_score(self, result):

        publication_date = self.extract_publication_date(result)

        if not publication_date:
            return 0.50

        current_date = datetime.now(timezone.utc)

        age_days = (
            current_date - publication_date
        ).total_seconds() / 86400

        if age_days < 0:
            return 0.0

        if age_days <= 7:
            return 1.0

        elif age_days <= 30:
            return 0.90

        elif age_days <= 60:
            return 0.75

        elif age_days <= 90:
            return 0.60

        elif age_days <= 180:
            return 0.40

        elif age_days <= 365:
            return 0.25

        return 0.10

    # ==================================================
    # SOURCE CREDIBILITY
    # ==================================================

    def classify_source(self, url, title=""):

        domain = self.get_domain(url)
        title = title.lower()

        academic_domains = [
            "arxiv.org",
            "acm.org",
            "ieee.org",
            "nature.com",
            "science.org",
            "sciencedirect.com",
            "springer.com",
            "researchgate.net",
            "pubmed.ncbi.nlm.nih.gov",
            "openreview.net",
            "preprints.org"
        ]

        official_technology_domains = [
            "openai.com",
            "deepmind.google",
            "research.google",
            "ai.google",
            "microsoft.com",
            "blogs.microsoft.com",
            "aws.amazon.com",
            "anthropic.com",
            "meta.com",
            "ai.meta.com",
            "nvidia.com",
            "developer.nvidia.com",
            "huggingface.co",
            "ibm.com",
            "apple.com",
            "cloud.google.com",
            "docs.cloud.google.com"
        ]

        government_domains = [
            ".gov",
            ".gov.in",
            ".gov.uk",
            ".europa.eu"
        ]

        news_domains = [
            "reuters.com",
            "bbc.com",
            "bbc.co.uk",
            "theverge.com",
            "techcrunch.com",
            "wired.com",
            "technologyreview.com",
            "arstechnica.com",
            "venturebeat.com",
            "cnbc.com"
        ]

                # Academic sources
        if any(
            domain == item or domain.endswith("." + item)
            for item in academic_domains
        ):
            if (
                "preprint" in title
                or "arxiv" in domain
                or "preprints.org" in domain
            ):
                return "research_preprint"

            return "research_paper"

        # Google Cloud release notes
        if (
            domain == "docs.cloud.google.com"
            and "release-notes" in url.lower()
        ):
            return "official_announcement"

        # Official technology sources
        if any(
            domain == item or domain.endswith("." + item)
            for item in official_technology_domains
        ):
            return "official_technical_blog"

        # Government sources
        if any(
            domain.endswith(item)
            for item in government_domains
        ):
            return "government_report"
            if (
                domain == "docs.cloud.google.com"
                and "release-notes" in url.lower()
            ):
                return "official_announcement"

        if any(
            domain == item or domain.endswith("." + item)
            for item in news_domains
        ):
            return "news_article"

        if any(
            word in title
            for word in [
                "announces",
                "launches",
                "introduces",
                "releases",
                "unveils"
            ]
        ):
            return "official_announcement"

        if (
            domain == "docs.oracle.com"
            and "releasenotes" in url.lower()
        ):
            return "official_announcement"

        if (
             domain == "docs.cloud.google.com"
             and "release-notes" in url.lower()
        ):
                return "official_announcement"

        # Additional research and technology publications

        if self.domain_matches(
            domain,
            "advancedsciencenews.com"
        ):
            return "expert_commentary"

        if self.domain_matches(
            domain,
            "futureagi.com"
        ):
            return "technical_blog"

        if self.domain_matches(
            domain,
            "reutersinstitute.politics.ox.ac.uk"
        ):
            return "expert_commentary"

        return "other"

    def calculate_credibility_score(self, result):

        url = str(result.get("url", "") or "")
        title = str(result.get("title", "") or "")

        source_type = self.classify_source(url, title)

        credibility_scores = {
            "research_preprint": 0.95,
            "research_paper": 1.00,
            "government_report": 0.90,
            "official_announcement": 0.95,
            "official_technical_blog": 0.95,
            "news_article": 0.85,
            "expert_commentary": 0.80,
            "technical_blog": 0.75,
            "other": 0.60
        }

        return credibility_scores.get(source_type, 0.60)

    # ==================================================
    # DEVELOPMENT SIGNALS
    # ==================================================

    def calculate_development_signal(self, title, content):

        text = f"{title} {content}".lower()

        development_keywords = [
            "announced",
            "announcement",
            "launched",
            "launch",
            "released",
            "release",
            "introduced",
            "introduction",
            "unveiled",
            "deployed",
            "deployment",
            "breakthrough",
            "new model",
            "new feature",
            "new capability",
            "new research",
            "research findings",
            "benchmark",
            "open sourced",
            "open-source",
            "published",
            "updated",
            "partnership",
            "integration",
            "acquisition",
            "funding",
            "inference",
            "reasoning model",
            "agentic ai"
        ]

        matches = sum(
            1 for keyword in development_keywords
            if keyword in text
        )

        return min(matches / 5, 1.0)

    # ==================================================
    # CITATION AND EVIDENCE SIGNALS
    # ==================================================

    def calculate_citation_signal(self, content):

        if not content:
            return 0.0

        content = content.lower()

        evidence_patterns = [
            "according to",
            "research paper",
            "researchers found",
            "study published",
            "clinical trial",
            "arxiv",
            "doi.org",
            "benchmark results",
            "experimental results",
            "technical report",
            "official documentation",
            "white paper",
            "dataset",
            "evaluation results",
            "peer-reviewed"
        ]

        matches = sum(
            1 for pattern in evidence_patterns
            if pattern in content
        )

        return min(matches / 4, 1.0)

    # ==================================================
    # CONTENT QUALITY
    # ==================================================

    def calculate_content_quality(self, result):

        content = self.get_best_article_content(result)
        title = str(result.get("title", "") or "")

        if not content:
            return 0.0

        content = content.strip()

        length = len(content)

        if length < self.minimum_content_length:
            return 0.0

        length_score = min(length / 2500, 1.0)

        paragraphs = [
            paragraph.strip()
            for paragraph in content.split("\n")
            if len(paragraph.strip()) > 50
        ]

        paragraph_score = min(len(paragraphs) / 5, 1.0)

        sentence_count = len(
            re.findall(r"[.!?]+", content)
        )

        sentence_score = min(sentence_count / 15, 1.0)

        title_score = 1.0 if len(title.strip()) >= 15 else 0.5

        quality_score = (
            length_score * 0.35
            + paragraph_score * 0.25
            + sentence_score * 0.25
            + title_score * 0.15
        )

        return round(
            max(0.0, min(quality_score, 1.0)),
            3
        )

    # ==================================================
    # DUPLICATE REMOVAL
    # ==================================================

    def remove_duplicate_results(self, results):

        unique_results = []
        seen_urls = set()
        seen_titles = set()

        for result in results:

            url = str(result.get("url", "") or "").strip()
            title = str(result.get("title", "") or "").strip()

            normalized_url = self.normalize_url(url)

            normalized_title = re.sub(
                r"[^a-z0-9]+",
                " ",
                title.lower()
            ).strip()

            if normalized_url and normalized_url in seen_urls:
                continue

            if normalized_title and normalized_title in seen_titles:
                continue

            if normalized_url:
                seen_urls.add(normalized_url)

            if normalized_title:
                seen_titles.add(normalized_title)

            unique_results.append(result)

        return unique_results
            # ==================================================
    # GEMINI RELEVANCE EVALUATION
    # ==================================================

    def evaluate_relevance_with_gemini(self, results):

        if not results:
            return []

        print(
            f"\nEvaluating {len(results)} sources "
            f"in Gemini batches..."
        )

        evaluated_results = []

        total_batches = (
            len(results) + self.batch_size - 1
        ) // self.batch_size

        max_attempts = 4
        retry_delay = 5

        for batch_number in range(total_batches):

            start = batch_number * self.batch_size
            end = start + self.batch_size

            batch = results[start:end]

            print(
                f"Evaluating batch {batch_number + 1}/"
                f"{total_batches} "
                f"({len(batch)} sources)..."
            )

            scores = None

            for attempt in range(1, max_attempts + 1):

                try:

                    prompt = self.build_relevance_prompt(batch)

                    response = self.llm.invoke(prompt)

                    response_content = getattr(
                        response,
                        "content",
                        response
                    )

                    if isinstance(response_content, list):

                        text_parts = []

                        for item in response_content:

                            if isinstance(item, dict):
                                text_parts.append(
                                    str(item.get("text", ""))
                                )

                            else:
                                text_parts.append(str(item))

                        response_text = "\n".join(text_parts)

                    else:
                        response_text = str(response_content)

                    parsed_scores = self.parse_gemini_scores(
                        response_text,
                        len(batch)
                    )

                    valid_count = sum(
                        1 for score in parsed_scores
                        if score > 0
                    )

                    if valid_count == 0:

                        raise ValueError(
                            "Gemini returned no valid relevance scores."
                        )

                    scores = parsed_scores

                    print(
                        f"Batch {batch_number + 1} successful: "
                        f"{valid_count}/{len(batch)} scores parsed."
                    )

                    break

                except Exception as error:

                    print(
                        f"Batch {batch_number + 1}, "
                        f"attempt {attempt}/{max_attempts} failed: "
                        f"{error}"
                    )

                    if attempt < max_attempts:

                        delay = retry_delay * attempt

                        print(
                            f"Retrying in {delay} seconds..."
                        )

                        time.sleep(delay)

            if scores is None:

                print(
                    f"Batch {batch_number + 1} failed "
                    f"after {max_attempts} attempts."
                )

                scores = [0.0] * len(batch)

            for index, result in enumerate(batch):

                result["gemini_relevance_score"] = scores[index]

                evaluated_results.append(result)

            time.sleep(1)

        parsed_count = sum(
            1
            for result in evaluated_results
            if result.get("gemini_relevance_score", 0) > 0
        )

        print(
            f"\nGemini evaluation completed: "
            f"{parsed_count}/{len(results)} scores parsed."
        )

        return evaluated_results
    # ==================================================
    # GEMINI PROMPT
    # ==================================================

    def build_relevance_prompt(self, batch):

        source_information = []

        for index, result in enumerate(batch):

            title = str(
                result.get("title", "") or ""
            )

            url = str(
                result.get("url", "") or ""
            )

            content = self.get_best_article_content(result)

            content = content[:2500]

            source_information.append(
                f"""
SOURCE INDEX: {index}

TITLE:
{title}

URL:
{url}

CONTENT:
{content}
"""
            )

        sources_text = "\n".join(source_information)

        prompt = f"""
You are an expert research evaluator specializing in
Generative AI, Artificial Intelligence, machine learning,
large language models, AI agents and related technologies.

The research topic is:

{self.current_topic}

Evaluate each source based on its relevance to the topic.

IMPORTANT EVALUATION RULES:

1. Give a score between 0.0 and 1.0.
2. A score of 1.0 means highly relevant and directly
   useful for understanding the research topic.
3. A score between 0.70 and 0.99 means relevant and useful.
4. A score between 0.40 and 0.69 means partially relevant.
5. A score below 0.40 means weakly relevant or unrelated.
6. Prefer actual developments, announcements, research
   findings, technical improvements and industry changes.
7. Do not give high scores merely because a source mentions
   artificial intelligence or generative AI.
8. General beginner tutorials and generic educational
   explanations should receive low scores.
9. Evaluate the actual information, not just the title.
10. Do not invent information.

Return ONLY a valid JSON array.

Required format:

[
    {{
        "index": 0,
        "score": 0.92,
        "reason": "Directly discusses a relevant AI development."
    }},
    {{
        "index": 1,
        "score": 0.45,
        "reason": "Only partially related to the research topic."
    }}
]

Do not include Markdown fences.
Do not include explanations outside the JSON.

SOURCES TO EVALUATE:

{sources_text}
"""

        return prompt

    # ==================================================
    # ROBUST GEMINI JSON PARSING
    # ==================================================

    def parse_gemini_scores(self, response_text, expected_count):

        scores = [0.0] * expected_count

        if not response_text:
            print("Gemini returned an empty response.")
            return scores

        cleaned_response = str(response_text).strip()

        # Remove Markdown code fences.
        cleaned_response = re.sub(
            r"```(?:json)?",
            "",
            cleaned_response,
            flags=re.IGNORECASE
        ).strip()

        parsed_data = None

        # Attempt 1: Parse the complete response as JSON.
        try:
            parsed_data = json.loads(cleaned_response)

        except (json.JSONDecodeError, TypeError):
            pass

        # Attempt 2: Parse as Python literal.
        if parsed_data is None:
            try:
                parsed_data = ast.literal_eval(cleaned_response)

            except (ValueError, SyntaxError):
                pass

        # Attempt 3: Extract JSON array.
        if parsed_data is None:
            try:
                match = re.search(
                    r"\[\s*\{.*?\}\s*\]",
                    cleaned_response,
                    flags=re.DOTALL
                )

                if match:
                    parsed_data = json.loads(match.group(0))

            except (json.JSONDecodeError, TypeError):
                pass

        # Attempt 4: Handle dictionary-based responses.
        if isinstance(parsed_data, dict):

            for key in ("results", "scores", "evaluations"):
                if isinstance(parsed_data.get(key), list):
                    parsed_data = parsed_data[key]
                    break

        # Handle a list of numeric scores.
        if isinstance(parsed_data, list):

            for position, item in enumerate(parsed_data):

                try:

                    if isinstance(item, (int, float, str)):

                        score = float(item)
                        index = position

                    elif isinstance(item, dict):

                        index = int(
                            item.get("index", position)
                        )

                        score = float(
                            item.get(
                                "score",
                                item.get(
                                    "relevance_score",
                                    item.get("relevance", 0)
                                )
                            )
                        )

                    else:
                        continue

                    if 0 <= index < expected_count:

                        scores[index] = max(
                            0.0,
                            min(score, 1.0)
                        )

                except (ValueError, TypeError):
                    continue

        # Report parsing failures instead of silently hiding them.
        parsed_count = sum(
            1 for score in scores if score > 0
        )

        if parsed_count == 0:

            print("\nWARNING: Gemini response could not be parsed.")
            print("Raw response sample:")
            print(cleaned_response[:1500])

        return scores

    # ==================================================
    # FINAL SOURCE SCORING
    # ==================================================

    def calculate_final_score(self, result):

        tavily_score = float(
            result.get("score", 0.0) or 0.0
        )

        keyword_score = float(
            result.get("keyword_score", 0.0) or 0.0
        )

        gemini_score = float(
            result.get("gemini_relevance_score", 0.0) or 0.0
        )

        credibility_score = (
            self.calculate_credibility_score(result)
        )

        freshness_score = (
            self.calculate_freshness_score(result)
        )

        citation_score = (
            self.calculate_citation_signal(
                self.get_best_article_content(result)
            )
        )

        content_quality = (
            self.calculate_content_quality(result)
        )

        # Main weighted scoring system.

        final_score = (
            tavily_score * 0.12
            + keyword_score * 0.12
            + gemini_score * 0.35
            + credibility_score * 0.18
            + freshness_score * 0.18
            + citation_score * 0.05
        )

        # Small adjustment based on source type.

        source_type = self.classify_source(
            result.get("url", ""),
            result.get("title", "")
        )

        source_priority = {
            "research_paper": 0.04,
            "research_preprint": 0.03,
            "official_technical_blog": 0.03,
            "official_announcement": 0.03,
            "government_report": 0.02,
            "news_article": 0.01,
            "expert_commentary": 0.01,
            "technical_blog": 0.00,
            "other": -0.02
        }

        final_score += source_priority.get(
            source_type,
            0.0
        )

        # Reward meaningful recent developments.

        development_signal = (
            self.calculate_development_signal(
                result.get("title", ""),
                self.get_best_article_content(result)
            )
        )

        publication_date = (
            self.extract_publication_date(result)
        )

        if publication_date:

            age_days = (
                datetime.now(timezone.utc)
                - publication_date
            ).total_seconds() / 86400

            if 0 <= age_days <= 30:

                final_score += (
                    development_signal * 0.05
                )

        # Store individual scores for transparency.

        result["keyword_score"] = keyword_score
        result["gemini_relevance_score"] = gemini_score
        result["credibility_score"] = credibility_score
        result["freshness_score"] = freshness_score
        result["citation_score"] = citation_score
        result["content_quality_score"] = content_quality
        result["development_signal"] = development_signal
        result["source_type"] = source_type

        result["final_score"] = round(
            max(0.0, min(final_score, 1.0)),
            4
        )

        return result["final_score"]

    # ==================================================
    # SOURCE DIVERSITY
    # ==================================================

    def apply_source_diversity(self, results):

        if not results:
            return []

        selected_results = []
        domain_counts = {}

        # Limit repeated sources from the same domain.

        maximum_per_domain = 2

        for result in results:

            url = str(
                result.get("url", "") or ""
            )

            domain = self.get_domain(url)

            if not domain:
                continue

            current_count = domain_counts.get(
                domain,
                0
            )

            if current_count >= maximum_per_domain:
                continue

            selected_results.append(result)

            domain_counts[domain] = current_count + 1

            if len(selected_results) >= self.maximum_results:
                break

        # If diversity filtering leaves too few results,
        # fill remaining positions with the best unused sources.

        if len(selected_results) < self.maximum_results:

            selected_urls = {
                self.normalize_url(
                    result.get("url", "")
                )
                for result in selected_results
            }

            for result in results:

                normalized_url = self.normalize_url(
                    result.get("url", "")
                )

                if normalized_url in selected_urls:
                    continue

                selected_results.append(result)

                selected_urls.add(normalized_url)

                if len(selected_results) >= self.maximum_results:
                    break

        return selected_results

    # ==================================================
    # RESULT ENRICHMENT
    # ==================================================

    def enrich_result(self, result):

        enriched = dict(result)

        title = str(
            enriched.get("title", "") or ""
        )

        url = str(
            enriched.get("url", "") or ""
        )

                # Preserve content already cleaned during STEP 4.
        content = str(
            enriched.get("content", "") or ""
        ).strip()

        # Use the best available content only as a fallback.
        if not content:
            content = self.get_best_article_content(
                enriched
            )

        # Ensure the final content is cleaned.
        content = self.clean_article_content(
            content
        )

        enriched["title"] = title.strip()
        enriched["url"] = url.strip()

        enriched["content"] = content

        enriched["domain"] = self.get_domain(url)

        enriched["source_type"] = self.classify_source(
            url,
            title
        )

        enriched["publication_date"] = (
            self.extract_publication_date(enriched)
        )

        enriched["freshness_score"] = (
            self.calculate_freshness_score(enriched)
        )

        enriched["credibility_score"] = (
            self.calculate_credibility_score(enriched)
        )

        enriched["content_quality_score"] = (
            self.calculate_content_quality(enriched)
        )

        enriched["citation_score"] = (
            self.calculate_citation_signal(content)
        )

        enriched["development_signal"] = (
            self.calculate_development_signal(
                title,
                content
            )
        )

        return enriched

    # ==================================================
    # PREPARE FINAL RESULTS
    # ==================================================

    def prepare_final_results(self, results):

        if not results:
            return []

        prepared_results = []

        for result in results:

            try:

                enriched = self.enrich_result(result)

                self.calculate_final_score(enriched)

                prepared_results.append(enriched)

            except Exception as error:

                print(
                    f"Could not prepare source "
                    f"{result.get('title', 'Unknown')}: {error}"
                )

        prepared_results.sort(
            key=lambda item: item.get(
                "final_score",
                0.0
            ),
            reverse=True
        )

        return prepared_results
            # ==================================================
    # TAVILY SEARCH
    # ==================================================

    def search_tavily(self, query, recent_topic=False):

        search_parameters = {
            "query": query,
            "search_depth": "advanced",
            "max_results": 10,
            "include_answer": False,
            "include_raw_content": True
        }

        if recent_topic:
            search_parameters["time_range"] = "month"

        try:

            response = self.tavily.search(
                **search_parameters
            )

            results = response.get("results", [])

            print(f"Results found: {len(results)}")

            return results

        except Exception as error:

            print(f"Tavily search failed: {error}")

            return []

    # ==================================================
    # COLLECT SEARCH RESULTS
    # ==================================================

    def collect_search_results(self, topic, recent_topic=False):

        search_queries = self.build_search_queries(
            topic
        )

        all_results = []

        for index, query in enumerate(search_queries):

            print(
                f"\nSearch {index + 1}/{len(search_queries)}: "
                f"{query}"
            )

            results = self.search_tavily(
                query,
                recent_topic=recent_topic
            )

            all_results.extend(results)

            # Avoid sending requests too quickly.

            if index < len(search_queries) - 1:
                time.sleep(1)

        print(
            f"\nInitial search results: {len(all_results)}"
        )

        return all_results

    # ==================================================
    # INITIAL RESULT FILTERING
    # ==================================================

    def initial_filter_results(self, results):

        filtered_results = []
        rejected_count = 0

        for result in results:

            try:

                if self.is_low_quality_source(result):

                    rejected_count += 1

                    print(
                        "Rejected during initial filtering: "
                        f"{result.get('title', 'Unknown')}"
                    )

                    continue

                filtered_results.append(result)

            except Exception as error:

                rejected_count += 1

                print(
                    f"Filtering error: {error}"
                )

        print(
            f"\nRejected during initial filtering: "
            f"{rejected_count}"
        )

        print(
            f"Results after initial filtering: "
            f"{len(filtered_results)}"
        )

        return filtered_results

    # ==================================================
    # CATEGORY FILTERING AND DEDUPLICATION
    # ==================================================

    def category_filter_results(self, results):

        filtered_results = []
        rejected_count = 0

        for result in results:

            url = str(
                result.get("url", "") or ""
            )

            title = str(
                result.get("title", "") or ""
            )

            if self.is_category_page(url, title):

                rejected_count += 1

                print(
                    "Rejected during category filtering: "
                    f"{title}"
                )

                continue

            filtered_results.append(result)

        print(
            f"\nRejected during category filtering: "
            f"{rejected_count}"
        )

        filtered_results = self.remove_duplicate_results(
            filtered_results
        )

        print(
            f"Results after category filtering "
            f"and deduplication: {len(filtered_results)}"
        )

        return filtered_results

    # ==================================================
    # CONTENT CLEANING
    # ==================================================

    def clean_results(self, results):

        cleaned_results = []

        for result in results:

            try:

                cleaned_result = dict(result)

                content = self.get_best_article_content(
                    cleaned_result
                )

                cleaned_content = self.clean_article_content(
                    content
                )

                if len(cleaned_content.strip()) < self.minimum_content_length:
                    continue

                cleaned_result["content"] = cleaned_content

                cleaned_results.append(cleaned_result)

            except Exception as error:

                print(
                    f"Could not clean result: {error}"
                )

        print(
            f"\nResults after cleaning: "
            f"{len(cleaned_results)}"
        )

        return cleaned_results

    # ==================================================
    # COMPLETE RESEARCH PIPELINE
    # ==================================================

    def research(self, topic):

        self.current_topic = topic

        print(
            f"\nResearch Agent is searching for: {topic}"
        )

        # Determine whether the topic requires recent information.

        recent_topic = self.is_recent_research_topic(topic)

        print(
            f"Recent-topic filtering: {recent_topic}"
        )

        # STEP 1: Collect Tavily search results.

        all_results = self.collect_search_results(
            topic,
            recent_topic=recent_topic
        )

        if not all_results:

            print("\nNo search results were found.")

            return []

        # STEP 2: Initial filtering.

        filtered_results = self.initial_filter_results(
            all_results
        )

        if not filtered_results:

            print("\nNo results passed initial filtering.")

            return []

        # STEP 3: Category filtering and deduplication.

        filtered_results = self.category_filter_results(
            filtered_results
        )

        if not filtered_results:

            print("\nNo results passed category filtering.")

            return []

        # STEP 4: Clean article content.

        cleaned_results = self.clean_results(
            filtered_results
        )

        if not cleaned_results:

            print("\nNo usable article content was found.")

            return []

        # STEP 5: Gemini relevance evaluation.

        evaluated_results = self.evaluate_relevance_with_gemini(
            cleaned_results
        )

        # STEP 6: Apply minimum Gemini relevance threshold.

        relevant_results = [
            result
            for result in evaluated_results
            if result.get(
                "gemini_relevance_score",
                0.0
            ) >= self.minimum_relevance
        ]

        print(
            f"\nResults passing Gemini relevance "
            f"(>= {self.minimum_relevance}): "
            f"{len(relevant_results)}"
        )

        if not relevant_results:

            print(
                "\nNo results passed the Gemini relevance threshold."
            )

            return []

        # STEP 7: Calculate final scores and enrich results.

        prepared_results = self.prepare_final_results(
            relevant_results
        )

        # STEP 8: Sort by final score.

        prepared_results.sort(
            key=lambda result: result.get(
                "final_score",
                0.0
            ),
            reverse=True
        )

        # STEP 9: Apply source diversity and select top results.

        final_results = self.apply_source_diversity(
            prepared_results
        )

        print(
            f"\nFinal research results: "
            f"{len(final_results)}"
        )

        return final_results

        # ==================================================
    # DISPLAY RESULTS
    # ==================================================

    def display_results(self, results):

        print("\n========== RESEARCH REPORT ==========")

        for index, result in enumerate(results, start=1):

            print(f"\nResult {index}")
            print("Title:", result.get("title", "N/A"))
            print("URL:", result.get("url", "N/A"))

            print("\nContent:")
            print(result.get("content", "")[:1000])

        print("\n========== RESEARCH COMPLETED ==========")
    # ==================================================
    # RUN RESEARCH
    # ==================================================

    def run_research(self, topic):

        results = self.research(topic)

        self.display_results(results)

        return results


# ==================================================
# STANDALONE EXECUTION
# ==================================================

if __name__ == "__main__":

    agent = ResearchAgent()

    research_topic = input(
        "\nEnter your research topic: "
    ).strip()

    if research_topic:

        results = agent.run_research(
            research_topic
        )

        if results:

            print(
                f"\nSuccessfully collected "
                f"{len(results)} high-quality sources."
            )

        else:

            print(
                "\nResearch completed, but no sources "
                "passed all filtering stages."
            )

    else:

        print("\nPlease enter a valid research topic.")
