# ENGINEERING UNIT CONVERTER
# ND1 Mechatronics Engineering mini project.
# Built with Python and the standard-library Tkinter graphical interface.
# Run: python unit_converter.py

import csv
import math
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk


# Unit pairs match all four categories named in the assignment brief.
CATEGORIES = {
    "Length": ("mm", "in"),
    "Temperature": ("°C", "°F"),
    "Mass": ("kg", "lb"),
    "Speed": ("km/h", "m/s"),
}

# Notes use defined conversion constants, not rounded display approximations.
DETAILS = {
    "Length": ("LENGTH / DIMENSION", "1 inch is exactly 25.4 millimetres.",
               "Used for drawings, components and tolerances."),
    "Temperature": ("TEMPERATURE / THERMAL", "Freezing point: 0 °C = 32 °F.",
                    "The scales have different zero points."),
    "Mass": ("MASS / MATERIALS", "1 pound is exactly 0.45359237 kilograms.",
             "Useful for loads, parts and specifications."),
    "Speed": ("SPEED / MOTION", "1 metre per second equals 3.6 kilometres per hour.",
              "Used for machines, vehicles and motion."),
}


def parse_measurement(text, category):
    """Convert a user's text to float() and explain invalid input."""
    try:
        value = float(text.strip())
    except (ValueError, AttributeError):
        raise ValueError("Enter a number, for example 12.5 or -10.") from None
    if not math.isfinite(value):
        raise ValueError("Please enter a finite number; infinity and NaN are not valid.")
    if category != "Temperature" and value < 0:
        raise ValueError("Use a non-negative value for length, mass or speed.")
    return value


def convert_value(category, from_unit, to_unit, value):
    """Convert a number using the exact factors specified by each unit pair."""
    if category not in CATEGORIES:
        raise ValueError("Choose one of the four engineering categories.")
    valid_units = CATEGORIES[category]
    if from_unit not in valid_units or to_unit not in valid_units:
        raise ValueError("The selected units do not belong to this category.")
    if not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("Enter a finite numeric value.")
    if category != "Temperature" and value < 0:
        raise ValueError("Only temperature can use negative values here.")
    if from_unit == to_unit:
        return value

    # Explicit if/elif/else makes every formula easy to explain at assessment.
    if category == "Length":
        result = value / 25.4 if from_unit == "mm" else value * 25.4
    elif category == "Temperature":
        result = value * 9 / 5 + 32 if from_unit == "°C" else (value - 32) * 5 / 9
    elif category == "Mass":
        result = value / 0.45359237 if from_unit == "kg" else value * 0.45359237
    else:  # category == "Speed"
        result = value / 3.6 if from_unit == "km/h" else value * 3.6

    if not math.isfinite(result):
        raise ValueError("The result is too large; enter a smaller value.")
    return result


def formula_description(category, from_unit, to_unit):
    """Return the rule in the direction the user selected."""
    if from_unit == to_unit:
        return "No change: source and destination use the same unit."
    rules = {
        "Length": ("in = mm ÷ 25.4", "mm = in × 25.4"),
        "Temperature": ("°F = (°C × 9/5) + 32", "°C = (°F − 32) × 5/9"),
        "Mass": ("lb = kg ÷ 0.45359237", "kg = lb × 0.45359237"),
        "Speed": ("m/s = km/h ÷ 3.6", "km/h = m/s × 3.6"),
    }
    return rules[category][0 if from_unit == CATEGORIES[category][0] else 1]


def format_number(value, places=4):
    """Format for readability, preserving tiny nonzero results with notation."""
    if not isinstance(places, int) or places not in (2, 4, 6, 8):
        raise ValueError("Precision must be 2, 4, 6, or 8 decimal places.")
    if abs(value) >= 1e12 or (value != 0 and abs(value) < 0.5 * 10 ** (-places)):
        return f"{value:.6e}"
    return f"{value:,.{places}f}"


