#!/usr/bin/env python3
"""
Extract definitions, theorems, propositions, lemmas, and corollaries
from Quarto (.qmd) chapter files and generate a summary PDF via XeLaTeX.

Usage:
    python3 generate_summary.py [--project-dir /path/to/project] [--output summary.pdf]
"""

import re
import os
import subprocess
import argparse
import sys

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

# Chapter files in order, with their display chapter numbers
# (matching the JS numbering on the website)
CHAPTER_MAP = [
    # (filename, chapter_display_number, chapter_title_override)
    # chapter_display_number=None means "extract from file"
    ("chapter_0.qmd",   "0", None),   # קבוצות ומספרים — JS shows "undefined", we use 0
    ("chapter_0_5.qmd", "1", None),   # פרק 1
    ("chapter_1.qmd",   "2", None),   # פרק 2
    ("chapter_2.qmd",   "3", None),   # פרק 3
    ("chapter_3.qmd",   "4", None),   # פרק 4
    ("chapter_4.qmd",   "5", None),   # פרק 5
    ("chapter_5.qmd",   "6", None),   # פרק 6
    ("chapter_6.qmd",   "7", None),   # פרק 7
]

# Environments that share the counter (all numbered envs)
ALL_NUMBERED_ENVS = [
    "definition", "example", "exercise", "remark",
    "theorem", "lemma", "proposition", "corollary"
]

# Environments to INCLUDE in the summary
TARGET_ENVS = ["definition", "theorem", "proposition", "lemma", "corollary"]

# Hebrew labels for each environment type
ENV_LABELS = {
    "definition":  "הגדרה",
    "theorem":     "משפט",
    "proposition": "טענה",
    "lemma":       "למה",
    "corollary":   "מסקנה",
}

# ──────────────────────────────────────────────
# QMD Parser
# ──────────────────────────────────────────────

def detect_env_class(line):
    """
    Detect if a line opens a fenced div environment.
    Handles both syntaxes:
      ::: {.definition}
      ::: {.definition #def-foo}
      ::: {.proposition #prp-bar label="..."}
      ::: definition
      ::: {.callout-note collapse="true" title="פתרון"}
      ::: {#fig-Foo .figure}
    Returns the environment class name or None.
    """
    line = line.strip().rstrip('\r\n')
    
    # Must start with :::
    if not line.startswith('::: '):
        return None
    
    rest = line[4:].strip()
    
    # Pattern 1: ::: {.classname ...}
    m = re.match(r'\{\.(\w+)', rest)
    if m:
        return m.group(1)
    
    # Pattern 2: ::: {#id .classname}  (like figures)
    m = re.match(r'\{#\S+\s+\.(\w+)', rest)
    if m:
        return m.group(1)
    
    # Pattern 3: ::: classname  (bare word, no braces)
    m = re.match(r'^(\w+)\s*$', rest)
    if m:
        return m.group(1)
    
    return None


def is_closing_fence(line):
    """Check if line is a closing ::: fence."""
    return line.strip().rstrip('\r\n') == ':::'


