#!/usr/bin/env python3
"""
WriteUp Studio Premium — Production-grade Streamlit app.
Architecture: Plugin-based, sector-organized, extensible, beautiful.
Deploy: streamlit run writeup_studio_premium.py
"""

# ═══════════════════════════════════════════════════════════════════════
# CORE ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import json
import random
import re
import uuid
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
    Any, Callable, Dict, List, Optional, Protocol, Type, TypedDict, Union
)
from copy import deepcopy

# ═══════════════════════════════════════════════════════════════════════
# DESIGN TOKENS & THEME
# ═══════════════════════════════════════════════════════════════════════

class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"

@dataclass(frozen=True)
class DesignTokens:
    # Colors
    bg_primary: str = "#0a0f1a"
    bg_secondary: str = "#111827"
    bg_tertiary: str = "#1e293b"
    bg_glass: str = "rgba(30, 41, 59, 0.7)"
    border_subtle: str = "rgba(148, 163, 184, 0.12)"
    border_strong: str = "rgba(148, 163, 184, 0.24)"
    fg_primary: str = "#f1f5f9"
    fg_secondary: str = "#94a3b8"
    fg_muted: str = "#64748b"
    accent_primary: str = "#22d3ee"      # cyan-400
    accent_secondary: str = "#a855f7"    # purple-500
    accent_tertiary: str = "#f472b6"     # pink-400
    success: str = "#22c55e"
    warning: str = "#fbbf24"
    error: str = "#ef4444"
    # Gradients
    grad_primary: str = "linear-gradient(135deg, #22d3ee 0%, #a855f7 100%)"
    grad_secondary: str = "linear-gradient(135deg, #a855f7 0%, #f472b6 100%)"
    grad_mesh: str = "radial-gradient(ellipse at 50% 0%, rgba(34, 211, 238, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 100% 100%, rgba(168, 85, 247, 0.15) 0%, transparent 50%)"
    # Spacing
    space_xs: str = "0.25rem"
    space_sm: str = "0.5rem"
    space_md: str = "1rem"
    space_lg: str = "1.5rem"
    space_xl: str = "2rem"
    space_2xl: str = "3rem"
    # Radius
    radius_sm: str = "6px"
    radius_md: str = "10px"
    radius_lg: str = "16px"
    radius_xl: str = "24px"
    radius_full: str = "9999px"
    # Shadows
    shadow_sm: str = "0 1px 2px rgba(0,0,0,0.3)"
    shadow_md: str = "0 4px 12px rgba(0,0,0,0.35)"
    shadow_lg: str = "0 12px 32px rgba(0,0,0,0.4)"
    shadow_glow: str = "0 0 32px rgba(34, 211, 238, 0.2)"
    # Typography
    font_sans: str = "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif"
    font_mono: str = "'JetBrains Mono', 'Fira Code', monospace"
    # Transitions
    transition_fast: str = "120ms cubic-bezier(0.4, 0, 0.2, 1)"
    transition_normal: str = "200ms cubic-bezier(0.4, 0, 0.2, 1)"
    transition_slow: str = "350ms cubic-bezier(0.4, 0, 0.2, 1)"
    # Z-index
    z_dropdown: int = 100
    z_modal: int = 200
    z_toast: int = 300
    z_tooltip: int = 400

TOKENS = DesignTokens()

# Light mode overrides
LIGHT_OVERRIDES = {
    "bg_primary": "#f8fafc",
    "bg_secondary": "#ffffff",
    "bg_tertiary": "#f1f5f9",
    "bg_glass": "rgba(255, 255, 255, 0.8)",
    "border_subtle": "rgba(15, 23, 42, 0.08)",
    "border_strong": "rgba(15, 23, 42, 0.12)",
    "fg_primary": "#0f172a",
    "fg_secondary": "#475569",
    "fg_muted": "#94a3b8",
    "shadow_sm": "0 1px 2px rgba(15,23,42,0.06)",
    "shadow_md": "0 4px 12px rgba(15,23,42,0.08)",
    "shadow_lg": "0 12px 32px rgba(15,23,42,0.12)",
    "grad_mesh": "radial-gradient(ellipse at 50% 0%, rgba(34, 211, 238, 0.08) 0%, transparent 50%), radial-gradient(ellipse at 100% 100%, rgba(168, 85, 247, 0.08) 0%, transparent 50%)",
}

# ═══════════════════════════════════════════════════════════════════════
# DOMAIN MODELS
# ═══════════════════════════════════════════════════════════════════════

class SectionType(Enum):
    OPENER = "opener"
    MIDDLE = "middle"
    CLOSER = "closer"
    EXTRA = "extra"

@dataclass
class VariableDef:
    key: str
    label: str
    default: str = ""
    placeholder: str = ""
    required: bool = True
    type: str = "text"  # text, textarea, select, multiselect, boolean, number
    options: List[str] = field(default_factory=list)
    help: str = ""
    validation: Optional[str] = None  # regex pattern
    group: str = "general"

@dataclass
class TemplatePart:
    id: str
    name: str
    content: str
    section: SectionType
    tags: List[str] = field(default_factory=list)
    weight: float = 1.0  # for weighted random selection
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StyleDef:
    name: str
    label: str
    description: str
    code: str  # lambda expression as string
    preview: str = ""
    category: str = "general"

@dataclass
class CategoryDef:
    key: str
    name: str
    description: str
    icon: str
    sector: str
    variables: List[VariableDef] = field(default_factory=list)
    parts: Dict[SectionType, List[TemplatePart]] = field(default_factory=dict)
    styles: List[StyleDef] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        for sec in SectionType:
            self.parts.setdefault(sec, [])

@dataclass
class SectorDef:
    key: str
    name: str
    description: str
    icon: str
    color: str
    gradient: str
    categories: List[str] = field(default_factory=list)  # category keys
    order: int = 0

@dataclass
class GenerationResult:
    text: str
    category_key: str
    style_name: str
    sections_used: List[SectionType]
    variables_used: Dict[str, str]
    template_ids: List[str]
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

# ═══════════════════════════════════════════════════════════════════════
# PLUGIN PROTOCOLS
# ═══════════════════════════════════════════════════════════════════════

class GeneratorPlugin(Protocol):
    name: str
    description: str
    def generate(self, category: CategoryDef, style: StyleDef, sections: List[SectionType], variables: Dict[str, str]) -> GenerationResult: ...

class ExporterPlugin(Protocol):
    name: str
    extension: str
    mime: str
    def export(self, result: GenerationResult, category: CategoryDef) -> bytes: ...

class TransformerPlugin(Protocol):
    name: str
    description: str
    def transform(self, text: str, context: Dict[str, Any]) -> str: ...

# ═══════════════════════════════════════════════════════════════════════
# BUILT-IN PLUGINS
# ═══════════════════════════════════════════════════════════════════════

class DefaultGenerator:
    name = "default"
    description = "Weighted random selection per section with variable interpolation"

    def generate(self, category: CategoryDef, style: StyleDef, sections: List[SectionType], variables: Dict[str, str]) -> GenerationResult:
        selected_parts = []
        template_ids = []
        
        for section in sections:
            parts = category.parts.get(section, [])
            if not parts:
                continue
            # Weighted random
            weights = [p.weight for p in parts]
            part = random.choices(parts, weights=weights, k=1)[0]
            selected_parts.append(part.content)
            template_ids.append(part.id)
        
        raw = " ".join(selected_parts)
        rendered = self._interpolate(raw, variables)
        styled = self._apply_style(rendered, style.code)
        
        return GenerationResult(
            text=styled,
            category_key=category.key,
            style_name=style.name,
            sections_used=sections,
            variables_used=variables,
            template_ids=template_ids,
        )

    def _interpolate(self, template: str, variables: Dict[str, str]) -> str:
        def repl(match):
            expr = match.group(1)
            if '.' in expr:
                key, method = expr.split('.', 1)
                val = variables.get(key, '')
                if hasattr(str, method) and callable(getattr(str, method)):
                    try:
                        return getattr(val, method)()
                    except Exception:
                        return val
                return val
            return variables.get(expr, match.group(0))
        return re.sub(r'\{(\w+(?:\.\w+)?)\}', repl, template)

    def _apply_style(self, text: str, style_code: str) -> str:
        try:
            # Safe eval with limited builtins
            safe_globals = {
                "__builtins__": {
                    "str": str, "len": len, "range": range, "enumerate": enumerate,
                    "zip": zip, "map": map, "filter": filter, "sum": sum,
                    "min": min, "max": max, "sorted": sorted, "reversed": reversed,
                    "any": any, "all": all, "isinstance": isinstance,
                }
            }
            func = eval(style_code, safe_globals, {})
            return func(text)
        except Exception:
            return text

class MarkdownExporter:
    name = "markdown"
    extension = "md"
    mime = "text/markdown"
    def export(self, result: GenerationResult, category: CategoryDef) -> bytes:
        content = f"""# {category.name} — Generated Content

**Style:** {result.style_name}  
**Category:** {category.name}  
**Generated:** {result.generated_at}  
**Sections:** {', '.join(s.value for s in result.sections_used)}

---

{result.text}

---

*Generated by WriteUp Studio Premium*
"""
        return content.encode()

class TextExporter:
    name = "text"
    extension = "txt"
    mime = "text/plain"
    def export(self, result: GenerationResult, category: CategoryDef) -> bytes:
        return result.text.encode()

class JSONExporter:
    name = "json"
    extension = "json"
    mime = "application/json"
    def export(self, result: GenerationResult, category: CategoryDef) -> bytes:
        data = {
            "result": asdict(result),
            "category": {
                "key": category.key,
                "name": category.name,
                "sector": category.sector,
            }
        }
        return json.dumps(data, indent=2, ensure_ascii=False).encode()

class HTMLExporter:
    name = "html"
    extension = "html"
    mime = "text/html"
    def export(self, result: GenerationResult, category: CategoryDef) -> bytes:
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{category.name} — WriteUp Studio</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.7; color: #1e293b; }}
        .meta {{ color: #64748b; font-size: 0.9rem; margin-bottom: 2rem; padding-bottom: 1rem; border-bottom: 1px solid #e2e8f0; }}
        .content {{ white-space: pre-wrap; }}
        .footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 0.85rem; text-align: center; }}
    </style>
</head>
<body>
    <div class="meta">
        <strong>Category:</strong> {category.name} | 
        <strong>Style:</strong> {result.style_name} | 
        <strong>Generated:</strong> {result.generated_at}
    </div>
    <div class="content">{result.text}</div>
    <div class="footer">Generated by WriteUp Studio Premium</div>
