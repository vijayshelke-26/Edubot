"""
Programming skill taxonomy with prerequisite relationships.
Used for ZPD-based quiz topic selection.
"""

SKILL_TREE = {
    # Basics (no prerequisites)
    "variables": {"name": "Variables", "prerequisites": [], "category": "Basics"},
    "data_types": {"name": "Data Types", "prerequisites": ["variables"], "category": "Basics"},
    "operators": {"name": "Operators", "prerequisites": ["variables"], "category": "Basics"},
    "strings": {"name": "Strings", "prerequisites": ["variables"], "category": "Basics"},
    "if_else": {"name": "If-Else Statements", "prerequisites": ["variables", "operators"], "category": "Basics"},
    "input_output": {"name": "Input & Output", "prerequisites": ["variables"], "category": "Basics"},

    # Loops
    "for_loop": {"name": "For Loops", "prerequisites": ["variables", "if_else"], "category": "Loops"},
    "while_loop": {"name": "While Loops", "prerequisites": ["variables", "if_else"], "category": "Loops"},
    "nested_loops": {"name": "Nested Loops", "prerequisites": ["for_loop", "while_loop"], "category": "Loops"},

    # Functions
    "functions": {"name": "Functions", "prerequisites": ["variables", "if_else"], "category": "Functions"},
    "scope": {"name": "Scope & Variables", "prerequisites": ["functions"], "category": "Functions"},
    "lambda": {"name": "Lambda Functions", "prerequisites": ["functions"], "category": "Functions"},
    "recursion": {"name": "Recursion", "prerequisites": ["functions", "if_else"], "category": "Functions"},
    "decorators": {"name": "Decorators", "prerequisites": ["functions", "lambda"], "category": "Functions"},
    "generators": {"name": "Generators", "prerequisites": ["functions", "for_loop"], "category": "Functions"},

    # OOP
    "classes": {"name": "Classes & Objects", "prerequisites": ["functions"], "category": "OOP"},
    "inheritance": {"name": "Inheritance", "prerequisites": ["classes"], "category": "OOP"},
    "polymorphism": {"name": "Polymorphism", "prerequisites": ["inheritance"], "category": "OOP"},
    "encapsulation": {"name": "Encapsulation", "prerequisites": ["classes"], "category": "OOP"},
    "abstraction": {"name": "Abstraction", "prerequisites": ["classes", "inheritance"], "category": "OOP"},

    # Data Structures
    "lists": {"name": "Lists", "prerequisites": ["variables", "for_loop"], "category": "Data Structures"},
    "tuples": {"name": "Tuples", "prerequisites": ["lists"], "category": "Data Structures"},
    "dictionaries": {"name": "Dictionaries", "prerequisites": ["lists"], "category": "Data Structures"},
    "sets": {"name": "Sets", "prerequisites": ["lists"], "category": "Data Structures"},
    "stacks": {"name": "Stacks", "prerequisites": ["lists"], "category": "Data Structures"},
    "queues": {"name": "Queues", "prerequisites": ["lists"], "category": "Data Structures"},
    "linked_lists": {"name": "Linked Lists", "prerequisites": ["classes", "lists"], "category": "Data Structures"},
    "trees": {"name": "Trees", "prerequisites": ["linked_lists", "recursion"], "category": "Data Structures"},
    "graphs": {"name": "Graphs", "prerequisites": ["lists", "dictionaries"], "category": "Data Structures"},
    "hash_tables": {"name": "Hash Tables", "prerequisites": ["dictionaries"], "category": "Data Structures"},

    # Algorithms
    "searching": {"name": "Searching Algorithms", "prerequisites": ["lists", "for_loop"], "category": "Algorithms"},
    "sorting": {"name": "Sorting Algorithms", "prerequisites": ["lists", "for_loop", "nested_loops"], "category": "Algorithms"},
    "big_o": {"name": "Big O Notation", "prerequisites": ["for_loop", "functions"], "category": "Algorithms"},
    "dynamic_programming": {"name": "Dynamic Programming", "prerequisites": ["recursion", "lists"], "category": "Algorithms"},

    # Advanced
    "exceptions": {"name": "Exception Handling", "prerequisites": ["functions"], "category": "Advanced"},
    "file_handling": {"name": "File Handling", "prerequisites": ["strings", "exceptions"], "category": "Advanced"},
    "modules": {"name": "Modules & Packages", "prerequisites": ["functions"], "category": "Advanced"},
    "regex": {"name": "Regular Expressions", "prerequisites": ["strings"], "category": "Advanced"},
    "list_comprehension": {"name": "List Comprehension", "prerequisites": ["lists", "for_loop"], "category": "Advanced"},
    "testing": {"name": "Testing", "prerequisites": ["functions", "exceptions"], "category": "Advanced"},
    "git": {"name": "Version Control (Git)", "prerequisites": [], "category": "Advanced"},
    "api": {"name": "APIs & REST", "prerequisites": ["dictionaries", "functions"], "category": "Advanced"},
}

