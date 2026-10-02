TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_rag",
            "description": "Search project knowledge using semantic and hybrid retrieval.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_details",
            "description": "Get detailed information about a specific GitHub project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "GitHub project name."
                    }
                },
                "required": ["project_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_github_projects",
            "description": (
                "Fetch additional GitHub projects when existing project data "
                "is insufficient. Use this tool when the user asks for projects "
                "that may not exist in the current database, especially recent "
                "or newly updated projects."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "GitHub repository search query. "
                            "Use GitHub search syntax when appropriate, such as "
                            "'topic:robotics AI agent' when the user specifies "
                            "a GitHub topic. Combine it with other relevant "
                            "keywords when needed."
                        )
                    },
                    "sort": {
                        "type": "string",
                        "enum": [
                            "stars",
                            "forks",
                            "help-wanted-issues",
                            "updated"
                        ],
                        "description": (
                            "Sort repositories by the selected field. "
                            "Use 'updated' when the user asks for recent or "
                            "recently updated projects."
                        )
                    },
                    "order": {
                        "type": "string",
                        "enum": [
                            "asc",
                            "desc"
                        ],
                        "description": (
                            "Sort order. Use 'desc' for most recent, most "
                            "popular, or highest-ranked results."
                        )
                    },
                    "max_results": {
                        "type": "integer",
                        "description": (
                            "Maximum number of repositories to fetch. "
                            "Maximum is 20."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    }
]