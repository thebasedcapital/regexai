# Regex Editor with AI Assistant

This is a desktop application built with Python and Tkinter that provides a text editor with enhanced features for finding and replacing text using regular expressions (regex).

It includes an integrated AI assistant sidebar (powered by OpenRouter) that can help generate regex patterns or answer questions based on natural language input, and a history log to track replacements.

## Features

*   **Text Editor:** Load, edit, and save plain text files (UTF-8 encoding).
*   **Regex Find & Replace:**
    *   Find text matching a Python-compatible regex pattern (`re` module).
    *   Supports Ignore Case, Multiline, and Dotall flags.
    *   Find the next match or highlight all matches.
    *   Replace the currently highlighted match or all matches.
*   **AI Assistant (OpenRouter):**
    *   Ask for help generating regex patterns or explaining regex concepts in natural language.
    *   Requires an API key from [OpenRouter](https://openrouter.ai/). Your key is saved locally for convenience.
    *   Uses the `google/gemini-flash-1.5` model by default.
*   **History Log:** Displays a log of replacement actions performed.
*   **Configurable UI:**
    *   Toggleable AI Sidebar (View Menu).
    *   Adjustable default font size (set in the script).
*   **Keyboard Shortcuts:**
    *   `Cmd+O`: Open File
    *   `Cmd+S`: Save File
    *   `Cmd+Shift+S`: Save As...
    *   `Enter` (in Pattern field): Find Next

## Requirements

*   Python 3.x
*   Tkinter (usually included with Python standard library)
*   `openai` library (`pip install openai`) for the AI assistant.

## Running from Source

1.  Ensure you have Python 3 installed.
2.  Install the required library:
    ```bash
    pip install openai
    ```
3.  Run the script from your terminal:
    ```bash
    python regex_editor.py
    ```
4.  (Optional) To use the AI Assistant:
    *   Toggle the "AI Pane" button or use the "View" -> "Show AI Sidebar" menu item.
    *   Enter your OpenRouter API key in the "OpenRouter API Key" field in the sidebar. See the section below on how to get one. The key will be stored locally in `~/.config/regex_editor/config.json`.
    *   Type your request into the "Ask the AI Assistant" box and click "Ask AI".

### Getting an OpenRouter API Key

The AI Assistant requires an API key from OpenRouter.ai.

1.  Go to [https://openrouter.ai/](https://openrouter.ai/).
2.  Sign up for a free account or log in if you already have one.
3.  Click on your account icon/name in the top right corner and select "Keys".
4.  Click the "+ Create Key" button.
5.  Give your key a name (e.g., "RegexEditor") and click "Create".
6.  **Important:** Copy the generated API key immediately. You won't be able to see it again after closing the dialog.
7.  Paste this key into the "OpenRouter API Key" field in the Regex Editor's AI sidebar.

## Building the Application (Example for macOS)

You can use tools like `pyinstaller` to create a standalone application bundle.

1.  Install `pyinstaller`:
    ```bash
    pip install pyinstaller
    ```
2.  Navigate to the project directory in your terminal.
3.  Run the build command (adjust options as needed):
    ```bash
    pyinstaller --windowed --name "Regex Editor" --add-data "path/to/your/icon.icns:." regex_editor.py
    ```
    *   Replace `path/to/your/icon.icns` if you have an application icon.
    *   The `--windowed` flag prevents a terminal window from appearing.
4.  The application bundle (`Regex Editor.app` on macOS) will be created in the `dist/` directory.

## Creating a Disk Image (.dmg - macOS Example)

After building the `.app` file with `pyinstaller`:

1.  Create the DMG file:
    ```bash
    hdiutil create "Regex Editor.dmg" -volname "Regex Editor" -fs HFS+ -srcfolder dist/"Regex Editor.app"
    ```
2.  This will create `Regex Editor.dmg` in the project directory, ready for distribution.

## Downloads

*(Optional: Add links here if you host pre-built binaries)*

*   **macOS (.dmg):** [Link to your DMG file]
*   **Windows (.exe):** [Link to your EXE file]

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs or feature suggestions.

## License

(MIT License) 