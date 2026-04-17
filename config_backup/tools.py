generate_cad_prototype_tool = {
    "name": "generate_cad_prototype",
    "description": "Generates a 3D wireframe prototype based on a user's description. Use this when the user asks to 'visualize', 'prototype', 'create a wireframe', or 'design' something in 3D.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {
                "type": "STRING",
                "description": "The user's description of the object to prototype."
            }
        },
        "required": ["prompt"]
    }
}

write_file_tool = {
    "name": "write_file",
    "description": "Writes content to a file at the specified path. Overwrites if exists.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "STRING",
                "description": "The path of the file to write to."
            },
            "content": {
                "type": "STRING",
                "description": "The content to write to the file."
            }
        },
        "required": ["path", "content"]
    }
}

read_directory_tool = {
    "name": "read_directory",
    "description": "Lists the contents of a directory.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "STRING",
                "description": "The path of the directory to list."
            }
        },
        "required": ["path"]
    }
}

read_file_tool = {
    "name": "read_file",
    "description": "Reads the content of a file.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "STRING",
                "description": "The path of the file to read."
            }
        },
        "required": ["path"]
    }
}

spotify_control_tool = {
    "name": "spotify_control",
    "description": "Controls Spotify playback: play, pause, next track, previous track, search and play a query, or open Spotify.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "Action to perform: 'play', 'pause', 'toggle', 'next', 'previous', 'open', 'search', 'play_query'."
            },
            "query": {
                "type": "STRING",
                "description": "Search query to play in Spotify (used with action 'search' or 'play_query')."
            }
        },
        "required": ["action"]
    }
}

screen_live_tool = {
    "name": "screen_live",
    "description": "Controls live screen streaming or captures a single frame. Use action='start' to begin continuous streaming at the specified interval (default 200ms), action='stop' to stop, or action='capture' for a one-shot frame.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "'capture' for one-shot, 'start' to begin streaming, 'stop' to end streaming."
            },
            "interval_ms": {
                "type": "INTEGER",
                "description": "Streaming interval in milliseconds (default 200, min 100). Used with action='start'."
            }
        }
    }
}

read_system_clipboard_tool = {
    "name": "read_system_clipboard",
    "description": "Reads the current system clipboard text content.",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    }
}

set_volume_tool = {
    "name": "set_volume",
    "description": "Sets the PC master volume to a specific percentage (0-100).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "percent": {
                "type": "INTEGER",
                "description": "Volume level from 0 (mute) to 100 (max)."
            }
        },
        "required": ["percent"]
    }
}

send_email_tool = {
    "name": "send_email",
    "description": "Sends an email via Gmail (archerbot666@gmail.com). Supports to, subject, body, and file attachments.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "to": {
                "type": "STRING",
                "description": "Recipient email address(es), comma or semicolon separated."
            },
            "subject": {
                "type": "STRING",
                "description": "Email subject line."
            },
            "body": {
                "type": "STRING",
                "description": "Email body text (plain text)."
            },
            "attachments": {
                "type": "STRING",
                "description": "Optional: comma-separated list of file paths to attach."
            }
        },
        "required": ["to", "subject", "body"]
    }
}

read_document_tool = {
    "name": "read_document",
    "description": "Reads and extracts content from any document file: Excel (.xlsx/.xls), Word (.docx), PDF (.pdf), CSV (.csv). Automatically detects file type. Returns structured content including sheet/table data for expert analysis.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {
                "type": "STRING", "description": "Full path to the document file."}
        },
        "required": ["path"]
    }
}

create_excel_tool = {
    "name": "create_excel",
    "description": "Creates a new Excel (.xlsx) file with one or more sheets. Use this when the user asks to create a spreadsheet, Excel file, or workbook. Specify sheet name(s) and optionally provide rows of data as lists.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Full path where the Excel file will be saved (e.g., 'C:/Users/raiot/Documents/report.xlsx')"},
            "sheets": {
                "type": "OBJECT",
                "description": "Object where keys are sheet names and values are arrays of row arrays. Example: {'Sheet1': [['Header1', 'Header2'], ['data1', 'data2']]}"
            }
        },
        "required": ["path", "sheets"]
    }
}

create_word_tool = {
    "name": "create_word",
    "description": "Creates a new Word (.docx) document. Use this when the user asks to create a Word document, DOCX file, or write a document with formatted text, headings, and paragraphs.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Full path where the Word file will be saved (e.g., 'C:/Users/raiot/Documents/report.docx')"},
            "title": {"type": "STRING", "description": "Document title (optional, becomes a Heading 1 style paragraph)"},
            "paragraphs": {"type": "ARRAY", "description": "Array of text strings, each becomes a paragraph. Use empty string for blank line. Use lines starting with '# ' for headings, '## ' for subheadings."}
        },
        "required": ["path", "paragraphs"]
    }
}