def convert_batch(category, from_unit, to_unit, multiline_text):
    """Convert each nonempty line; return errors beside their line numbers."""
    lines = multiline_text.splitlines()
    if len(lines) > 500:
        raise ValueError("Batch limit is 500 lines. Split larger lists into smaller batches.")
    results = []
    for line_number, text in enumerate(lines, start=1):
        if not text.strip():
            continue
        try:
            source_value = parse_measurement(text, category)
            converted_value = convert_value(category, from_unit, to_unit, source_value)
            results.append((line_number, source_value, converted_value, ""))
        except ValueError as error:
            results.append((line_number, None, None, str(error)))
    return results


# Light surfaces mimic a printed engineering measurement sheet.
# Deep teal marks selected actions and the pale-teal destination panel.
BACKGROUND = "#EFF5F3"
WHITE = "#FFFFFF"
NAVY = "#17343D"
INK = "#18343D"
TEAL = "#087E81"
PALE_TEAL = "#E2F4F0"
MIST = "#F6FAF9"
BORDER = "#D4E3E0"
MUTED = "#61777C"
BAD = "#B34848"
GOOD = "#14795F"
FONT = "DejaVu Sans"


class ConverterApp(tk.Tk):
    """A conversion workspace designed for quick, error-resistant operation."""

    def __init__(self):
        super().__init__()
        self.title("MeasureKit | Engineering Unit Converter")
        self.geometry("1260x740")
        self.minsize(1080, 710)
        self.configure(bg=BACKGROUND)
        self.category = "Length"
        self.mode = "single"
        self.history = []
        self.last_result = None
        self.precision = tk.StringVar(value="4")
        self.value_var = tk.StringVar(value="25.4")
        self.from_var = tk.StringVar()
        self.to_var = tk.StringVar()
        self.nav_buttons = {}
        self.make_styles()
        self.build_header()
        self.build_layout()
        self.set_category("Length")
        self.value_var.trace_add("write", lambda *_: self.refresh_preview())
        self.bind("<Return>", self.on_enter)
        self.bind("<Escape>", lambda event: self.clear_current())
        self.bind("<Control-Shift-C>", lambda event: self.copy_result())

    def make_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Unit.TCombobox", padding=9, fieldbackground=MIST,
                        background=MIST, foreground=INK)
        style.map("Unit.TCombobox",
                  fieldbackground=[("readonly", MIST)],
                  foreground=[("readonly", INK)],
                  selectbackground=[("readonly", MIST)],
                  selectforeground=[("readonly", INK)])

    def label(self, parent, text, size=11, color=INK, bold=False, **kwargs):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=(FONT, size, "bold" if bold else "normal"), **kwargs)

    def panel(self, parent):
        return tk.Frame(parent, bg=WHITE, highlightbackground=BORDER,
                        highlightthickness=1)

    def button(self, parent, text, command, bg=TEAL, fg=WHITE):
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         activebackground=bg, activeforeground=fg, relief="flat",
                         cursor="hand2", bd=0, padx=15, pady=11,
                         font=(FONT, 10, "bold"))

    def build_header(self):
        header = tk.Frame(self, bg=BACKGROUND)
        header.pack(fill="x", padx=28, pady=(22, 18))
        brand = tk.Frame(header, bg=TEAL, width=52, height=52)
        brand.pack(side="left")
        brand.pack_propagate(False)
        tk.Label(brand, bg=TEAL, fg=WHITE, text="↔",
                 font=(FONT, 22, "bold")).pack(expand=True)
        title = tk.Frame(header, bg=BACKGROUND)
        title.pack(side="left", padx=15)
        self.label(title, "MEASUREKIT", 19, NAVY, True).pack(anchor="w")
        self.label(title, "ENGINEERING  /  UNIT CONVERTER", 9,
                   MUTED, True).pack(anchor="w", pady=(4, 0))
        right = tk.Frame(header, bg=BACKGROUND)
        right.pack(side="right")
        self.label(right, "4 ESSENTIAL UNIT PAIRS", 10, TEAL, True).pack(anchor="e")
        self.label(right, "Enter to save  •  Esc to reset", 9,
                   MUTED).pack(anchor="e", pady=(5, 0))

    def build_layout(self):
        body = tk.Frame(self, bg=BACKGROUND)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 25))
        body.columnconfigure(0, minsize=220)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, minsize=266)
        body.rowconfigure(0, weight=1)
        nav = self.panel(body)
        nav.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        middle = tk.Frame(body, bg=BACKGROUND)
        middle.grid(row=0, column=1, sticky="nsew", padx=12)
        middle.rowconfigure(0, weight=3)
        middle.rowconfigure(1, weight=2)
        middle.columnconfigure(0, weight=1)
        aside = tk.Frame(body, bg=BACKGROUND)
        aside.grid(row=0, column=2, sticky="nsew", padx=(12, 0))
        aside.rowconfigure(0, weight=3)
        aside.rowconfigure(1, weight=2)
        aside.columnconfigure(0, weight=1)
        self.build_navigation(nav)
        self.build_converter(middle)
        self.build_batch(middle)
        self.build_reference(aside)
        self.build_history(aside)

    def build_navigation(self, parent):
        self.label(parent, "CONVERSION LIBRARY", 10, MUTED,
                   True).pack(anchor="w", padx=19, pady=(23, 16))
        descriptions = {"Length": "mm   ↔   in", "Temperature": "°C   ↔   °F",
                        "Mass": "kg   ↔   lb", "Speed": "km/h   ↔   m/s"}
        for category in CATEGORIES:
            b = tk.Button(parent, text=f"{category}\n{descriptions[category]}",
                          anchor="w", justify="left", bd=0, relief="flat",
                          cursor="hand2", padx=18, pady=14,
                          font=(FONT, 11, "bold"),
                          command=lambda c=category: self.set_category(c))
            b.pack(fill="x", padx=11, pady=4)
            self.nav_buttons[category] = b
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=19, pady=(23, 15))
        self.label(parent, "DESIGNED FOR", 9, MUTED, True).pack(anchor="w", padx=19)
        self.label(parent, "Measurements\nSpecifications\nLab calculations",
                   10, INK, justify="left").pack(anchor="w", padx=19, pady=(9, 0))
        self.label(parent, "All conversions are reversible.\nNo internet connection required.",
                   9, MUTED, justify="left", wraplength=195).pack(
            anchor="w", side="bottom", padx=18, pady=(0, 22))

    def build_converter(self, parent):
        card = self.panel(parent)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, 18))
        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill="both", expand=True, padx=23, pady=8)
        top = tk.Frame(inner, bg=WHITE)
        top.pack(fill="x")
        self.category_eyebrow = self.label(top, "LENGTH / DIMENSION", 9,
                                           TEAL, True)
        self.category_eyebrow.pack(side="left")
        self.button(top, "SWAP  ↔", self.swap_units, PALE_TEAL,
                    TEAL).pack(side="right")
        self.label(inner, "Convert with confidence.", 18, NAVY,
                   True).pack(anchor="w", pady=(5, 0))
        self.label(inner, "Enter a value. Swap keeps the same measurement.",
                   9, MUTED).pack(anchor="w")

        fields = tk.Frame(inner, bg=WHITE)
        fields.pack(fill="x", pady=(8, 0))
        fields.columnconfigure(0, weight=4)
        fields.columnconfigure(1, weight=2)
        self.label(fields, "SOURCE VALUE", 9, MUTED, True).grid(
            row=0, column=0, sticky="w", pady=(0, 7))
        self.label(fields, "FROM UNIT", 9, MUTED, True).grid(
            row=0, column=1, sticky="w", padx=(13, 0), pady=(0, 7))
        self.value_entry = tk.Entry(fields, textvariable=self.value_var,
                                    font=(FONT, 19, "bold"), bg=MIST, fg=NAVY,
                                    insertbackground=TEAL, relief="flat", bd=0,
                                    highlightthickness=1, highlightcolor=TEAL,
                                    highlightbackground=BORDER)
        self.value_entry.grid(row=1, column=0, sticky="ew", ipady=11, ipadx=12)
        self.from_box = ttk.Combobox(fields, textvariable=self.from_var, state="readonly",
                                     style="Unit.TCombobox", font=(FONT, 12, "bold"))
        self.from_box.grid(row=1, column=1, sticky="ew", padx=(13, 0), ipady=9)
        self.from_box.bind("<<ComboboxSelected>>", self.units_changed)

        target_row = tk.Frame(inner, bg=PALE_TEAL)
        target_row.pack(fill="x", pady=(8, 0))
        target_left = tk.Frame(target_row, bg=PALE_TEAL)
        target_left.pack(side="left", fill="both", expand=True, padx=15, pady=9)
        self.label(target_left, "CONVERTED RESULT", 9, TEAL, True).pack(anchor="w")
        self.result_number = self.label(target_left, "—", 23,
                                        NAVY, True, wraplength=465, justify="left")
        self.result_number.pack(anchor="w", pady=(4, 0))
        right_units = tk.Frame(target_row, bg=PALE_TEAL)
        right_units.pack(side="right", padx=(0, 14))
        self.label(right_units, "TO UNIT", 9, TEAL, True).pack(anchor="w", pady=(0, 8))
        self.to_box = ttk.Combobox(right_units, textvariable=self.to_var,
                                   state="readonly", style="Unit.TCombobox",
                                   width=8, font=(FONT, 11, "bold"))
        self.to_box.pack()
        self.to_box.bind("<<ComboboxSelected>>", self.units_changed)
        control = tk.Frame(inner, bg=WHITE)
        control.pack(fill="x", pady=(7, 0))
        self.button(control, "CONVERT & SAVE  →", self.convert_and_save).pack(side="left")
        self.button(control, "Copy result", self.copy_result,
                    MIST, NAVY).pack(side="left", padx=(8, 0))
        precision_box = ttk.Combobox(control, textvariable=self.precision,
                                     state="readonly", width=3,
                                     values=("2", "4", "6", "8"),
                                     font=(FONT, 10, "bold"))
        precision_box.pack(side="right")
        self.label(control, "DECIMALS", 9, MUTED, True).pack(side="right", padx=(7, 7))
        precision_box.bind("<<ComboboxSelected>>", self.precision_changed)
        self.status = self.label(inner, "", 10, MUTED, wraplength=560,
                                 justify="left")
        self.status.pack(fill="x", pady=(3, 0), anchor="w")

    def build_batch(self, parent):
        card = self.panel(parent)
        card.grid(row=1, column=0, sticky="nsew")
        top = tk.Frame(card, bg=WHITE)
        top.pack(fill="x", padx=22, pady=(12, 7))
        self.label(top, "BATCH CONVERSION", 11, NAVY, True).pack(side="left")
        self.label(top, "ONE VALUE PER LINE", 9, MUTED, True).pack(side="right")
        two_cols = tk.Frame(card, bg=WHITE)
        two_cols.pack(fill="both", expand=True, padx=22)
        two_cols.columnconfigure(0, weight=1)
        two_cols.columnconfigure(1, weight=1)
        two_cols.rowconfigure(0, weight=1)
        input_frame = tk.Frame(two_cols, bg=WHITE)
        input_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        result_frame = tk.Frame(two_cols, bg=WHITE)
        result_frame.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.label(input_frame, "INPUT VALUES", 9, MUTED, True).pack(anchor="w", pady=(0, 7))
        self.batch_entry = tk.Text(input_frame, bg=MIST, fg=INK,
                                   insertbackground=TEAL, relief="flat", bd=0,
                                   font=(FONT, 10), height=3, padx=10, pady=7,
                                   highlightbackground=BORDER, highlightthickness=1)
        self.batch_entry.pack(fill="both", expand=True)
        self.batch_entry.insert("1.0", "1\n10\n100")
        self.label(result_frame, "CONVERTED VALUES", 9, MUTED, True).pack(
            anchor="w", pady=(0, 7))
        self.batch_output = tk.Text(result_frame, bg=MIST, fg=INK,
                                    relief="flat", bd=0, font=(FONT, 10),
                                    height=3, padx=10, pady=7, state="disabled",
                                    highlightbackground=BORDER, highlightthickness=1)
        self.batch_output.pack(fill="both", expand=True)
        bottom = tk.Frame(card, bg=WHITE)
        bottom.pack(fill="x", padx=22, pady=(7, 9))
        self.button(bottom, "RUN BATCH  →", self.run_batch,
                    TEAL, WHITE).pack(side="left")
        self.button(bottom, "Copy results", self.copy_batch,
                    MIST, NAVY).pack(side="left", padx=(6, 0))
        self.batch_status = self.label(bottom, "Up to 500 lines; invalid lines are identified.",
                                       9, MUTED)
        self.batch_status.pack(side="left", padx=(10, 0))

    def build_reference(self, parent):
        card = self.panel(parent)
        card.grid(row=0, column=0, sticky="nsew", pady=(0, 18))
        content = tk.Frame(card, bg=WHITE)
        content.pack(fill="both", expand=True, padx=19, pady=13)
        self.label(content, "REFERENCE / METHOD", 10, TEAL, True).pack(anchor="w")
        self.label(content, "The rule behind the result", 12,
                   NAVY, True, wraplength=220, justify="left").pack(
            anchor="w", pady=(9, 4))
        self.formula_label = self.label(content, "", 12, NAVY, True,
                                        wraplength=222, justify="left")
        self.formula_label.pack(anchor="w", pady=(3, 5))
        tk.Frame(content, bg=BORDER, height=1).pack(fill="x", pady=9)
        self.exact_note = self.label(content, "", 10, INK,
                                     wraplength=222, justify="left")
        self.exact_note.pack(anchor="w", pady=(0, 8))
        self.context_note = self.label(content, "", 9, MUTED,
                                       wraplength=220, justify="left")
        self.context_note.pack(anchor="w")
        tk.Frame(content, bg=BORDER, height=1).pack(fill="x", pady=10)
        self.label(content, "TRY AN EXAMPLE", 9, TEAL, True).pack(anchor="w")
        # Each example is an actual control, so the reference panel is useful
        # for first-time users rather than being decorative text.
        self.references = []
        for index in range(3):
            button = tk.Button(content, text="", bg=MIST, fg=INK, relief="flat",
                               anchor="w", justify="left", cursor="hand2",
                               font=(FONT, 9), bd=0, padx=8, pady=8,
                               wraplength=204,
                               command=lambda n=index: self.use_reference(n))
            button.pack(fill="x", pady=(5, 0))
            self.references.append(button)

    def build_history(self, parent):
        card = self.panel(parent)
        card.grid(row=1, column=0, sticky="nsew")
        content = tk.Frame(card, bg=WHITE)
        content.pack(fill="both", expand=True, padx=17, pady=12)
        self.label(content, "RECENT CONVERSIONS", 11, NAVY, True).pack(anchor="w")
        history_frame = tk.Frame(content, bg=WHITE)
        history_frame.pack(fill="both", expand=True, pady=(7, 6))
        self.history_list = tk.Listbox(history_frame, bg=WHITE, fg=INK,
                                       selectbackground=PALE_TEAL,
                                       selectforeground=NAVY, relief="flat",
                                       bd=0, highlightthickness=0,
                                       font=(FONT, 9), activestyle="none",
                                       height=5)
        self.history_list.pack(side="left", fill="both", expand=True)
        history_scroll = ttk.Scrollbar(history_frame, orient="vertical",
                                       command=self.history_list.yview)
        history_scroll.pack(side="right", fill="y")
        self.history_list.configure(yscrollcommand=history_scroll.set)
        actions = tk.Frame(content, bg=WHITE)
        actions.pack(fill="x")
        self.button(actions, "Export CSV", self.export_history,
                    PALE_TEAL, TEAL).pack(side="left")
        self.button(actions, "Clear", self.clear_history,
                    MIST, MUTED).pack(side="right")

    def set_category(self, category):
        self.category = category
        self.last_result = None
        for key, button in self.nav_buttons.items():
            selected = key == category
            button.configure(bg=TEAL if selected else WHITE,
                             fg=WHITE if selected else INK,
                             activebackground=TEAL if selected else PALE_TEAL,
                             activeforeground=WHITE if selected else INK)
        first, second = CATEGORIES[category]
        self.from_box["values"] = (first, second)
        self.to_box["values"] = (first, second)
        self.from_var.set(first)
        self.to_var.set(second)
        self.category_eyebrow.configure(text=DETAILS[category][0])
        self.value_var.set("25.4" if category == "Length" else
                           "25" if category == "Temperature" else "1")
        self.update_context()
        self.refresh_preview()
        self.value_entry.focus_set()

    def units_changed(self, event=None):
        self.update_context()
        self.refresh_preview()

    def swap_units(self):
        """Reverse direction while keeping the same physical measurement.

        Example: 25.4 mm → 1 in becomes 1 in → 25.4 mm. If the current
        input is invalid, reverse the units without changing that input.
        """
        converted = self.last_result[1] if self.last_result is not None else None
        original_from = self.from_var.get()
        self.from_var.set(self.to_var.get())
        self.to_var.set(original_from)
        if converted is not None:
            self.value_var.set(repr(converted))
        self.update_context()
        self.refresh_preview()

    def precision_changed(self, event=None):
        self.refresh_preview()

    def update_context(self):
        category = self.category
        source, destination = self.from_var.get(), self.to_var.get()
        self.formula_label.configure(text=formula_description(category, source, destination))
        self.exact_note.configure(text=DETAILS[category][1])
        self.context_note.configure(text=DETAILS[category][2])
        samples = (0, 25, 100) if category == "Temperature" else (1, 10, 100)
        self.reference_samples = samples
        for idx, number in enumerate(samples):
            converted = convert_value(category, source, destination, number)
            self.references[idx].configure(
                text=f"TRY   {number:g} {source}  →  {format_number(converted, 4)} {destination}")

    def use_reference(self, index):
        """Click a reference example to fill the editable input field."""
        self.value_var.set(str(self.reference_samples[index]))
        self.value_entry.focus_set()
        self.value_entry.select_range(0, "end")

    def refresh_preview(self):
        try:
            amount = parse_measurement(self.value_var.get(), self.category)
            converted = convert_value(self.category, self.from_var.get(),
                                      self.to_var.get(), amount)
            digits = int(self.precision.get())  # Required int() input conversion.
            output_text = f"{format_number(converted, digits)} {self.to_var.get()}"
            self.result_number.configure(text=output_text, fg=NAVY)
            self.status.configure(text="Live preview — select Convert & Save to record it.",
                                  fg=MUTED)
            self.last_result = (amount, converted, self.from_var.get(),
                                self.to_var.get())
        except ValueError as error:
            self.last_result = None
            self.result_number.configure(text="—", fg=BAD)
            self.status.configure(text=str(error), fg=BAD)

    def convert_and_save(self):
        self.refresh_preview()
        if self.last_result is None:
            return
        amount, converted, src, dst = self.last_result
        date = datetime.now().strftime("%H:%M")
        self.history.append((date, self.category, amount, src, converted, dst, "Single"))
        text = f"{format_number(amount, 4)} {src} → {format_number(converted, 4)} {dst}"
        self.history_list.insert(0, text)
        self.status.configure(text="Conversion added to session history.", fg=GOOD)

    def run_batch(self):
        text = self.batch_entry.get("1.0", "end-1c")
        try:
            rows = convert_batch(self.category, self.from_var.get(),
                                 self.to_var.get(), text)
        except ValueError as error:
            self.batch_status.configure(text=str(error), fg=BAD)
            return
        if not rows:
            self.batch_status.configure(text="Enter at least one value, one per line.", fg=BAD)
            return
        converted_count = 0
        errors = 0
        display_lines = []
        for number, original, converted, error in rows:
            if error:
                errors += 1
                display_lines.append(f"Line {number}: ERROR — {error}")
            else:
                converted_count += 1
                display_lines.append(
                    f"{format_number(original, int(self.precision.get()))} {self.from_var.get()}"
                    f" → {format_number(converted, int(self.precision.get()))} {self.to_var.get()}")
                self.history.append((datetime.now().strftime("%H:%M"), self.category,
                                     original, self.from_var.get(), converted,
                                     self.to_var.get(), "Batch"))
        self.batch_output.configure(state="normal")
        self.batch_output.delete("1.0", "end")
        self.batch_output.insert("1.0", "\n".join(display_lines) or "No values entered.")
        self.batch_output.configure(state="disabled")
        self.batch_status.configure(text=f"{converted_count} converted / {errors} errors",
                                    fg=BAD if errors else GOOD)
        for record in self.history[-converted_count:] if converted_count else []:
            _, _, amount, src, output, dst, _ = record
            self.history_list.insert(0,
                f"{format_number(amount, 4)} {src} → {format_number(output, 4)} {dst}")

    def copy_batch(self):
        """Copy the displayed batch, including any line-level error messages."""
        result = self.batch_output.get("1.0", "end-1c").strip()
        if not result:
            self.batch_status.configure(text="Run a batch before copying results.", fg=BAD)
            return
        self.clipboard_clear()
        self.clipboard_append(result)
        self.batch_status.configure(text="Batch results copied to clipboard.", fg=GOOD)

    def on_enter(self, event):
        # In a multi-line Text widget, Enter must insert a new line instead.
        if self.focus_get() == self.batch_entry:
            return
        self.convert_and_save()

    def clear_current(self):
        self.value_var.set("")
        # Clearing is intentional; show a neutral prompt, not an error state.
        self.result_number.configure(text="—", fg=NAVY)
        self.status.configure(text="Ready. Enter a measurement to preview a result.", fg=MUTED)
        self.batch_entry.delete("1.0", "end")
        self.batch_output.configure(state="normal")
        self.batch_output.delete("1.0", "end")
        self.batch_output.configure(state="disabled")
        self.batch_status.configure(text="Input cleared.", fg=MUTED)
        self.value_entry.focus_set()

    def copy_result(self):
        if self.last_result is None:
            self.status.configure(text="Enter a valid value to copy the result.", fg=BAD)
            return
        _, converted, _, destination = self.last_result
        self.clipboard_clear()
        self.clipboard_append(f"{converted:.12g} {destination}")
        self.status.configure(text="Result copied to clipboard.", fg=GOOD)

    def clear_history(self):
        self.history.clear()
        self.history_list.delete(0, "end")

    def export_history(self):
        if not self.history:
            messagebox.showinfo("No history", "Convert a measurement before exporting.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")],
                                            initialfile="measurekit_history.csv")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Time", "Category", "Input", "From unit",
                                 "Output", "To unit", "Mode"])
                for row in self.history:
                    writer.writerow(row)
            self.status.configure(text="Session history exported to CSV.", fg=GOOD)
        except OSError as error:
            messagebox.showerror("Export failed", f"Could not save the CSV: {error}")


if __name__ == "__main__":
    app = ConverterApp()
    app.mainloop()  # The event loop lets users convert repeatedly until they quit.
