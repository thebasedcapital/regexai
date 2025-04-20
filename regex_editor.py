import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
import json # Added for config file handling
# import requests # No longer needed for API
# import json     # No longer needed for API
from openai import OpenAI, APIError, APIConnectionError, AuthenticationError, RateLimitError # Added for OpenAI library
import tkinter.font as tkFont # Import the font module

# Define config file path in user's home directory
CONFIG_DIR = os.path.expanduser("~/.config/regex_editor")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class RegexEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Regex Editor")
        self.root.state('zoomed') # Start maximized/zoomed

        self.current_file_path = None
        self.last_search_end = "1.0" # Tkinter text index (line.char)
        self.ai_sidebar_visible = False # Start with sidebar hidden
        self.history_log = [] # List to store history entries

        # Regex flag variables
        self.ignore_case_var = tk.BooleanVar()
        self.multiline_var = tk.BooleanVar(value=True) # Default MULTILINE to True as it was hardcoded
        self.dotall_var = tk.BooleanVar()

        # --- Menu Bar ---
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open", command=self.open_file, accelerator="Cmd+O")
        self.file_menu.add_command(label="Save", command=self.save_file, accelerator="Cmd+S")
        self.file_menu.add_command(label="Save As...", command=self.save_as_file, accelerator="Cmd+Shift+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        # Add View menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        self.view_menu.add_checkbutton(label="Show AI Sidebar", command=self.toggle_ai_sidebar, variable=tk.BooleanVar(value=self.ai_sidebar_visible)) # Reflect initial state

        # Bind shortcuts
        self.root.bind_all("<Command-o>", lambda event: self.open_file())
        self.root.bind_all("<Command-s>", lambda event: self.save_file())
        self.root.bind_all("<Command-Shift-s>", lambda event: self.save_as_file())
        self.root.bind_all("<Command-Shift-S>", lambda event: self.save_as_file()) # Handle case variation

        # --- Main Layout (Paned Window) ---
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        # --- Left Pane (Editor Controls + Text Area) ---
        self.editor_frame = ttk.Frame(self.paned_window, padding=0)
        self.paned_window.add(self.editor_frame) # Give editor more initial space

        # --- Regex Controls Frame (Now inside editor_frame) ---
        self.control_frame = ttk.Frame(self.editor_frame, padding="10")
        self.control_frame.pack(fill=tk.X)

        ttk.Label(self.control_frame, text="Pattern:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.pattern_entry = ttk.Entry(self.control_frame, width=40)
        self.pattern_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.pattern_entry.bind("<Return>", lambda event: self.find_next()) # Find on Enter in pattern field

        # --- Regex Flags ---
        flags_frame = ttk.Frame(self.control_frame)
        flags_frame.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Checkbutton(flags_frame, text="Ignore Case", variable=self.ignore_case_var, command=self._reset_search).pack(side=tk.LEFT)
        ttk.Checkbutton(flags_frame, text="Multiline", variable=self.multiline_var, command=self._reset_search).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Checkbutton(flags_frame, text="Dotall", variable=self.dotall_var, command=self._reset_search).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(self.control_frame, text="Replace:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.replace_entry = ttk.Entry(self.control_frame, width=40)
        self.replace_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        # --- Buttons Frame ---
        buttons_frame = ttk.Frame(self.control_frame)
        buttons_frame.grid(row=0, column=3, rowspan=2, padx=5, pady=0, sticky=(tk.N, tk.S, tk.W, tk.E)) # Span 2 rows, adjust padding

        self.find_button = ttk.Button(buttons_frame, text="Find Next", command=self.find_next)
        self.find_button.pack(side=tk.TOP, fill=tk.X, pady=(0, 2)) # Adjust padding

        self.find_all_button = ttk.Button(buttons_frame, text="Find All", command=self.find_all)
        self.find_all_button.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        self.replace_button = ttk.Button(buttons_frame, text="Replace", command=self.replace_current)
        self.replace_button.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        self.replace_all_button = ttk.Button(buttons_frame, text="Replace All", command=self.replace_all)
        self.replace_all_button.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        self.toggle_ai_button = ttk.Button(buttons_frame, text="AI Pane", command=self.toggle_ai_sidebar)
        self.toggle_ai_button.pack(side=tk.TOP, fill=tk.X)

        self.control_frame.columnconfigure(1, weight=1) # Make entry fields expandable

        # --- Text Area (Now inside editor_frame) ---
        self.text_area = scrolledtext.ScrolledText(self.editor_frame, wrap=tk.WORD, undo=True)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=(0, 10))
        self.text_area.tag_configure("highlight", background="yellow")
        self.text_area.bind("<KeyRelease>", self._reset_search) # Reset search if text is modified

        # --- History Log Area ---
        history_label = ttk.Label(self.editor_frame, text="History:", padding=(10, 5, 10, 0))
        history_label.pack(fill=tk.X)
        self.history_text_area = scrolledtext.ScrolledText(self.editor_frame, wrap=tk.WORD, height=5, state=tk.DISABLED) # Start disabled
        self.history_text_area.pack(expand=False, fill=tk.X, padx=10, pady=(0, 10)) # Fill horizontally, fixed height

        # --- Right Pane (AI Assistant Sidebar) ---
        self.ai_sidebar_frame = ttk.Frame(self.paned_window, padding="10", width=250) # Initial width
        self.paned_window.add(self.ai_sidebar_frame)
        # self.paned_window.sash_place(0, 450, 0) # No need to place sash initially

        self._create_ai_sidebar_widgets()
        self._load_api_key() # Load saved API key on startup

        # --- Hide AI Sidebar Initially ---
        if not self.ai_sidebar_visible:
             self.paned_window.forget(self.ai_sidebar_frame)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self._update_status("Ready") # Initial status

    def _create_ai_sidebar_widgets(self):
        """Create widgets for the AI Assistant sidebar."""
        # --- AI Controls ---
        ai_controls_label = ttk.Label(self.ai_sidebar_frame, text="AI Assistant", font=('TkDefaultFont', 12, 'bold'))
        ai_controls_label.pack(pady=(0, 10), anchor=tk.W)

        # API Key
        api_key_frame = ttk.Frame(self.ai_sidebar_frame)
        api_key_frame.pack(fill=tk.X, pady=2)
        ttk.Label(api_key_frame, text="OpenRouter API Key:").pack(side=tk.LEFT, padx=(0, 5))
        self.api_key_entry = ttk.Entry(api_key_frame, show="*") # Use show="*" to hide key
        self.api_key_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        # !! SECURITY WARNING: Storing API keys like this is convenient but not foolproof.
        # The key is stored in plain text in the config file.
        # Consider environment variables or more secure methods for sensitive production applications.

        # Natural Language Input
        ttk.Label(self.ai_sidebar_frame, text="Ask the AI Assistant:").pack(anchor=tk.W, pady=(10, 2))
        self.ai_query_input = scrolledtext.ScrolledText(self.ai_sidebar_frame, height=5, wrap=tk.WORD)
        self.ai_query_input.pack(fill=tk.X, pady=2)

        # Ask Button
        self.ask_ai_button = ttk.Button(self.ai_sidebar_frame, text="Ask AI", command=self.ask_ai_assistant)
        self.ask_ai_button.pack(pady=5)

        # AI Response Output Area
        ttk.Label(self.ai_sidebar_frame, text="AI Response:").pack(anchor=tk.W, pady=(10, 2))
        self.ai_response_output = scrolledtext.ScrolledText(self.ai_sidebar_frame, height=10, wrap=tk.WORD, state=tk.DISABLED) # Start disabled
        self.ai_response_output.pack(fill=tk.BOTH, expand=True, pady=2)

    def _reset_search(self, event=None):
        """Reset search position when text changes"""
        self.last_search_end = "1.0"
        self.text_area.tag_remove("highlight", "1.0", tk.END)

    def open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        try:
            self.text_area.delete("1.0", tk.END)
            with open(filepath, "r", encoding='utf-8') as input_file:
                text = input_file.read()
                self.text_area.insert(tk.END, text)
            self.current_file_path = filepath
            self.root.title(f"Regex Editor - {os.path.basename(filepath)}")
            self._reset_search() # Reset search on new file
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Could not open file: {e}")
            self.current_file_path = None
            self.root.title("Regex Editor")

    def save_file(self):
        if self.current_file_path:
            try:
                text = self.text_area.get("1.0", tk.END)
                # Tkinter adds a newline at the end, decide if you want to keep it
                # if text.endswith('\n'):
                #     text = text[:-1]
                with open(self.current_file_path, "w", encoding='utf-8') as output_file:
                    output_file.write(text)
                # Optional: Add status update or confirmation
            except Exception as e:
                messagebox.showerror("Error Saving File", f"Could not save file: {e}")
        else:
            self.save_as_file()

    def save_as_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=os.path.basename(self.current_file_path) if self.current_file_path else "untitled.txt"
        )
        if not filepath:
            return
        self.current_file_path = filepath
        self.root.title(f"Regex Editor - {os.path.basename(filepath)}")
        self.save_file() # Call save_file now that path is set

    def find_next(self):
        pattern_str = self.pattern_entry.get()
        if not pattern_str:
            return

        # Remove previous highlight
        self.text_area.tag_remove("highlight", "1.0", tk.END)

        try:
            # Compile regex with selected flags
            flags = self._get_regex_flags()
            regex = re.compile(pattern_str, flags)
            text_content = self.text_area.get(self.last_search_end, tk.END) # Search from last match end

            match = regex.search(text_content)

            if match:
                # Calculate start and end positions relative to the beginning of the text_area
                start_char_offset = match.start()
                end_char_offset = match.end()

                # Convert character offsets from self.last_search_end to absolute indices
                base_index = self.text_area.index(self.last_search_end)
                start_index = self.text_area.index(f"{base_index}+{start_char_offset}c")
                end_index = self.text_area.index(f"{base_index}+{end_char_offset}c")

                # Highlight the match
                self.text_area.tag_add("highlight", start_index, end_index)
                self.text_area.see(start_index) # Scroll to the match
                self.text_area.mark_set(tk.INSERT, start_index) # Move cursor to start of match
                self.last_search_end = end_index # Update for next search
            else:
                # No more matches from the current position, wrap around?
                if self.last_search_end != "1.0":
                    # Ask user or automatically wrap
                    # For now, just reset and inform
                    self._update_status("No more matches found. Search reset.")
                    self._reset_search()
                else:
                    self._update_status("Pattern not found.")

        except re.error as e:
            messagebox.showerror("Regex Error", f"Invalid regular expression: {e}")
            self._reset_search()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during find: {e}")
            self._reset_search()

    def find_all(self):
        pattern_str = self.pattern_entry.get()
        if not pattern_str:
            return

        # Remove previous highlights
        self.text_area.tag_remove("highlight", "1.0", tk.END)

        try:
            # Compile regex with selected flags
            flags = self._get_regex_flags()
            regex = re.compile(pattern_str, flags)
            text_content = self.text_area.get("1.0", tk.END)
            
            count = 0
            for match in regex.finditer(text_content):
                start_char_offset = match.start()
                end_char_offset = match.end()

                # Convert character offsets to absolute indices
                # finditer gives absolute offsets, so no need for base_index calculation like find_next
                start_index = self.text_area.index(f"1.0 + {start_char_offset}c")
                end_index = self.text_area.index(f"1.0 + {end_char_offset}c")

                # Highlight the match
                self.text_area.tag_add("highlight", start_index, end_index)
                count += 1

            if count > 0:
                self._update_status(f"Found {count} matches.")
                # Optionally scroll to the first match?
                first_match_start = self.text_area.tag_ranges("highlight")[0]
                self.text_area.see(first_match_start)
            else:
                self._update_status("Pattern not found.")
            
            self.last_search_end = "1.0" # Reset search for find_next after find_all

        except re.error as e:
            messagebox.showerror("Regex Error", f"Invalid regular expression: {e}")
            self._reset_search()
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred during find all: {e}")
             self._reset_search()

    def replace_current(self):
        pattern_str = self.pattern_entry.get()
        replace_str = self.replace_entry.get()
        if not pattern_str:
            return

        # Check if there's a highlighted selection (from find_next)
        selected_ranges = self.text_area.tag_ranges("highlight") # Use highlight tag

        if selected_ranges:
            start_index, end_index = selected_ranges
            try:
                # Get the highlighted text
                selected_text = self.text_area.get(start_index, end_index)
                # Verify it actually matches the current pattern before replacing
                # regex = re.compile(pattern_str)
                # >>> REMOVED check: Since find_next found it, we trust the highlight <<< 
                # if regex.fullmatch(selected_text): # Use fullmatch to ensure the selection *is* the pattern
                
                # Perform replacement
                self.text_area.delete(start_index, end_index)
                self.text_area.insert(start_index, replace_str)
                self._reset_search() # Reset search after replacement
                # Log the change
                log_entry = f"Replaced '{selected_text}' with '{replace_str}' at {start_index}."
                self._add_history_entry(log_entry)
                    # Maybe automatically find the next one?
                    # self.find_next()
                # else:
                #      messagebox.showwarning("Replace", "Highlighted text does not match the current pattern.")
            except re.error as e:
                 messagebox.showerror("Regex Error", f"Invalid regular expression: {e}")
            except Exception as e:
                 messagebox.showerror("Error", f"An unexpected error occurred during replace: {e}")

        else:
            # If nothing highlighted, maybe find the next one first?
            self._update_status("No match selected. Use 'Find Next' first.")
            # Or implement replace without prior find (finds and replaces the first match from cursor)

    def replace_all(self):
        pattern_str = self.pattern_entry.get()
        replace_str = self.replace_entry.get()
        if not pattern_str:
            return

        try:
            text_content = self.text_area.get("1.0", tk.END)
            # Compile regex with selected flags
            flags = self._get_regex_flags()
            regex = re.compile(pattern_str, flags)

            # Use re.sub for replacement
            new_text_content, num_replacements = regex.subn(replace_str, text_content)

            if num_replacements > 0:
                # Record current scroll position and cursor position
                scroll_pos = self.text_area.yview()
                cursor_pos = self.text_area.index(tk.INSERT)

                # Update text area content
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert("1.0", new_text_content)

                # Try to restore scroll and cursor position (might be approximate)
                self.text_area.yview_moveto(scroll_pos[0])
                try:
                    # If the cursor position is still valid
                    self.text_area.mark_set(tk.INSERT, cursor_pos)
                except tk.TclError:
                    # If old cursor position is invalid (e.g., text became shorter)
                    self.text_area.mark_set(tk.INSERT, "1.0") # Go to beginning

                self._update_status(f"Made {num_replacements} replacements.")
                self._reset_search() # Reset search state
                # Log the change
                log_entry = f"Replaced all occurrences of pattern '{pattern_str}' with '{replace_str}' ({num_replacements} replacements)."
                self._add_history_entry(log_entry)
            else:
                 self._update_status("No matches found to replace.")

        except re.error as e:
            messagebox.showerror("Regex Error", f"Invalid regular expression: {e}")
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred during replace all: {e}")

    def ask_ai_assistant(self):
        """Handle the 'Ask AI' button click."""
        api_key = self.api_key_entry.get()
        # Get query from the new input widget
        ai_query = self.ai_query_input.get("1.0", tk.END).strip()

        if not api_key:
            # Consider using a status bar or logging instead of repeated message boxes
            self._update_status("API Key Missing. Please enter your OpenRouter API Key.")
            return

        if not ai_query:
            self._update_status("Input Missing. Please enter your question for the AI assistant.")
            return

        # model_name = "google/gemini-flash-1.5" # Or let user choose?
        # No longer need this variable here
        # api_endpoint = "https://openrouter.ai/api/v1/chat/completions"
        model_name = "google/gemini-flash-1.5" # Example: Choose a suitable model!

        # Construct a more general prompt
        prompt = (
            f"Please fulfill the request by providing only the regex code snippet unless asked otherwise. Note that regex is based only on python re module syntax. "
            f"If it involves a regular expression, provide only the regex pattern unless asked otherwise.\n\n"
            f"Request: {ai_query}\n\n"
            f"Response:"
        )

        data = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500, # Increased max_tokens for potentially longer answers/code
            "temperature": 0.5, # Slightly higher temp for more varied answers
        }

        # Update UI before API call
        self.ask_ai_button.config(state=tk.DISABLED)
        self.ai_response_output.config(state=tk.NORMAL)
        self.ai_response_output.delete("1.0", tk.END)
        self.ai_response_output.insert("1.0", "Asking AI...")
        self.ai_response_output.config(state=tk.DISABLED)
        self.root.update_idletasks()

        try:
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1", # CORRECT BASE URL
                api_key=api_key, # Use the entered key
            )

            completion = client.chat.completions.create(
                extra_headers={ # Optional headers
                    # "HTTP-Referer": "YOUR_SITE_URL",
                    # "X-Title": "YOUR_SITE_NAME",
                },
                model=model_name,
                messages=data["messages"],
                max_tokens=data["max_tokens"],
                temperature=data["temperature"]
            )

            ai_response = completion.choices[0].message.content.strip()

            # Display response in the ScrolledText widget
            self.ai_response_output.config(state=tk.NORMAL)
            self.ai_response_output.delete("1.0", tk.END)
            if ai_response:
                self.ai_response_output.insert("1.0", ai_response)
            else:
                self.ai_response_output.insert("1.0", "AI returned an empty response.")
            # Leave it enabled for copying, or disable again?
            # self.ai_response_output.config(state=tk.DISABLED)

        except AuthenticationError as e:
            error_message = f"API Authentication Error: Invalid API Key or insufficient permissions. {e}"
            messagebox.showerror("AI Error", error_message)
            self._display_ai_error(error_message)
        except APIConnectionError as e:
            error_message = f"API Connection Error: Failed to connect to OpenRouter API. {e}"
            messagebox.showerror("AI Error", error_message)
            self._display_ai_error(error_message)
        except RateLimitError as e:
            error_message = f"API Rate Limit Error: Rate limit exceeded. {e}"
            messagebox.showerror("AI Error", error_message)
            self._display_ai_error(error_message)
        except APIError as e:
            error_message = f"OpenRouter API Error: {e}"
            messagebox.showerror("AI Error", error_message)
            self._display_ai_error(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred: {e}"
            messagebox.showerror("Error", error_message)
            self._display_ai_error(error_message)
        finally:
            self.ask_ai_button.config(state=tk.NORMAL)

        # --- Save API key on successful call ---
        # If the call was successful (no exception before this point), save the key
        if 'completion' in locals() and completion: # Check if completion was successful
             self._save_api_key(api_key)

    def _display_ai_error(self, error_message):
        """Helper to display errors in the AI output area."""
        try:
            self.ai_response_output.config(state=tk.NORMAL)
            self.ai_response_output.delete("1.0", tk.END)
            self.ai_response_output.insert("1.0", f"Error:\n{error_message}")
            self.ai_response_output.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error displaying AI error in text widget: {e}") # Fallback print

    def toggle_ai_sidebar(self):
        """Toggle the visibility of the AI sidebar"""
        if self.ai_sidebar_visible:
            # Hide sidebar by setting its width to 0
            self.paned_window.forget(self.ai_sidebar_frame)
            self.ai_sidebar_visible = False
        else:
            # Show sidebar and set sash position
            self.paned_window.add(self.ai_sidebar_frame)
            # Wait for window layout to update
            self.root.update_idletasks()
            # Calculate sash position for 2/3 editor, 1/3 sidebar
            try:
                total_width = self.paned_window.winfo_width()
                sash_pos = int(total_width * 2 / 3)
                if sash_pos > 0:
                    self.paned_window.sash_place(0, sash_pos, 0)
                else: # Fallback if width is 0 initially
                    self.paned_window.sash_place(0, 450, 0) # Use previous default
            except tk.TclError:
                 # If something goes wrong getting width or setting sash, use default
                 self.paned_window.sash_place(0, 450, 0)
            self.ai_sidebar_visible = True

    # --- API Key Persistence ---
    def _load_api_key(self):
        """Load API key from the config file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    api_key = config_data.get('api_key')
                    if api_key:
                        self.api_key_entry.delete(0, tk.END)
                        self.api_key_entry.insert(0, api_key)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load API key from {CONFIG_FILE}. Error: {e}") # Log warning instead of showing popup

    def _save_api_key(self, api_key):
        """Save API key to the config file."""
        try:
            # Ensure the config directory exists
            os.makedirs(CONFIG_DIR, exist_ok=True)
            config_data = {'api_key': api_key}
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
        except IOError as e:
            # Don't bother the user with a popup for save errors unless critical
            print(f"Warning: Could not save API key to {CONFIG_FILE}. Error: {e}")

    # --- Status Update Method ---
    def _update_status(self, message):
        """Update the status bar text."""
        self.status_var.set(message)
        # Optionally clear after a delay?
        # self.root.after(5000, lambda: self.status_var.set("Ready") if self.status_var.get() == message else None)

    def _get_regex_flags(self):
        """Build the regex flags based on checkbox states."""
        flags = 0
        if self.ignore_case_var.get():
            flags |= re.IGNORECASE
        if self.multiline_var.get():
            flags |= re.MULTILINE
        if self.dotall_var.get():
            flags |= re.DOTALL
        return flags

    # --- History Log Method ---
    def _add_history_entry(self, entry_text):
        """Add an entry to the history list and the history text area."""
        self.history_log.append(entry_text)
        try:
            self.history_text_area.config(state=tk.NORMAL)
            # Add entry with a newline
            self.history_text_area.insert(tk.END, entry_text + "\n")
            # Auto-scroll to the bottom
            self.history_text_area.see(tk.END)
            self.history_text_area.config(state=tk.DISABLED)
        except Exception as e:
            print(f"Error updating history widget: {e}") # Log error

if __name__ == "__main__":
    root = tk.Tk()
    # Set the default font size
    default_font = tkFont.nametofont("TkDefaultFont")
    default_font.configure(size=15)
    app = RegexEditor(root)
    root.mainloop() 