create_powerpoint_tool = {
    "name": "create_powerpoint",
    "description": "Creates a new PowerPoint (.pptx) presentation. Use this when the user asks to create a presentation, slideshow, or PowerPoint file. Each element in the slides array is a slide descriptor.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Full path where the PowerPoint file will be saved (e.g., 'C:/Users/raiot/Documents/presentation.pptx')"},
            "title": {"type": "STRING", "description": "Presentation title (first slide will be a title slide)"},
            "slides": {"type": "ARRAY", "description": "Array of slide descriptors. Each descriptor can be: a string (text-only slide), an object with 'title' and 'bullets' keys (title + bullet points), or an object with 'title' and 'content' keys (content paragraph)."}
        },
        "required": ["path", "slides"]
    }
}

analyze_document_tool = {
    "name": "analyze_document",
    "description": "Reads and performs deep analysis on Excel (.xlsx/.xls), Word (.docx), or PowerPoint (.pptx) files. Returns structure, content summary, statistics, and key insights. Use this when the user asks to 'analyze', 'review', 'summarize', or 'understand' a document.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Full path to the document file to analyze."}
        },
        "required": ["path"]
    }
}

edit_document_tool = {
    "name": "edit_document",
    "description": "Edits an existing Excel, Word, or PowerPoint file. Supports appending rows/sheets to Excel, adding paragraphs/tables to Word, and adding slides to PowerPoint. Use this when the user wants to modify or add content to an existing document.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Full path to the existing document to edit."},
            "action": {"type": "STRING", "description": "Edit action: 'add_rows' (Excel: append rows to a sheet), 'add_sheet' (Excel: create new sheet), 'add_paragraphs' (Word: append paragraphs), 'add_slide' (PowerPoint: append slide)"},
            "data": {"type": "STRING", "description": "Data for the edit action (JSON string for Excel rows, text content for Word/PowerPoint)."},
            "sheet_name": {"type": "STRING", "description": "Sheet name for Excel operations (required for 'add_rows' if target sheet exists)."}
        },
        "required": ["path", "action", "data"]
    }
}

shutdown_pc_tool = {
    "name": "shutdown_pc",
    "description": "Shuts down the PC after a countdown (default 30 seconds). Use cancel=true to abort an active countdown.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "delay_seconds": {
                "type": "INTEGER",
                "description": "Countdown in seconds before shutdown (default 30)."
            },
            "cancel": {
                "type": "BOOLEAN",
                "description": "Set true to cancel an active shutdown countdown."
            }
        }
    }
}

read_inbox_tool = {
    "name": "read_inbox",
    "description": "Reads recent emails from the Gmail inbox (archerbot666@gmail.com). Shows sender, subject, date, and preview. Use unread_only=true to see only new emails.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "limit": {
                "type": "INTEGER",
                "description": "Number of emails to retrieve (default 10, max 50)."
            },
            "unread_only": {
                "type": "BOOLEAN",
                "description": "If true, only fetch unread emails."
            }
        }
    }
}

search_inbox_tool = {
    "name": "search_inbox",
    "description": "Search emails in the Gmail inbox by subject, sender, or keyword.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Search term to match against subject and sender."
            },
            "limit": {
                "type": "INTEGER",
                "description": "Max results to return (default 10)."
            }
        },
        "required": ["query"]
    }
}

get_system_info_tool = {
    "name": "get_system_info",
    "description": "Returns current CPU usage, RAM usage (used/total), and disk usage for the PC.",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    }
}

remind_me_tool = {
    "name": "remind_me",
    "description": "Sets a reminder that fires after the specified number of seconds. ADA will remember the message and can remind you verbally.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "seconds": {
                "type": "INTEGER",
                "description": "Seconds to wait before the reminder fires (e.g. 300 for 5 minutes)."
            },
            "message": {
                "type": "STRING",
                "description": "What to be reminded about."
            }
        },
        "required": ["seconds", "message"]
    }
}

screen_action_tool = {
    "name": "screen_action",
    "description": "Performs actions on the screen: reads visible text (OCR), clicks at coordinates, finds and clicks text, or scrolls. Routes through VisualActionResolver for fuzzy matching, memory, and compound actions. Use this when the user wants ADA to interact with what's on the screen — clicking buttons, reading content, scrolling, or navigating UI elements.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "enum": ["read", "click", "find_and_click", "scroll", "scroll_up", "scroll_down", "scroll_left", "scroll_right"],
                "description": "Action to perform: 'read' captures screen and extracts text, 'click' clicks at x,y coordinates, 'find_and_click' locates text on screen via VisualActionResolver and clicks it, 'scroll' scrolls the viewport, 'scroll_up/down/left/right' scroll in a direction."
            },
            "x": {
                "type": "INTEGER",
                "description": "X coordinate for click action."
            },
            "y": {
                "type": "INTEGER",
                "description": "Y coordinate for click action."
            },
            "text": {
                "type": "STRING",
                "description": "Text to search for on screen (for find_and_click action). Case-insensitive. Uses fuzzy matching via VisualActionResolver."
            },
            "button": {
                "type": "STRING",
                "description": "Mouse button to click: 'left', 'right', or 'middle' (default: left)."
            },
            "amount": {
                "type": "INTEGER",
                "description": "Scroll amount in units (default: 450). Positive = up/right, negative = down/left."
            }
        },
        "required": ["action"]
    }
}

