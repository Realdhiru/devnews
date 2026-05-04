KEYWORD_MAP = {
    "security": ["cve", "vulnerability", "exploit", "breach", "zero-day", "ransomware", "malware", "patch", "hack", "cybersecurity", "security", "threat"],
    "ai": ["ai", "machine learning", "llm", "neural", "gpt", "claude", "gemini", "artificial intelligence", "deep learning", "transformer", "diffusion"],
    "linux": ["linux", "kernel", "ubuntu", "arch", "debian", "fedora", "systemd", "gnome", "kde"],
    "engineering": ["architecture", "backend", "performance", "database", "database", "distributed systems", "scaling", "optimization", "rust", "golang", "systems programming"],
    "hackathon": ["hackathon", "contest", "competition", "prize", "devfolio", "unstop", "mlh"],
    "open_source": ["open source", "github", "repository", "contributor", "gsoc", "lfx", "outreachy", "maintainer", "foss"],
    "webdev": ["javascript", "typescript", "react", "vue", "css", "frontend", "nodejs", "nextjs", "web dev", "browser"],
    "devops": ["docker", "kubernetes", "ci/cd", "deployment", "cloud", "aws", "devops", "terraform", "ansible"],
    "events": ["conference", "meetup", "summit", "workshop", "webinar", "talk", "luma"]
}

CATEGORY_PRIORITY = ["security", "engineering", "hackathon", "open_source", "ai", "linux", "webdev", "devops", "events"]

CATEGORY_DISPLAY_MAP = {
    "security": "Security",
    "engineering": "Engineering",
    "hackathon": "Events",
    "open_source": "Open Source",
    "ai": "AI",
    "linux": "Linux",
    "webdev": "Web Dev",
    "devops": "DevOps",
    "events": "Events",
    "tech": "Tech",
    "general": "Other"
}

def generate_tags(title: str, summary: str) -> dict:
    text = f"{title} {summary}".lower()
    
    matched_keys = []
    for key, keywords in KEYWORD_MAP.items():
        if any(kw in text for kw in keywords):
            matched_keys.append(key)
            
    primary_key = "general"
    for cat in CATEGORY_PRIORITY:
        if cat in matched_keys:
            primary_key = cat
            break
            
    if primary_key == "general" and any(k in matched_keys for k in KEYWORD_MAP.keys()):
        primary_key = "tech"
        
    categories_set = set()
    categories_set.add(CATEGORY_DISPLAY_MAP.get(primary_key, "General"))
    for k in matched_keys:
        categories_set.add(CATEGORY_DISPLAY_MAP.get(k, "General"))
        
    return {
        "primary_category": CATEGORY_DISPLAY_MAP.get(primary_key, "General"),
        "categories": list(categories_set),
        "tags": matched_keys[:3]
    }