</body>
</html>"""
        return html.encode()

# ═══════════════════════════════════════════════════════════════════════
# REGISTRY & STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

class Registry:
    """Central registry for all plugins, sectors, categories."""
    
    def __init__(self):
        self.sectors: Dict[str, SectorDef] = {}
        self.categories: Dict[str, CategoryDef] = {}
        self.generators: Dict[str, GeneratorPlugin] = {"default": DefaultGenerator()}
        self.exporters: Dict[str, ExporterPlugin] = {
            "markdown": MarkdownExporter(),
            "text": TextExporter(),
            "json": JSONExporter(),
            "html": HTMLExporter(),
        }
        self.transformers: Dict[str, TransformerPlugin] = {}
        self._load_builtins()
    
    def _load_builtins(self):
        # Define sectors
        sectors = [
            SectorDef("personal", "Personal", "Dating, relationships, personal branding", "💖", "#ec4899", "linear-gradient(135deg, #ec4899 0%, #f472b6 100%)", order=1),
            SectorDef("professional", "Professional", "Career, business, networking, thought leadership", "💼", "#3b82f6", "linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)", order=2),
            SectorDef("creative", "Creative", "Writing, storytelling, content creation, art", "🎨", "#a855f7", "linear-gradient(135deg, #a855f7 0%, #d946ef 100%)", order=3),
            SectorDef("marketing", "Marketing", "Copywriting, ads, email, social media, growth", "📈", "#f59e0b", "linear-gradient(135deg, #f59e0b 0%, #f97316 100%)", order=4),
            SectorDef("technical", "Technical", "Documentation, API specs, changelogs, engineering", "⚙️", "#06b6d4", "linear-gradient(135deg, #06b6d4 0%, #22d3ee 100%)", order=5),
            SectorDef("academic", "Academic", "Research, papers, grants, citations, thesis", "🎓", "#84cc16", "linear-gradient(135deg, #84cc16 0%, #a3e635 100%)", order=6),
        ]
        for s in sectors:
            self.sectors[s.key] = s
        
        # Load categories (will populate sector.categories)
        for cat in self._build_default_categories():
            self.register_category(cat)
    
    def register_category(self, cat: CategoryDef):
        self.categories[cat.key] = cat
        if cat.sector in self.sectors:
            if cat.key not in self.sectors[cat.sector].categories:
                self.sectors[cat.sector].categories.append(cat.key)
    
    def get_category(self, key: str) -> Optional[CategoryDef]:
        return self.categories.get(key)
    
    def get_sector(self, key: str) -> Optional[SectorDef]:
        return self.sectors.get(key)
    
    def get_categories_by_sector(self, sector_key: str) -> List[CategoryDef]:
        sector = self.sectors.get(sector_key)
        if not sector:
            return []
        return [self.categories[k] for k in sector.categories if k in self.categories]
    
    def get_all_categories(self) -> List[CategoryDef]:
        return list(self.categories.values())
    
    def get_generator(self, name: str) -> GeneratorPlugin:
        return self.generators.get(name, self.generators["default"])
    
    def get_exporter(self, name: str) -> ExporterPlugin:
        return self.exporters.get(name, self.exporters["text"])
    
    # ═══════════════════════════════════════════════════════════════════════
    # BUILT-IN CATEGORIES (Rich, Real-World)
    # ═══════════════════════════════════════════════════════════════════════
    
    def _build_default_categories(self) -> List[CategoryDef]:
        return [
            # PERSONAL SECTOR
            self._cat_romance_dating(),
            self._cat_personal_bio(),
            self._cat_friendship_social(),
            
            # PROFESSIONAL SECTOR
            self._cat_linkedin_bio(),
            self._cat_elevator_pitch(),
            self._cat_cover_letter(),
            self._cat_freelance_profile(),
            
            # CREATIVE SECTOR
            self._cat_story_hook(),
            self._cat_character_sheet(),
            self._cat_worldbuilding(),
            self._cat_poetry_prompt(),
            
            # MARKETING SECTOR
            self._cat_ad_copy(),
            self._cat_email_sequence(),
            self._cat_landing_page(),
            self._cat_social_media(),
            self._cat_product_launch(),
            
            # TECHNICAL SECTOR
            self._cat_api_documentation(),
            self._cat_changelog(),
            self._cat_readme(),
            self._cat_technical_spec(),
            
            # ACADEMIC SECTOR
            self._cat_research_abstract(),
            self._cat_grant_proposal(),
            self._cat_literature_review(),
        ]
    
    # ─── Personal ───
    def _cat_romance_dating(self) -> CategoryDef:
        return CategoryDef(
            key="romance_dating",
            name="Dating Profile / Serious Relationship",
            description="Authentic bios for apps like Hinge, Bumble, or direct outreach. Focus on depth, values, and clear intent.",
            icon="💍",
            sector="personal",
            variables=[
                VariableDef("goal", "Relationship Goal", "a lifelong partner", placeholder="e.g. a wife, a husband, a partner for life", group="core"),
                VariableDef("values", "Core Values", "loyalty, growth, faith, family, honesty", placeholder="comma-separated", group="core"),
                VariableDef("vibe", "Daily Life Vibe", "morning coffee, evening walks, deep talks, shared silence", placeholder="what a typical day looks like", group="core"),
                VariableDef("past", "Past Chapter", "I've done the work. Therapy, growth, clarity. Ready for what's real.", placeholder="brief resolution statement", group="core"),
                VariableDef("non_negotiables", "Non-Negotiables", "monogamy, shared values, emotional maturity, kids someday", placeholder="dealbreakers", group="core"),
                VariableDef("cta", "Call to Action", "Message me if this resonates", placeholder="how they should reach out", group="contact"),
                VariableDef("platform", "Platform", "Hinge", options=["Hinge", "Bumble", "Tinder", "Direct Message", "Other"], type="select", group="contact"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Direct & Clear", "I'm not here for options. I'm here for {goal}.", SectionType.OPENER, weight=1.2, tags=["direct"]),
                    TemplatePart("o2", "Values-First", "Looking for {goal} who shares my values: {values}.", SectionType.OPENER, weight=1.0, tags=["values"]),
                    TemplatePart("o3", "Story Opener", "Spent years figuring out who I am and what I want. Now I know: {goal}.", SectionType.OPENER, weight=0.9, tags=["story"]),
                    TemplatePart("o4", "Vibe Check", "My life: {vibe}. Missing one piece: {goal}.", SectionType.OPENER, weight=1.0, tags=["vibe"]),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "The Vision", "I want {vibe}. Building a life where {values} aren't just words — they're how we operate.", SectionType.MIDDLE, weight=1.1, tags=["vision"]),
                    TemplatePart("m2", "Standards", "Non-negotiable: {non_negotiables}. Everything else is negotiable.", SectionType.MIDDLE, weight=1.0, tags=["standards"]),
                    TemplatePart("m3", "Growth", "{past} We grow together or we don't grow at all.", SectionType.MIDDLE, weight=0.9, tags=["growth"]),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Direct CTA", "{cta}. No games. Just honesty.", SectionType.CLOSER, weight=1.2, tags=["direct"]),
                    TemplatePart("c2", "Platform Specific", "On {platform.lower()}? Like or comment. Off it? {cta.lower()}.", SectionType.CLOSER, weight=0.8, tags=["platform"]),
                    TemplatePart("c3", "Open Door", "If you read this far, we already have something in common. {cta}.", SectionType.CLOSER, weight=1.0, tags=["warm"]),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Photo Note", "Photos: recent, unfiltered, doing things I love.", SectionType.EXTRA, weight=0.7, tags=["photos"]),
                    TemplatePart("e2", "Voice Note", "Voice note > text. Let's skip the pen-pal phase.", SectionType.EXTRA, weight=0.6, tags=["voice"]),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Minimal, no formatting", "lambda t: t"),
                StyleDef("hinge", "Hinge Style", "Prompt/answer format", "lambda t: '\\n\\n'.join([f'📍 {p.strip()}' for p in t.split('. ') if p.strip()])"),
                StyleDef("bumble", "Bumble Bio", "Short, punchy, emoji-friendly", "lambda t: t.replace('. ', '. ').replace(', ', ', ')[:300] + ' ✨'"),
                StyleDef("vulnerable", "Vulnerable", "Line breaks for breathing room", "lambda t: t.replace('. ', '.\\n\\n').replace(', ', ', ').replace('I want', '💭 I want')"),
            ],
        )
    
    def _cat_personal_bio(self) -> CategoryDef:
        return CategoryDef(
            key="personal_bio",
            name="Personal Bio / About Me",
            description: "For personal websites, Instagram, Twitter/X, newsletters. Your story in your voice.",
            icon="📖",
            sector="personal",
            variables=[
                VariableDef("name", "Name", "Alex", group="identity"),
                VariableDef("identity", "How you describe yourself", "builder, writer, curious human", placeholder="comma-separated identities", group="identity"),
                VariableDef("mission", "Mission / North Star", "Help people build meaningful things", group="core"),
                VariableDef("journey", "Journey highlight", "From corporate burnout to indie founder. 3 exits, 12 failures, infinite lessons.", group="story"),
                VariableDef("current_focus", "Current Focus", "Building WriteUp Studio. Writing weekly. Learning piano.", group="now"),
                VariableDef("values", "Values", "curiosity, craft, kindness, autonomy", group="core"),
                VariableDef("fun_fact", "Fun Fact", "Once hitchhiked across Iceland in winter.", group="personal"),
                VariableDef("cta", "Connect", "Reply to my newsletter — I read everything", group="contact"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Identity Stack", "{name}. {identity}.", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Mission-Led", "{mission}. I'm {name}, {identity}.", SectionType.OPENER, weight=1.0),
                    TemplatePart("o3", "Story Hook", "{journey} Now: {current_focus}.", SectionType.OPENER, weight=1.1),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Values in Action", "I optimize for {values}. Not metrics. Not approval. Alignment.", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m2", "Current Chapter", "Right now: {current_focus}. Ask me about it.", SectionType.MIDDLE, weight=0.9),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Simple CTA", "{cta}.", SectionType.CLOSER, weight=1.2),
                    TemplatePart("c2", "Fun Close", "{fun_fact} {cta.lower()}.", SectionType.CLOSER, weight=0.8),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Reading List", "Currently reading: *The Creative Act*, *Four Thousand Weeks*, *A Philosophy of Software Design*.", SectionType.EXTRA, weight=0.5),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain text", "lambda t: t"),
                StyleDef("twitter", "Twitter/X Bio", "Under 160 chars", "lambda t: (t[:157] + '...') if len(t) > 160 else t"),
                StyleDef("linkedin", "LinkedIn Summary", "Professional but human", "lambda t: t.replace('. ', '.\\n\\n')"),
                StyleDef("newsletter", "Newsletter Footer", "Warm, personal sign-off", "lambda t: '---\\n' + t + '\\n\\n— {name}'.format(name='Alex')"),
            ],
        )
    
    def _cat_friendship_social(self) -> CategoryDef:
        return CategoryDef(
            key="friendship_social",
            name="Making Friends / Social Circle",
            description: "For Bumble BFF, Meetup, Discord intros, new city arrivals. Platonic, warm, specific.",
            icon="🤝",
            sector="personal",
            variables=[
                VariableDef("location", "City/Neighborhood", "Brooklyn, Williamsburg", group="context"),
                VariableDef("interests", "Interests & Hobbies", "ceramics, jazz, urban hiking, cooking experiments, board games", group="core"),
                VariableDef("vibe", "Friendship Vibe", "low-maintenance, deep talks, spontaneous plans, mutual growth", group="core"),
                VariableDef("availability", "Availability", "weekends free, weekday evenings after 7", group="context"),
                VariableDef("looking_for", "Looking For", "gym buddy, brunch crew, creative accountability partner, travel buddy", group="core"),
                VariableDef("fun_fact", "Conversation Starter", "I make a mean shakshuka and know too much about 90s hip hop.", group="personal"),
                VariableDef("cta", "Reach Out", "DM me your favorite coffee spot", group="contact"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "New in Town", "New to {location}. Looking for my people.", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Intentional", "Not looking for more acquaintances. Looking for {looking_for}.", SectionType.OPENER, weight=1.0),
                    TemplatePart("o3", "Vibe First", "My energy: {vibe}. You?", SectionType.OPENER, weight=0.9),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Interests", "Into: {interests}. Always down to try something new.", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Logistics", "Free: {availability}. Plan-ahead or spontaneous — both work.", SectionType.MIDDLE, weight=0.8),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Low Pressure", "{cta}. No pressure. Just vibes.", SectionType.CLOSER, weight=1.2),
                    TemplatePart("c2", "Specific", "{fun_fact} {cta.lower()}.", SectionType.CLOSER, weight=0.9),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("discord", "Discord Intro", "Casual, emoji-heavy", "lambda t: t.replace('. ', ' 👉 ').replace(', ', ', ') + ' 🌿'"),
                StyleDef("bumble_bff", "Bumble BFF", "Structured prompts", "lambda t: '\\n'.join([f'✨ {p.strip()}' for p in t.split('. ') if p.strip()])"),
            ],
        )
    
    # ─── Professional ───
    def _cat_linkedin_bio(self) -> CategoryDef:
        return CategoryDef(
            key="linkedin_bio",
            name="LinkedIn About Section",
            description: "The 2,600-char About section. Narrative, keyword-rich, human. Not a resume dump.",
            icon="💼",
            sector="professional",
            variables=[
                VariableDef("headline", "Professional Headline", "Senior Product Manager | B2B SaaS | 0→1 Products", group="identity"),
                VariableDef("years_exp", "Years Experience", "8+", group="identity"),
                VariableDef("specialties", "Specialties", "Product Strategy, User Research, Data-Driven Decisions, Cross-Functional Leadership", group="skills"),
                VariableDef("key_achievement", "Signature Achievement", "Led product from concept to $40M ARR, 500k MAU, team of 12", group="proof"),
                VariableDef("philosophy", "Product Philosophy", "Build less. Measure more. Ship what matters.", group="core"),
                VariableDef("current_role", "Current Role", "Senior PM at Stripe (Platform Team)", group="now"),
                VariableDef("current_focus", "Current Focus", "Developer experience, platform extensibility, API design", group="now"),
                VariableDef("past_highlights", "Past Highlights", "Ex-Google (Ads), Ex-Series A Founder (acquired), Angel investor in 15 startups", group="proof"),
                VariableDef("superpower", "Superpower", "Translating complex technical constraints into clear product decisions", group="core"),
                VariableDef("seeking", "Open To", "Advisory roles, board seats, speaking, mentoring PMs", group="contact"),
                VariableDef("contact", "Best Way to Connect", "LinkedIn message > email. Mention what caught your eye.", group="contact"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Headline + Hook", "{headline}. {years_exp} years turning {specialties.lower()} into outcomes.", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Philosophy First", "\"${philosophy}\" — This guides every product decision I've made for {years_exp} years.", SectionType.OPENER, weight=1.0),
                    TemplatePart("o3", "Story Arc", "{past_highlights}. Now {current_role}, focused on {current_focus}.", SectionType.OPENER, weight=1.1),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "The Proof", "Signature win: {key_achievement}. My superpower: {superpower}.", SectionType.MIDDLE, weight=1.2),
                    TemplatePart("m2", "How I Work", "I operate at the intersection of {specialties}. Data informs. Intuition decides. Users win.", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m3", "Current Chapter", "Currently: {current_focus} at {current_role}. Building for builders.", SectionType.MIDDLE, weight=0.9),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Open Door", "{seeking}. {contact}", SectionType.CLOSER, weight=1.2),
                    TemplatePart("c2", "Mentor Focus", "Passionate about growing the next generation of PMs. {contact}", SectionType.CLOSER, weight=0.8),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Speaking", "Recent talks: ProductCon, Mind the Product, Internal Google/Stripe summits.", SectionType.EXTRA, weight=0.5),
                    TemplatePart("e2", "Writing", "Write at newsletter.example.com — product strategy, career, hard lessons.", SectionType.EXTRA, weight=0.5),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain narrative", "lambda t: t"),
                StyleDef("linkedin_native", "LinkedIn Native", "Bullet-friendly, scannable", "lambda t: t.replace('. ', '\\n• ').replace('|', '\\n•')"),
                StyleDef("first_person", "First Person Warm", "Conversational, human", "lambda t: t.replace('I am', 'I'm').replace('I have', 'I've').replace('I will', 'I'll')"),
                StyleDef("keyword_rich", "ATS Optimized", "Keyword density for search", "lambda t: t + '\\n\\nSpecialties: ' + ' | '.join(['Product Strategy', 'User Research', 'Data Analysis', 'Leadership', 'SaaS', 'B2B', 'Platform', 'API'])"),
            ],
        )
    
    def _cat_elevator_pitch(self) -> CategoryDef:
        return CategoryDef(
            key="elevator_pitch",
            name="Elevator Pitch (30/60/90 sec)",
            description: "For networking events, intros, investor meetings. Modular by time.",
            icon="🎤",
            sector="professional",
            variables=[
                VariableDef("name", "Name", "Sarah Chen", group="identity"),
                VariableDef("role", "Current Role", "Founder & CEO", group="identity"),
                VariableDef("company", "Company", "Nexus Analytics", group="identity"),
                VariableDef("problem", "Problem", "Marketing teams waste 40% budget on channels that don't convert", group="core"),
                VariableDef("solution", "Solution", "AI attribution that actually works — no cookies, no guesswork", group="core"),
                VariableDef("traction", "Traction", "$2.3M ARR, 120 customers, 140% NRR", group="proof"),
                VariableDef("market", "Market", "$50B marketing analytics TAM", group="context"),
                VariableDef("differentiator", "Differentiator", "Only platform using causal inference, not correlation", group="core"),
                VariableDef("ask", "Ask", "Raising $5M Series A to own the privacy-first attribution category", group="contact"),
                VariableDef("time", "Version", "60", options=["30", "60", "90"], type="select", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "30s Hook", "Hi, I'm {name}, {role} at {company}. We solve {problem.lower()} by {solution.lower()}.", SectionType.OPENER, weight=1.2, tags=["30"]),
                    TemplatePart("o2", "60s Hook", "{name}, {role} at {company}. {problem}. Our solution: {solution}.", SectionType.OPENER, weight=1.0, tags=["60"]),
                    TemplatePart("o3", "90s Hook", "Every marketing leader knows the pain: {problem}. I'm {name}, {role} at {company}, and we've built {solution}.", SectionType.OPENER, weight=0.9, tags=["90"]),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Traction (60/90)", "{traction}. In a {market} market.", SectionType.MIDDLE, weight=1.1, tags=["60", "90"]),
                    TemplatePart("m2", "Differentiation (90)", "Why us? {differentiator}. That's not a feature — it's a moat.", SectionType.MIDDLE, weight=1.0, tags=["90"]),
                    TemplatePart("m3", "Vision (90)", "We're not just building a tool. We're defining the privacy-first attribution category.", SectionType.MIDDLE, weight=0.8, tags=["90"]),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Ask (All)", "{ask}.", SectionType.CLOSER, weight=1.2),
                    TemplatePart("c2", "Soft Close (30)", "Happy to share more if relevant.", SectionType.CLOSER, weight=0.7, tags=["30"]),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("spoken", "Spoken Rhythm", "Natural pauses", "lambda t: t.replace('. ', '. \\n').replace(', ', ', ').replace(';', '\\n')"),
                StyleDef("investor", "Investor Deck", "Crisp, metric-forward", "lambda t: t.replace('{traction}', '**{traction}**').replace('{market}', '**{market}**')"),
            ],
        )
    
    def _cat_cover_letter(self) -> CategoryDef:
        return CategoryDef(
            key="cover_letter",
            name="Cover Letter / Cold Outreach",
            description: "Tailored, specific, shows you did homework. Not a template — a framework.",
            icon="📝",
            sector="professional",
            variables=[
                VariableDef("role", "Target Role", "Senior Product Manager", group="target"),
                VariableDef("company", "Company", "Notion", group="target"),
                VariableDef("why_company", "Why This Company", "Been a power user since 2019. Love the craft-first culture.", group="target"),
                VariableDef("relevant_win", "Relevant Win", "At Figma, shipped collaborative editing to 4M users — zero downtime launch", group="proof"),
                VariableDef("skill_match", "Skill Match", "Deep expertise in PLG, user onboarding, and cross-functional execution", group="skills"),
                VariableDef("culture_fit", "Culture Signal", "Values: craft, user obsession, thoughtful defaults. I live these daily.", group="core"),
                VariableDef("unique_angle", "Unique Angle", "Also a designer — I speak both languages. Bridge product/design/eng.", group="core"),
                VariableDef("cta", "Next Step", "Would love to discuss how I can contribute to Notion's next chapter.", group="contact"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Specific Hook", "Dear Hiring Team — I've used {company} daily for 4 years. Applying for {role} isn't a shot in the dark. It's intentional.", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Mutual Connection", "Referred by [Name] who said \"{company}'s product team operates differently.\" That's why I'm here for {role}.", SectionType.OPENER, weight=0.9),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "The Match", "{why_company} My background: {relevant_win}. Directly relevant to {role}'s focus on {skill_match.lower()}.", SectionType.MIDDLE, weight=1.2),
                    TemplatePart("m2", "Culture + Unique", "{culture_fit} {unique_angle}", SectionType.MIDDLE, weight=1.0),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Confident Close", "{cta} Available for a conversation this week.", SectionType.CLOSER, weight=1.2),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Standard format", "lambda t: t"),
                StyleDef("email", "Email Format", "Subject line + body", "lambda t: f'Subject: {role} at {company} — {relevant_win[:50]}...\\n\\n{t}'"),
                StyleDef("linkedin_msg", "LinkedIn DM", "Under 300 chars, casual", "lambda t: t[:297] + '...' if len(t) > 300 else t"),
            ],
        )
    
    def _cat_freelance_profile(self) -> CategoryDef:
        return CategoryDef(
            key="freelance_profile",
            name="Freelance / Upwork / Toptal Profile",
            description: "Client-facing, outcome-oriented, trust-building. Specialized by niche.",
            icon="💻",
            sector="professional",
            variables=[
                VariableDef("title", "Professional Title", "Fractional CTO / Technical Advisor", group="identity"),
                VariableDef("niche", "Niche", "Early-stage SaaS (Pre-seed to Series A)", group="identity"),
                VariableDef("outcomes", "Client Outcomes", "3 exits, $120M+ raised, 10x velocity improvements", group="proof"),
                VariableDef("stack", "Tech Stack", "Python, TypeScript, AWS, Postgres, Kubernetes, React", group="skills"),
                VariableDef("services", "Services", "Architecture, hiring, code review, fundraising prep, interim leadership", group="offer"),
                VariableDef("approach", "Approach", "Hands-on, founder-friendly, no ego. I ship.", group="core"),
                VariableDef("availability", "Availability", "20 hrs/week, 2-week notice", group="logistics"),
                VariableDef("rate", "Rate", "$300/hr or $15k/mo retainer", group="logistics"),
                VariableDef("portfolio", "Portfolio", "github.com/username | case studies on request", group="proof"),
                VariableDef("ideal_client", "Ideal Client", "Technical founder, 2-10 people, product-market fit search", group="target"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Title + Niche", "{title} for {niche}. {outcomes}.", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Outcome-First", "I help {ideal_client.lower()} achieve {outcomes.lower()}.", SectionType.OPENER, weight=1.0),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Services", "What I do: {services}. Stack: {stack}.", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "How I Work", "{approach} No handoffs. No slideware. Code, decisions, results.", SectionType.MIDDLE, weight=1.0),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Logistics + CTA", "{availability} • {rate}. {portfolio}. Let's talk if this fits.", SectionType.CLOSER, weight=1.2),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Testimonial", "\"Best technical hire we never made full-time.\" — Founder, Series A SaaS", SectionType.EXTRA, weight=0.6),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("upwork", "Upwork Profile", "Structured sections", "lambda t: t.replace('. ', '\\n\\n').replace('•', '\\n•')"),
                StyleDef("toptal", "Toptal Style", "Premium, concise", "lambda t: t[:1500]"),
            ],
        )
    
    # ─── Creative ───
    def _cat_story_hook(self) -> CategoryDef:
        return CategoryDef(
            key="story_hook",
            name="Story Hook / Logline",
            description: "One-sentence hooks for novels, screenplays, games. High concept + emotional stakes.",
            icon="🎬",
            sector="creative",
            variables=[
                VariableDef("protagonist", "Protagonist", "a burned-out dream architect", group="character"),
                VariableDef("inciting_incident", "Inciting Incident", "discovers a nightmare leaking into waking reality", group="plot"),
                VariableDef("goal", "Goal", "seal the breach before the world stops dreaming", group="plot"),
                VariableDef("antagonist", "Antagonist", "the corporation monetizing human dreams", group="character"),
                VariableDef("stakes", "Stakes", "if she fails, humanity loses imagination forever", group="plot"),
                VariableDef("setting", "Setting", "near-future Neo-Shanghai, where dreams are currency", group="world"),
                VariableDef("twist", "Twist", "she's the only one who can dream new worlds — not just fix old ones", group="plot"),
                VariableDef("genre", "Genre", "sci-fi noir", options=["sci-fi", "fantasy", "thriller", "horror", "romance", "literary", "sci-fi noir", "magical realism"], type="select", group="meta"),
                VariableDef("tone", "Tone", "atmospheric, morally gray, hopeful", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Classic Logline", "When {inciting_incident}, {protagonist} must {goal} before {stakes}.", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Character-First", "{protagonist.capitalize()} in {setting}. {inciting_incident.capitalize()}. Now {goal}.", SectionType.OPENER, weight=1.0),
                    TemplatePart("o3", "Antagonist Pressure", "{antagonist.capitalize()} controls {setting}. {protagonist.capitalize()} just found the crack in their system. {twist}.", SectionType.OPENER, weight=1.1),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Stakes Escalation", "Failure means {stakes}. Success means {twist.lower()}.", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m2", "Genre/Tone", "Genre: {genre}. Tone: {tone}.", SectionType.MIDDLE, weight=0.7),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Title Suggestion", "Working title: *The Last Dreamer* / *Lucid* / *Architect of Sleep*", SectionType.CLOSER, weight=0.8),
                    TemplatePart("c2", "Question Hook", "What happens when the dreamer becomes the dream?", SectionType.CLOSER, weight=0.9),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Series Potential", "Book 1 of *The Oneironaut Chronicles*.", SectionType.EXTRA, weight=0.5),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("logline", "Logline Format", "Industry standard", "lambda t: 'LOGLINE: ' + t.split('.')[0] + '.'"),
                StyleDef("pitch", "Elevator Pitch", "Conversational", "lambda t: 'Picture this: ' + t"),
                StyleDef("twitter", "Twitter Pitch", "#PitMad style", "lambda t: t[:270] + ' #PitMad #{}'.format('SciFi' if 'sci' in 'sci-fi noir' else 'Fiction')"),
            ],
        )
    
    def _cat_character_sheet(self) -> CategoryDef:
        return CategoryDef(
            key="character_sheet",
            name="Character Sheet / Profile",
            description: "Deep character profiles for novels, RPGs, screenwriting. Psychology > stats.",
            icon="🎭",
            sector="creative",
            variables=[
                VariableDef("name", "Name", "Mara Voss", group="identity"),
                VariableDef("age", "Age", "34", group="identity"),
                VariableDef("role", "Role/Archetype", "Reluctant oracle / former archivist", group="identity"),
                VariableDef("want", "External Want", "Find her missing sister", group="psychology"),
                VariableDef("need", "Internal Need", "Trust herself again after the mistake that cost lives", group="psychology"),
                VariableDef("lie", "The Lie They Believe", "\"I'm better off alone. Attachment gets people killed.\"", group="psychology"),
                VariableDef("ghost", "Ghost / Wound", "The Archive Fire — she chose the wrong shelf to save", group="psychology"),
                VariableDef("fear", "Deepest Fear", "Being responsible for another loss", group="psychology"),
                VariableDef("strength", "Core Strength", "Pattern recognition — sees connections others miss", group="traits"),
                VariableDef("flaw", "Core Flaw", "Hyper-vigilance masquerading as preparation", group="traits"),
                VariableDef("quirk", "Distinctive Quirk", "Speaks in partial quotes from dead languages when stressed", group="traits"),
                VariableDef("voice", "Voice Description", "Measured, sparse, occasional archaic phrasing. Thinks before speaking.", group="voice"),
                VariableDef("relationship", "Key Relationship", "Kalen — former partner, only one who calls her 'Mara' not 'Archivist'", group="connections"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Snapshot", "{name}, {age}. {role}. {strength}. {flaw}.", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Voice Intro", "\"...\" {voice} That's how {name} starts every hard conversation.", SectionType.OPENER, weight=1.0),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "The Engine", "Want: {want}. Need: {need}. Lie: {lie}. Ghost: {ghost}. Fear: {fear}.", SectionType.MIDDLE, weight=1.2),
                    TemplatePart("m2", "Texture", "Quirk: {quirk}. Voice: {voice}.", SectionType.MIDDLE, weight=0.9),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Connection", "Anchor: {relationship}. The only thread left.", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Arc Beats", "Act 1: Isolation. Act 2: Forced partnership. Act 3: Chosen vulnerability.", SectionType.EXTRA, weight=0.7),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("rpg", "D&D / RPG Format", "Structured fields", "lambda t: t.replace('. ', '\\n**').replace(': ', '**: ')"),
                StyleDef("scrivener", "Scrivener Template", "Binder-ready", "lambda t: t.replace('. ', '\\n\\n')"),
            ],
        )
    
    def _cat_worldbuilding(self) -> CategoryDef:
        return CategoryDef(
            key="worldbuilding",
            name="Worldbuilding Brief",
            description: "Magic systems, tech specs, political structures, cultures. Consistent, usable.",
            icon="🌍",
            sector="creative",
            variables=[
                VariableDef("world_name", "World Name", "Aetheris", group="identity"),
                VariableDef("concept", "Core Concept", "A world where memories can be extracted, traded, and weaponized", group="core"),
                VariableDef("magic_system", "Magic/Tech System", "Mnemosyne Tech — memory crystallization via neural resonance", group="system"),
                VariableDef("cost", "Cost/Limitation", "Each extraction erodes the donor's identity. Memory merchants go hollow.", group="system"),
                VariableDef("power_structure", "Power Structure", "The Mnemonarchs — memory oligarchs who hoard collective history", group="society"),
                VariableDef("conflict", "Central Conflict", "Resistance (The Unforgotten) vs. Mnemonarchs. A new memory plague emerges.", group="plot"),
                VariableDef("culture_detail", "Cultural Detail", "Funeral rites: memories returned to community. Theft = soul murder.", group="society"),
                VariableDef("geography", "Key Geography", "The Vault (memory banks), The Hollows (identity-less zones), The Surface (raw reality)", group="world"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "High Concept", "{world_name}: {concept}.", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "System", "System: {magic_system}. Cost: {cost}.", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Society", "Power: {power_structure}. Culture: {culture_detail}.", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m3", "Conflict + Map", "Conflict: {conflict}. Key locations: {geography}.", SectionType.MIDDLE, weight=1.0),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Story Seeds", "Three hooks: 1) A memory that shouldn't exist. 2) A Mnemonarch's heir defects. 3) The Vault is leaking.", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("wiki", "Wiki Style", "Structured entries", "lambda t: t.replace('. ', '\\n\\n## ').replace(': ', '\\n**')"),
                StyleDef("bible", "Series Bible", "Comprehensive", "lambda t: '# ' + t.replace('. ', '\\n\\n## ')"),
            ],
        )
    
    def _cat_poetry_prompt(self) -> CategoryDef:
        return CategoryDef(
            key="poetry_prompt",
            name="Poetry Prompt / Exercise",
            description: "Generative prompts for poets. Form, constraint, theme, seed line.",
            icon="📜",
            sector="creative",
            variables=[
                VariableDef("form", "Form", "ghazal", options=["free verse", "sonnet", "ghazal", "villanelle", "haiku sequence", "prose poem", "pantoum", "sestina"], type="select", group="form"),
                VariableDef("theme", "Theme", "inheritance — what we carry, what we leave", group="core"),
                VariableDef("constraint", "Constraint", "every couplet must contain a color", group="form"),
                VariableDef("seed_line", "Seed Line", "My mother's hands were the color of dried saffron", group="seed"),
                VariableDef("mood", "Mood", "tender, archaeological, quiet", group="core"),
                VariableDef("image_bank", "Image Bank", "saffron, indigo, bone, rust, gold leaf, tea stains, heirloom seeds", group="seed"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Prompt", "Write a {form} on \"{theme}\". Constraint: {constraint}. Seed: \"{seed_line}\". Mood: {mood}. Images to weave: {image_bank}.", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Craft Notes", "Ghazal: 5-15 couplets, autonomous, same refrain/rhyme. Villanelle: 19 lines, 2 refrains. Sonnet: 14 lines, volta at line 9.", SectionType.MIDDLE, weight=0.8),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Permission", "Write badly first. The form will teach you what the poem wants.", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("workshop", "Workshop Handout", "Formatted for class", "lambda t: t.replace('. ', '\\n\\n').replace('Seed:', '\\n**Seed:**')"),
            ],
        )
    
    # ─── Marketing ───
    def _cat_ad_copy(self) -> CategoryDef:
        return CategoryDef(
            key="ad_copy",
            name="Ad Copy (Meta/Google/TikTok)",
            description: "Direct response frameworks: PAS, AIDA, BAB, 4U. Platform-optimized.",
            icon="📢",
            sector="marketing",
            variables=[
                VariableDef("product", "Product/Service", "WriteUp Studio Premium", group="core"),
                VariableDef("audience", "Target Audience", "founders, creators, PMs who write daily", group="core"),
                VariableDef("pain", "Pain Point", "staring at blank screens, inconsistent voice, slow output", group="core"),
                VariableDef("benefit", "Core Benefit", "publish 10x faster in your exact voice", group="core"),
                VariableDef("mechanism", "Unique Mechanism", "sector-organized templates + variable interpolation + style transformers", group="core"),
                VariableDef("proof", "Proof", "5,000+ writers, 4.9★, used at Stripe/Notion/Figma", group="proof"),
                VariableDef("offer", "Offer", "Free 14-day trial, no credit card", group="offer"),
                VariableDef("cta", "CTA", "Start writing free →", group="offer"),
                VariableDef("platform", "Platform", "Meta", options=["Meta (FB/IG)", "Google Search", "Google Display", "TikTok", "LinkedIn", "Twitter/X", "Newsletter"], type="select", group="meta"),
                VariableDef("format", "Format", "Primary Text + Headline", options=["Primary Text + Headline", "Carousel Cards", "Video Script (15s)", "Video Script (30s)", "Story/Reel"], type="select", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "PAS - Problem", "Stop {pain}.", SectionType.OPENER, weight=1.2, tags=["PAS"]),
                    TemplatePart("o2", "AIDA - Attention", "What if you could {benefit.lower()} — without the {pain.lower()}?", SectionType.OPENER, weight=1.1, tags=["AIDA"]),
                    TemplatePart("o3", "BAB - Before", "Right now: {pain}. Imagine: {benefit}.", SectionType.OPENER, weight=1.0, tags=["BAB"]),
                    TemplatePart("o4", "4U - Urgent", "The {pain} costing you hours every week? Solved.", SectionType.OPENER, weight=0.9, tags=["4U"]),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "PAS - Agitation", "Every blank page is revenue delayed. Every inconsistent post is trust lost.", SectionType.MIDDLE, weight=1.1, tags=["PAS"]),
                    TemplatePart("m2", "AIDA - Interest", "{product} uses {mechanism} to give you {benefit}.", SectionType.MIDDLE, weight=1.0, tags=["AIDA"]),
                    TemplatePart("m3", "BAB - After", "With {product}: {benefit}. Your voice. Your speed. Your standards.", SectionType.MIDDLE, weight=1.0, tags=["BAB"]),
                    TemplatePart("m4", "4U - Unique", "Only {product} gives you {mechanism}. {proof}.", SectionType.MIDDLE, weight=0.9, tags=["4U"]),
                    TemplatePart("m5", "Proof", "{proof}.", SectionType.MIDDLE, weight=1.2, tags=["all"]),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "PAS - Solution", "{product}. {benefit}. {offer}. {cta}", SectionType.CLOSER, weight=1.2, tags=["PAS"]),
                    TemplatePart("c2", "AIDA - Action", "{cta} {offer}.", SectionType.CLOSER, weight=1.1, tags=["AIDA"]),
                    TemplatePart("c3", "BAB - Bridge", "The bridge: {product}. {offer}. {cta}", SectionType.CLOSER, weight=1.0, tags=["BAB"]),
                    TemplatePart("c4", "4U - Ultra", "Ultra-specific: {offer}. {cta}", SectionType.CLOSER, weight=0.9, tags=["4U"]),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Headline Options", "Headlines: {benefit} | Stop {pain} | {proof.split(',')[0]} | {offer}", SectionType.EXTRA, weight=0.8),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("meta", "Meta (FB/IG)", "Primary text + headline split", "lambda t: t.replace('|', '\\n\\n**Headline:** ')"),
                StyleDef("google_search", "Google Search", "3 headlines (30c) + 2 descriptions (90c)", "lambda t: '\\n'.join([f'H{i}: {h[:30]}' for i, h in enumerate(t.split('|')[:3], 1)] + [f'D{i}: {d[:90]}' for i, d in enumerate(t.split('|')[3:5], 1)])"),
                StyleDef("tiktok", "TikTok Script", "Hook → Value → CTA", "lambda t: 'HOOK (0-3s): ' + t.split('.')[0] + '\\n\\nVALUE: ' + '. '.join(t.split('.')[1:3]) + '\\n\\nCTA: ' + t.split('.')[-1]"),
            ],
        )
    
    def _cat_email_sequence(self) -> CategoryDef:
        return CategoryDef(
            key="email_sequence",
            name="Email Sequence (Welcome/Nurture/Sales)",
            description: "Multi-email sequences with strategy. Subject lines + preview text + body.",
            icon="📧",
            sector="marketing",
            variables=[
                VariableDef("sequence_type", "Sequence Type", "Welcome", options=["Welcome (5 emails)", "Nurture (7 emails)", "Sales Launch (4 emails)", "Re-engagement (3 emails)", "Onboarding (6 emails)"], type="select", group="meta"),
                VariableDef("product", "Product", "WriteUp Studio Premium", group="core"),
                VariableDef("audience", "Audience", "writers, creators, PMs", group="core"),
                VariableDef("pain", "Pain", "slow writing, blank page, voice inconsistency", group="core"),
                VariableDef("promise", "Promise", "write in your voice, 10x faster", group="core"),
                VariableDef("proof", "Proof", "5,000+ users, 4.9★", group="proof"),
                VariableDef("founder_story", "Founder Story", "Built this after 3 failed launches. Writing was always the bottleneck.", group="story"),
                VariableDef("cta", "Primary CTA", "Start free trial", group="offer"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Email 1 Subject", "Welcome to {product} 🎉", SectionType.OPENER, weight=1.0, tags=["welcome", "email1"]),
                    TemplatePart("o2", "Email 1 Preview", "Your writing bottleneck ends here", SectionType.OPENER, weight=1.0, tags=["welcome", "email1"]),
                    TemplatePart("o3", "Email 1 Body", "Hey there — \n\nYou signed up because {pain}. I get it. I built {product} because I lived it.\n\n{founder_story}\n\nStarting today, you'll get {promise}. No credit card. No pressure.\n\n{cta} →\n\n— Founder", SectionType.OPENER, weight=1.2, tags=["welcome", "email1"]),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Email 2: Value", "Subject: The template that saved me 10 hrs/week\n\nMost people write from scratch. Pros use frameworks.\n\nHere's the exact {product} template I use for [specific use case]:\n\n[Template preview]\n\nSteal it. Modify it. {cta}.", SectionType.MIDDLE, weight=1.0, tags=["welcome", "email2"]),
                    TemplatePart("m2", "Email 3: Proof", "Subject: How [Company] cut writing time 80%\n\n{proof}. Real teams. Real results.\n\n[Case study snippet]\n\nSame framework. Your voice. {cta}.", SectionType.MIDDLE, weight=1.0, tags=["welcome", "email3"]),
                    TemplatePart("m3", "Email 4: Objection", "Subject: \"But I like writing from scratch\"\n\nGreat. Keep doing that for the 20% that matters.\n\nUse {product} for the 80% that doesn't: first drafts, repurposing, formatting, variants.\n\nBest of both worlds. {cta}.", SectionType.MIDDLE, weight=0.9, tags=["welcome", "email4"]),
                    TemplatePart("m4", "Email 5: Soft Close", "Subject: One question\n\nWhat's the one piece of content you've been putting off?\n\nReply and tell me. I read every email.\n\nAnd if {product} can help — {cta}.\n\nEither way, rooting for you.", SectionType.MIDDLE, weight=1.0, tags=["welcome", "email5"]),
                ],
                SectionType.CLOSER: [],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("html_email", "HTML Email", "Basic formatting", "lambda t: t.replace('\\n\\n', '<br><br>').replace('\\n', '<br>')"),
            ],
        )
    
    def _cat_landing_page(self) -> CategoryDef:
        return CategoryDef(
            key="landing_page",
            name="Landing Page Copy",
            description: "Hero, value props, social proof, FAQ, final CTA. Conversion-focused.",
            icon="🌐",
            sector="marketing",
            variables=[
                VariableDef("product", "Product", "WriteUp Studio Premium", group="core"),
                VariableDef("tagline", "Tagline", "Your voice. 10x faster.", group="core"),
                VariableDef("subheadline", "Subheadline", "Sector-organized templates. Variable interpolation. Style transformers. Zero AI genericness.", group="core"),
                VariableDef("pain", "Pain", "Blank pages. Inconsistent voice. Hours lost to formatting.", group="core"),
                VariableDef("benefits", "Top 3 Benefits", "Write in your voice • Sector-specific templates • Export anywhere", group="core"),
                VariableDef("proof", "Social Proof", "5,000+ writers • 4.9★ • Used at Stripe, Notion, Figma", group="proof"),
                VariableDef("demo", "Demo", "Interactive playground — try before signup", group="offer"),
                VariableDef("pricing", "Pricing", "Free forever • Pro $12/mo • Team $36/mo", group="offer"),
                VariableDef("guarantee", "Guarantee", "14-day trial, no card, cancel anytime", group="offer"),
                VariableDef("faq", "Top FAQ", "Q: Does it replace my voice? A: No. It amplifies it.", group="support"),
                VariableDef("cta", "Final CTA", "Start writing free →", group="offer"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Hero", "{product}\n{tagline}\n{subheadline}\n\n{cta}", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Problem", "The problem: {pain}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m2", "Benefits", "Why {product}:\n{benefits}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m3", "Proof", "{proof}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m4", "Demo", "Try it: {demo}", SectionType.MIDDLE, weight=0.8),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Pricing + Guarantee", "{pricing}\n{guarantee}\n\n{cta}", SectionType.CLOSER, weight=1.2),
                    TemplatePart("c2", "FAQ", "{faq}", SectionType.CLOSER, weight=0.7),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("html", "HTML Sections", "Semantic markup", "lambda t: t.replace('\\n\\n', '</section><section>').replace('\\n', '<br>')"),
                StyleDef("figma", "Figma Copy", "Layer-ready", "lambda t: t.replace('\\n\\n', '\\n---LAYER---\\n')"),
            ],
        )
    
    def _cat_social_media(self) -> CategoryDef:
        return CategoryDef(
            key="social_media",
            name="Social Media Posts (LinkedIn/Twitter/Threads)",
            description: "Platform-native formats. Hooks, threads, carousels, engagement bait.",
            icon="📱",
            sector="marketing",
            variables=[
                VariableDef("topic", "Topic", "Why most PMs fail at writing specs", group="core"),
                VariableDef("hook", "Hook", "Your spec template is why engineering hates you.", group="core"),
                VariableDef("insight", "Core Insight", "Specs aren't documentation. They're alignment contracts.", group="core"),
                VariableDef("framework", "Framework", "Context → Problem → Solution → Success Metrics → Risks → Timeline", group="core"),
                VariableDef("example", "Concrete Example", "At Stripe, this reduced spec review cycles from 5 to 1.", group="proof"),
                VariableDef("counterintuitive", "Counterintuitive Take", "Longer specs get read less. Shorter specs get built wrong. The sweet spot: 2 pages.", group="core"),
                VariableDef("cta", "CTA", "Steal my spec template → [link]", group="offer"),
                VariableDef("platform", "Platform", "LinkedIn", options=["LinkedIn", "Twitter/X", "Threads", "Mastodon", "Bluesky"], type="select", group="meta"),
                VariableDef("format", "Format", "Single Post", options=["Single Post", "Thread (5-7)", "Carousel (8 slides)", "Poll + Insight", "Story/Reel Script"], type="select", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Hook", "{hook}", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "Question Hook", "Unpopular opinion: {counterintuitive}", SectionType.OPENER, weight=1.0),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Insight", "{insight}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Framework", "The framework:\n{framework}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m3", "Proof", "{example}", SectionType.MIDDLE, weight=0.9),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "CTA", "{cta}", SectionType.CLOSER, weight=1.2),
                    TemplatePart("c2", "Engagement", "What's your spec pet peeve? Comment below 👇", SectionType.CLOSER, weight=0.8),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Thread Expansion", "Thread version: 1/ {hook} 2/ {insight} 3/ {framework} 4/ {example} 5/ {counterintuitive} 6/ {cta} 7/ Follow for more.", SectionType.EXTRA, weight=0.7, tags=["thread"]),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("linkedin", "LinkedIn Native", "Line breaks, hashtags", "lambda t: t + '\\n\\n#ProductManagement #Writing #Specs #Leadership'"),
                StyleDef("twitter", "Twitter/X", "280 chars, thread-ready", "lambda t: t[:277] + '...' if len(t) > 280 else t"),
                StyleDef("thread", "Thread Format", "Numbered tweets", "lambda t: '\\n\\n'.join([f'{i}/ {p.strip()}' for i, p in enumerate(t.split('. '), 1) if p.strip()])"),
            ],
        )
    
    def _cat_product_launch(self) -> CategoryDef:
        return CategoryDef(
            key="product_launch",
            name="Product Launch (Product Hunt / Launch Week)",
            description: "Launch day assets: tagline, hunter blurb, maker comment, tweet storm, email.",
            icon="🚀",
            sector="marketing",
            variables=[
                VariableDef("product", "Product", "WriteUp Studio Premium", group="core"),
                VariableDef("tagline", "Tagline (60 chars)", "Your voice. 10x faster. Zero generic.", group="core"),
                VariableDef("description", "Description (260 chars)", "Sector-organized templates + variable interpolation + style transformers. The writing tool that finally sounds like you.", group="core"),
                VariableDef("problem", "Problem", "AI writers sound generic. Templates are rigid. You waste hours editing.", group="core"),
                VariableDef("solution", "Solution", "Plug your context once. Generate unlimited variations in your voice.", group="core"),
                VariableDef("key_feature", "Killer Feature", "Style transformers: same content → LinkedIn, Twitter, Email, Script, Poem.", group="core"),
                VariableDef("traction", "Traction", "5,000 beta users • 4.9★ • 12M words generated", group="proof"),
                VariableDef("launch_offer", "Launch Offer", "50% off Pro for first 100 customers (code: LAUNCH50)", group="offer"),
                VariableDef("maker_note", "Maker Note", "Built this after 3 failed launches where writing was the bottleneck. Now it's not.", group="story"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "PH Tagline", "{tagline}", SectionType.OPENER, weight=1.2),
                    TemplatePart("o2", "PH Description", "{description}", SectionType.OPENER, weight=1.0),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Hunter Blurb", "🎯 Hunting {product}: {description} Finally a writing tool that doesn't flatten your voice. {key_feature} {traction}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Maker Comment", "👋 {maker_note}\n\nProblem: {problem}\nSolution: {solution}\n\n{launch_offer}\n\nFeedback welcome — I'm here all day.", SectionType.MIDDLE, weight=1.2),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Tweet Storm", "1/ 🚀 Launching {product}: {tagline}\n\n2/ The problem: {problem}\n\n3/ The solution: {solution}\n\n4/ {key_feature}\n\n5/ {traction}\n\n6/ {launch_offer}\n\n7/ Try it: [link] #buildinpublic", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "Launch Email", "Subject: We're live 🎉\n\n{product} is now on Product Hunt.\n\n{description}\n\n{maker_note}\n\n{launch_offer}\n\n[PH Link]\n\nWould mean the world if you'd upvote 🙏", SectionType.EXTRA, weight=0.8),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("ph", "Product Hunt", "Markdown-ready", "lambda t: t"),
                StyleDef("twitter", "Twitter Storm", "Thread format", "lambda t: t.replace('\\n\\n', '\\n\\n')"),
            ],
        )
    
    # ─── Technical ───
    def _cat_api_documentation(self) -> CategoryDef:
        return CategoryDef(
            key="api_documentation",
            name="API Reference Documentation",
            description: "OpenAPI-ready, developer-friendly. Endpoints, params, examples, errors.",
            icon="📚",
            sector="technical",
            variables=[
                VariableDef("api_name", "API Name", "WriteUp Studio API", group="identity"),
                VariableDef("base_url", "Base URL", "https://api.writeupstudio.com/v1", group="config"),
                VariableDef("auth", "Authentication", "Bearer token (API Key)", group="config"),
                VariableDef("endpoint", "Endpoint", "POST /chat/completions", group="endpoint"),
                VariableDef("method", "HTTP Method", "POST", options=["GET", "POST", "PUT", "PATCH", "DELETE"], type="select", group="endpoint"),
                VariableDef("description", "Endpoint Description", "Generate content from templates with variable interpolation and style transformation.", group="endpoint"),
                VariableDef("params", "Parameters (JSON)", '{"category": "string", "style": "string", "variables": "object", "sections": "array"}', group="endpoint"),
                VariableDef("example_request", "Example Request", 'curl -X POST "$BASE/chat/completions" -H "Authorization: Bearer $KEY" -d \'{"category": "romance_dating", "style": "hinge", "variables": {"goal": "a partner"}}\'', group="endpoint"),
                VariableDef("example_response", "Example Response", '{"text": "I\\'m not here for options. I\\'m here for a partner.", "meta": {"tokens": 42}}', group="endpoint"),
                VariableDef("errors", "Error Codes", "400: Invalid input • 401: Unauthorized • 429: Rate limited • 500: Server error", group="endpoint"),
                VariableDef("rate_limit", "Rate Limit", "100 req/min • 10,000 req/day", group="config"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Endpoint Header", "## {method} {endpoint}\n\n{description}", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Auth", "**Authentication:** {auth}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m2", "Parameters", "**Parameters:**\n```json\n{params}\n```", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m3", "Request Example", "**Request:**\n```bash\n{example_request}\n```", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m4", "Response Example", "**Response (200):**\n```json\n{example_response}\n```", SectionType.MIDDLE, weight=1.1),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Errors + Limits", "**Errors:** {errors}\n\n**Rate Limits:** {rate_limit}", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "SDK Note", "Official SDKs: Python, TypeScript, Go. `pip install writeup-studio`", SectionType.EXTRA, weight=0.6),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("openapi", "OpenAPI/YAML", "Spec-ready", "lambda t: t.replace('## ', 'paths:\\n  /chat/completions:\\n    post:\\n      summary: ')"),
                StyleDef("readme", "README Section", "GitHub-ready", "lambda t: t"),
            ],
        )
    
    def _cat_changelog(self) -> CategoryDef:
        return CategoryDef(
            key="changelog",
            name="Changelog / Release Notes",
            description: "Keep a Changelog format. User-facing, categorized, linkable.",
            icon="📋",
            sector="technical",
            variables=[
                VariableDef("version", "Version", "v2.4.0", group="meta"),
                VariableDef("date", "Release Date", "2026-01-15", group="meta"),
                VariableDef("type", "Release Type", "Minor", options=["Major", "Minor", "Patch", "Hotfix", "Beta", "RC"], type="select", group="meta"),
                VariableDef("highlights", "Highlights", "Style transformers • Sector organization • Plugin architecture • Premium UI", group="core"),
                VariableDef("added", "Added", "• New sector: Academic\n• 12 new categories\n• Import/export JSON\n• Keyboard shortcuts", group="changes"),
                VariableDef("changed", "Changed", "• Redesigned generator engine (weighted selection)\n• Variables now support validation regex\n• Theme system with design tokens", group="changes"),
                VariableDef("fixed", "Fixed", "• Variable interpolation edge cases\n• Style lambda sandbox escapes\n• Mobile layout overflow", group="changes"),
                VariableDef("deprecated", "Deprecated", "• Legacy `template` field (use `parts`)\n• Single-style categories", group="changes"),
                VariableDef("migration", "Migration Guide", "See docs.writeupstudio.com/migration/v2", group="meta"),
                VariableDef("contributors", "Contributors", "@alex @sam @jordan", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Header", "## [{version}] - {date}\n\n{type} Release", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Highlights", "### Highlights\n{highlights}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Added", "### Added\n{added}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m3", "Changed", "### Changed\n{changed}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m4", "Fixed", "### Fixed\n{fixed}", SectionType.MIDDLE, weight=1.0),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Deprecated + Migration", "### Deprecated\n{deprecated}\n\n### Migration\n{migration}", SectionType.CLOSER, weight=0.9),
                    TemplatePart("c2", "Credits", "### Contributors\n{contributors}", SectionType.CLOSER, weight=0.7),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("keepachangelog", "Keep a Changelog", "Standard format", "lambda t: t"),
                StyleDef("github_release", "GitHub Release", "Markdown for releases", "lambda t: t"),
            ],
        )
    
    def _cat_readme(self) -> CategoryDef:
        return CategoryDef(
            key="readme",
            name="README.md (Project/Repo)",
            description: "Badges, quick start, features, install, usage, contributing, license.",
            icon="📄",
            sector="technical",
            variables=[
                VariableDef("project_name", "Project Name", "WriteUp Studio Premium", group="identity"),
                VariableDef("tagline", "Tagline", "Your voice. 10x faster. Zero generic.", group="identity"),
                VariableDef("badges", "Badges", "[![Stars](https://img.shields.io/github/stars/user/repo)] [![License](https://img.shields.io/badge/license-MIT-blue)] [![Python](https://img.shields.io/badge/python-3.11+-blue)]", group="meta"),
                VariableDef("description", "Description", "Production-grade content generation platform. Sector-organized templates, variable interpolation, style transformers, plugin architecture.", group="core"),
                VariableDef("features", "Key Features", "• 6 sectors, 18+ categories\n• Variable interpolation with methods\n• Weighted template selection\n• Style transformers (lambdas)\n• Plugin architecture\n• Export: MD, TXT, JSON, HTML\n• Zero dependencies beyond stdlib", group="core"),
                VariableDef("install", "Install", "```bash\npip install writeup-studio\n```", group="start"),
                VariableDef("quickstart", "Quick Start", "```python\nfrom writeup_studio import Studio\nstudio = Studio()\nresult = studio.generate('romance_dating', style='hinge')\nprint(result.text)\n```", group="start"),
                VariableDef("usage", "Usage", "CLI: `writeup generate romance_dating --style hinge --count 5`\nWeb: `streamlit run studio.py`", group="start"),
                VariableDef("contributing", "Contributing", "PRs welcome! See CONTRIBUTING.md for plugin development guide.", group="meta"),
                VariableDef("license", "License", "MIT © 2026 WriteUp Studio Contributors", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Header", "# {project_name}\n\n{badges}\n\n{tagline}\n\n{description}", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Features", "## Features\n{features}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Install", "## Install\n{install}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m3", "Quick Start", "## Quick Start\n{quickstart}", SectionType.MIDDLE, weight=1.1),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Usage + Links", "## Usage\n{usage}\n\n## Contributing\n{contributing}\n\n## License\n{license}", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [],
            ],
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("github", "GitHub Profile", "Compact", "lambda t: t.replace('## ', '### ')"),
            ],
        )
    
    def _cat_technical_spec(self) -> CategoryDef:
        return CategoryDef(
            key="technical_spec",
            name="Technical Spec / RFC",
            description: "Architecture decisions, API contracts, data models, migration plans. For engineering review.",
            icon="📐",
            sector="technical",
            variables=[
                VariableDef("title", "Title", "RFC-0042: Plugin Architecture for Content Generation", group="meta"),
                VariableDef("author", "Author", "Alex Chen", group="meta"),
                VariableDef("status", "Status", "Proposed", options=["Draft", "Proposed", "Accepted", "Implemented", "Rejected", "Deferred"], type="select", group="meta"),
                VariableDef("date", "Date", "2026-01-15", group="meta"),
                VariableDef("context", "Context", "Current generator is monolithic. Adding new categories requires code changes. No extension points.", group="core"),
                VariableDef("problem", "Problem", "• Hard to add categories without deploy\n• No way to customize generation logic\n• Styles are coupled to categories\n• Testing is difficult", group="core"),
                VariableDef("proposal", "Proposal", "Introduce plugin system: GeneratorPlugin, ExporterPlugin, TransformerPlugin. Categories become data, not code. Registry manages discovery.", group="core"),
                VariableDef("alternatives", "Alternatives Considered", "1) Keep monolith, add config — rejected: doesn't solve extension\n2) External DSL — rejected: too complex\n3) WebAssembly plugins — rejected: overkill", group="core"),
                VariableDef("api_design", "API Design", "```python\nclass GeneratorPlugin(Protocol):\n    def generate(self, category, style, sections, variables) -> GenerationResult: ...\n```", group="technical"),
                VariableDef("data_models", "Data Models", "CategoryDef, SectorDef, TemplatePart, VariableDef, StyleDef, GenerationResult", group="technical"),
                VariableDef("migration", "Migration Plan", "Phase 1: Extract current logic to DefaultGenerator plugin\nPhase 2: Migrate categories to JSON\nPhase 3: Add plugin discovery\nPhase 4: Deprecate old code", group="technical"),
                VariableDef("risks", "Risks", "• Plugin sandbox security (eval lambdas)\n• Version compatibility\n• Performance overhead", group="technical"),
                VariableDef("rollback", "Rollback", "Feature flag: `USE_PLUGIN_ARCHITECTURE`. Can disable instantly.", group="technical"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "RFC Header", "# {title}\n\n**Author:** {author}  \n**Status:** {status}  \n**Date:** {date}", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Context + Problem", "## Context\n{context}\n\n## Problem\n{problem}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Proposal + Alternatives", "## Proposal\n{proposal}\n\n## Alternatives Considered\n{alternatives}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m3", "Technical Design", "## API Design\n{api_design}\n\n## Data Models\n{data_models}", SectionType.MIDDLE, weight=1.2),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Migration + Risks", "## Migration Plan\n{migration}\n\n## Risks & Mitigation\n{risks}\n\n## Rollback\n{rollback}", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [],
            ],
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("markdown", "Markdown RFC", "GitHub-ready", "lambda t: t"),
                StyleDef("notion", "Notion Export", "Block-friendly", "lambda t: t.replace('## ', '\\n## ').replace('### ', '\\n### ')"),
            ],
        )
    
    # ─── Academic ───
    def _cat_research_abstract(self) -> CategoryDef:
        return CategoryDef(
            key="research_abstract",
            name="Research Paper Abstract",
            description: "Structured abstract: Background, Methods, Results, Conclusions. Journal-ready.",
            icon="🔬",
            sector="academic",
            variables=[
                VariableDef("title", "Paper Title", "Plugin Architectures for Generative Content Systems: A Modular Approach", group="meta"),
                VariableDef("background", "Background", "Content generation tools increasingly require domain-specific templates and style adaptation. Current monolithic architectures limit extensibility and user customization.", group="core"),
                VariableDef("methods", "Methods", "We designed a plugin-based architecture separating category definitions (data) from generation logic (code). Evaluated via usability study (n=47) and performance benchmarks.", group="core"),
                VariableDef("results", "Results", "Plugin architecture reduced category addition time from 2.3 hours to 4 minutes. Generation latency <50ms. User satisfaction 4.7/5 vs 3.2/5 for monolithic baseline.", group="core"),
                VariableDef("conclusions", "Conclusions", "Decoupling data from logic via plugin registry enables rapid domain adaptation while maintaining type safety and sandboxed execution.", group="core"),
                VariableDef("keywords", "Keywords", "generative AI, plugin architecture, content generation, human-computer interaction, software architecture", group="meta"),
                VariableDef("doi", "DOI", "10.1234/writeup.2026.001", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Structured Abstract", "**Background:** {background}\n\n**Methods:** {methods}\n\n**Results:** {results}\n\n**Conclusions:** {conclusions}\n\n**Keywords:** {keywords}", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Citation", "{title}. DOI: {doi}", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("apa", "APA 7th", "Formatted", "lambda t: t.replace('**Background:**', 'Background:').replace('**Methods:**', 'Methods:').replace('**Results:**', 'Results:').replace('**Conclusions:**', 'Conclusions:')"),
                StyleDef("structured", "Structured (JAMA)", "Labeled sections", "lambda t: t"),
            ],
        )
    
    def _cat_grant_proposal(self) -> CategoryDef:
        return CategoryDef(
            key="grant_proposal",
            name="Grant Proposal (NIH/NSF/EU Style)",
            description: "Specific aims, significance, innovation, approach, timeline. Reviewer-friendly.",
            icon="💰",
            sector="academic",
            variables=[
                VariableDef("title", "Project Title", "Democratizing High-Quality Content Generation via Modular Plugin Architectures", group="meta"),
                VariableDef("pi", "PI", "Dr. Alex Chen", group="meta"),
                VariableDef("institution", "Institution", "Institute for Creative Technology", group="meta"),
                VariableDef("funding_mechanism", "Mechanism", "NSF CISE IIS", options=["NIH R01", "NSF CISE", "ERC Starting Grant", "DOE Early Career", "Foundation"], type="select", group="meta"),
                VariableDef("amount", "Requested Amount", "$1.2M over 3 years", group="meta"),
                VariableDef("specific_aims", "Specific Aims", "Aim 1: Build plugin registry with sandboxed execution\nAim 2: Develop sector-organized template library (10+ domains)\nAim 3: Validate via randomized controlled trial with 200 content creators", group="core"),
                VariableDef("significance", "Significance", "Current tools force tradeoff: speed vs. quality vs. voice. This work eliminates the tradeoff.", group="core"),
                VariableDef("innovation", "Innovation", "First plugin architecture for generative content with formal safety guarantees on user-provided lambdas.", group="core"),
                VariableDef("approach", "Approach", "Year 1: Core registry + sandbox. Year 2: Domain libraries + RCT. Year 3: Open-source platform + community governance.", group="core"),
                VariableDef("timeline", "Timeline", "Q1-2: Architecture. Q3-4: Beta. Y2: RCT. Y3: Scale.", group="core"),
                VariableDef("preliminary_data", "Preliminary Data", "Beta (n=500): 94% retention, 4.8★, 12M words generated. Latency p99 < 50ms.", group="proof"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Cover", "**{title}**\nPI: {pi} ({institution})\nMechanism: {funding_mechanism}\nAmount: {amount}", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Specific Aims", "## Specific Aims\n{specific_aims}", SectionType.MIDDLE, weight=1.2),
                    TemplatePart("m2", "Significance", "## Significance\n{significance}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m3", "Innovation", "## Innovation\n{innovation}", SectionType.MIDDLE, weight=1.0),
                    TemplatePart("m4", "Approach", "## Approach\n{approach}\n\n## Timeline\n{timeline}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m5", "Preliminary Data", "## Preliminary Data\n{preliminary_data}", SectionType.MIDDLE, weight=1.0),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Budget Justification", "Budget: Personnel (60%), Compute (20%), Participant compensation (15%), Travel/Dissemination (5%).", SectionType.CLOSER, weight=0.8),
                ],
                SectionType.EXTRA: [],
            ],
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("nih", "NIH Format", "Specific Aims page", "lambda t: t"),
                StyleDef("nsf", "NSF Format", "Project Summary", "lambda t: t[:4600]"),
            ],
        )
    
    def _cat_literature_review(self) -> CategoryDef:
        return CategoryDef(
            key="literature_review",
            name="Literature Review Section",
            description: "Thematic synthesis, gap identification, theoretical framework. Not a bibliography dump.",
            icon="📚",
            sector="academic",
            variables=[
                VariableDef("topic", "Topic", "Plugin architectures for generative content systems", group="core"),
                VariableDef("gap", "Research Gap", "No prior work combines sandboxed user-defined transformers with sector-organized template libraries in a unified registry.", group="core"),
                VariableDef("themes", "Key Themes", "1) Template-based generation (Smith et al. 2021)\n2) Style transfer in NLG (Chen & Liu 2022)\n3) Plugin systems for ML (Garcia 2023)\n4) Human-AI co-creation (Wang et al. 2024)", group="core"),
                VariableDef("theoretical_framework", "Framework", "Sociotechnical systems theory + Cognitive load theory", group="core"),
                VariableDef("key_findings", "Key Findings", "• Templates reduce cognitive load 40% (Smith 2021)\n• Style transfer degrades semantic fidelity 12-18% (Chen 2022)\n• Plugin sandboxes introduce <5% latency (Garcia 2023)\n• Co-creation improves perceived ownership (Wang 2024)", group="proof"),
                VariableDef("hypothesis", "Hypothesis", "H1: Plugin architecture + sector templates → 50% faster domain adaptation\nH2: Sandboxed lambdas → <5% fidelity loss vs. fine-tuning", group="core"),
                VariableDef("citations", "Key Citations", "Smith et al. 2021 (TOCHI), Chen & Liu 2022 (ACL), Garcia 2023 (OSDI), Wang et al. 2024 (CHI)", group="meta"),
            ],
            parts={
                SectionType.OPENER: [
                    TemplatePart("o1", "Opening", "Research on {topic} spans four interconnected themes:", SectionType.OPENER, weight=1.2),
                ],
                SectionType.MIDDLE: [
                    TemplatePart("m1", "Themes", "{themes}", SectionType.MIDDLE, weight=1.1),
                    TemplatePart("m2", "Synthesis", "## Synthesis\n{key_findings}\n\n## Theoretical Framework\n{theoretical_framework}", SectionType.MIDDLE, weight=1.2),
                    TemplatePart("m3", "Gap + Hypothesis", "## Gap\n{gap}\n\n## Hypotheses\n{hypothesis}", SectionType.MIDDLE, weight=1.1),
                ],
                SectionType.CLOSER: [
                    TemplatePart("c1", "Transition", "Building on these foundations, we propose a plugin architecture that addresses the identified gap while preserving the benefits of template-based generation and style adaptation.", SectionType.CLOSER, weight=1.0),
                ],
                SectionType.EXTRA: [
                    TemplatePart("e1", "References", "{citations}", SectionType.EXTRA, weight=0.7),
                ],
            },
            styles=[
                StyleDef("clean", "Clean", "Plain", "lambda t: t"),
                StyleDef("apa", "APA Style", "In-text citations", "lambda t: t"),
                StyleDef("narrative", "Narrative Flow", "Prose-heavy", "lambda t: t.replace('•', '').replace('\\n', ' ').replace('  ', ' ').replace('. ', '. ').replace('## ', '\\n\\n')"),
            ],
        )

# ═══════════════════════════════════════════════════════════════════════
# STREAMLIT APP — PREMIUM UI
# ═══════════════════════════════════════════════════════════════════════

def inject_premium_css():
    """Inject complete premium design system."""
    css = f"""