read_screen_tool = {
    "name": "read_screen",
    "description": "Captures the screen and extracts visible text using OCR. Fast (1-3 seconds). Returns the text found on screen and a summary of what's visible. Use when the user asks what is on the screen or to read visible content.",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    }
}

set_verbosity_tool = {
    "name": "set_verbosity",
    "description": "Sets how verbose ADA's responses should be. Use 'brief' for short answers, 'normal' for standard responses, or 'detailed' for comprehensive explanations. This affects only the level of detail in ADA's verbal responses.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "level": {
                "type": "STRING",
                "description": "Verbosity level: 'brief' (short answers), 'normal' (standard responses), or 'detailed' (comprehensive explanations).",
                "enum": ["brief", "normal", "detailed"]
            }
        },
        "required": ["level"]
    }
}

observe_system_state_tool = {
    "name": "observe_system_state",
    "description": "Returns the current active window, open windows, running processes, and general system state. Use this to know exactly what's on screen, what programs are running, and the current state of the PC. Fast and accurate — no screenshots needed for window queries.",
    "parameters": {
        "type": "OBJECT",
        "properties": {}
    }
}

focus_window_tool = {
    "name": "focus_window",
    "description": "Brings a window to the foreground by title, process name, or PID. Use this when asked to switch to, focus, or bring forward a window. Returns the result of the operation.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {
                "type": "STRING",
                "description": "Window title (or part of it) to match."
            },
            "process": {
                "type": "STRING",
                "description": "Process name to match (e.g., 'msedge', 'chrome', 'explorer')."
            },
            "pid": {
                "type": "INTEGER",
                "description": "Process ID of the window to focus."
            }
        }
    }
}

close_window_tool = {
    "name": "close_window",
    "description": "Closes a window by title, process name, or PID. Use this when asked to close a window or program.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {
                "type": "STRING",
                "description": "Window title (or part of it) to match."
            },
            "process": {
                "type": "STRING",
                "description": "Process name to close."
            },
            "pid": {
                "type": "INTEGER",
                "description": "Process ID of the window to close."
            }
        }
    }
}

consult_agent_tool = {
    "name": "consult_agent",
    "description": "Sends a message to the agent to request advice or help with a task. The agent will respond in a shared file. Use this when you need guidance or want to delegate something.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "message": {
                "type": "STRING",
                "description": "The message to send to the agent."
            }
        },
        "required": ["message"]
    }
}

run_command_tool = {
    "name": "run_command",
    "description": "Executes a shell command (CMD or PowerShell) and returns the output. Use shell='powershell' for PowerShell commands, shell='cmd' for CMD. Perfect for system tasks, network checks, process management, and running any CLI tool.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "command": {
                "type": "STRING",
                "description": "The command to execute."
            },
            "shell": {
                "type": "STRING",
                "description": "Shell to use: 'cmd' (default) or 'powershell'.",
                "enum": ["cmd", "powershell"]
            },
            "cwd": {
                "type": "STRING",
                "description": "Optional working directory for the command."
            },
            "timeout": {
                "type": "INTEGER",
                "description": "Timeout in seconds (default 30, max 120)."
            }
        },
        "required": ["command"]
    }
}

run_python_tool = {
    "name": "run_python",
    "description": "Executes Python code and returns the output. Use this to run Python scripts, calculations, or any Python task. The code runs in a temporary subprocess.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "code": {
                "type": "STRING",
                "description": "The Python code to execute."
            },
            "timeout": {
                "type": "INTEGER",
                "description": "Timeout in seconds (default 30, max 120)."
            }
        },
        "required": ["code"]
    }
}

tools_list = [{"function_declarations": [
    generate_cad_prototype_tool,
    write_file_tool,
    read_directory_tool,
    read_file_tool,
    spotify_control_tool,
    screen_live_tool,
    read_system_clipboard_tool,
    set_volume_tool,
    send_email_tool,
    read_document_tool,
    shutdown_pc_tool,
    read_inbox_tool,
    search_inbox_tool,
    get_system_info_tool,
    remind_me_tool,
    screen_action_tool,
    set_verbosity_tool,
    consult_agent_tool,
    observe_system_state_tool,
    focus_window_tool,
    close_window_tool,
    read_screen_tool,
    run_command_tool,
    run_python_tool,
    create_excel_tool,
    create_word_tool,
    create_powerpoint_tool,
    analyze_document_tool,
    edit_document_tool,
]}]
