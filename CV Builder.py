# cv_builder_app.py  —  FIXED VERSION

import customtkinter as ctk
from tkinter import filedialog, messagebox, StringVar
import tkinter as tk
from tkcalendar import DateEntry
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import sys
from datetime import datetime
from PIL import Image as PILImage, ImageTk, ImageDraw
import io

# ─────────────────────────────────────────────
# App Theme Configuration
# ─────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT       = "#4F8EF7"
ACCENT_DARK  = "#2563EB"
BG_DARK      = "#0F1117"
BG_CARD      = "#1A1D27"
BG_SECTION   = "#141720"
TEXT_PRIMARY = "#F1F5F9"
TEXT_MUTED   = "#94A3B8"
BORDER_COLOR = "#2D3348"
SUCCESS      = "#22C55E"
DANGER       = "#EF4444"

PREDEFINED_OBJECTIVES = [
    "Custom (type below)...",
    "Seeking a challenging position to leverage my technical expertise and contribute meaningfully to organizational growth.",
    "Motivated professional seeking to apply my skills in a dynamic environment that fosters innovation and professional development.",
    "To obtain a position that allows me to utilize my educational background and experience to contribute to team success.",
    "Results-driven individual looking to join a forward-thinking company where I can make significant contributions.",
    "Dedicated professional aiming to bring strong problem-solving and leadership skills to a growth-oriented organization.",
    "To pursue a rewarding career in my field while continuously developing my abilities and delivering outstanding results.",
    "Passionate about leveraging my background to drive impactful solutions and grow within a collaborative team environment.",
]

# ─────────────────────────────────────────────
# Helper Widgets
# ─────────────────────────────────────────────

class SectionCard(ctk.CTkFrame):
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent,
                         fg_color=BG_CARD,
                         corner_radius=12,
                         border_width=1,
                         border_color=BORDER_COLOR,
                         **kwargs)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 4))

        accent_bar = ctk.CTkFrame(header, width=4, height=22,
                                  fg_color=ACCENT, corner_radius=2)
        accent_bar.pack(side="left", padx=(0, 10))
        accent_bar.pack_propagate(False)

        ctk.CTkLabel(header, text=title,
                     font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        sep = ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR)
        sep.pack(fill="x", padx=20, pady=(4, 12))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=20, pady=(0, 16))


def make_label(parent, text, required=False):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(anchor="w", pady=(6, 1))
    ctk.CTkLabel(frame,
                 text=text,
                 font=ctk.CTkFont(family="Segoe UI", size=12),
                 text_color=TEXT_MUTED).pack(side="left")
    if required:
        ctk.CTkLabel(frame, text=" *",
                     font=ctk.CTkFont(size=12),
                     text_color=DANGER).pack(side="left")


def make_entry(parent, placeholder="", width=400, textvariable=None):
    return ctk.CTkEntry(parent,
                        placeholder_text=placeholder,
                        width=width,
                        height=36,
                        fg_color="#0F1117",
                        border_color=BORDER_COLOR,
                        text_color=TEXT_PRIMARY,
                        placeholder_text_color=TEXT_MUTED,
                        corner_radius=8,
                        textvariable=textvariable)


def make_textbox(parent, height=80, width=400):
    return ctk.CTkTextbox(parent,
                          height=height,
                          width=width,
                          fg_color="#0F1117",
                          border_color=BORDER_COLOR,
                          text_color=TEXT_PRIMARY,
                          corner_radius=8,
                          border_width=1)


def primary_btn(parent, text, command, width=140, color=ACCENT):
    return ctk.CTkButton(parent,
                         text=text,
                         command=command,
                         width=width,
                         height=36,
                         fg_color=color,
                         hover_color=ACCENT_DARK,
                         corner_radius=8,
                         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                         text_color="white")


def ghost_btn(parent, text, command, width=110):
    return ctk.CTkButton(parent,
                         text=text,
                         command=command,
                         width=width,
                         height=30,
                         fg_color="transparent",
                         hover_color=BG_SECTION,
                         border_width=1,
                         border_color=BORDER_COLOR,
                         corner_radius=7,
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color=TEXT_MUTED)


def make_date_entry(parent):
    """
    FIX: Use lowercase 'mm/dd/yyyy' — the only pattern tkcalendar
    reliably accepts cross-platform. We display only month/year in
    labels but store the full date object.
    """
    return DateEntry(
        parent,
        width=13,
        date_pattern="mm/dd/yyyy",   # <-- FIXED: was "MM/yyyy"
        showweeknumbers=False,
        showothermonthdays=False,
        background="#1A1D27",
        foreground="white",
        headersbackground="#1e3a8a",
        headersforeground="white",
        selectbackground="#4F8EF7",
        selectforeground="white",
        normalbackground="#0F1117",
        normalforeground="#F1F5F9",
        weekendbackground="#141720",
        weekendforeground="#94A3B8",
        bordercolor="#2D3348",
        borderwidth=1,
    )