<style>
:root {{
    --bg-primary: {TOKENS.bg_primary};
    --bg-secondary: {TOKENS.bg_secondary};
    --bg-tertiary: {TOKENS.bg_tertiary};
    --bg-glass: {TOKENS.bg_glass};
    --border-subtle: {TOKENS.border_subtle};
    --border-strong: {TOKENS.border_strong};
    --fg-primary: {TOKENS.fg_primary};
    --fg-secondary: {TOKENS.fg_secondary};
    --fg-muted: {TOKENS.fg_muted};
    --accent-primary: {TOKENS.accent_primary};
    --accent-secondary: {TOKENS.accent_secondary};
    --accent-tertiary: {TOKENS.accent_tertiary};
    --success: {TOKENS.success};
    --warning: {TOKENS.warning};
    --error: {TOKENS.error};
    --grad-primary: {TOKENS.grad_primary};
    --grad-secondary: {TOKENS.grad_secondary};
    --grad-mesh: {TOKENS.grad_mesh};
    --space-xs: {TOKENS.space_xs};
    --space-sm: {TOKENS.space_sm};
    --space-md: {TOKENS.space_md};
    --space-lg: {TOKENS.space_lg};
    --space-xl: {TOKENS.space_xl};
    --space-2xl: {TOKENS.space_2xl};
    --radius-sm: {TOKENS.radius_sm};
    --radius-md: {TOKENS.radius_md};
    --radius-lg: {TOKENS.radius_lg};
    --radius-xl: {TOKENS.radius_xl};
    --radius-full: {TOKENS.radius_full};
    --shadow-sm: {TOKENS.shadow_sm};
    --shadow-md: {TOKENS.shadow_md};
    --shadow-lg: {TOKENS.shadow_lg};
    --shadow-glow: {TOKENS.shadow_glow};
    --font-sans: {TOKENS.font_sans};
    --font-mono: {TOKENS.font_mono};
    --transition-fast: {TOKENS.transition_fast};
    --transition-normal: {TOKENS.transition_normal};
    --transition-slow: {TOKENS.transition_slow};
}}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: var(--bg-primary) !important;
    color: var(--fg-primary) !important;
    font-family: var(--font-sans) !important;
}}

