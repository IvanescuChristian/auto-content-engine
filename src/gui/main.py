import tkinter as tk
from tkinter import messagebox, ttk
from gtts import gTTS
import os
from script_gen.generator import get_script

def process_audio(text):
    if not text.strip():
        messagebox.showwarning("Warning", "The script is empty!")
        return
    try:
        tts = gTTS(text=text, lang='en') 
        output_path = "video_final.mp3"
        tts.save(output_path)
        messagebox.showinfo("Success", f"Audio generated successfully: {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Audio generation failed: {e}")

def update_ui_style(event=None):
    method = combo_method.get()
    if method == "Manual":
        btn_generate.config(text="Paste Script & Generate Audio", bg="#10b981")
    else:
        btn_generate.config(text="Generate Video Content", bg="#3b82f6")

def on_generate(event=None):
    method = combo_method.get()

    if method == "Manual":
        manual_window = tk.Toplevel(root)
        manual_window.title("Manual Input")
        manual_window.geometry("600x500")
        
        tk.Label(manual_window, text="Paste your English script here:", font=("Arial", 11, "bold")).pack(pady=10)
        
        txt_area = tk.Text(manual_window, wrap=tk.WORD, width=70, height=20, font=("Arial", 10))
        txt_area.pack(padx=10, pady=10)
        
        def start_manual_processing():
            script_content = txt_area.get("1.0", tk.END).strip()
            process_audio(script_content)
            manual_window.destroy()

        tk.Button(manual_window, text="START GENERATING AUDIO", bg="#10b981", fg="white", 
                  font=("Arial", 11, "bold"), command=start_manual_processing).pack(pady=10)
    else:
        topic = entry_topic.get()
        if not topic:
            messagebox.showwarning("Warning", "Please enter a topic for AI Generation!")
            return
            
        messagebox.showinfo("Processing", f"AI is thinking... Please wait.")
        try:
            script = get_script(topic, entry_subtopics.get(), entry_minutes.get(), method)
            with open("generated_script.txt", "w", encoding="utf-8") as f:
                f.write(script)
            process_audio(script)
        except Exception as e:
            messagebox.showerror("Error", f"AI Generation failed: {e}")

root = tk.Tk()
root.title("YouTube Automator")
root.geometry("450x550")
root.resizable(False, False)

font_label = ("Arial", 11, "bold")
font_entry = ("Arial", 11)


tk.Label(root, text="Step 1: Choose Source", font=font_label).pack(pady=(25, 5))

combo_method = ttk.Combobox(root, values=["Manual", "Gemini"], state="readonly", font=font_entry)
combo_method.set("Manual")
combo_method.pack()
combo_method.bind("<<ComboboxSelected>>", update_ui_style)

tk.Label(root, text="------------------------------------------").pack(pady=10)

tk.Label(root, text="Main Topic (Only for AI):", font=font_label).pack(pady=(15, 5))
entry_topic = tk.Entry(root, width=45, font=font_entry)
entry_topic.pack()

tk.Label(root, text="Subtopics (Only for AI):", font=font_label).pack(pady=(15, 5))
entry_subtopics = tk.Entry(root, width=45, font=font_entry)
entry_subtopics.pack()

tk.Label(root, text="Est. Duration (minutes):", font=font_label).pack(pady=(15, 5))
entry_minutes = tk.Entry(root, width=15, font=font_entry)
entry_minutes.pack()


btn_generate = tk.Button(root, text="Paste Script & Generate Audio", font=("Arial", 12, "bold"), 
                         bg="#10b981", fg="white", command=on_generate, height=2, width=30)
btn_generate.pack(pady=40)

root.bind('<Return>', on_generate)


update_ui_style()

root.mainloop()