def format_date_display(date_entry_widget):
    """Return a readable 'Mon YYYY' string from a DateEntry widget."""
    try:
        d = date_entry_widget.get_date()
        return d.strftime("%b %Y")          # e.g. "Jan 2022"
    except Exception:
        return date_entry_widget.get()


# ─────────────────────────────────────────────
# Dynamic Entry Row — Education
# ─────────────────────────────────────────────

class EducationEntry(ctk.CTkFrame):
    def __init__(self, parent, on_remove, index, **kwargs):
        super().__init__(parent, fg_color=BG_SECTION,
                         corner_radius=8, border_width=1,
                         border_color=BORDER_COLOR, **kwargs)
        self.on_remove = on_remove
        self.index     = index
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(top,
                     text=f"Education #{self.index}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        ghost_btn(top, "Remove", self._remove, width=80).pack(side="right")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 10))

        # Row 1 — degree / institution / grade
        r1 = ctk.CTkFrame(grid, fg_color="transparent")
        r1.pack(fill="x", pady=3)
        self.degree      = make_entry(r1, "Degree / Qualification", width=220)
        self.degree.pack(side="left", padx=(0, 8))
        self.institution = make_entry(r1, "Institution / University", width=220)
        self.institution.pack(side="left", padx=(0, 8))
        self.grade       = make_entry(r1, "Grade / GPA", width=120)
        self.grade.pack(side="left")

        # Row 2 — date pickers   *** FIXED HERE ***
        r2 = ctk.CTkFrame(grid, fg_color="transparent")
        r2.pack(fill="x", pady=3)

        ctk.CTkLabel(r2, text="From:", text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
        self.date_from = make_date_entry(r2)          # FIXED
        self.date_from.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(r2, text="To:", text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
        self.date_to = make_date_entry(r2)            # FIXED
        self.date_to.pack(side="left", padx=(0, 16))

        self.current_var = tk.BooleanVar()
        ctk.CTkCheckBox(r2, text="Present / Ongoing",
                        variable=self.current_var,
                        text_color=TEXT_MUTED,
                        fg_color=ACCENT,
                        font=ctk.CTkFont(size=11)).pack(side="left")

    def _remove(self):
        self.on_remove(self)

    def get_data(self):
        return {
            "degree":      self.degree.get().strip(),
            "institution": self.institution.get().strip(),
            "grade":       self.grade.get().strip(),
            "from":        format_date_display(self.date_from),
            "to":          "Present" if self.current_var.get()
                           else format_date_display(self.date_to),
        }


# ─────────────────────────────────────────────
# Dynamic Entry Row — Experience
# ─────────────────────────────────────────────

class ExperienceEntry(ctk.CTkFrame):
    def __init__(self, parent, on_remove, index, **kwargs):
        super().__init__(parent, fg_color=BG_SECTION,
                         corner_radius=8, border_width=1,
                         border_color=BORDER_COLOR, **kwargs)
        self.on_remove = on_remove
        self.index     = index
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(top, text=f"Experience #{self.index}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        ghost_btn(top, "Remove", self._remove, width=80).pack(side="right")

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=(0, 10))

        r1 = ctk.CTkFrame(grid, fg_color="transparent")
        r1.pack(fill="x", pady=3)
        self.title    = make_entry(r1, "Job Title / Role", width=220)
        self.title.pack(side="left", padx=(0, 8))
        self.company  = make_entry(r1, "Company / Organization", width=220)
        self.company.pack(side="left", padx=(0, 8))
        self.location = make_entry(r1, "Location", width=130)
        self.location.pack(side="left")

        # Row 2 — date pickers   *** FIXED HERE ***
        r2 = ctk.CTkFrame(grid, fg_color="transparent")
        r2.pack(fill="x", pady=3)

        ctk.CTkLabel(r2, text="From:", text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
        self.date_from = make_date_entry(r2)          # FIXED
        self.date_from.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(r2, text="To:", text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
        self.date_to = make_date_entry(r2)            # FIXED
        self.date_to.pack(side="left", padx=(0, 16))

        self.current_var = tk.BooleanVar()
        ctk.CTkCheckBox(r2, text="Currently working here",
                        variable=self.current_var,
                        text_color=TEXT_MUTED, fg_color=ACCENT,
                        font=ctk.CTkFont(size=11)).pack(side="left")

        ctk.CTkLabel(grid, text="Responsibilities / Description:",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(4, 2))
        self.desc = make_textbox(grid, height=70, width=590)
        self.desc.pack(fill="x", pady=(0, 2))

    def _remove(self):
        self.on_remove(self)

    def get_data(self):
        return {
            "title":    self.title.get().strip(),
            "company":  self.company.get().strip(),
            "location": self.location.get().strip(),
            "from":     format_date_display(self.date_from),
            "to":       "Present" if self.current_var.get()
                        else format_date_display(self.date_to),
            "desc":     self.desc.get("1.0", "end").strip(),
        }


# ─────────────────────────────────────────────
# Dynamic Entry Row — Certificate
# ─────────────────────────────────────────────

class CertificateEntry(ctk.CTkFrame):
    def __init__(self, parent, on_remove, index, **kwargs):
        super().__init__(parent, fg_color=BG_SECTION,
                         corner_radius=8, border_width=1,
                         border_color=BORDER_COLOR, **kwargs)
        self.on_remove = on_remove
        self.index     = index
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(top, text=f"Certificate #{self.index}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        ghost_btn(top, "Remove", self._remove, width=80).pack(side="right")

        r = ctk.CTkFrame(self, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=(0, 10))

        self.name   = make_entry(r, "Certificate Name", width=230)
        self.name.pack(side="left", padx=(0, 8))
        self.issuer = make_entry(r, "Issuing Organization", width=200)
        self.issuer.pack(side="left", padx=(0, 8))

        ctk.CTkLabel(r, text="Date:", text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 4))
        self.date = make_date_entry(r)                # FIXED
        self.date.pack(side="left")

    def _remove(self):
        self.on_remove(self)

    def get_data(self):
        return {
            "name":   self.name.get().strip(),
            "issuer": self.issuer.get().strip(),
            "date":   format_date_display(self.date),
        }


# ─────────────────────────────────────────────
# Dynamic Entry Row — Language
# ─────────────────────────────────────────────

class LanguageEntry(ctk.CTkFrame):
    def __init__(self, parent, on_remove, index, **kwargs):
        super().__init__(parent, fg_color=BG_SECTION,
                         corner_radius=8, border_width=1,
                         border_color=BORDER_COLOR, **kwargs)
        self.on_remove = on_remove
        self.index     = index
        self._build()

    def _build(self):
        r = ctk.CTkFrame(self, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(r, text=f"#{self.index}", text_color=ACCENT,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     width=25).pack(side="left")
        self.lang = make_entry(r, "Language (e.g. English)", width=200)
        self.lang.pack(side="left", padx=(4, 8))

        ctk.CTkLabel(r, text="Level:", text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))
        self.level = ctk.CTkOptionMenu(r,
                                       values=["Native", "Fluent", "Advanced",
                                               "Intermediate", "Basic", "Elementary"],
                                       width=140, height=32,
                                       fg_color="#0F1117",
                                       button_color=ACCENT,
                                       dropdown_fg_color=BG_CARD,
                                       text_color=TEXT_PRIMARY,
                                       corner_radius=8)
        self.level.pack(side="left", padx=(0, 8))
        ghost_btn(r, "Remove", self._remove, width=80).pack(side="left")

    def _remove(self):
        self.on_remove(self)

    def get_data(self):
        return {
            "language": self.lang.get().strip(),
            "level":    self.level.get(),
        }


# ─────────────────────────────────────────────
# Dynamic Entry Row — Skill
# ─────────────────────────────────────────────

class SkillEntry(ctk.CTkFrame):
    def __init__(self, parent, on_remove, index, **kwargs):
        super().__init__(parent, fg_color=BG_SECTION,
                         corner_radius=8, border_width=1,
                         border_color=BORDER_COLOR, **kwargs)
        self.on_remove = on_remove
        self.index     = index
        self._build()

    def _build(self):
        r = ctk.CTkFrame(self, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(r, text=f"#{self.index}", text_color=ACCENT,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     width=25).pack(side="left")
        self.skill = make_entry(r, "Skill (e.g. Python, Photoshop...)", width=240)
        self.skill.pack(side="left", padx=(4, 8))

        ctk.CTkLabel(r, text="Proficiency:", text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=(0, 6))
        self.level = ctk.CTkOptionMenu(r,
                                       values=["Expert", "Advanced",
                                               "Intermediate", "Beginner"],
                                       width=130, height=32,
                                       fg_color="#0F1117",
                                       button_color=ACCENT,
                                       dropdown_fg_color=BG_CARD,
                                       text_color=TEXT_PRIMARY,
                                       corner_radius=8)
        self.level.pack(side="left", padx=(0, 8))
        ghost_btn(r, "Remove", self._remove, width=80).pack(side="left")

    def _remove(self):
        self.on_remove(self)

    def get_data(self):
        return {
            "skill": self.skill.get().strip(),
            "level": self.level.get(),
        }


# ─────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────

class CVBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CV Builder v1.0.0")
        self.geometry("900x780")
        self.minsize(820, 600)
        self.configure(fg_color=BG_DARK)

        self.photo_path          = None
        self.photo_preview       = None
        self.education_entries   = []
        self.experience_entries  = []
        self.certificate_entries = []
        self.language_entries    = []
        self.skill_entries       = []

        self._build_ui()

    # ── UI Construction ──────────────────────────
    def _build_ui(self):
        # Header bar
        header = ctk.CTkFrame(self, fg_color=BG_CARD, height=60,
                              corner_radius=0, border_width=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=24)

        icon_box = ctk.CTkFrame(logo_frame, width=36, height=36,
                                fg_color=ACCENT, corner_radius=8)
        icon_box.pack(side="left", padx=(0, 10))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="CV",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="white").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(logo_frame, text="CV Builder",
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        ctk.CTkLabel(header,
                     text="Fill in your information and generate a professional PDF resume\n---Designed and Developed by Najam Awan---",
                     font=ctk.CTkFont(family="Segoe UI", size=11),
                     text_color=TEXT_MUTED).pack(side="left", padx=20)

        ctk.CTkButton(header,
                      text="Generate PDF",
                      command=self._generate_pdf,
                      width=160, height=38,
                      fg_color=SUCCESS,
                      hover_color="#16A34A",
                      corner_radius=8,
                      font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                      text_color="white").pack(side="right", padx=24)

        # Scrollable content
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG_DARK,
            scrollbar_button_color=ACCENT,
            scrollbar_button_hover_color=ACCENT_DARK
        )
        self.scroll.pack(fill="both", expand=True)

        container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_personal_section(container)
        self._build_objective_section(container)
        self._build_education_section(container)
        self._build_experience_section(container)
        self._build_certificate_section(container)
        self._build_languages_section(container)
        self._build_skills_section(container)

        # Bottom generate button
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 8))
        ctk.CTkButton(btn_frame,
                      text="Generate CV as PDF",
                      command=self._generate_pdf,
                      width=260, height=48,
                      fg_color=SUCCESS,
                      hover_color="#16A34A",
                      corner_radius=10,
                      font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                      text_color="white").pack(anchor="center")

    # ── Personal Info ────────────────────────────
    def _build_personal_section(self, parent):
        card = SectionCard(parent, "Personal Information")
        card.pack(fill="x", pady=(0, 16))
        body = card.content

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x")

        # Photo panel
        photo_panel = ctk.CTkFrame(row, fg_color="transparent", width=150)
        photo_panel.pack(side="left", padx=(0, 24))
        photo_panel.pack_propagate(False)

        self.photo_label = ctk.CTkLabel(
            photo_panel, text="No\nPhoto",
            width=150, height=150,
            fg_color=BG_SECTION,
            corner_radius=5,
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED
        )
        self.photo_label.pack(pady=(0, 8))
        primary_btn(photo_panel, "Upload Photo",
                    self._upload_photo, width=110).pack()

        # Fields
        fields = ctk.CTkFrame(row, fg_color="transparent")
        fields.pack(side="left", fill="both", expand=True)

        # Full Name
        r1 = ctk.CTkFrame(fields, fg_color="transparent")
        r1.pack(fill="x", pady=(0, 6))
        make_label(r1, "Full Name", required=True)
        self.name_entry = make_entry(r1, "Enter your name", width=400)
        self.name_entry.pack(anchor="w")

        # Phone + Email
        r2 = ctk.CTkFrame(fields, fg_color="transparent")
        r2.pack(fill="x", pady=(0, 6))
        c1 = ctk.CTkFrame(r2, fg_color="transparent")
        c1.pack(side="left", padx=(0, 16))
        make_label(c1, "Mobile / Phone", required=True)
        self.phone_entry = make_entry(c1, "Enter Mobile No", width=190)
        self.phone_entry.pack(anchor="w")

        c2 = ctk.CTkFrame(r2, fg_color="transparent")
        c2.pack(side="left")
        make_label(c2, "Email Address", required=True)
        self.email_entry = make_entry(c2, "you@example.com", width=220)
        self.email_entry.pack(anchor="w")

        # Address + Headline
        r3 = ctk.CTkFrame(fields, fg_color="transparent")
        r3.pack(fill="x", pady=(0, 6))
        c3 = ctk.CTkFrame(r3, fg_color="transparent")
        c3.pack(side="left", padx=(0, 16))
        make_label(c3, "Address / Location")
        self.address_entry = make_entry(c3, "City, Country", width=190)
        self.address_entry.pack(anchor="w")

        c4 = ctk.CTkFrame(r3, fg_color="transparent")
        c4.pack(side="left")
        make_label(c4, "Job Title / Headline")
        self.headline_entry = make_entry(c4, "Enter your Job Title", width=220)
        self.headline_entry.pack(anchor="w")

        # LinkedIn + Website
        r4 = ctk.CTkFrame(fields, fg_color="transparent")
        r4.pack(fill="x", pady=(0, 2))
        c5 = ctk.CTkFrame(r4, fg_color="transparent")
        c5.pack(side="left", padx=(0, 16))
        make_label(c5, "LinkedIn (optional)")
        self.linkedin_entry = make_entry(c5, "linkedin.com/in/username", width=190)
        self.linkedin_entry.pack(anchor="w")

        c6 = ctk.CTkFrame(r4, fg_color="transparent")
        c6.pack(side="left")
        make_label(c6, "Website / Portfolio (optional)")
        self.website_entry = make_entry(c6, "yourportfolio.com", width=220)
        self.website_entry.pack(anchor="w")

    # ── Objective ────────────────────────────────
    def _build_objective_section(self, parent):
        card = SectionCard(parent, "Career Objective / Summary")
        card.pack(fill="x", pady=(0, 16))
        body = card.content

        make_label(body, "Select a predefined objective or write your own:")
        self.obj_var = StringVar(value=PREDEFINED_OBJECTIVES[0])
        ctk.CTkOptionMenu(body,
                          variable=self.obj_var,
                          values=PREDEFINED_OBJECTIVES,
                          width=600, height=36,
                          fg_color="#0F1117",
                          button_color=ACCENT,
                          dropdown_fg_color=BG_CARD,
                          text_color=TEXT_PRIMARY,
                          corner_radius=8,
                          command=self._on_objective_select).pack(anchor="w", pady=(0, 8))

        make_label(body, "Custom Objective (edit or type here):")
        self.objective_box = make_textbox(body, height=80, width=600)
        self.objective_box.pack(anchor="w")
        self.objective_box.insert(
            "1.0",
            "Seeking a challenging position to leverage my technical expertise "
            "and contribute meaningfully to organizational growth."
        )

    def _on_objective_select(self, value):
        if value != PREDEFINED_OBJECTIVES[0]:
            self.objective_box.delete("1.0", "end")
            self.objective_box.insert("1.0", value)

    # ── Education ────────────────────────────────
    def _build_education_section(self, parent):
        card = SectionCard(parent, "Education")
        card.pack(fill="x", pady=(0, 16))
        self.edu_container = card.content

        btn_row = ctk.CTkFrame(self.edu_container, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        primary_btn(btn_row, "+ Add Education",
                    self._add_education, width=160).pack(side="left")
        ctk.CTkLabel(btn_row,
                     text="Click to add each educational qualification",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont(size=11)).pack(side="left", padx=12)

        self.edu_list_frame = ctk.CTkFrame(self.edu_container, fg_color="transparent")
        self.edu_list_frame.pack(fill="x")
        self._add_education()

    def _add_education(self):
        idx   = len(self.education_entries) + 1
        entry = EducationEntry(self.edu_list_frame,
                               on_remove=self._remove_education,
                               index=idx)
        entry.pack(fill="x", pady=(0, 8))
        self.education_entries.append(entry)

    def _remove_education(self, widget):
        if len(self.education_entries) <= 1:
            messagebox.showwarning("Warning",
                                   "At least one education entry is required.")
            return
        self.education_entries.remove(widget)
        widget.destroy()

    # ── Experience ───────────────────────────────
    def _build_experience_section(self, parent):
        card = SectionCard(parent, "Work Experience")
        card.pack(fill="x", pady=(0, 16))
        body = card.content

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        primary_btn(btn_row, "+ Add Experience",
                    self._add_experience, width=165).pack(side="left")

        self.exp_list_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.exp_list_frame.pack(fill="x")

    def _add_experience(self):
        idx   = len(self.experience_entries) + 1
        entry = ExperienceEntry(self.exp_list_frame,
                                on_remove=self._remove_experience,
                                index=idx)
        entry.pack(fill="x", pady=(0, 8))
        self.experience_entries.append(entry)

    def _remove_experience(self, widget):
        self.experience_entries.remove(widget)
        widget.destroy()

    # ── Certificates ─────────────────────────────
    def _build_certificate_section(self, parent):
        card = SectionCard(parent, "Certificates & Courses")
        card.pack(fill="x", pady=(0, 16))
        body = card.content

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        primary_btn(btn_row, "+ Add Certificate",
                    self._add_certificate, width=165).pack(side="left")

        self.cert_list_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.cert_list_frame.pack(fill="x")

    def _add_certificate(self):
        idx   = len(self.certificate_entries) + 1
        entry = CertificateEntry(self.cert_list_frame,
                                 on_remove=self._remove_certificate,
                                 index=idx)
        entry.pack(fill="x", pady=(0, 8))
        self.certificate_entries.append(entry)

    def _remove_certificate(self, widget):
        self.certificate_entries.remove(widget)
        widget.destroy()

    # ── Languages ────────────────────────────────
    def _build_languages_section(self, parent):
        card = SectionCard(parent, "Languages")
        card.pack(fill="x", pady=(0, 16))
        body = card.content

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        primary_btn(btn_row, "+ Add Language",
                    self._add_language, width=155).pack(side="left")

        self.lang_list_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.lang_list_frame.pack(fill="x")
        self._add_language()

    def _add_language(self):
        idx   = len(self.language_entries) + 1
        entry = LanguageEntry(self.lang_list_frame,
                              on_remove=self._remove_language,
                              index=idx)
        entry.pack(fill="x", pady=(0, 6))
        self.language_entries.append(entry)

    def _remove_language(self, widget):
        self.language_entries.remove(widget)
        widget.destroy()

    # ── Skills ───────────────────────────────────
    def _build_skills_section(self, parent):
        card = SectionCard(parent, "Skills")
        card.pack(fill="x", pady=(0, 16))
        body = card.content

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 8))
        primary_btn(btn_row, "+ Add Skill",
                    self._add_skill, width=140).pack(side="left")

        self.skill_list_frame = ctk.CTkFrame(body, fg_color="transparent")
        self.skill_list_frame.pack(fill="x")
        self._add_skill()

    def _add_skill(self):
        idx   = len(self.skill_entries) + 1
        entry = SkillEntry(self.skill_list_frame,
                           on_remove=self._remove_skill,
                           index=idx)
        entry.pack(fill="x", pady=(0, 6))
        self.skill_entries.append(entry)

    def _remove_skill(self, widget):
        self.skill_entries.remove(widget)
        widget.destroy()

    # ── Photo Upload ─────────────────────────────
    def _upload_photo(self):
        path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image files",
                        "*.jpg *.jpeg *.png *.bmp *.gif *.webp")]
        )
        if not path:
            return
        self.photo_path = path
        try:
            img  = PILImage.open(path).convert("RGBA")
            size = (110, 110)
            img  = img.resize(size, PILImage.LANCZOS)

            # Circular crop
            mask   = PILImage.new("L", size, 0)
            draw   = ImageDraw.Draw(mask)
            draw.ellipse([0, 0, size[0], size[1]], fill=255)
            output = PILImage.new("RGBA", size, (0, 0, 0, 0))
            output.paste(img, (0, 0), mask)

            self.photo_preview = ImageTk.PhotoImage(output)
            self.photo_label.configure(
                image=self.photo_preview,
                text="",
                fg_color="transparent"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Could not load image:\n{e}")

    # ── Data Collection ──────────────────────────
    def _collect_data(self):
        return {
            "name":         self.name_entry.get().strip(),
            "phone":        self.phone_entry.get().strip(),
            "email":        self.email_entry.get().strip(),
            "address":      self.address_entry.get().strip(),
            "headline":     self.headline_entry.get().strip(),
            "linkedin":     self.linkedin_entry.get().strip(),
            "website":      self.website_entry.get().strip(),
            "photo":        self.photo_path,
            "objective":    self.objective_box.get("1.0", "end").strip(),
            "education":    [e.get_data() for e in self.education_entries],
            "experience":   [e.get_data() for e in self.experience_entries],
            "certificates": [e.get_data() for e in self.certificate_entries],
            "languages":    [e.get_data() for e in self.language_entries],
            "skills":       [e.get_data() for e in self.skill_entries],
        }

    def _validate(self, data):
        errors = []
        if not data["name"]:
            errors.append("Full Name is required.")
        if not data["phone"]:
            errors.append("Mobile / Phone is required.")
        if not data["email"]:
            errors.append("Email Address is required.")
        return errors

    # ── PDF Generation ───────────────────────────
    def _generate_pdf(self):
        data   = self._collect_data()
        errors = self._validate(data)
        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=(
                f"{data['name'].replace(' ', '_')}_CV.pdf"
                if data["name"] else "CV.pdf"
            ),
            title="Save CV as PDF",
        )
        if not save_path:
            return

        try:
            self._build_pdf(data, save_path)
            messagebox.showinfo(
                "Success",
                f"CV successfully generated!\n\nSaved to:\n{save_path}"
            )
            if sys.platform.startswith("win"):
                os.startfile(save_path)
            elif sys.platform == "darwin":
                os.system(f"open '{save_path}'")
            else:
                os.system(f"xdg-open '{save_path}'")
        except Exception as e:
            messagebox.showerror("PDF Error", f"Failed to generate PDF:\n{e}")

    # ── PDF Builder ──────────────────────────────
    def _build_pdf(self, data, path):
        from reportlab.platypus.frames import Frame
        from reportlab.platypus import BaseDocTemplate, PageTemplate, FrameBreak

        PAGE_W, PAGE_H = A4
        SIDEBAR_W = 62 * mm
        HDR_H     = 50 * mm
        MARGIN_B  = 10 * mm
        SIDE_PAD  = 5  * mm
        MAIN_PAD  = 8  * mm
        MAIN_W    = PAGE_W - SIDEBAR_W - MAIN_PAD - 10 * mm
        MARGIN_T  = HDR_H + 5 * mm

        C_DARK   = colors.HexColor("#1A1D27")
        C_ACCENT = colors.HexColor("#4F8EF7")
        C_WHITE  = colors.white
        C_MUTED  = colors.HexColor("#94A3B8")
        C_NAVY   = colors.HexColor("#1e3a8a")
        C_BODY   = colors.HexColor("#374151")
        C_LIGHT  = colors.HexColor("#F1F5F9")
        C_SIDE_H = colors.HexColor("#bfdbfe")
        C_CONTACT= colors.HexColor("#dbeafe")
        C_BORDER = colors.HexColor("#334155")

        def S(name, fontName="Helvetica", size=10, color=colors.black,
              leading=14, align=TA_LEFT, sb=0, sa=2, li=0, bold=False):
            fn = f"{fontName}-Bold" if bold else fontName
            return ParagraphStyle(
                name, fontName=fn, fontSize=size,
                textColor=color, leading=leading,
                alignment=align, spaceBefore=sb,
                spaceAfter=sa, leftIndent=li
            )

        s_sec   = S("Sec",  bold=True, size=12, color=C_DARK,
                    leading=16, sb=8, sa=2)
        s_job   = S("Job",  bold=True, size=10, color=C_DARK,   leading=14)
        s_co    = S("Co",   size=9,    color=C_ACCENT,           leading=13)
        s_date  = S("Dt",   size=8,    color=C_MUTED,
                    leading=12, align=TA_RIGHT)
        s_body  = S("Bd",   size=9,    color=C_BODY,             leading=13)
        s_obj   = S("Ob",   size=10,   color=C_BODY,
                    leading=15, sa=4)
        s_sh    = S("Sh",   bold=True, size=10, color=C_WHITE,
                    leading=14, sb=8, sa=3)
        s_sb    = S("Sb",   bold=True, size=9,  color=C_ACCENT,  leading=13)
        s_sl    = S("Sl",   size=9,    color=C_LIGHT,            leading=13)

        # ── Sidebar content ──
        sidebar = []

        if any(e["skill"] for e in data["skills"]):
            sidebar.append(Paragraph("SKILLS", s_sh))
            sidebar.append(HRFlowable(width="100%", thickness=0.5,
                                      color=C_BORDER, spaceAfter=4))
            for sk in data["skills"]:
                if sk["skill"]:
                    sidebar.append(Paragraph(f"<b>{sk['skill']}</b>", s_sb))
                    sidebar.append(Paragraph(sk["level"], s_sl))
                    sidebar.append(Spacer(1, 2 * mm))

        if any(e["language"] for e in data["languages"]):
            sidebar.append(Paragraph("LANGUAGES", s_sh))
            sidebar.append(HRFlowable(width="100%", thickness=0.5,
                                      color=C_BORDER, spaceAfter=4))
            for la in data["languages"]:
                if la["language"]:
                    sidebar.append(Paragraph(f"<b>{la['language']}</b>", s_sb))
                    sidebar.append(Paragraph(la["level"], s_sl))
                    sidebar.append(Spacer(1, 2 * mm))

        if any(e["name"] for e in data["certificates"]):
            sidebar.append(Paragraph("CERTIFICATIONS", s_sh))
            sidebar.append(HRFlowable(width="100%", thickness=0.5,
                                      color=C_BORDER, spaceAfter=4))
            for cert in data["certificates"]:
                if cert["name"]:
                    sidebar.append(Paragraph(f"<b>{cert['name']}</b>", s_sb))
                    if cert["issuer"]:
                        sidebar.append(Paragraph(cert["issuer"], s_sl))
                    sidebar.append(Paragraph(cert["date"], s_sl))
                    sidebar.append(Spacer(1, 2 * mm))

        # ── Main content ──
        main = []

        if data["objective"]:
            main.append(Paragraph("OBJECTIVE", s_sec))
            main.append(HRFlowable(width="100%", thickness=1.5,
                                   color=C_ACCENT, spaceAfter=4))
            main.append(Paragraph(data["objective"], s_obj))
            main.append(Spacer(1, 4 * mm))

        edu_list = [e for e in data["education"]
                    if e["degree"] or e["institution"]]
        if edu_list:
            main.append(Paragraph("EDUCATION", s_sec))
            main.append(HRFlowable(width="100%", thickness=1.5,
                                   color=C_ACCENT, spaceAfter=4))
            for ed in edu_list:
                dur  = f"{ed['from']}  -  {ed['to']}"
                t    = Table(
                    [[Paragraph(ed["degree"], s_job),
                      Paragraph(dur, s_date)]],
                    colWidths=[MAIN_W * 0.65, MAIN_W * 0.35]
                )
                t.setStyle(TableStyle([
                    ("VALIGN",         (0,0),(-1,-1),"TOP"),
                    ("LEFTPADDING",    (0,0),(-1,-1), 0),
                    ("RIGHTPADDING",   (0,0),(-1,-1), 0),
                    ("TOPPADDING",     (0,0),(-1,-1), 0),
                    ("BOTTOMPADDING",  (0,0),(-1,-1), 1),
                ]))
                main.append(t)
                inst = ed["institution"]
                if ed["grade"]:
                    inst += f"  -  GPA: {ed['grade']}"
                main.append(Paragraph(inst, s_co))
                main.append(Spacer(1, 4 * mm))

        exp_list = [e for e in data["experience"]
                    if e["title"] or e["company"]]
        if exp_list:
            main.append(Paragraph("WORK EXPERIENCE", s_sec))
            main.append(HRFlowable(width="100%", thickness=1.5,
                                   color=C_ACCENT, spaceAfter=4))
            for ex in exp_list:
                dur = f"{ex['from']}  -  {ex['to']}"
                t   = Table(
                    [[Paragraph(ex["title"], s_job),
                      Paragraph(dur, s_date)]],
                    colWidths=[MAIN_W * 0.65, MAIN_W * 0.35]
                )
                t.setStyle(TableStyle([
                    ("VALIGN",        (0,0),(-1,-1),"TOP"),
                    ("LEFTPADDING",   (0,0),(-1,-1), 0),
                    ("RIGHTPADDING",  (0,0),(-1,-1), 0),
                    ("TOPPADDING",    (0,0),(-1,-1), 0),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 1),
                ]))
                main.append(t)
                loc = ex["company"]
                if ex["location"]:
                    loc += f"  |  {ex['location']}"
                main.append(Paragraph(loc, s_co))
                for line in ex["desc"].splitlines():
                    line = line.strip()
                    if line:
                        main.append(Paragraph(f"- {line}", s_body))
                main.append(Spacer(1, 4 * mm))

        # ── Two-column page template ──
        class TwoColDoc(BaseDocTemplate):
            def __init__(self, filename, cv_data, **kw):
                super().__init__(filename, **kw)
                self.cv_data = cv_data
                sidebar_frame = Frame(
                    SIDE_PAD, MARGIN_B,
                    SIDEBAR_W - 2 * SIDE_PAD,
                    PAGE_H - MARGIN_T - MARGIN_B,
                    leftPadding=4, rightPadding=4,
                    topPadding=4,  bottomPadding=4,
                    id="sidebar",
                )
                main_frame = Frame(
                    SIDEBAR_W + MAIN_PAD, MARGIN_B,
                    MAIN_W,
                    PAGE_H - MARGIN_T - MARGIN_B,
                    leftPadding=0, rightPadding=0,
                    topPadding=4,  bottomPadding=4,
                    id="main",
                )
                self.addPageTemplates([
                    PageTemplate(
                        id="TwoCols",
                        frames=[sidebar_frame, main_frame],
                        onPage=self._draw_bg,
                    )
                ])

            def _draw_bg(self, canvas, doc):
                cv = self.cv_data
                canvas.saveState()

                # Dark sidebar background
                canvas.setFillColor(C_DARK)
                canvas.rect(0, 0, SIDEBAR_W, PAGE_H, fill=1, stroke=0)

                # Blue header strip (full width)
                canvas.setFillColor(C_ACCENT)
                canvas.rect(0, PAGE_H - HDR_H, PAGE_W, HDR_H,
                            fill=1, stroke=0)

                # Navy overlay on sidebar header
                canvas.setFillColor(C_NAVY)
                canvas.rect(0, PAGE_H - HDR_H, SIDEBAR_W, HDR_H,
                            fill=1, stroke=0)

                # Photo
                photo = cv.get("photo")
                if photo and os.path.isfile(photo):
                    try:
                        pi = PILImage.open(photo).convert("RGB")
                        pi = pi.resize((80, 80), PILImage.LANCZOS)
                        from reportlab.lib.utils import ImageReader

                        img_reader = ImageReader(pi)

                        canvas.drawImage(img_reader,
                                         SIDE_PAD + 3 * mm,
                                         PAGE_H - HDR_H + 5 * mm,
                                         width=22 * mm, height=22 * mm,
                                         mask="auto")
                    except Exception:
                        pass

                # Name
                tx = SIDEBAR_W + MAIN_PAD
                canvas.setFont("Helvetica-Bold", 22)
                canvas.setFillColor(C_WHITE)
                canvas.drawString(tx, PAGE_H - 18 * mm,
                                  cv.get("name", ""))

                y = PAGE_H - 27 * mm
                if cv.get("headline"):
                    canvas.setFont("Helvetica", 10)
                    canvas.setFillColor(C_SIDE_H)
                    canvas.drawString(tx, y, cv["headline"])
                    y -= 9

                canvas.setFont("Helvetica", 8)
                canvas.setFillColor(C_CONTACT)
                parts = [p for p in [cv.get("phone"), cv.get("email"),
                                     cv.get("address")] if p]
                if parts:
                    canvas.drawString(tx, y - 3, "  |  ".join(parts))
                    y -= 9

                parts2 = [p for p in [cv.get("linkedin"),
                                      cv.get("website")] if p]
                if parts2:
                    canvas.drawString(tx, y - 3, "  |  ".join(parts2))

                canvas.restoreState()

        story = sidebar + [FrameBreak()] + main

        TwoColDoc(
            path,
            cv_data=data,
            pagesize=A4,
            leftMargin=0, rightMargin=0,
            topMargin=0,  bottomMargin=MARGIN_B,
        ).build(story)


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = CVBuilderApp()
    app.mainloop()
