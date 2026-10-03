TOOL_DEFINITIONS = [

    {
        "type": "function",
        "function": {
            "name": "search_rag",
            "description": (
                "Search the existing project knowledge base. "
                "Use this for projects already stored in the database, "
                "including related, similar, relevant, or recommended projects. "
                "Do not use this tool when the user explicitly asks for "
                "latest, recent, or recently updated GitHub projects."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural language search query for finding "
                            "projects in the existing knowledge base."
                        )
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
            "description": (
                "Get detailed information about ONE SPECIFIC GitHub project that "
                "the user has already identified by name. "
                "Use this tool only when the user explicitly refers to a known "
                "project, such as 'Give me the details of Flowise' or "
                "'Tell me more about rosa'. "
                "Do NOT use this tool to search for projects, find related projects, "
                "find similar projects, or answer general project discovery questions. "
                "For those requests, use search_rag instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": (
                            "Name of the specific GitHub project to inspect."
                        )
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
                "Search GitHub for projects that are not necessarily in the "
                "existing project database. MUST use this tool when the user "
                "asks for latest, recent, newly updated, or currently updated "
                "GitHub projects. For latest or recent projects, use "
                "sort='updated' and order='desc'. Use max_results to match "
                "the number of projects requested by the user. Do not use "
                "this tool for ordinary related, similar, or recommended "
                "project searches when existing database data is sufficient."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "GitHub repository search query. "
                            "Use GitHub search syntax when appropriate, "
                            "such as 'topic:robotics AI agent' when the "
                            "user specifies a GitHub topic. Combine it with "
                            "other relevant keywords when needed."
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
                            "Use 'updated' when the user asks for latest, "
                            "recent, or recently updated projects. "
                            "Use 'stars' for popularity and 'forks' for "
                            "fork count."
                        )
                    },
                    "order": {
                        "type": "string",
                        "enum": [
                            "asc",
                            "desc"
                        ],
                        "description": (
                            "Sort order. Use 'desc' for latest, most recent, "
                            "most popular, or highest-ranked results."
                        )
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "description": (
                            "Maximum number of repositories to fetch. "
                            "Use 1 when the user asks for one project. "
                            "Maximum is 20."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    }

]