/* Mesh gradient background */
[data-testid="stAppViewContainer"]::before {{
    content: "";
    position: fixed;
    inset: 0;
    background: var(--grad-mesh);
    pointer-events: none;
    z-index: -1;
}}

/* Main container */
.main .block-container {{
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
}}

/* Premium Card */
.premium-card {{
    background: var(--bg-glass);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-md);
    box-shadow: var(--shadow-md);
    transition: all var(--transition-normal);
}}
.premium-card:hover {{
    border-color: var(--border-strong);
    box-shadow: var(--shadow-lg);
}}

/* Glass Card (lighter) */
.glass-card {{
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-bottom: var(--space-sm);
}}

/* Gradient Border Card */
.grad-border-card {{
    position: relative;
    background: var(--bg-secondary);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-md);
    overflow: hidden;
}}
.grad-border-card::before {{
    content: "";
    position: absolute;
    inset: 0;
    border-radius: var(--radius-lg);
    padding: 1px;
    background: var(--grad-primary);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    opacity: 0.6;
}}

/* Buttons */
.stButton > button {{
    background: var(--bg-tertiary) !important;
    color: var(--fg-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    padding: 0.625rem 1.25rem !important;
    font-weight: 500 !important;
    font-family: var(--font-sans) !important;
    font-size: 0.875rem !important;
    transition: all var(--transition-fast) !important;
    position: relative !important;
    overflow: hidden !important;
}}
.stButton > button:hover {{
    background: var(--bg-glass) !important;
    border-color: var(--accent-primary) !important;
    box-shadow: var(--shadow-glow) !important;
    transform: translateY(-1px) !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}
.stButton > button[kind="primary"] {{
    background: var(--grad-primary) !important;
    color: var(--bg-primary) !important;
    border: none !important;
    font-weight: 600 !important;
}}
.stButton > button[kind="primary"]:hover {{
    box-shadow: 0 0 24px rgba(34, 211, 238, 0.4) !important;
}}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div,
.stNumberInput > div > div > input {{
    background: var(--bg-tertiary) !important;
    color: var(--fg-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    font-family: var(--font-sans) !important;
    transition: all var(--transition-fast) !important;
}}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > div:focus-within {{
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.15) !important;
}}

/* Selectbox dropdown */
.stSelectbox [data-baseweb="popover"] {{
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-lg) !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: transparent !important;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--fg-secondary) !important;
    border: none !important;
    border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
    padding: var(--space-sm) var(--space-md) !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    position: relative !important;
    transition: all var(--transition-fast) !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: var(--fg-primary) !important;
    background: var(--bg-tertiary) !important;
}}
.stTabs [aria-selected="true"] {{
    color: var(--accent-primary) !important;
    background: var(--bg-tertiary) !important;
}}
.stTabs [aria-selected="true"]::after {{
    content: "";
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--grad-primary);
    border-radius: 2px 2px 0 0;
}}

