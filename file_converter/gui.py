import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from file_converter.log_config import ERROR_LOG_FILE, configure_logging

from file_converter.errors import ConversionError
from file_converter.registry import REGISTRY, ConversionRequest, available_targets, execute

SOURCE_PATTERNS = sorted({f"*{source_format}" for (source_format, _) in REGISTRY})


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Konwerter plików")
        self.resizable(False, False)

        self.source_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.target_format_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Wybierz plik do konwersji.")

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None

        ttk.Label(self, text="Plik wejściowy:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(self, textvariable=self.source_var, width=50, state="readonly").grid(row=0, column=1, padx=8, pady=4)
        ttk.Button(self, text="Wybierz...", command=self.choose_source).grid(row=0, column=2, padx=8, pady=4)

        ttk.Label(self, text="Folder zapisu:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(self, textvariable=self.output_dir_var, width=50, state="readonly").grid(row=1, column=1, padx=8, pady=4)
        ttk.Button(self, text="Wybierz...", command=self.choose_output_dir).grid(row=1, column=2, padx=8, pady=4)

        ttk.Label(self, text="Format docelowy:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        self.format_combobox = ttk.Combobox(self, textvariable=self.target_format_var, state="disabled")
        self.format_combobox.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        self.convert_button = ttk.Button(self, text="Konwertuj", command=self.start_conversion)
        self.convert_button.grid(row=3, column=1, pady=8)

        ttk.Label(self, textvariable=self.status_var).grid(row=4, column=0, columnspan=3, sticky="w", padx=8, pady=4)

    def choose_source(self) -> None:
        path = filedialog.askopenfilename(
            title="Wybierz plik",
            filetypes=[("Obsługiwane pliki", SOURCE_PATTERNS), ("Wszystkie pliki", "*.*")],
        )
        if not path:
            return

        self.source_var.set(path)
        targets = available_targets(Path(path))
        self.format_combobox["values"] = targets

        if targets:
            self.target_format_var.set(targets[0])
            self.format_combobox.config(state="readonly")
            self.status_var.set("Wybierz folder zapisu i format, a potem kliknij Konwertuj.")
        else:
            self.target_format_var.set("")
            self.format_combobox.config(state="disabled")
            self.status_var.set(f"Pliki {Path(path).suffix} nie są obsługiwane. Wybierz inny plik.")

    def choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Wybierz folder zapisu")
        if path:
            self.output_dir_var.set(path)

    def start_conversion(self) -> None:
        if not self.source_var.get() or not self.output_dir_var.get() or not self.target_format_var.get():
            messagebox.showwarning("Brak danych", "Wybierz plik wejściowy, folder zapisu i format docelowy.")
            return

        request = ConversionRequest(
            Path(self.source_var.get()), self.target_format_var.get(), Path(self.output_dir_var.get())
        )

        if request.target_path.exists():
            if not messagebox.askyesno("Plik istnieje", f"Plik {request.target_path.name} już istnieje. Nadpisać go?"):
                return
            request = ConversionRequest(request.source, request.target_format, request.output_dir, overwrite=True)

        self.convert_button.config(state="disabled")
        self.status_var.set("Trwa konwersja...")
        self.future = self.executor.submit(execute, request)
        self.after(100, self.check_result)

    def check_result(self) -> None:
        if not self.future.done():
            self.after(100, self.check_result)
            return

        self.convert_button.config(state="normal")

        try:
            target = self.future.result()
            self.status_var.set(f"Gotowe: {target}")
            messagebox.showinfo("Gotowe", f"Utworzono plik:\n{target}")
        except ConversionError as error:
            self.status_var.set("Konwersja nie powiodła się.")
            messagebox.showerror("Błąd konwersji", str(error))
        except Exception as error:
            self.status_var.set("Konwersja nie powiodła się.")
            messagebox.showerror(
                "Nieoczekiwany błąd",
                f"Wystąpił nieoczekiwany błąd: {error}\nSzczegóły zapisano w pliku {ERROR_LOG_FILE}.",
            )


def main() -> None:
    configure_logging()
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()