def extract_chapter_title(filepath):
    """Extract the H1 title from a QMD file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip().rstrip('\r\n')
            m = re.match(r'^#\s+(.+?)(?:\s*\{.*\})?\s*$', line)
            if m:
                return m.group(1).strip()
    return os.path.basename(filepath)


def parse_chapter(filepath):
    """
    Parse a QMD file and extract all numbered environments with their content.
    Returns a list of (env_class, content_lines) in document order.
    """
    environments = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        env_class = detect_env_class(line)
        
        if env_class is not None:
            # We found an opening fence; collect content until matching close
            depth = 1
            content_lines = []
            i += 1
            while i < len(lines) and depth > 0:
                if detect_env_class(lines[i]) is not None:
                    depth += 1
                    content_lines.append(lines[i])
                elif is_closing_fence(lines[i]):
                    depth -= 1
                    if depth > 0:
                        content_lines.append(lines[i])
                else:
                    content_lines.append(lines[i])
                i += 1
            
            environments.append((env_class, content_lines))
        else:
            i += 1
    
    return environments


def assign_numbers_and_filter(environments, chapter_num):
    """
    Assign shared counter numbers to environments and filter to target types.
    Returns list of (env_class, label, number_str, content_lines).
    """
    counter = 0
    results = []
    
    for env_class, content_lines in environments:
        # Only numbered environments increment the counter
        if env_class in ALL_NUMBERED_ENVS:
            counter += 1
            number_str = f"{chapter_num}.{counter}"
            
            if env_class in TARGET_ENVS:
                label = ENV_LABELS[env_class]
                results.append((env_class, label, number_str, content_lines))
    
    return results


# ──────────────────────────────────────────────
# QMD → LaTeX content conversion
# ──────────────────────────────────────────────

def qmd_content_to_latex(content_lines):
    """
    Convert QMD content (inside an environment) to LaTeX.
    Handles: math, bold, basic text.
    """
    text = ''.join(content_lines)
    text = text.replace('\r', '')  # Normalize line endings
    text = text.strip('\n')
    
    # Replace \0 macro with \mathbf{0} (since \0 is hard to define in LaTeX)
    # Only replace \0 when followed by non-digit (to avoid \0 in \mathbf{0})
    text = re.sub(r'\\0(?!\d)', r'\\mathbf{0}', text)
    
    # Remove images: ![caption](path){...}
    text = re.sub(r'!\[.*?\]\(.*?\)(?:\{.*?\})?', '', text)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # ── Extract math blocks using a character-level scanner ──
    # This avoids regex pitfalls with nested/mismatched $ signs
    display_maths = []
    inline_maths = []
    result = []
    i = 0
    n = len(text)
    
    while i < n:
        if i < n - 1 and text[i] == '$' and text[i+1] == '$':
            # Display math opening $$
            end = text.find('$$', i + 2)
            if end != -1:
                math_content = text[i+2:end]
                idx = len(display_maths)
                display_maths.append(math_content)
                result.append(f'\x01D{idx}\x01')
                i = end + 2
            else:
                # Fallback: look for single $ close (mismatched $$...$)
                end = text.find('$', i + 2)
                if end != -1:
                    math_content = text[i+2:end]
                    idx = len(display_maths)
                    display_maths.append(math_content)
                    result.append(f'\x01D{idx}\x01')
                    i = end + 1
                else:
                    result.append(text[i])
                    i += 1
        elif text[i] == '$':
            # Inline math opening $
            end = text.find('$', i + 1)
            if end != -1 and end - i < 500:  # sanity limit
                math_content = text[i+1:end]
                # Skip if content looks like it's not math (e.g., empty or just spaces)
                if math_content.strip():
                    idx = len(inline_maths)
                    inline_maths.append(math_content)
                    result.append(f'\x01I{idx}\x01')
                    i = end + 1
                else:
                    result.append(text[i])
                    i += 1
            else:
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    
    text = ''.join(result)
    
    # ── Process non-math text ──
    
    # Convert markdown bold **text** to \textbf{text}
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    
    # Remove remaining markdown italic markers *
    text = re.sub(r'(?<!\*)\*(?!\*)', '', text)
    
    # Escape special LaTeX chars in text portions
    for char in ['&', '%', '#', '_']:
        text = text.replace(char, '\\' + char)
    
    # Handle Hebrew quotes: \"  → ״ (escaped LaTeX quote to Hebrew gershayim)
    # and remaining " → ״
    text = text.replace('\\"', '״')
    text = text.replace('"', '״')
    
    # ── Restore math blocks ──
    
    # Restore inline math
    for idx, m in enumerate(inline_maths):
        text = text.replace(f'\x01I{idx}\x01', f'${m}$')
    
    # Restore display math as \[ \]
    for idx, m in enumerate(display_maths):
        # Strip whitespace to avoid blank lines inside \[...\] (LaTeX error)
        m_clean = m.strip()
        text = text.replace(f'\x01D{idx}\x01', f'\n\\[\n{m_clean}\n\\]\n')
    
    # Convert Quarto cross-refs to plain text
    text = re.sub(r'\[-?@[\w-]+\]', '', text)
    text = re.sub(r'\[([^\]]+)\]\(#[\w-]+\)', r'\1', text)
    
    # Remove Quarto equation labels {#eq-...}
    text = re.sub(r'\{#eq-[\w-]+\}', '', text)
    
    # Remove Quarto span syntax: [text]{.class} → text
    text = re.sub(r'\[([^\]]+)\]\{\.[\w-]+\}', r'\1', text)
    
    # Remove Quarto div attributes that leaked through
    text = re.sub(r'\{#[\w-]+\s*(?:\.[\w-]+)?\s*\}', '', text)
    
    # Convert Latin list markers (a. b. c. ...) to Hebrew letters (א. ב. ג. ...)
    hebrew_letters = 'אבגדהוזחטיכלמנסעפצקרשת'
    def latin_to_hebrew_marker(m):
        letter = m.group(1).lower()
        idx = ord(letter) - ord('a')
        if 0 <= idx < len(hebrew_letters):
            return hebrew_letters[idx] + '.'
        return m.group(0)
    text = re.sub(r'^([a-zA-Z])\.', latin_to_hebrew_marker, text, flags=re.MULTILINE)

    # Clean up multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


# ──────────────────────────────────────────────
# LaTeX document generation
# ──────────────────────────────────────────────

LATEX_PREAMBLE = r"""
\documentclass[a4paper, 11pt]{article}

