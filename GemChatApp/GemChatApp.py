import tkinter as tk
from tkinter import filedialog, scrolledtext
from PIL import Image, ImageTk
import os
from dotenv import load_dotenv
import google.generativeai as genai

class GeminiChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GGT")

        self.context = []
        self.ctrl_pressed = False
        self.period_pressed = 0
        self.image_path = None
        self.chat_mode = tk.BooleanVar(value=True)  # Chat mode flag

        self.create_widgets()

        # Load API key from .env file
        load_dotenv()
        self.api_key = os.getenv('API_KEY')

        if not self.api_key:
            self.log_message("No API key found in .env file. Using hardcoded API key.")
            self.api_key = "Hard-Coded-Api"

        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            self.log_message("No API key available. The application may not function properly.")

        self.root.bind('<Control_L>', self.control_press)
        self.root.bind('<KeyRelease-Control_L>', self.control_release)
        self.root.bind('<period>', self.period_press)
        self.root.bind('<KeyRelease-period>', self.period_release)

    def create_widgets(self):
        self.log_text = scrolledtext.ScrolledText(self.root, width=20, height=3, state='disabled')
        self.log_text.grid(column=0, row=0, padx=1, pady=1)

        self.process_button = tk.Button(self.root, text="P(Ctrl+..)", command=self.process_input)
        self.process_button.grid(column=0, row=1, padx=1, pady=1)

        self.image_button = tk.Button(self.root, text="S", command=self.select_image)
        self.image_button.grid(column=0, row=2, padx=1, pady=1)

        self.unselect_button = tk.Button(self.root, text="Un", command=self.unselect_image)
        self.unselect_button.grid(column=0, row=3, padx=1, pady=1)

        self.image_label = tk.Label(self.root)
        self.image_label.grid(column=0, row=4, padx=1, pady=1)

        self.chat_toggle = tk.Checkbutton(self.root, text="C", variable=self.chat_mode)
        self.chat_toggle.grid(column=0, row=5, padx=1, pady=1)

    def log_message(self, message):
        if self.log_text:
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.configure(state='disabled')
            self.log_text.yview(tk.END)
        else:
            print(message)

    def read_input_file(self):
        try:
            with open('input.txt', 'r') as file:
                input_text = file.read()
            self.log_message("Input file read successfully.")
            return input_text
        except Exception as e:
            self.log_message(f"Error reading input file: {e}")
            return None

    def write_output_file(self, output_text):
        try:
            with open('output.txt', 'w') as file:
                file.write(output_text)
            self.log_message("Output file written successfully.")
        except Exception as e:
            self.log_message(f"Error writing output file: {e}")

    def append_to_history_file(self, output_text):
        try:
            with open('history.txt', 'a') as file:
                file.write(output_text + "\n")
                file.write("." * 50 + "\n")  # Append a dotted line
            self.log_message("Output appended to history file.")
        except Exception as e:
            self.log_message(f"Error appending to history file: {e}")

    def select_image(self):
        self.image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if self.image_path:
            img = Image.open(self.image_path)
            img.thumbnail((10, 10))
            img = ImageTk.PhotoImage(img)
            self.image_label.configure(image=img)
            self.image_label.image = img
            self.log_message(f"Image selected: {self.image_path}")

    def unselect_image(self):
        self.image_path = None
        self.image_label.configure(image='')
        self.image_label.image = None
        self.log_message("Image unselected.")

    def call_gemini_api(self, input_text):
        try:
            model_name = 'gemini-pro-vision' if self.image_path else 'gemini-pro'
            model = genai.GenerativeModel(model_name)

            if self.chat_mode.get():
                # Chat mode: Use the context for a multi-turn conversation
                chat = model.start_chat(history=self.context)
                response = chat.send_message(input_text)
                self.context = chat.history  # Update the context with the chat history
                response_text = response.text if response else 'No response from API.'
            else:
                # Single-turn mode
                if self.image_path:
                    img = Image.open(self.image_path)
                    response = model.generate_content([input_text, img])
                else:
                    response = model.generate_content([input_text])
                response.resolve()
                response_text = response.text if response else 'No response from API.'

            self.log_message("API call successful.")
            return response_text
        except Exception as e:
            self.log_message(f"Unexpected error: {e}")
            return None

    def process_input(self):
        input_text = self.read_input_file()
        if not input_text:
            self.log_message("No input text to process.")
            return

        response_text = self.call_gemini_api(input_text)
        if response_text:
            self.write_output_file(response_text)
            self.append_to_history_file(response_text)
            self.log_message("Processing completed.")
        else:
            self.log_message("No response received.")

    def control_press(self, event):
        self.ctrl_pressed = True

    def control_release(self, event):
        self.ctrl_pressed = False

    def period_press(self, event):
        if self.ctrl_pressed:
            self.period_pressed += 1
            if self.period_pressed >= 2:
                self.process_input()

    def period_release(self, event):
        if not self.ctrl_pressed:
            self.period_pressed = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = GeminiChatApp(root)
    root.mainloop()