ALL_SKILLS = list(SKILL_TREE.keys())


def get_prerequisites_met(mastered_skills: set[str]) -> list[str]:
    """Return skills whose prerequisites are all met (ZPD-ready)."""
    ready = []
    for skill_id, info in SKILL_TREE.items():
        if skill_id in mastered_skills:
            continue
        prereqs = info["prerequisites"]
        if all(p in mastered_skills for p in prereqs):
            ready.append(skill_id)
    return ready


# Map common keywords to skill IDs for topic extraction from chat
TOPIC_KEYWORDS = {}
for skill_id, info in SKILL_TREE.items():
    # Add skill name words as keywords
    for word in info["name"].lower().split():
        if len(word) > 2:
            TOPIC_KEYWORDS[word] = skill_id
    # Add skill_id itself
    TOPIC_KEYWORDS[skill_id.replace("_", " ")] = skill_id

# Manual keyword overrides for better matching
_EXTRA_KEYWORDS = {
    "variable": "variables", "var": "variables",
    "string": "strings", "str": "strings", "text": "strings",
    "loop": "for_loop", "for": "for_loop", "iterate": "for_loop",
    "while": "while_loop",
    "if": "if_else", "else": "if_else", "elif": "if_else", "conditional": "if_else",
    "function": "functions", "def": "functions", "return": "functions", "parameter": "functions",
    "lambda": "lambda",
    "recursion": "recursion", "recursive": "recursion",
    "decorator": "decorators",
    "generator": "generators", "yield": "generators",
    "class": "classes", "object": "classes", "oop": "classes",
    "inherit": "inheritance", "super": "inheritance", "parent": "inheritance",
    "polymorph": "polymorphism", "overrid": "polymorphism",
    "encapsulat": "encapsulation", "private": "encapsulation",
    "abstract": "abstraction",
    "list": "lists", "array": "lists", "append": "lists",
    "tuple": "tuples",
    "dict": "dictionaries", "dictionary": "dictionaries", "key": "dictionaries",
    "set": "sets",
    "stack": "stacks", "lifo": "stacks",
    "queue": "queues", "fifo": "queues",
    "linked": "linked_lists", "node": "linked_lists",
    "tree": "trees", "binary": "trees", "bst": "trees",
    "graph": "graphs", "vertex": "graphs", "edge": "graphs",
    "hash": "hash_tables",
    "search": "searching", "binary search": "searching",
    "sort": "sorting", "bubble": "sorting", "merge": "sorting", "quick": "sorting",
    "big o": "big_o", "complexity": "big_o", "notation": "big_o",
    "dynamic programming": "dynamic_programming", "memoiz": "dynamic_programming",
    "exception": "exceptions", "try": "exceptions", "except": "exceptions", "error": "exceptions",
    "file": "file_handling", "open": "file_handling", "read": "file_handling", "write": "file_handling",
    "module": "modules", "import": "modules", "package": "modules", "pip": "modules",
    "regex": "regex", "regular expression": "regex", "pattern": "regex",
    "comprehension": "list_comprehension",
    "test": "testing", "pytest": "testing", "unittest": "testing",
    "git": "git", "version control": "git", "commit": "git", "branch": "git",
    "api": "api", "rest": "api", "endpoint": "api",
    "scope": "scope", "global": "scope", "local": "scope",
    "input": "input_output", "output": "input_output", "print": "input_output",
    "operator": "operators", "arithmetic": "operators",
    "data type": "data_types", "int": "data_types", "float": "data_types", "boolean": "data_types",
    "nested": "nested_loops",
}
TOPIC_KEYWORDS.update(_EXTRA_KEYWORDS)


def extract_topics(text: str) -> list[str]:
    """Extract skill topics mentioned in a chat message."""
    text_lower = text.lower()
    found = set()

    # Check multi-word keywords first
    for keyword, skill_id in sorted(TOPIC_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in text_lower:
            found.add(skill_id)

    return list(found)
