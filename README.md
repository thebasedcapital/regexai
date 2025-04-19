# regexai

# Regex Editor with AI Assistant

This is a simple desktop application built with Python and Tkinter that provides a basic text editor with features for finding and replacing text using regular expressions (regex).

It also includes an integrated AI assistant sidebar (powered by OpenRouter) that can help generate regex patterns or answer questions based on natural language input.

## Features

*   **Text Editor:** Load, edit, and save plain text files.
*   **Regex Find:** Find text matching a Python-compatible regex pattern.
*   **Regex Replace:** Replace the currently highlighted match or all matches of a pattern.
*   **AI Assistant (OpenRouter):** 
    *   Ask for help generating regex patterns in natural language.
    *   Requires an API key from [OpenRouter](https://openrouter.ai/).
*   **Toggleable AI Sidebar:** Show or hide the AI assistant panel via the "View" menu.

## Requirements

*   Python 3.x
*   Tkinter (usually included with Python)
*   `openai` library (`pip install openai`)
*   (Optional) `pyinstaller` for building (`pip install pyinstaller`)

## Running from Source

1.  Ensure you have Python 3 installed.
2.  Install the required library: `pip install openai`
3.  Run the script from your terminal: `python regex_editor.py`
4.  (Optional) Enter your OpenRouter API key in the sidebar to use the AI features.

## Building the Application (macOS)

1.  Install `pyinstaller`: `pip install pyinstaller`
2.  Navigate to the project directory in your terminal.
3.  Run the build command: `pyinstaller --windowed --name "Regex Editor" regex_editor.py`
4.  The application bundle (`Regex Editor.app`) will be created in the `dist/` directory.

## Creating a Disk Image (.dmg - macOS)

After building the `.app` file:

1.  Run the command: `hdiutil create "Regex Editor.dmg" -volname "Regex Editor" -fs HFS+ -srcfolder dist/"Regex Editor.app"`
2.  This will create `Regex Editor.dmg` in the project directory.

## Contributing

(Add contribution guidelines if applicable)

## License

(Add license information if applicable - e.g., MIT License) 