% ── Fonts ──
\usepackage{fontspec}
\setmainfont{Arial}
\setsansfont{Arial}
\setmonofont{Consolas}

% ── Math ──
\usepackage{amsmath, amssymb, amsfonts}

% ── Math macros (matching the book) ──
\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\Z}{\mathbb{Z}}
\newcommand{\Q}{\mathbb{Q}}
\newcommand{\C}{\mathbb{C}}
\newcommand{\F}{\mathbb{F}}
\newcommand{\M}{\mathbb{M}}
\newcommand{\Set}[1]{\left\{#1\right\}}

% ── Page layout ──
\usepackage[margin=2cm]{geometry}

% ── Colors for environment boxes ──
\usepackage{tcolorbox}
\tcbuselibrary{breakable, skins}

\definecolor{defcolor}{RGB}{220, 53, 69}
\definecolor{thmcolor}{RGB}{230, 126, 34}

% ── RTL support (must be loaded LAST) ──
\usepackage{bidi}

\newtcolorbox{envbox}[2][]{%
  enhanced, breakable,
  colback=#1!3,
  colframe=#1!60,
  coltitle=black,
  fonttitle=\bfseries,
  title={#2},
  boxrule=0.6pt,
  arc=2pt,
  left=8pt, right=8pt, top=6pt, bottom=6pt,
  attach boxed title to top right={yshift=-2mm, xshift=-4mm},
  boxed title style={
    arc=2pt, boxrule=0.4pt,
    colback=#1!20,
    colframe=#1!60,
  },
  before skip=10pt,
  after skip=10pt,
}

% ── Section style ──
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries}{}{0pt}{}
\titlespacing*{\section}{0pt}{20pt}{10pt}
\setcounter{secnumdepth}{0}

% ── Hebrew TOC title ──
\renewcommand{\contentsname}{תוכן עניינים}

% ── No paragraph indent, add spacing ──
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}

\begin{document}
\setRTL

% ── Title Page ──
\vspace*{2cm}
\begin{center}
{\Huge\bfseries סיכום הגדרות ומשפטים}\\[14pt]
{\Large אלגברה לינארית להנדסה}\\[10pt]
{\normalsize ד״ר יונתן שלח \quad·\quad ד״ר נדב מאיר}
\end{center}
\vspace{1.5cm}

\tableofcontents
\newpage
"""

LATEX_EPILOGUE = r"""
\end{document}
"""

def get_env_color(env_class):
    if env_class == "definition":
        return "defcolor"
    return "thmcolor"


def generate_latex(all_chapters_data):
    """
    Generate the complete LaTeX document.
    all_chapters_data is a list of (chapter_title, chapter_num, items)
    where items is a list of (env_class, label, number_str, content_lines).
    """
    parts = [LATEX_PREAMBLE]
    
    for chapter_title, chapter_num, items in all_chapters_data:
        if not items:
            continue
        
        parts.append(f'\\section{{פרק {chapter_num}: {chapter_title}}}\n')
        
        for env_class, label, number_str, content_lines in items:
            color = get_env_color(env_class)
            latex_content = qmd_content_to_latex(content_lines)
            
            if not latex_content.strip():
                continue
            
            parts.append(f'\\begin{{envbox}}[{color}]{{{label} {number_str}}}')
            parts.append(latex_content)
            parts.append('\\end{envbox}\n')
        
        parts.append('\\newpage\n')
    
    parts.append(LATEX_EPILOGUE)
    return '\n'.join(parts)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Generate summary PDF of definitions and theorems')
    parser.add_argument('--project-dir', default='.',
                        help='Path to the Quarto project directory')
    parser.add_argument('--output', default='summary.pdf',
                        help='Output PDF path')
    parser.add_argument('--latex-only', action='store_true',
                        help='Only generate .tex file, do not compile')
    args = parser.parse_args()
    
    all_data = []
    
    for filename, chapter_num, title_override in CHAPTER_MAP:
        filepath = os.path.join(args.project_dir, filename)
        if not os.path.exists(filepath):
            print(f"⚠ Skipping {filename} (not found)")
            continue
        
        # Get chapter title
        title = title_override or extract_chapter_title(filepath)
        
        # Parse environments
        environments = parse_chapter(filepath)
        
        # Assign numbers and filter
        items = assign_numbers_and_filter(environments, chapter_num)
        
        if items:
            print(f"✅ {filename} (פרק {chapter_num}): {len(items)} environments found")
            for env_class, label, num, _ in items:
                print(f"   {label} {num}")
        else:
            print(f"⬚ {filename} (פרק {chapter_num}): no target environments")
        
        all_data.append((title, chapter_num, items))
    
    # Generate LaTeX
    latex_source = generate_latex(all_data)
    
    tex_path = args.output.replace('.pdf', '.tex')
    with open(tex_path, 'w', encoding='utf-8') as f:
        f.write(latex_source)
    print(f"\n📄 LaTeX source written to {tex_path}")
    
    if args.latex_only:
        return
    
    # Compile with XeLaTeX (twice for ToC)
    work_dir = os.path.dirname(os.path.abspath(tex_path))
    tex_basename = os.path.basename(tex_path)
    
    # Find xelatex executable
    import shutil
    xelatex_cmd = shutil.which('xelatex')
    if not xelatex_cmd:
        # Try common Windows MiKTeX path
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        candidate = os.path.join(local_appdata, 'Programs', 'MiKTeX', 'miktex', 'bin', 'x64', 'xelatex.exe')
        if os.path.exists(candidate):
            xelatex_cmd = candidate
        else:
            print("❌ xelatex not found! Make sure LaTeX is installed and in your PATH.")
            sys.exit(1)
    
    for run in [1, 2]:
        print(f"\n🔨 XeLaTeX pass {run}/2...")
        result = subprocess.run(
            [xelatex_cmd, '-interaction=nonstopmode', tex_basename],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        # Count errors
        errors = [l for l in result.stdout.split('\n') if l.startswith('!')]
        if errors:
            print(f"   ⚠ {len(errors)} error(s) in pass {run}:")
            for e in errors[:5]:
                print(f"     {e}")
            if len(errors) > 5:
                print(f"     ... and {len(errors)-5} more")
    
    pdf_path = tex_path.replace('.tex', '.pdf')
    if os.path.exists(pdf_path):
        print(f"\n✅ PDF generated: {pdf_path}")
        # Copy to output if needed
        if args.output != pdf_path:
            import shutil
            shutil.copy2(pdf_path, args.output)
            print(f"📋 Copied to {args.output}")
    else:
        print("❌ PDF not found after compilation")
        sys.exit(1)


if __name__ == '__main__':
    main()
