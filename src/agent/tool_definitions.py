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
            "description": "Fetch additional GitHub projects when existing project data is insufficient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "GitHub repository search query. "
                            "Use GitHub search syntax when appropriate, such as "
                            "'topic:robotics AI agent' when the user specifies a GitHub topic."
                            "Combine it with other relevant keywords when needed."
                        )
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of repositories to fetch. Maximum is 20."
                    }
                },
                "required": ["query"]
            }
        }
    }
]