/* Expander */
.streamlit-expanderHeader {{
    background: var(--bg-tertiary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
    color: var(--fg-primary) !important;
    font-weight: 500 !important;
    padding: var(--space-sm) var(--space-md) !important;
}}
.streamlit-expanderContent {{
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius-md) var(--radius-md) !important;
    padding: var(--space-md) !important;
}}

/* Data Editor / DataFrame */
.stDataFrame {{
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
}}

/* Code blocks */
.stCodeBlock, .stCodeBlock > div {{
    background: #0d1117 !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--radius-md) !important;
}}
.stCodeBlock code {{
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    line-height: 1.6 !important;
}}

/* Output Display */
.output-display {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: var(--space-xl);
    min-height: 280px;
    font-family: var(--font-sans);
    line-height: 1.8;
    white-space: pre-wrap;
    word-wrap: break-word;
    position: relative;
    overflow: hidden;
}}
.output-display::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--grad-primary);
}}
.output-placeholder {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 280px;
    color: var(--fg-muted);
    text-align: center;
    padding: var(--space-2xl);
}}
.output-placeholder .icon {{
    font-size: 3rem;
    margin-bottom: var(--space-md);
    opacity: 0.5;
}}
.output-placeholder .title {{
    font-size: 1.125rem;
    font-weight: 500;
    color: var(--fg-secondary);
    margin-bottom: var(--space-xs);
}}
.output-placeholder .desc {{
    font-size: 0.875rem;
    color: var(--fg-muted);
}}

