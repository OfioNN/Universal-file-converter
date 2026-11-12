import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, ttk

from file_converter.errors import ConversionError
from file_converter.log_config import ERROR_LOG_FILE, configure_logging
from file_converter.registry import REGISTRY, ConversionRequest, available_targets, execute

SOURCE_FORMATS = sorted({source_format for (source_format, _) in REGISTRY})
SOURCE_PATTERNS = [f"*{source_format}" for source_format in SOURCE_FORMATS]

BACKGROUND = "#F3F4F8"
SURFACE = "#FFFFFF"
ACCENT = "#4F46E5"
ACCENT_DARK = "#4338CA"
ACCENT_LIGHT = "#EEF2FF"
ACCENT_DISABLED = "#A5B4FC"
TEXT = "#1F2937"
MUTED = "#6B7280"
BORDER = "#CBD5E1"
ERROR = "#DC2626"
ERROR_LIGHT = "#FEF2F2"
SUCCESS = "#16A34A"

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_BOLD = ("Segoe UI Semibold", 10)
FONT_TITLE = ("Segoe UI Semibold", 12)

BOX_SIZE = 220


def configure_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TLabel", background=BACKGROUND, foreground=TEXT, font=FONT)
    style.configure("Heading.TLabel", font=FONT_BOLD)
    style.configure("Status.TLabel", foreground=MUTED)
    style.configure("Dialog.TLabel", background=SURFACE)
    style.configure("DialogTitle.TLabel", background=SURFACE, font=FONT_TITLE)

    style.configure(
        "TCombobox", padding=8, arrowsize=16, arrowcolor=ACCENT,
        bordercolor=BORDER, lightcolor=SURFACE, darkcolor=SURFACE,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("disabled", BACKGROUND), ("readonly", SURFACE)],
        background=[("disabled", BACKGROUND), ("readonly", SURFACE)],
        foreground=[("disabled", MUTED), ("readonly", TEXT)],
        selectbackground=[("readonly", SURFACE)],
        selectforeground=[("readonly", TEXT)],
        bordercolor=[("focus", ACCENT)],
        arrowcolor=[("disabled", BORDER)],
    )
    root.option_add("*TCombobox*Listbox.font", FONT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", SURFACE)

    style.configure(
        "Accent.TButton", font=FONT_BOLD, padding=(20, 12), foreground=SURFACE, background=ACCENT,
        bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT, focuscolor=ACCENT,
    )
    hover_colors = [("disabled", ACCENT_DISABLED), ("pressed", ACCENT_DARK), ("active", ACCENT_DARK)]
    style.map(
        "Accent.TButton",
        foreground=[("disabled", SURFACE)],
        background=hover_colors, bordercolor=hover_colors, lightcolor=hover_colors, darkcolor=hover_colors,
    )
    style.configure("Dialog.Accent.TButton", padding=(28, 6))


def show_message(parent: tk.Tk, title: str, message: str, success: bool = False) -> None:
    dialog = tk.Toplevel(parent, bg=SURFACE, padx=24, pady=20)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(parent)

    color, symbol = (SUCCESS, "✓") if success else (ERROR, "!")
    icon = tk.Canvas(dialog, width=40, height=40, bg=SURFACE, highlightthickness=0)
    icon.create_oval(2, 2, 38, 38, fill=color, outline=color)
    icon.create_text(20, 20, text=symbol, fill=SURFACE, font=("Segoe UI", 16, "bold"))
    icon.grid(row=0, column=0, rowspan=2, sticky="n", padx=(0, 16))

    ttk.Label(dialog, text=title, style="DialogTitle.TLabel").grid(row=0, column=1, sticky="w")
    ttk.Label(dialog, text=message, style="Dialog.TLabel", wraplength=340, justify="left").grid(
        row=1, column=1, sticky="w", pady=(4, 0)
    )
    ok_button = ttk.Button(dialog, text="OK", style="Dialog.Accent.TButton", command=dialog.destroy)
    ok_button.grid(row=2, column=1, sticky="e", pady=(20, 0))

    dialog.bind("<Return>", lambda event: dialog.destroy())
    dialog.bind("<Escape>", lambda event: dialog.destroy())

    dialog.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width() - dialog.winfo_reqwidth()) // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - dialog.winfo_reqheight()) // 2
    dialog.geometry(f"+{x}+{y}")

    ok_button.focus_set()
    dialog.grab_set()
    dialog.wait_window()


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Konwerter plików")
        self.configure(bg=BACKGROUND, padx=28, pady=24)
        self.resizable(False, False)
        configure_styles(self)

        self.source: Path | None = None
        self.hovered = False
        self.format_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Nie wybrano pliku.")

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None

        ttk.Label(self, text="Wybierz plik", style="Heading.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Label(self, text="Format eksportu", style="Heading.TLabel").grid(
            row=0, column=1, sticky="w", padx=(28, 0), pady=(0, 8)
        )

        self.file_box = tk.Canvas(
            self, width=BOX_SIZE, height=BOX_SIZE, bg=BACKGROUND, highlightthickness=0, cursor="hand2"
        )
        self.file_box.grid(row=1, column=0, rowspan=2)
        self.file_box.bind("<Button-1>", lambda event: self.choose_source())
        self.file_box.bind("<Enter>", lambda event: self.set_hovered(True))
        self.file_box.bind("<Leave>", lambda event: self.set_hovered(False))

        self.format_combobox = ttk.Combobox(
            self, textvariable=self.format_var, state="disabled", font=FONT, width=22
        )
        self.format_combobox.grid(row=1, column=1, sticky="new", padx=(28, 0))

        self.convert_button = ttk.Button(
            self, text="Konwertuj", style="Accent.TButton", command=self.start_conversion
        )
        self.convert_button.grid(row=2, column=1, sticky="sew", padx=(28, 0))
        self.rowconfigure(1, weight=1)

        ttk.Label(self, textvariable=self.status_var, style="Status.TLabel").grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(16, 0)
        )

        self.draw_file_box()

    def set_hovered(self, hovered: bool) -> None:
        self.hovered = hovered
        self.draw_file_box()

    def draw_file_box(self) -> None:
        box = self.file_box
        box.delete("all")
        center = BOX_SIZE // 2

        if self.source is None:
            box.create_rectangle(
                2, 2, BOX_SIZE - 2, BOX_SIZE - 2, width=2, dash=(6, 4),
                fill=ACCENT_LIGHT if self.hovered else SURFACE,
                outline=ACCENT if self.hovered else BORDER,
            )
            box.create_line(center, 70, center, 130, fill=ACCENT, width=4, capstyle="round")
            box.create_line(center - 30, 100, center + 30, 100, fill=ACCENT, width=4, capstyle="round")
            box.create_text(center, 170, text="Kliknij, aby wybrać plik", fill=MUTED, font=FONT)
            return

        supported = bool(available_targets(self.source))
        color = ACCENT if supported else ERROR
        box.create_rectangle(
            2, 2, BOX_SIZE - 2, BOX_SIZE - 2, width=2, outline=color,
            fill=ACCENT_LIGHT if supported else ERROR_LIGHT,
        )

        left, top, right, bottom, fold = center - 32, 36, center + 32, 120, 18
        box.create_polygon(
            left, top, right - fold, top, right, top + fold, right, bottom, left, bottom,
            fill=SURFACE, outline=color, width=2, joinstyle="round",
        )
        box.create_polygon(
            right - fold, top, right - fold, top + fold, right, top + fold,
            fill=ACCENT_LIGHT if supported else ERROR_LIGHT, outline=color, width=2, joinstyle="round",
        )
        box.create_text(center, 86, text=self.source.suffix[1:].upper() or "?", fill=color, font=FONT_TITLE)

        name = self.source.name if len(self.source.name) <= 26 else self.source.name[:23] + "…"
        box.create_text(center, 152, text=name, fill=TEXT, font=FONT_BOLD)
        box.create_text(center, 178, text="Kliknij, aby zmienić plik", fill=MUTED, font=FONT_SMALL)

    def choose_source(self) -> None:
        path = filedialog.askopenfilename(
            title="Wybierz plik",
            filetypes=[("Obsługiwane pliki", SOURCE_PATTERNS), ("Wszystkie pliki", "*.*")],
        )
        if not path:
            return

        self.source = Path(path)
        formats = [target[1:].upper() for target in available_targets(self.source)]
        self.format_combobox["values"] = formats
        self.format_var.set(formats[0] if formats else "")
        self.format_combobox.config(state="readonly" if formats else "disabled")
        if formats:
            self.status_var.set(f"Wybrano plik: {self.source.name}")
        else:
            self.status_var.set(f"Wybrano plik: {self.source.name} – ten format nie jest obsługiwany.")
        self.draw_file_box()

    def find_problem(self) -> str | None:
        if self.source is None:
            return "Nie wybrano pliku. Kliknij pole „Wybierz plik” i wskaż plik do konwersji."
        if not self.source.is_file():
            return f"Nie znaleziono pliku {self.source.name}. Mógł zostać przeniesiony lub usunięty – wybierz go ponownie."
        if not available_targets(self.source):
            return (
                f"Pliki {self.source.suffix or 'bez rozszerzenia'} nie są obsługiwane. "
                f"Wybierz plik w jednym z formatów: {', '.join(SOURCE_FORMATS)}."
            )
        if not self.format_var.get():
            return "Nie wybrano formatu eksportu. Wybierz format z listy."
        return None

    def start_conversion(self) -> None:
        problem = self.find_problem()
        if problem:
            show_message(self, "Nie można rozpocząć konwersji", problem)
            return

        target_format = "." + self.format_var.get().lower()
        path = filedialog.asksaveasfilename(
            title="Zapisz plik jako",
            initialdir=self.source.parent,
            initialfile=f"{self.source.stem}{target_format}",
            defaultextension=target_format,
            filetypes=[(f"Plik {self.format_var.get()}", f"*{target_format}")],
        )
        if not path:
            return

        target = Path(path)
        request = ConversionRequest(
            self.source, target_format, target.parent, overwrite=True, target_name=target.name
        )

        self.convert_button.config(state="disabled", text="Konwertowanie…")
        self.status_var.set(f"Trwa konwersja pliku {self.source.name}…")
        self.future = self.executor.submit(execute, request)
        self.after(100, self.check_result)

    def check_result(self) -> None:
        if not self.future.done():
            self.after(100, self.check_result)
            return

        self.convert_button.config(state="normal", text="Konwertuj")

        try:
            target = self.future.result()
        except ConversionError as error:
            self.status_var.set("Konwersja nie powiodła się.")
            show_message(self, "Błąd konwersji", str(error))
        except Exception as error:
            self.status_var.set("Konwersja nie powiodła się.")
            show_message(
                self,
                "Nieoczekiwany błąd",
                f"Wystąpił nieoczekiwany błąd: {error}\nSzczegóły zapisano w pliku {ERROR_LOG_FILE}.",
            )
        else:
            self.status_var.set(f"Zapisano: {target.name}")
            show_message(self, "Konwersja zakończona", f"Utworzono plik:\n{target}", success=True)


def main() -> None:
    configure_logging()
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