/* History Item */
.history-item {{
    background: var(--bg-tertiary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-bottom: var(--space-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
    position: relative;
    overflow: hidden;
}}
.history-item::before {{
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: var(--grad-primary);
    opacity: 0;
    transition: opacity var(--transition-fast);
}}
.history-item:hover {{
    background: var(--bg-glass);
    border-color: var(--accent-primary);
    transform: translateX(4px);
}}
.history-item:hover::before {{
    opacity: 1;
}}
.history-item.current {{
    border-color: var(--accent-primary);
    background: rgba(34, 211, 238, 0.05);
}}
.history-item.current::before {{
    opacity: 1;
}}
.history-preview {{
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--fg-primary);
    margin-bottom: var(--space-xs);
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
.history-meta {{
    display: flex;
    gap: var(--space-md);
    font-size: 0.7rem;
    color: var(--fg-muted);
    flex-wrap: wrap;
}}
.history-badge {{
    padding: 2px 8px;
    border-radius: var(--radius-full);
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}}

/* Sector Pill */
.sector-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    cursor: pointer;
    transition: all var(--transition-fast);
    border: 1px solid transparent;
}}
.sector-pill:hover {{
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}}
.sector-pill.active {{
    box-shadow: 0 0 0 2px var(--bg-primary), 0 0 0 4px currentColor;
}}

/* Category Card */
.category-card {{
    background: var(--bg-tertiary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
    cursor: pointer;
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}}
.category-card::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--sector-gradient);
    opacity: 0;
    transition: opacity var(--transition-normal);
}}
.category-card:hover {{
    border-color: var(--border-strong);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}}
.category-card:hover::before {{
    opacity: 1;
}}
.category-card.selected {{
    border-color: var(--sector-color);
    background: rgba(var(--sector-color-rgb), 0.08);
}}
.category-card.selected::before {{
    opacity: 1;
}}
.category-icon {{
    font-size: 1.5rem;
    margin-bottom: var(--space-xs);
}}
.category-name {{
    font-weight: 600;
    font-size: 0.9375rem;
    color: var(--fg-primary);
    margin-bottom: 2px;
}}
.category-desc {{
    font-size: 0.75rem;
    color: var(--fg-muted);
    line-height: 1.4;
}}

/* Variable Row */
.variable-row {{
    display: grid;
    grid-template-columns: 140px 1fr 80px 40px;
    gap: var(--space-sm);
    align-items: start;
    padding: var(--space-sm) 0;
    border-bottom: 1px solid var(--border-subtle);
}}
.variable-row:last-child {{ border-bottom: none; }}
.variable-label {{
    font-size: 0.8125rem;
    color: var(--fg-secondary);
    font-weight: 500;
}}
.variable-required::after {{
    content: "*";
    color: var(--error);
    margin-left: 2px;
}}

/* Template Part Card */
.part-card {{
    background: var(--bg-tertiary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: var(--space-md);
    margin-bottom: var(--space-sm);
    transition: all var(--transition-fast);
}}
.part-card:hover {{
    border-color: var(--border-strong);
}}
.part-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
}}
.part-id {{
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--fg-muted);
    background: var(--bg-primary);
    padding: 2px 8px;
    border-radius: var(--radius-sm);
}}
.part-name {{
    font-weight: 600;
    font-size: 0.875rem;
}}
.part-content {{
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--fg-secondary);
    background: var(--bg-primary);
    padding: var(--space-sm);
    border-radius: var(--radius-sm);
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 120px;
    overflow-y: auto;
}}

/* Toast */
.toast-container {{
    position: fixed;
    bottom: var(--space-xl);
    right: var(--space-xl);
    z-index: {TOKENS.z_toast};
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
    pointer-events: none;
}}
.toast {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-md);
    padding: var(--space-md) var(--space-lg);
    box-shadow: var(--shadow-lg);
    display: flex;
    align-items: center;
    gap: var(--space-md);
    min-width: 280px;
    max-width: 400px;
    animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    pointer-events: auto;
}}
.toast.success {{ border-left: 3px solid var(--success); }}
.toast.error {{ border-left: 3px solid var(--error); }}
.toast.warning {{ border-left: 3px solid var(--warning); }}
.toast.info {{ border-left: 3px solid var(--accent-primary); }}
@keyframes slideIn {{
    from {{ opacity: 0; transform: translateX(100px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes slideOut {{
    from {{ opacity: 1; transform: translateX(0); }}
    to {{ opacity: 0; transform: translateX(100px); }}
}}

/* Modal Overlay */
.modal-overlay {{
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    backdrop-filter: blur(4px);
    z-index: {TOKENS.z_modal};
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-lg);
    animation: fadeIn 0.2s ease;
}}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.modal {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-xl);
    padding: var(--space-xl);
    max-width: 560px;
    width: 100%;
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: var(--shadow-lg);
    animation: slideUp 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}
@keyframes slideUp {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
.modal-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-lg);
    padding-bottom: var(--space-md);
    border-bottom: 1px solid var(--border-subtle);
}}
.modal-title {{
    font-size: 1.125rem;
    font-weight: 600;
}}
.modal-close {{
    background: none;
    border: none;
    color: var(--fg-muted);
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    transition: color var(--transition-fast);
}}
.modal-close:hover {{ color: var(--fg-primary); }}

/* Keyboard Shortcut Hint */
.kbd {{
    font-family: var(--font-mono);
    font-size: 0.7rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    padding: 2px 6px;
    color: var(--fg-muted);
    white-space: nowrap;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: var(--bg-primary); }}
::-webkit-scrollbar-thumb {{ background: var(--border-strong); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--fg-muted); }}

/* Hide Streamlit chrome */
#MainMenu, footer, header, .stDeployButton {{ visibility: hidden !important; }}
[data-testid="stToolbar"] {{ display: none !important; }}

/* Responsive */
@media (max-width: 768px) {{
    .main .block-container {{ padding-left: var(--space-md) !important; padding-right: var(--space-md) !important; }}
    .variable-row {{ grid-template-columns: 1fr; }}
    .variable-label {{ grid-column: 1 / -1; }}
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

def init_session_state():
    defaults = {
        "registry": Registry(),
        "current_sector": "personal",
        "current_category": "romance_dating",
        "history": [],
        "theme_mode": ThemeMode.DARK,
        "toasts": [],
        "modal_open": None,
        "modal_data": None,
        "editing_part": None,
        "adding_part_section": None,
        "adding_variable": False,
        "show_new_category": False,
        "show_new_sector": False,
        "live_preview": True,
        "auto_generate": False,
        "keyboard_shortcuts": True,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

registry: Registry = st.session_state.registry
current_cat: CategoryDef = registry.get_category(st.session_state.current_category)
current_sector: SectorDef = registry.get_sector(st.session_state.current_sector)

# ═══════════════════════════════════════════════════════════════════════
# UI COMPONENTS
# ═══════════════════════════════════════════════════════════════════════

def render_toast(message: str, type: str = "info", duration: int = 3000):
    st.session_state.toasts.append({"id": str(uuid.uuid4()), "message": message, "type": type, "time": datetime.now()})
    # Auto-clean handled in render_toasts()

def render_toasts():
    if not st.session_state.toasts:
        return
    now = datetime.now()
    st.session_state.toasts = [t for t in st.session_state.toasts if (now - t["time"]).total_seconds() * 1000 < 5000]
    
    toast_html = '<div class="toast-container">'
    for toast in st.session_state.toasts:
        toast_html += f'<div class="toast {toast["type"]}">{toast["message"]}</div>'
    toast_html += '</div>'
    st.markdown(toast_html, unsafe_allow_html=True)

def render_modal():
    if not st.session_state.modal_open:
        return
    
    title, content, actions = st.session_state.modal_data
    
    modal_html = f"""
<div class="modal-overlay" onclick="parent.postMessage({{'type': 'modal_close'}}, '*')">
    <div class="modal" onclick="event.stopPropagation()">
        <div class="modal-header">
            <span class="modal-title">{title}</span>
            <button class="modal-close" onclick="parent.postMessage({{'type': 'modal_close'}}, '*')">×</button>
        </div>
        {content}
    </div>
</div>
"""
    st.markdown(modal_html, unsafe_allow_html=True)
    
    # Handle actions via session state
    for action_key, action_fn in actions.items():
        if st.session_state.get(f"modal_action_{action_key}"):
            action_fn()
            st.session_state[f"modal_action_{action_key}"] = False
            st.session_state.modal_open = False
            st.rerun()

def open_modal(title: str, content: str, actions: Dict[str, Callable]):
    st.session_state.modal_open = True
    st.session_state.modal_data = (title, content, actions)

def close_modal():
    st.session_state.modal_open = False
    st.session_state.modal_data = None

# ═══════════════════════════════════════════════════════════════════════
# SIDEBAR — SECTOR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="padding: var(--space-md) 0; border-bottom: 1px solid var(--border-subtle); margin-bottom: var(--space-md);">
        <div style="display: flex; align-items: center; gap: var(--space-sm);">
            <div style="width: 40px; height: 40px; border-radius: var(--radius-md); background: var(--grad-primary); display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">✍️</div>
            <div>
                <div style="font-weight: 700; font-size: 1.125rem; background: var(--grad-primary); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">WriteUp Studio</div>
                <div style="font-size: 0.7rem; color: var(--fg-muted); text-transform: uppercase; letter-spacing: 0.05em;">Premium Edition</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sector Pills
    st.markdown("### Sectors")
    sectors_sorted = sorted(registry.sectors.values(), key=lambda s: s.order)
    for sector in sectors_sorted:
        is_active = sector.key == st.session_state.current_sector
        cats = registry.get_categories_by_sector(sector.key)
        cat_count = len(cats)
        
        pill_html = f"""
        <div class="sector-pill {'active' if is_active else ''}" style="background: {sector.gradient}; color: white; margin-bottom: 6px;" 
             onclick="parent.postMessage({{'type': 'sector_select', 'sector': '{sector.key}'}}, '*')">
            <span>{sector.icon}</span>
            <span>{sector.name}</span>
            <span style="margin-left: auto; background: rgba(255,255,255,0.2); padding: 2px 8px; border-radius: var(--radius-full); font-size: 0.65rem;">{cat_count}</span>
        </div>
        """
        st.markdown(pill_html, unsafe_allow_html=True)
    
    # Handle sector selection via query params / session state hack
    # Streamlit doesn't support onclick directly, so we use a selectbox as fallback
    sector_options = {s.key: s.name for s in sectors_sorted}
    selected_sector = st.selectbox(
        "Navigate Sector",
        options=list(sector_options.keys()),
        format_func=lambda k: sector_options[k],
        index=list(sector_options.keys()).index(st.session_state.current_sector),
        label_visibility="collapsed",
        key="sector_nav_select"
    )
    if selected_sector != st.session_state.current_sector:
        st.session_state.current_sector = selected_sector
        # Auto-select first category in sector
        cats = registry.get_categories_by_sector(selected_sector)
        if cats:
            st.session_state.current_category = cats[0].key
        st.rerun()
    
    st.divider()
    
    # Categories in current sector
    st.markdown("### Categories")
    cats_in_sector = registry.get_categories_by_sector(st.session_state.current_sector)
    for cat in cats_in_sector:
        is_selected = cat.key == st.session_state.current_category
        sector_color = registry.get_sector(cat.sector).color if registry.get_sector(cat.sector) else TOKENS.accent_primary
        
        card_html = f"""
        <div class="category-card {'selected' if is_selected else ''}" 
             style="--sector-gradient: {registry.get_sector(cat.sector).gradient if registry.get_sector(cat.sector) else TOKENS.grad_primary}; --sector-color: {sector_color}; --sector-color-rgb: {tuple(int(sector_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))};"
             onclick="parent.postMessage({{'type': 'category_select', 'category': '{cat.key}'}}, '*')">
            <div class="category-icon">{cat.icon}</div>
            <div class="category-name">{cat.name}</div>
            <div class="category-desc">{cat.description[:80]}{'...' if len(cat.description) > 80 else ''}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    
    # Category selectbox fallback
    cat_options = {c.key: c.name for c in cats_in_sector}
    if cat_options:
        selected_cat = st.selectbox(
            "Select Category",
            options=list(cat_options.keys()),
            format_func=lambda k: cat_options[k],
            index=list(cat_options.keys()).index(st.session_state.current_category) if st.session_state.current_category in cat_options else 0,
            label_visibility="collapsed",
            key="cat_nav_select"
        )
        if selected_cat != st.session_state.current_category:
            st.session_state.current_category = selected_cat
            st.rerun()
    
    st.divider()
    
    # Quick Actions
    st.markdown("### Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Category", use_container_width=True):
            st.session_state.show_new_category = True
            st.rerun()
    with col2:
        if st.button("📥 Import", use_container_width=True):
            st.session_state.modal_open = True
            st.session_state.modal_data = ("Import Category", render_import_modal_content(), {"import": do_import_category})
            st.rerun()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("📤 Export All", use_container_width=True):
            export_all_categories()
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.modal_open = True
            st.session_state.modal_data = ("Settings", render_settings_modal_content(), {"save_settings": save_settings})
            st.rerun()
    
    # Theme Toggle
    theme_col1, theme_col2, theme_col3 = st.columns(3)
    theme_icons = {"dark": "🌙", "light": "☀️", "auto": "🖥️"}
    for i, (mode, icon) in enumerate(theme_icons.items()):
        with [theme_col1, theme_col2, theme_col3][i]:
            if st.button(icon, use_container_width=True, type="primary" if st.session_state.theme_mode == ThemeMode(mode) else "secondary"):
                st.session_state.theme_mode = ThemeMode(mode)
                st.rerun()
    
    st.divider()
    st.caption(f"v2.1.0 • {len(registry.categories)} categories • {len(registry.sectors)} sectors")

# ═══════════════════════════════════════════════════════════════════════
# MODAL CONTENTS
# ═══════════════════════════════════════════════════════════════════════

def render_import_modal_content() -> str:
    return """
    <div style="display: flex; flex-direction: column; gap: var(--space-md);">
        <p style="color: var(--fg-secondary); margin: 0;">Paste category JSON or upload a .json file</p>
        <textarea id="import-json" style="width: 100%; min-height: 200px; background: var(--bg-tertiary); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--fg-primary); padding: var(--space-md); font-family: var(--font-mono); font-size: 0.75rem; resize: vertical;" placeholder='{"name": "My Category", "key": "my_category", "sector": "personal", ...}'></textarea>
        <div style="display: flex; gap: var(--space-sm); justify-content: flex-end;">
            <button class="stButton" onclick="parent.postMessage({type: 'modal_close'}, '*')">Cancel</button>
            <button class="stButton" kind="primary" onclick="doImport()">Import</button>
        </div>
    </div>
    <script>
    function doImport() {
        const json = document.getElementById('import-json').value;
        parent.postMessage({type: 'import_category', json: json}, '*');
    }
    </script>
    """

def render_settings_modal_content() -> str:
    return f"""
    <div style="display: flex; flex-direction: column; gap: var(--space-lg);">
        <div>
            <label style="display: block; font-weight: 500; margin-bottom: var(--space-sm);">Theme</label>
            <div style="display: flex; gap: var(--space-sm);">
                <button class="stButton {'primary' if st.session_state.theme_mode == ThemeMode.DARK else 'secondary'}" onclick="parent.postMessage({{type: 'set_theme', mode: 'dark'}}, '*')">🌙 Dark</button>
                <button class="stButton {'primary' if st.session_state.theme_mode == ThemeMode.LIGHT else 'secondary'}" onclick="parent.postMessage({{type: 'set_theme', mode: 'light'}}, '*')">☀️ Light</button>
                <button class="stButton {'primary' if st.session_state.theme_mode == ThemeMode.AUTO else 'secondary'}" onclick="parent.postMessage({{type: 'set_theme', mode: 'auto'}}, '*')">🖥️ Auto</button>
            </div>
        </div>
        <div>
            <label style="display: block; font-weight: 500; margin-bottom: var(--space-sm);">Live Preview</label>
            <label style="display: flex; align-items: center; gap: var(--space-sm); cursor: pointer;">
                <input type="checkbox" {"checked" if st.session_state.live_preview else ""} onchange="parent.postMessage({{type: 'set_live_preview', value: this.checked}}, '*')">
                <span>Generate preview as you type</span>
            </label>
        </div>
        <div>
            <label style="display: block; font-weight: 500; margin-bottom: var(--space-sm);">Keyboard Shortcuts</label>
            <label style="display: flex; align-items: center; gap: var(--space-sm); cursor: pointer;">
                <input type="checkbox" {"checked" if st.session_state.keyboard_shortcuts else ""} onchange="parent.postMessage({{type: 'set_shortcuts', value: this.checked}}, '*')">
                <span>Enable keyboard shortcuts (Ctrl+G generate, Ctrl+S save, etc.)</span>
            </label>
        </div>
        <div style="display: flex; gap: var(--space-sm); justify-content: flex-end; margin-top: var(--space-md);">
            <button class="stButton" onclick="parent.postMessage({{type: 'modal_close'}}, '*')">Cancel</button>
            <button class="stButton" kind="primary" onclick="parent.postMessage({{type: 'save_settings'}}, '*')">Save</button>
        </div>
    </div>
    """

# ═══════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════

# Re-fetch current category after potential changes
current_cat = registry.get_category(st.session_state.current_category)
current_sector = registry.get_sector(st.session_state.current_sector)

tab_generate, tab_variables, tab_templates, tab_styles, tab_analytics, tab_plugins = st.tabs([
    "🎲 Generate", "🔧 Variables", "📝 Templates", "🎨 Styles", "📊 Analytics", "🔌 Plugins"
])

# ═══════════════════════════════════════════════════════════════════════
# TAB: GENERATE
# ═══════════════════════════════════════════════════════════════════════

with tab_generate:
    # Header with category info
    sector_grad = current_sector.gradient if current_sector else TOKENS.grad_primary
    sector_color = current_sector.color if current_sector else TOKENS.accent_primary
    
    st.markdown(f"""
    <div class="grad-border-card" style="--sector-gradient: {sector_grad};">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: var(--space-md);">
            <div style="display: flex; align-items: center; gap: var(--space-md);">
                <span style="font-size: 2rem;">{current_cat.icon}</span>
                <div>
                    <h2 style="margin: 0; font-size: 1.5rem; font-weight: 700;">{current_cat.name}</h2>
                    <p style="margin: 0; color: var(--fg-secondary);">{current_cat.description}</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: var(--space-sm);">
                <span class="sector-pill" style="background: {sector_grad}; color: white;">{current_sector.icon} {current_sector.name}</span>
                <span class="badge badge-accent">v{current_cat.version}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Generation Controls
    with st.container():
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        
        col_style, col_sections, col_actions = st.columns([2, 3, 2], gap="large")
        
        with col_style:
            st.markdown("**Style**")
            style_options = {s.name: s.label for s in current_cat.styles}
            style_default = "clean" if "clean" in style_options else list(style_options.keys())[0]
            selected_style_name = st.selectbox(
                "Style",
                options=list(style_options.keys()),
                format_func=lambda k: style_options[k],
                index=list(style_options.keys()).index(style_default),
                label_visibility="collapsed",
                key="gen_style"
            )
            selected_style = next(s for s in current_cat.styles if s.name == selected_style_name)
            st.caption(selected_style.description)
        
        with col_sections:
            st.markdown("**Sections to Include**")
            sec_cols = st.columns(4)
            include_sections = []
            section_defaults = {
                SectionType.OPENER: True,
                SectionType.MIDDLE: True,
                SectionType.CLOSER: True,
                SectionType.EXTRA: False,
            }
            for i, sec in enumerate(SectionType):
                with sec_cols[i]:
                    count = len(current_cat.parts.get(sec, []))
                    label = f"{sec.value.capitalize()} ({count})"
                    if st.checkbox(label, value=section_defaults[sec], key=f"inc_{sec.value}"):
                        include_sections.append(sec)
        
        with col_actions:
            st.markdown("<br>", unsafe_allow_html=True)
            gen_col1, gen_col2 = st.columns(2)
            with gen_col1:
                generate_btn = st.button("🎲 Generate", type="primary", use_container_width=True, key="btn_generate")
            with gen_col2:
                batch_btn = st.button("🎲×5 Batch", use_container_width=True, key="btn_batch")
            
            st.markdown("<br>", unsafe_allow_html=True)
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                export_format = st.selectbox("Export", ["Markdown", "Text", "JSON", "HTML"], label_visibility="collapsed")
            with exp_col2:
                if st.button("💾 Export", use_container_width=True, key="btn_export"):
                    if st.session_state.history:
                        export_current(export_format.lower())
                    else:
                        render_toast("Nothing to export — generate first", "warning")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate Logic
    if generate_btn and include_sections:
        generator = registry.get_generator("default")
        variables = {v.key: v.default for v in current_cat.variables}
        result = generator.generate(current_cat, selected_style, include_sections, variables)
        st.session_state.history.insert(0, result)
        st.session_state.history = st.session_state.history[:100]
        render_toast(f"Generated with {selected_style.label} style", "success")
        st.rerun()
    
    if batch_btn and include_sections:
        generator = registry.get_generator("default")
        variables = {v.key: v.default for v in current_cat.variables}
        results = []
        for _ in range(5):
            results.append(generator.generate(current_cat, selected_style, include_sections, variables))
        
        combined_text = "\n\n" + "="*60 + "\n\n".join(r.text for r in results) + "\n"
        batch_result = GenerationResult(
            text=combined_text,
            category_key=current_cat.key,
            style_name=selected_style.name,
            sections_used=include_sections,
            variables_used=variables,
            template_ids=[tid for r in results for tid in r.template_ids],
            metadata={"batch": True, "count": len(results)}
        )
        st.session_state.history.insert(0, batch_result)
        st.session_state.history = st.session_state.history[:100]
        render_toast(f"Generated {len(results)} variations", "success")
        st.rerun()
    
    # Output Display
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### Output")
    
    if st.session_state.history:
        latest = st.session_state.history[0]
        
        # Action bar
        act_cols = st.columns([1, 1, 1, 1, 2])
        with act_cols[0]:
            if st.button("📋 Copy", use_container_width=True, key="copy_latest"):
                st.code(latest.text, language=None)
                render_toast("Copied to clipboard", "success")
        with act_cols[1]:
            st.download_button(
                "💾 Save",
                data=latest.text,
                file_name=f"writeup_{current_cat.key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with act_cols[2]:
            if st.button("🔄 Regenerate", use_container_width=True, key="regenerate"):
                generator = registry.get_generator("default")
                variables = {v.key: v.default for v in current_cat.variables}
                result = generator.generate(current_cat, selected_style, include_sections, variables)
                st.session_state.history[0] = result
                render_toast("Regenerated", "success")
                st.rerun()
        with act_cols[3]:
            if st.button("🗑️ Clear All", use_container_width=True, key="clear_history"):
                st.session_state.history.clear()
                render_toast("History cleared", "info")
                st.rerun()
        
        # Output content
        st.markdown(f'<div class="output-display">{latest.text}</div>', unsafe_allow_html=True)
        
        # Metadata
        meta_cols = st.columns(4)
        with meta_cols[0]:
            st.caption(f"Style: **{latest.style_name}**")
        with meta_cols[1]:
            st.caption(f"Sections: **{', '.join(s.value for s in latest.sections_used)}**")
        with meta_cols[2]:
            st.caption(f"Templates: **{len(latest.template_ids)}**")
        with meta_cols[3]:
            st.caption(f"Generated: **{latest.generated_at[:19].replace('T', ' ')}**")
    
    else:
        st.markdown(f"""
        <div class="output-placeholder">
            <div class="icon">🎲</div>
            <div class="title">Ready to Generate</div>
            <div class="desc">Select sections and click <strong>Generate</strong> to create your first write-up</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # History Sidebar (right side)
    # Note: In Streamlit we can't do true side-by-side with tabs easily, so we put history below
    if st.session_state.history:
        with st.expander(f"📜 History ({len(st.session_state.history)})", expanded=False):
            for i, item in enumerate(st.session_state.history[:20]):
                is_current = i == 0
                preview = item.text[:120].replace('\n', ' ') + ("…" if len(item.text) > 120 else "")
                batch_badge = " 📦 BATCH" if item.metadata.get("batch") else ""
                
                item_html = f"""
                <div class="history-item {'current' if is_current else ''}" onclick="parent.postMessage({{'type': 'history_select', 'index': {i}}}, '*')">
                    <div class="history-preview">{preview}</div>
                    <div class="history-meta">
                        <span class="history-badge">{item.style_name}{batch_badge}</span>
                        <span class="history-badge">{', '.join(s.value for s in item.sections_used)}</span>
                        <span class="history-badge">{item.generated_at[:16].replace('T', ' ')}</span>
                    </div>
                </div>
                """
                st.markdown(item_html, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TAB: VARIABLES
# ═══════════════════════════════════════════════════════════════════════

with tab_variables:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### Variables")
    st.caption("Define the placeholders used in templates. Values are saved per category and used during generation.")
    
    # Add Variable Modal Trigger
    if st.button("➕ Add Variable", use_container_width=False, key="btn_add_var"):
        st.session_state.adding_variable = True
        st.rerun()
    
    if st.session_state.adding_variable:
        with st.form("add_var_form", clear_on_submit=True):
            st.markdown("#### New Variable")
            vc1, vc2 = st.columns(2)
            with vc1:
                new_key = st.text_input("Key *", placeholder="e.g. goal", help="No spaces, lowercase, underscore only")
                new_label = st.text_input("Label *", placeholder="Relationship Goal")
                new_type = st.selectbox("Type", ["text", "textarea", "select", "multiselect", "boolean", "number"])
            with vc2:
                new_default = st.text_area("Default Value", placeholder="a wife, a partner, a forever love", height=100)
                new_required = st.checkbox("Required", value=True)
                new_group = st.text_input("Group", value="general", placeholder="core, contact, style, etc.")
                new_options = st.text_area("Options (comma-separated)", placeholder="option1, option2, option3", help="For select/multiselect types")
                new_help = st.text_input("Help Text", placeholder="Shown as tooltip")
                new_validation = st.text_input("Validation Regex", placeholder="^[a-z]+$")
            
            if st.form_submit_button("Add Variable", type="primary"):
                if new_key and new_label:
                    key = new_key.strip().lower().replace(' ', '_')
                    if not re.match(r'^[a-z][a-z0-9_]*$', key):
                        render_toast("Key must start with letter, only lowercase/underscore", "error")
                    elif any(v.key == key for v in current_cat.variables):
                        render_toast("Key already exists", "error")
                    else:
                        opts = [o.strip() for o in new_options.split(",")] if new_options else []
                        current_cat.variables.append(VariableDef(
                            key=key, label=new_label.strip(), default=new_default,
                            required=new_required, type=new_type, options=opts,
                            help=new_help, validation=new_validation or None, group=new_group.strip()
                        ))
                        current_cat.updated_at = datetime.now().isoformat()
                        registry.register_category(current_cat)
                        st.session_state.adding_variable = False
                        render_toast(f"Added variable: {key}", "success")
                        st.rerun()
                else:
                    render_toast("Key and Label are required", "error")
            
            if st.form_submit_button("Cancel"):
                st.session_state.adding_variable = False
                st.rerun()
    
    st.divider()
    
    # Variable Editor
    if current_cat.variables:
        # Group by group
        groups = {}
        for var in current_cat.variables:
            groups.setdefault(var.group, []).append(var)
        
        for group_name, vars_in_group in groups.items():
            st.markdown(f"**{group_name.title()}**")
            for var in vars_in_group:
                with st.container():
                    st.markdown('<div class="variable-row">', unsafe_allow_html=True)
                    
                    vcol1, vcol2, vcol3, vcol4 = st.columns([3, 5, 1, 1])
                    
                    with vcol1:
                        # Key (read-only)
                        st.text_input("Key", value=var.key, key=f"var_key_{var.key}", label_visibility="collapsed", disabled=True)
                    
                    with vcol2:
                        # Label + Input based on type
                        new_label = st.text_input("Label", value=var.label, key=f"var_label_{var.key}", label_visibility="collapsed")
                        
                        if var.type == "textarea":
                            new_val = st.text_area("Value", value=var.default, key=f"var_val_{var.key}", label_visibility="collapsed", height=80)
                        elif var.type == "select":
                            new_val = st.selectbox("Value", options=var.options, index=var.options.index(var.default) if var.default in var.options else 0, key=f"var_val_{var.key}", label_visibility="collapsed")
                        elif var.type == "multiselect":
                            default_list = var.default.split(",") if var.default else []
                            new_val_list = st.multiselect("Value", options=var.options, default=default_list, key=f"var_val_{var.key}", label_visibility="collapsed")
                            new_val = ",".join(new_val_list)
                        elif var.type == "boolean":
                            new_val = str(st.checkbox("Value", value=var.default.lower() in ("true", "1", "yes", "on"), key=f"var_val_{var.key}", label_visibility="collapsed")).lower()
                        elif var.type == "number":
                            new_val = str(st.number_input("Value", value=float(var.default) if var.default else 0, key=f"var_val_{var.key}", label_visibility="collapsed"))
                        else:
                            new_val = st.text_input("Value", value=var.default, key=f"var_val_{var.key}", label_visibility="collapsed")
                    
                    with vcol3:
                        new_required = st.checkbox("Required", value=var.required, key=f"var_req_{var.key}")
                    
                    with vcol4:
                        if st.button("🗑️", key=f"var_del_{var.key}", help="Delete variable"):
                            current_cat.variables = [v for v in current_cat.variables if v.key != var.key]
                            current_cat.updated_at = datetime.now().isoformat()
                            registry.register_category(current_cat)
                            render_toast(f"Deleted variable: {var.key}", "info")
                            st.rerun()
                    
                    # Auto-save on change
                    if new_label != var.label or new_val != var.default or new_required != var.required:
                        var.label = new_label
                        var.default = new_val
                        var.required = new_required
                        current_cat.updated_at = datetime.now().isoformat()
                        registry.register_category(current_cat)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No variables yet. Click **Add Variable** to create your first one.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TAB: TEMPLATES
# ═══════════════════════════════════════════════════════════════════════

with tab_templates:
    section_tabs = st.tabs([s.value.capitalize() for s in SectionType])
    
    for sec, sec_tab in zip(SectionType, section_tabs):
        with sec_tab:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            
            # Add Part Button
            add_key = f"add_part_{sec.value}"
            is_adding = st.session_state.adding_part_section == sec.value
            
            if st.button(f"➕ Add {sec.value.capitalize()} Part", key=f"btn_{add_key}", use_container_width=not is_adding):
                st.session_state.adding_part_section = sec.value if not is_adding else None
                st.rerun()
            
            if is_adding:
                with st.form(f"add_part_form_{sec.value}", clear_on_submit=True):
                    st.markdown(f"#### New {sec.value.capitalize()} Part")
                    pcol1, pcol2 = st.columns(2)
                    with pcol1:
                        part_id = st.text_input("ID *", placeholder=f"{sec.value[0]}{random.randint(10,99)}", help="Unique identifier")
                        part_name = st.text_input("Name *", placeholder="e.g. Direct, Vision, Hook")
                        part_weight = st.number_input("Weight", min_value=0.1, max_value=10.0, value=1.0, step=0.1, help="Higher = more likely to be selected")
                        part_tags = st.text_input("Tags (comma-separated)", placeholder="direct, values, short")
                    with pcol2:
                        st.caption("Use `{variable}` placeholders. Supports `{var.method}` like `{topic.capitalize()}`")
                        st.caption("Available variables: " + ", ".join([f"`{v.key}`" for v in current_cat.variables]))
                    part_content = st.text_area("Content *", height=140, placeholder="I'm not chasing a crowd. I'm chasing {goal}.")
                    
                    if st.form_submit_button("Add Part", type="primary"):
                        if part_id and part_name and part_content:
                            if any(p.id == part_id for p in current_cat.parts[sec]):
                                render_toast("ID already exists in this section", "error")
                            else:
                                current_cat.parts[sec].append(TemplatePart(
                                    id=part_id.strip(), name=part_name.strip(),
                                    content=part_content.strip(), section=sec,
                                    tags=[t.strip() for t in part_tags.split(",")] if part_tags else [],
                                    weight=part_weight
                                ))
                                current_cat.updated_at = datetime.now().isoformat()
                                registry.register_category(current_cat)
                                st.session_state.adding_part_section = None
                                render_toast(f"Added to {sec.value}", "success")
                                st.rerun()
                        else:
                            render_toast("All fields required", "error")
                    
                    if st.form_submit_button("Cancel"):
                        st.session_state.adding_part_section = None
                        st.rerun()
            
            st.divider()
            
            # Parts List
            parts = current_cat.parts.get(sec, [])
            if parts:
                for i, part in enumerate(parts):
                    with st.container():
                        st.markdown('<div class="part-card">', unsafe_allow_html=True)
                        
                        # Header
                        hcol1, hcol2, hcol3 = st.columns([4, 1, 1])
                        with hcol1:
                            st.markdown(f'<span class="part-id">{part.id}</span> <span class="part-name">{part.name}</span>', unsafe_allow_html=True)
                            if part.tags:
                                tags_html = " ".join([f'<span style="font-size: 0.65rem; background: var(--bg-primary); border: 1px solid var(--border-subtle); padding: 1px 6px; border-radius: var(--radius-full); margin-left: 4px;">{t}</span>' for t in part.tags])
                                st.markdown(tags_html, unsafe_allow_html=True)
                        with hcol2:
                            if st.button("✏️ Edit", key=f"edit_part_{sec.value}_{i}", use_container_width=True):
                                st.session_state.editing_part = (sec.value, i)
                                st.rerun()
                        with hcol3:
                            if st.button("🗑️", key=f"del_part_{sec.value}_{i}", use_container_width=True):
                                current_cat.parts[sec].pop(i)
                                current_cat.updated_at = datetime.now().isoformat()
                                registry.register_category(current_cat)
                                render_toast("Part deleted", "info")
                                st.rerun()
                        
                        # Edit Form
                        if st.session_state.editing_part == (sec.value, i):
                            with st.form(f"edit_part_form_{sec.value}_{i}"):
                                new_name = st.text_input("Name", value=part.name)
                                new_weight = st.number_input("Weight", min_value=0.1, max_value=10.0, value=part.weight, step=0.1)
                                new_tags = st.text_input("Tags", value=", ".join(part.tags))
                                new_content = st.text_area("Content", value=part.content, height=120)
                                
                                ecol1, ecol2, ecol3 = st.columns(3)
                                with ecol1:
                                    if st.form_submit_button("💾 Save", type="primary"):
                                        part.name = new_name.strip()
                                        part.weight = new_weight
                                        part.tags = [t.strip() for t in new_tags.split(",")] if new_tags else []
                                        part.content = new_content.strip()
                                        current_cat.updated_at = datetime.now().isoformat()
                                        registry.register_category(current_cat)
                                        st.session_state.editing_part = None
                                        render_toast("Saved", "success")
                                        st.rerun()
                                with ecol2:
                                    if st.form_submit_button("👁️ Preview"):
                                        vars_dict = {v.key: v.default for v in current_cat.variables}
                                        generator = registry.get_generator("default")
                                        preview = generator._interpolate(part.content, vars_dict)
                                        render_toast(f"Preview: {preview[:100]}...", "info")
                                with ecol3:
                                    if st.form_submit_button("✖️ Cancel"):
                                        st.session_state.editing_part = None
                                        st.rerun()
                        
                        # Live Preview
                        if st.session_state.live_preview:
                            with st.expander("🔍 Live Preview", expanded=False):
                                vars_dict = {v.key: v.default for v in current_cat.variables}
                                generator = registry.get_generator("default")
                                preview = generator._interpolate(part.content, vars_dict)
                                st.code(preview, language=None)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info(f"No {sec.value} parts yet. Click **Add {sec.value.capitalize()} Part** to create one.")
            
            st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TAB: STYLES
# ═══════════════════════════════════════════════════════════════════════

with tab_styles:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### Style Transformers")
    st.caption("Python lambda functions that transform generated text. Variable `t` = input text. Safe eval environment.")
    
    # Add Style
    with st.expander("➕ Add Style", expanded=False):
        with st.form("add_style_form", clear_on_submit=True):
            scol1, scol2 = st.columns([1, 3])
            with scol1:
                style_name = st.text_input("Name *", placeholder="emoji")
                style_label = st.text_input("Label *", placeholder="Emoji Style")
            with scol2:
                style_desc = st.text_input("Description", placeholder="Adds emojis to key terms")
                style_code = st.text_area("Lambda Code *", height=100, placeholder="lambda t: t.replace('wife', 'wife 👑').replace('forever', 'forever ❤️')")
                style_category = st.text_input("Category", value="general", placeholder="formatting, platform, tone")
            
            if st.form_submit_button("Add Style", type="primary"):
                if style_name and style_code:
                    if not style_code.strip().startswith("lambda"):
                        render_toast("Must be a lambda expression", "error")
                    else:
                        current_cat.styles.append(StyleDef(
                            name=style_name.strip(), label=style_label.strip() or style_name.strip(),
                            description=style_desc.strip(), code=style_code.strip(), category=style_category.strip()
                        ))
                        current_cat.updated_at = datetime.now().isoformat()
                        registry.register_category(current_cat)
                        render_toast(f"Added style: {style_name}", "success")
                        st.rerun()
                else:
                    render_toast("Name and lambda required", "error")
    
    # Style List with Live Test
    if current_cat.styles:
        for style in current_cat.styles:
            with st.container():
                st.markdown('<div class="part-card">', unsafe_allow_html=True)
                
                scol1, scol2, scol3 = st.columns([1, 4, 1])
                with scol1:
                    st.markdown(f'<span class="badge badge-accent">{style.name}</span>', unsafe_allow_html=True)
                    st.caption(style.label)
                with scol2:
                    st.code(style.code, language="python")
                    if style.description:
                        st.caption(style.description)
                with scol3:
                    if st.button("🧪 Test", key=f"test_style_{style.name}", use_container_width=True):
                        # Test with sample text
                        sample = "I'm looking for a wife and a forever love. We'll build a family together."
                        generator = registry.get_generator("default")
                        try:
                            safe_globals = {"__builtins__": {"str": str, "len": len}}
                            func = eval(style.code, safe_globals, {})
                            result = func(sample)
                            render_toast(f"Result: {result[:80]}...", "success")
                        except Exception as e:
                            render_toast(f"Error: {e}", "error")
                    
                    if st.button("🗑️", key=f"del_style_{style.name}", use_container_width=True):
                        current_cat.styles = [s for s in current_cat.styles if s.name != style.name]
                        current_cat.updated_at = datetime.now().isoformat()
                        registry.register_category(current_cat)
                        render_toast("Style deleted", "info")
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No styles yet. Add one above.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TAB: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════

with tab_analytics:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### Generation Analytics")
    
    if st.session_state.history:
        total = len(st.session_state.history)
        by_category = {}
        by_style = {}
        by_section = {s: 0 for s in SectionType}
        
        for item in st.session_state.history:
            by_category[item.category_key] = by_category.get(item.category_key, 0) + 1
            by_style[item.style_name] = by_style.get(item.style_name, 0) + 1
            for sec in item.sections_used:
                by_section[sec] += 1
        
        # Metrics
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.metric("Total Generations", total)
        with mcol2:
            st.metric("Categories Used", len(by_category))
        with mcol3:
            st.metric("Styles Used", len(by_style))
        with mcol4:
            avg_sections = sum(len(h.sections_used) for h in st.session_state.history) / total if total else 0
            st.metric("Avg Sections/Gen", f"{avg_sections:.1f}")
        
        # Charts (using simple bars since no plotly)
        st.markdown("#### By Category")
        for cat_key, count in sorted(by_category.items(), key=lambda x: -x[1])[:10]:
            cat_obj = registry.get_category(cat_key)
            pct = count / total * 100
            bar_width = int(pct * 2)
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: var(--space-sm); margin: 4px 0;">
                <span style="width: 120px; font-size: 0.8rem;">{cat_obj.icon if cat_obj else '📦'} {cat_key[:18]}</span>
                <div style="flex: 1; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden;">
                    <div style="width: {bar_width}%; height: 100%; background: var(--grad-primary); border-radius: 4px; transition: width 0.3s ease;"></div>
                </div>
                <span style="width: 50px; text-align: right; font-size: 0.75rem; color: var(--fg-muted);">{count} ({pct:.0f}%)</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### By Style")
        for style_name, count in sorted(by_style.items(), key=lambda x: -x[1])[:10]:
            pct = count / total * 100
            bar_width = int(pct * 2)
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: var(--space-sm); margin: 4px 0;">
                <span style="width: 120px; font-size: 0.8rem;">🎨 {style_name[:18]}</span>
                <div style="flex: 1; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden;">
                    <div style="width: {bar_width}%; height: 100%; background: var(--grad-secondary); border-radius: 4px; transition: width 0.3s ease;"></div>
                </div>
                <span style="width: 50px; text-align: right; font-size: 0.75rem; color: var(--fg-muted);">{count} ({pct:.0f}%)</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("#### Section Usage")
        for sec, count in sorted(by_section.items(), key=lambda x: -x[1]):
            pct = count / total * 100 if total else 0
            bar_width = int(pct * 2)
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: var(--space-sm); margin: 4px 0;">
                <span style="width: 120px; font-size: 0.8rem;">📄 {sec.value.capitalize()}</span>
                <div style="flex: 1; height: 8px; background: var(--bg-primary); border-radius: 4px; overflow: hidden;">
                    <div style="width: {bar_width}%; height: 100%; background: var(--accent-tertiary); border-radius: 4px; transition: width 0.3s ease;"></div>
                </div>
                <span style="width: 50px; text-align: right; font-size: 0.75rem; color: var(--fg-muted);">{count} ({pct:.0f}%)</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No generation history yet. Create some content to see analytics!")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# TAB: PLUGINS (Extensibility)
# ═══════════════════════════════════════════════════════════════════════

with tab_plugins:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### Plugin System")
    st.caption("Extend WriteUp Studio with custom generators, exporters, and transformers.")
    
    # Generators
    st.markdown("#### Generators")
    for name, gen in registry.generators.items():
        st.markdown(f"""
        <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>{name}</strong> — {gen.description}
            </div>
            <span class="badge badge-accent">Built-in</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Exporters
    st.markdown("#### Exporters")
    for name, exp in registry.exporters.items():
        st.markdown(f"""
        <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>.{exp.extension}</strong> — {exp.mime}
            </div>
            <span class="badge" style="background: var(--accent-secondary); color: var(--bg-primary);">Built-in</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Add Custom Plugin (Code Editor)
    st.markdown("#### Add Custom Plugin")
    with st.expander("🔧 Create Generator Plugin", expanded=False):
        with st.form("custom_generator_form"):
            plug_name = st.text_input("Plugin Name", placeholder="my_generator")
            plug_desc = st.text_input("Description", placeholder="Custom generator for X")
            plug_code = st.text_area("Plugin Code", height=200, placeholder='''
class MyGenerator:
    name = "my_generator"
    description = "Custom generator"
    
    def generate(self, category, style, sections, variables):
        # Your logic here
        from dataclasses import dataclass
        @dataclass
        class Result:
            text: str
            category_key: str
            style_name: str
            sections_used: list
            variables_used: dict
            template_ids: list
        
        return Result(
            text="Custom output",
            category_key=category.key,
            style_name=style.name,
            sections_used=sections,
            variables_used=variables,
            template_ids=[]
        )
''')
            if st.form_submit_button("Register Plugin", type="primary"):
                try:
                    exec(plug_code, {"__builtins__": {}})
                    # In real app, would register properly
                    render_toast("Plugin code accepted (demo only — not persisted)", "success")
                except Exception as e:
                    render_toast(f"Error: {e}", "error")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def export_current(format: str):
    if not st.session_state.history:
        return
    result = st.session_state.history[0]
    cat = registry.get_category(result.category_key)
    exporter = registry.get_exporter(format)
    data = exporter.export(result, cat)
    st.download_button(
        f"Download .{exporter.extension}",
        data=data,
        file_name=f"writeup_{result.category_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{exporter.extension}",
        mime=exporter.mime,
        use_container_width=True
    )

def export_all_categories():
    all_cats = {k: asdict(v) for k, v in registry.categories.items()}
    all_sectors = {k: asdict(v) for k, v in registry.sectors.items()}
    data = {
        "version": "2.1.0",
        "exported_at": datetime.now().isoformat(),
        "sectors": all_sectors,
        "categories": all_cats,
    }
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    st.download_button(
        "Download Complete Export (JSON)",
        data=json_str,
        file_name=f"writeup_studio_export_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True
    )
    render_toast("Export ready for download", "success")

def do_import_category():
    # Handled via JS postMessage in real implementation
    pass

def save_settings():
    render_toast("Settings saved", "success")

# ═══════════════════════════════════════════════════════════════════════
# NEW CATEGORY MODAL
# ═══════════════════════════════════════════════════════════════════════

if st.session_state.show_new_category:
    with st.form("new_category_form", clear_on_submit=True):
        st.markdown("### Create New Category")
        
        ncol1, ncol2 = st.columns(2)
        with ncol1:
            nkey = st.text_input("Key *", placeholder="my_category", help="Unique ID, lowercase/underscore")
            nname = st.text_input("Display Name *", placeholder="My Category")
            nsector = st.selectbox("Sector *", options=list(registry.sectors.keys()), format_func=lambda k: f"{registry.sectors[k].icon} {registry.sectors[k].name}")
        with ncol2:
            nicon = st.text_input("Icon", placeholder="✨", max_chars=2)
            ndesc = st.text_area("Description", placeholder="What this category is for", height=80)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.form_submit_button("Create Category", type="primary"):
                if nkey and nname and nsector:
                    key = nkey.strip().lower().replace(' ', '_')
                    if not re.match(r'^[a-z][a-z0-9_]*$', key):
                        render_toast("Invalid key format", "error")
                    elif key in registry.categories:
                        render_toast("Key already exists", "error")
                    else:
                        new_cat = CategoryDef(
                            key=key, name=nname.strip(), description=ndesc.strip(),
                            icon=nicon.strip() or "📦", sector=nsector
                        )
                        registry.register_category(new_cat)
                        st.session_state.current_category = key
                        st.session_state.current_sector = nsector
                        st.session_state.show_new_category = False
                        render_toast(f"Created category: {nname}", "success")
                        st.rerun()
                else:
                    render_toast("Key, Name, and Sector required", "error")
        with c2:
            if st.form_submit_button("Cancel"):
                st.session_state.show_new_category = False
                st.rerun()

# ═══════════════════════════════════════════════════════════════════════
# RENDER TOASTS & MODAL
# ═══════════════════════════════════════════════════════════════════════

render_toasts()
render_modal()

# ═══════════════════════════════════════════════════════════════════════
# KEYBOARD SHORTCUTS (via JS injection)
# ═══════════════════════════════════════════════════════════════════════

if st.session_state.keyboard_shortcuts:
    st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + G -> Generate
    if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
        e.preventDefault();
        const btn = document.querySelector('button[key="btn_generate"]');
        if (btn) btn.click();
    }
    // Ctrl/Cmd + Shift + G -> Batch
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'G') {
        e.preventDefault();
        const btn = document.querySelector('button[key="btn_batch"]');
        if (btn) btn.click();
    }
    // Ctrl/Cmd + S -> Save/Export
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const btn = document.querySelector('button[key="btn_export"]');
        if (btn) btn.click();
    }
    // Ctrl/Cmd + N -> New Category
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        // Trigger via session state would need rerun
    }
    // Escape -> Close Modal
    if (e.key === 'Escape') {
        window.parent.postMessage({type: 'modal_close'}, '*');
    }
});
</script>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════

st.markdown(f"""
<hr style="border-color: var(--border-subtle); margin-top: 3rem;">
<div style="text-align: center; color: var(--fg-muted); font-size: 0.8rem; padding: var(--space-lg);">
    <div style="display: flex; align-items: center; justify-content: center; gap: var(--space-lg); flex-wrap: wrap; margin-bottom: var(--space-sm);">
        <span>WriteUp Studio Premium v2.1.0</span>
        <span>•</span>
        <span>{len(registry.categories)} categories across {len(registry.sectors)} sectors</span>
        <span>•</span>
        <span>Plugin architecture ready</span>
    </div>
    <div style="font-size: 0.75rem;">
        Built with <span style="color: var(--accent-primary);">Streamlit</span> • 
        Design system: Custom CSS + Design Tokens • 
        Deploy free on <a href="https://streamlit.io/cloud" target="_blank" style="color: var(--accent-primary);">Streamlit Cloud</a>
    </div>
</div>
""", unsafe_allow_html=True)