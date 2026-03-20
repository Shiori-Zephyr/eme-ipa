#!/usr/bin/env python3
"""
Sumerian Transliteration → IPA Converter
Based on: Jagersma, A.H. (2010) "A Descriptive Grammar of Sumerian", Chapter 3: Phonology

Converts standard Assyriological transliteration to IPA.
Marks uncertain/reconstructed values.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import re

# =============================================================================
# MAPPING TABLES
# =============================================================================

# Period selection affects voicing of b/d/g/z
PERIOD_3RD_MIL = "3rd_mil"       # before ~2000 BCE
PERIOD_POST_2000 = "post_2000"   # after ~2000 BCE

# --- Consonant mappings ---
# Format: transliteration -> { period: (ipa, uncertain?) }
# uncertain = True means reconstruction is debated or approximate

CONSONANTS = {
    # Voiceless aspirated stops (§3.2.2)
    'p':  {PERIOD_3RD_MIL: ('pʰ', False), PERIOD_POST_2000: ('pʰ', False)},
    't':  {PERIOD_3RD_MIL: ('tʰ', False), PERIOD_POST_2000: ('tʰ', False)},
    'k':  {PERIOD_3RD_MIL: ('kʰ', False), PERIOD_POST_2000: ('kʰ', False)},

    # Plain voiceless stops -> voiced after ~2000 BCE in most environments (§3.2.3)
    # Word-initial/intervocalic: voiced after 2000; word-final/clusters: remain voiceless
    # We mark post-2000 as context-dependent
    'b':  {PERIOD_3RD_MIL: ('p', False),  PERIOD_POST_2000: ('p~b', True)},
    'd':  {PERIOD_3RD_MIL: ('t', False),  PERIOD_POST_2000: ('t~d', True)},
    'g':  {PERIOD_3RD_MIL: ('k', False),  PERIOD_POST_2000: ('k~ɡ', True)},

    # Glottal stop (§3.2.4) - lost progressively during 2nd half of 3rd mil
    '÷':  {PERIOD_3RD_MIL: ('ʔ', False),  PERIOD_POST_2000: ('ʔ~∅', True)},

    # Affricates (§3.3)
    'z':  {PERIOD_3RD_MIL: ('ts', False),  PERIOD_POST_2000: ('ts~dz', True)},
    'ř':  {PERIOD_3RD_MIL: ('tsʰ', False), PERIOD_POST_2000: ('—', False)},  # lost as phoneme

    # Fricatives (§3.4)
    's':  {PERIOD_3RD_MIL: ('s', False),   PERIOD_POST_2000: ('s', False)},
    'š':  {PERIOD_3RD_MIL: ('ʃ', False),   PERIOD_POST_2000: ('ʃ', False)},
    'ḫ':  {PERIOD_3RD_MIL: ('x', False),   PERIOD_POST_2000: ('x', False)},
    'h':  {PERIOD_3RD_MIL: ('h', True),    PERIOD_POST_2000: ('—', False)},  # lost by Ur III

    # Nasals (§3.5)
    'm':  {PERIOD_3RD_MIL: ('m', False),   PERIOD_POST_2000: ('m', False)},
    'n':  {PERIOD_3RD_MIL: ('n', False),   PERIOD_POST_2000: ('n', False)},
    'ĝ':  {PERIOD_3RD_MIL: ('ŋ', False),   PERIOD_POST_2000: ('ŋ', False)},

    # Lateral (§3.6)
    'l':  {PERIOD_3RD_MIL: ('l', False),   PERIOD_POST_2000: ('l', False)},

    # Tap (§3.7) - NOT a trill; single closure like Spanish pero
    'r':  {PERIOD_3RD_MIL: ('ɾ', False),   PERIOD_POST_2000: ('ɾ', False)},

    # Semivowel (§3.8) - lost progressively, gone by end of Ur III
    'j':  {PERIOD_3RD_MIL: ('j', True),    PERIOD_POST_2000: ('—', False)},
}

# Alternate input forms that users might type
CONSONANT_ALIASES = {
    'h̬': 'ḫ', 'ḥ': 'ḫ', 'x': 'ḫ',  # various ways people write ḫ
    'ĝ': 'ĝ', 'ŋ': 'ĝ', 'g̃': 'ĝ', 'ĝ': 'ĝ',  # velar nasal
    'ř': 'ř', 'dr': 'ř', 'ř': 'ř',
    'š': 'š', 'sh': 'š',
    'ś': 's',  # per Jagersma, Sumerian /s/ = OA /ś/
}

# --- Vowel mappings ---
# Short vowels (§3.9.1)
SHORT_VOWELS = {
    'a': 'a',
    'e': 'e',
    'i': 'i',
    'u': 'u',
}

# Long vowels (§3.9.2) - indicated by macron or doubled spelling
LONG_VOWELS = {
    'ā': 'aː',
    'ē': 'eː',
    'ī': 'iː',
    'ū': 'uː',
}

# Diphthong (§3.8): /aj/ → /eː/ (documented for é < *haj and a < *÷aj)
# This is handled contextually, not as a simple mapping.


# =============================================================================
# CONVERTER LOGIC
# =============================================================================

class SumerianIPAConverter:
    def __init__(self):
        self.period = PERIOD_3RD_MIL

    def set_period(self, period):
        self.period = period

    def _normalize(self, text):
        """Normalize various input conventions."""
        result = text.lower()
        # Handle common alternate inputs
        # Multi-char aliases first (longer strings first to avoid partial matches)
        sorted_aliases = sorted(CONSONANT_ALIASES.items(), key=lambda x: -len(x[0]))
        for alias, canonical in sorted_aliases:
            result = result.replace(alias, canonical)
        return result

    def _strip_indices(self, token):
        """
        Remove numeric subscript indices from transliteration tokens.
        e.g. sa10 -> sa, gu4 -> gu, den -> den, keše2 -> keše
        Also handle 'x' subscripts like sa₁₀.
        """
        # Remove trailing digits (subscript indices in ASCII transliteration)
        stripped = re.sub(r'\d+$', '', token)
        # Remove Unicode subscript digits
        stripped = re.sub(r'[₀₁₂₃₄₅₆₇₈₉]+$', '', stripped)
        return stripped if stripped else token

    def _is_vowel(self, ch):
        return ch in SHORT_VOWELS or ch in LONG_VOWELS

    def _convert_segment(self, seg):
        """
        Convert a single phonological segment (consonant or vowel) to IPA.
        Returns (ipa_string, is_uncertain, note).
        """
        # Check long vowels first
        if seg in LONG_VOWELS:
            return (LONG_VOWELS[seg], False, '')

        # Check short vowels
        if seg in SHORT_VOWELS:
            return (SHORT_VOWELS[seg], False, '')

        # Check consonants
        if seg in CONSONANTS:
            mapping = CONSONANTS[seg]
            if self.period in mapping:
                ipa, uncertain = mapping[self.period]
                note = ''
                if ipa == '—':
                    note = f'/{seg}/ lost as phoneme by this period'
                elif '~' in ipa:
                    note = 'context-dependent (see notes)'
                return (ipa, uncertain, note)

        return (seg, True, 'unknown segment')

    def convert_token(self, raw_token):
        """
        Convert a single transliteration token to IPA.
        Returns list of (ipa_string, is_uncertain, note) tuples.
        """
        token = self._normalize(raw_token)
        token = self._strip_indices(token)

        # Handle determinatives: remove d (divine), ĝiš (wood), etc. prefix markers
        # Users often write dEN.LÍL or ĝiš-... — we just process what remains

        results = []
        i = 0
        chars = list(token)
        length = len(chars)

        while i < length:
            ch = chars[i]

            # Try two-char consonant sequences first (for digraphs)
            if i + 1 < length:
                digraph = ch + chars[i+1]
                if digraph in CONSONANTS:
                    results.append(self._convert_segment(digraph))
                    i += 2
                    continue

            # Single character
            if ch in CONSONANTS:
                results.append(self._convert_segment(ch))
            elif ch in LONG_VOWELS:
                results.append(self._convert_segment(ch))
            elif ch in SHORT_VOWELS:
                # Check if next char is same vowel (plene spelling = long)
                if i + 1 < length and chars[i+1] == ch:
                    long_v = ch + '\u0304'  # add macron: ā, ē, ī, ū
                    if long_v in LONG_VOWELS:
                        results.append(self._convert_segment(long_v))
                    else:
                        results.append((SHORT_VOWELS[ch] + 'ː', False, 'long (plene)'))
                    i += 2
                    continue
                else:
                    results.append(self._convert_segment(ch))
            elif ch in ('-', '.', ' ', '='):
                # Morpheme/word boundaries - pass through as separator
                results.append(('.', False, ''))
            elif ch == '÷' or ch == 'ʔ':
                results.append(self._convert_segment('÷'))
            else:
                # Unknown character, pass through
                results.append((ch, True, 'unrecognized'))

            i += 1

        return results

    def convert_text(self, text):
        """
        Convert a full transliteration string.
        Returns list of (token, [(ipa, uncertain, note), ...]) pairs.
        """
        # Split on whitespace, preserving hyphens within tokens
        tokens = text.split()
        output = []
        for tok in tokens:
            # Split compound tokens on hyphens but keep track for display
            subtokens = tok.split('-')
            token_results = []
            for j, sub in enumerate(subtokens):
                sub_results = self.convert_token(sub)
                token_results.extend(sub_results)
                if j < len(subtokens) - 1:
                    token_results.append(('.', False, ''))  # morpheme boundary
            output.append((tok, token_results))
        return output


# =============================================================================
# REFERENCE TABLE DATA
# =============================================================================

REFERENCE_DATA = [
    ('Consonants', [
        ('b', '[p]', '[p~b]', 'plain voiceless → voiced in most env. after ~2000 BCE (§3.2.3)'),
        ('d', '[t]', '[t~d]', 'plain voiceless → voiced in most env. after ~2000 BCE (§3.2.3)'),
        ('g', '[k]', '[k~ɡ]', 'plain voiceless → voiced in most env. after ~2000 BCE (§3.2.3)'),
        ('p', '[pʰ]', '[pʰ]', 'voiceless aspirated bilabial stop (§3.2.2)'),
        ('t', '[tʰ]', '[tʰ]', 'voiceless aspirated dental/alveolar stop (§3.2.2)'),
        ('k', '[kʰ]', '[kʰ]', 'voiceless aspirated velar stop (§3.2.2)'),
        ('÷', '[ʔ]', '[ʔ~∅]', 'glottal stop; progressively lost (§3.2.4)'),
        ('z', '[ts]', '[ts~dz]', 'voiceless affricate → voiced in some env. (§3.3.1)'),
        ('ř', '[tsʰ]', '—', 'aspirated affricate; lost as phoneme before Ur III (§3.3.2)'),
        ('s', '[s]', '[s]', 'voiceless alveolar fricative (§3.4.1)'),
        ('š', '[ʃ]', '[ʃ]', 'voiceless postalveolar fricative (§3.4.2)'),
        ('ḫ', '[x]', '[x]', 'voiceless velar fricative (§3.4.3)'),
        ('h', '[h]', '—', 'glottal fricative; lost by Ur III at latest (§3.4.4)'),
        ('m', '[m]', '[m]', 'voiced bilabial nasal (§3.5.2)'),
        ('n', '[n]', '[n]', 'voiced dental/alveolar nasal (§3.5.3)'),
        ('ĝ', '[ŋ]', '[ŋ]', 'voiced velar nasal (§3.5.4)'),
        ('l', '[l]', '[l]', 'voiced dental/alveolar lateral (§3.6)'),
        ('r', '[ɾ]', '[ɾ]', 'voiced alveolar tap, NOT trill (§3.7)'),
        ('j', '[j]', '—', 'palatal semivowel; lost by end of Ur III (§3.8)'),
    ]),
    ('Vowels', [
        ('a', '[a]', '[a]', 'low back unrounded (§3.9.1)'),
        ('e', '[e]', '[e]', 'low front unrounded (§3.9.1)'),
        ('i', '[i]', '[i]', 'high front unrounded (§3.9.1)'),
        ('u', '[u]', '[u]', 'high back rounded (§3.9.1)'),
        ('ā', '[aː]', '[aː]', 'long /a/ (§3.9.2)'),
        ('ē', '[eː]', '[eː]', 'long /e/ (§3.9.2)'),
        ('ī', '[iː]', '[iː]', 'long /i/ (§3.9.2)'),
        ('ū', '[uː]', '[uː]', 'long /u/ (§3.9.2)'),
    ]),
]

NOTES_TEXT = """Key notes from Jagersma (2010) Ch.3:

▸ b/d/g were PLAIN VOICELESS [p t k] in the 3rd millennium, NOT voiced.
  They only became voiced (in most environments) around 2000 BCE.
  They remained voiceless word-finally and in voiceless clusters. (§3.2.3)

▸ p/t/k were VOICELESS ASPIRATED [pʰ tʰ kʰ], proven by Greek transcriptions
  (Graeco-Babyloniaca) and loanword patterns. (§3.2.2)

▸ z was an AFFRICATE [ts], not a fricative [z]. Evidence from Akkadian
  loanword correspondences and Berossos' Greek spelling Ξ for /z/. (§3.3.1)

▸ ř was an ASPIRATED AFFRICATE [tsʰ], the aspirated counterpart of /z/.
  Lost as a phoneme during the 2nd half of the 3rd millennium, merging
  with /r/ (south) or /d/ (north). (§3.3.2)

▸ r was a TAP [ɾ], not a trill. Evidence: sound change t→r between vowels,
  and confusion of syllable-final /r/ with /d/ and /t/. (§3.7)

▸ ĝ was a VELAR NASAL [ŋ]. Word-initially reflected as /g/ or /k/ in
  Akkadian loanwords, word-finally as /n/, intervocalically as /ng/. (§3.5.4)

▸ Glottal stop /÷/ [ʔ] was phonemic in Old Sumerian but progressively
  lost. It assimilated to preceding consonants and contracted between
  vowels. (§3.2.4)

▸ /h/ [h] and /j/ [j] were early phonemes, both lost by the Ur III period.
  Their presence is reconstructable for a few morphemes only. (§3.4.4, §3.8)

▸ Vowel /e/ was a genuinely distinct phoneme from /i/ in Sumerian,
  unlike in Akkadian. Many transliterations may show /i/ where Sumerian
  actually had /e/ due to Akkadian scribal interference. (§3.9.1)

▸ Stress fell on the FINAL SYLLABLE of words. Evidence from loanword
  accentuation patterns in Akkadian. (§3.11)

▸ Syllable structure: always CV or CVC. No initial vowels — all apparent
  initial vowels had an initial glottal stop, /h/, or /j/. (§3.10)

⚠ VALUES MARKED WITH ? ARE UNCERTAIN OR CONTEXT-DEPENDENT.
  This tool provides an approximation; Sumerian phonology is reconstructed
  and many details remain debated among scholars."""


# =============================================================================
# GUI
# =============================================================================

class SumerianIPAApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sumerian → IPA (Jagersma 2010)")
        self.root.configure(bg='#1a1a1a')
        self.root.geometry("860x720")
        self.root.minsize(640, 500)

        self.converter = SumerianIPAConverter()

        # Colors
        self.BG = '#1a1a1a'
        self.SURFACE = '#242424'
        self.SURFACE2 = '#2e2e2e'
        self.BORDER = '#3a3a3a'
        self.TEXT = '#e0ddd5'
        self.TEXT_DIM = '#8a8680'
        self.ACCENT = '#c9a96e'
        self.UNCERTAIN_COLOR = '#d08050'
        self.IPA_COLOR = '#d4c4a0'
        self.LOST_COLOR = '#705050'

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background=self.BG, foreground=self.TEXT)
        style.configure('TFrame', background=self.BG)
        style.configure('TLabel', background=self.BG, foreground=self.TEXT)
        style.configure('TNotebook', background=self.BG)
        style.configure('TNotebook.Tab', background=self.SURFACE, foreground=self.TEXT_DIM,
                        padding=[12, 4])
        style.map('TNotebook.Tab',
                  background=[('selected', self.SURFACE2)],
                  foreground=[('selected', self.ACCENT)])
        style.configure('Accent.TLabel', foreground=self.ACCENT)
        style.configure('Dim.TLabel', foreground=self.TEXT_DIM, font=('Segoe UI', 9))

    def _build_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        # Title
        title_lbl = ttk.Label(main, text="𒅴𒂠  Sumerian → IPA", style='Accent.TLabel',
                              font=('Segoe UI', 15, 'bold'))
        title_lbl.pack(anchor='w')
        sub_lbl = ttk.Label(main, text="Based on Jagersma (2010) A Descriptive Grammar of Sumerian, Ch.3",
                            style='Dim.TLabel')
        sub_lbl.pack(anchor='w', pady=(0, 10))

        # Notebook tabs
        notebook = ttk.Notebook(main)
        notebook.pack(fill=tk.BOTH, expand=True)

        # --- Tab 1: Converter ---
        conv_frame = ttk.Frame(notebook)
        notebook.add(conv_frame, text='  Converter  ')
        self._build_converter_tab(conv_frame)

        # --- Tab 2: Reference Table ---
        ref_frame = ttk.Frame(notebook)
        notebook.add(ref_frame, text='  Reference  ')
        self._build_reference_tab(ref_frame)

        # --- Tab 3: Notes ---
        notes_frame = ttk.Frame(notebook)
        notebook.add(notes_frame, text='  Notes  ')
        self._build_notes_tab(notes_frame)

    def _build_converter_tab(self, parent):
        # Period selector
        period_frame = ttk.Frame(parent)
        period_frame.pack(fill=tk.X, pady=(10, 6))

        ttk.Label(period_frame, text="Period:", style='Dim.TLabel').pack(side=tk.LEFT, padx=(0, 8))

        self.period_var = tk.StringVar(value=PERIOD_3RD_MIL)

        self.btn_3rd = tk.Button(period_frame, text="3rd millennium BCE",
                                 command=lambda: self._set_period(PERIOD_3RD_MIL),
                                 bg=self.SURFACE2, fg=self.ACCENT,
                                 activebackground=self.SURFACE2, activeforeground=self.ACCENT,
                                 bd=1, relief='solid', padx=10, pady=3,
                                 font=('Segoe UI', 9))
        self.btn_3rd.pack(side=tk.LEFT, padx=2)

        self.btn_post = tk.Button(period_frame, text="~2000 BCE onwards",
                                  command=lambda: self._set_period(PERIOD_POST_2000),
                                  bg=self.SURFACE, fg=self.TEXT_DIM,
                                  activebackground=self.SURFACE2, activeforeground=self.ACCENT,
                                  bd=1, relief='solid', padx=10, pady=3,
                                  font=('Segoe UI', 9))
        self.btn_post.pack(side=tk.LEFT, padx=2)

        # Legend
        legend_frame = ttk.Frame(period_frame)
        legend_frame.pack(side=tk.RIGHT, padx=(0, 4))
        tk.Label(legend_frame, text="?", fg=self.UNCERTAIN_COLOR, bg=self.BG,
                 font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Label(legend_frame, text=" = uncertain/context-dependent", style='Dim.TLabel').pack(side=tk.LEFT)

        # Input
        input_lbl = ttk.Label(parent, text="Transliteration input:", style='Dim.TLabel')
        input_lbl.pack(anchor='w', pady=(8, 2))

        self.input_text = tk.Text(parent, height=4, bg=self.SURFACE, fg=self.TEXT,
                                  insertbackground=self.ACCENT, selectbackground=self.ACCENT,
                                  selectforeground=self.BG, bd=1, relief='solid',
                                  highlightthickness=1, highlightcolor=self.BORDER,
                                  highlightbackground=self.BORDER,
                                  font=('Noto Sans', 12), wrap=tk.WORD, padx=8, pady=6,
                                  exportselection=False)
        self.input_text.pack(fill=tk.X, pady=(0, 4))
        self.input_text.insert('1.0', 'ul-ḫuš')
        self.input_text.bind('<KeyRelease>', lambda e: self._on_convert())

        # Hint
        hint = ttk.Label(parent, text="Type transliteration using standard Assyriological conventions. "
                         "Numeric indices (e.g. sa₁₀, gu₄) are stripped automatically. "
                         "Use - for morpheme boundaries.",
                         style='Dim.TLabel', wraplength=800)
        hint.pack(anchor='w', pady=(0, 8))

        # Output
        output_header = ttk.Frame(parent)
        output_header.pack(fill=tk.X, pady=(0, 2))
        ttk.Label(output_header, text="IPA output:", style='Dim.TLabel').pack(side=tk.LEFT)
        self.copy_btn = tk.Button(output_header, text="Copy", command=self._copy_ipa,
                                  bg=self.SURFACE, fg=self.TEXT_DIM,
                                  activebackground=self.SURFACE2, activeforeground=self.ACCENT,
                                  bd=1, relief='solid', padx=8, pady=1,
                                  font=('Segoe UI', 8), cursor='hand2')
        self.copy_btn.pack(side=tk.RIGHT)

        self.output_text = tk.Text(parent, height=4, bg=self.SURFACE2, fg=self.IPA_COLOR,
                                   bd=1, relief='solid',
                                   highlightthickness=1, highlightcolor=self.BORDER,
                                   highlightbackground=self.BORDER,
                                   font=('Noto Sans', 14), wrap=tk.WORD, padx=8, pady=6,
                                   exportselection=True)
        self.output_text.bind('<Key>', self._readonly_handler)
        self.output_text.bind('<ButtonPress-1>', lambda e: self.output_text.focus_set())
        self.output_text.pack(fill=tk.X, pady=(0, 8))
        self.output_text.tag_configure('uncertain', foreground=self.UNCERTAIN_COLOR)
        self.output_text.tag_configure('lost', foreground=self.LOST_COLOR)
        self.output_text.tag_configure('normal', foreground=self.IPA_COLOR)
        self.output_text.tag_configure('boundary', foreground=self.TEXT_DIM)

        # Detail panel
        detail_lbl = ttk.Label(parent, text="Segment details:", style='Dim.TLabel')
        detail_lbl.pack(anchor='w', pady=(0, 2))

        self.detail_text = tk.Text(parent, height=8, bg=self.SURFACE, fg=self.TEXT,
                                   bd=1, relief='solid',
                                   highlightthickness=1, highlightcolor=self.BORDER,
                                   highlightbackground=self.BORDER,
                                   font=('Consolas', 10), wrap=tk.WORD, padx=8, pady=6,
                                   exportselection=True)
        self.detail_text.bind('<Key>', self._readonly_handler)
        self.detail_text.bind('<ButtonPress-1>', lambda e: self.detail_text.focus_set())
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        self.detail_text.tag_configure('header', foreground=self.ACCENT, font=('Consolas', 10, 'bold'))
        self.detail_text.tag_configure('uncertain_detail', foreground=self.UNCERTAIN_COLOR)
        self.detail_text.tag_configure('normal_detail', foreground=self.TEXT)
        self.detail_text.tag_configure('dim', foreground=self.TEXT_DIM)

        # Initial conversion
        self._on_convert()

    def _build_reference_tab(self, parent):
        canvas = tk.Canvas(parent, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=scroll_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=8)

        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all('<MouseWheel>', _on_mousewheel)

        for section_name, rows in REFERENCE_DATA:
            sec_lbl = tk.Label(scroll_frame, text=section_name, fg=self.ACCENT, bg=self.BG,
                               font=('Segoe UI', 11, 'bold'), anchor='w')
            sec_lbl.pack(fill=tk.X, pady=(12, 4), padx=4)

            # Header row
            hdr = ttk.Frame(scroll_frame)
            hdr.pack(fill=tk.X, padx=4)
            for col, w in [('Translit.', 8), ('3rd mil.', 10), ('~2000+', 10), ('Description', 50)]:
                tk.Label(hdr, text=col, fg=self.TEXT_DIM, bg=self.BG,
                         font=('Segoe UI', 9, 'bold'), width=w, anchor='w').pack(side=tk.LEFT, padx=2)

            for translit, ipa_3rd, ipa_post, desc in rows:
                row = ttk.Frame(scroll_frame)
                row.pack(fill=tk.X, padx=4)
                tk.Label(row, text=translit, fg=self.ACCENT, bg=self.BG,
                         font=('Noto Sans', 10, 'bold'), width=8, anchor='w').pack(side=tk.LEFT, padx=2)
                tk.Label(row, text=ipa_3rd, fg=self.IPA_COLOR, bg=self.BG,
                         font=('Noto Sans', 10), width=10, anchor='w').pack(side=tk.LEFT, padx=2)
                color = self.LOST_COLOR if ipa_post == '—' else self.IPA_COLOR
                tk.Label(row, text=ipa_post, fg=color, bg=self.BG,
                         font=('Noto Sans', 10), width=10, anchor='w').pack(side=tk.LEFT, padx=2)
                tk.Label(row, text=desc, fg=self.TEXT_DIM, bg=self.BG,
                         font=('Segoe UI', 9), anchor='w', wraplength=420).pack(side=tk.LEFT, padx=2)

    def _build_notes_tab(self, parent):
        notes = scrolledtext.ScrolledText(parent, bg=self.SURFACE, fg=self.TEXT,
                                          font=('Consolas', 10), wrap=tk.WORD,
                                          padx=12, pady=10, bd=0,
                                          highlightthickness=0)
        notes.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        notes.insert('1.0', NOTES_TEXT)
        notes.configure(state=tk.DISABLED)

    def _set_period(self, period):
        self.period_var.set(period)
        self.converter.set_period(period)

        if period == PERIOD_3RD_MIL:
            self.btn_3rd.configure(bg=self.SURFACE2, fg=self.ACCENT)
            self.btn_post.configure(bg=self.SURFACE, fg=self.TEXT_DIM)
        else:
            self.btn_3rd.configure(bg=self.SURFACE, fg=self.TEXT_DIM)
            self.btn_post.configure(bg=self.SURFACE2, fg=self.ACCENT)

        self._on_convert()

    def _on_convert(self):
        raw = self.input_text.get('1.0', tk.END).strip()
        if not raw:
            self._clear_output()
            return

        results = self.converter.convert_text(raw)

        # Build IPA output
        self.output_text.delete('1.0', tk.END)

        self.detail_text.delete('1.0', tk.END)

        first_word = True
        for token, segments in results:
            if not first_word:
                self.output_text.insert(tk.END, '  ', 'boundary')
            first_word = False

            # Detail header
            self.detail_text.insert(tk.END, f'{token}', 'header')
            self.detail_text.insert(tk.END, '  →  ', 'dim')

            ipa_parts = []
            for ipa, uncertain, note in segments:
                if ipa == '.':
                    self.output_text.insert(tk.END, '.', 'boundary')
                    ipa_parts.append('.')
                elif ipa == '—':
                    self.output_text.insert(tk.END, '∅', 'lost')
                    ipa_parts.append('∅')
                elif uncertain:
                    self.output_text.insert(tk.END, ipa, 'uncertain')
                    self.output_text.insert(tk.END, '?', 'uncertain')
                    ipa_parts.append(f'{ipa}?')
                else:
                    self.output_text.insert(tk.END, ipa, 'normal')
                    ipa_parts.append(ipa)

            # Detail line
            ipa_str = ''.join(ipa_parts)
            self.detail_text.insert(tk.END, f'/{ipa_str}/\n', 'normal_detail')

            # Per-segment notes
            for ipa, uncertain, note in segments:
                if note and ipa != '.':
                    tag = 'uncertain_detail' if uncertain else 'dim'
                    marker = '  ⚠ ' if uncertain else '    '
                    self.detail_text.insert(tk.END, f'{marker}{ipa}: {note}\n', tag)

            self.detail_text.insert(tk.END, '\n', 'dim')


    def _copy_ipa(self):
        """Copy IPA output text to clipboard."""
        content = self.output_text.get('1.0', tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        # Brief visual feedback
        self.copy_btn.configure(text="Copied!", fg=self.ACCENT)
        self.root.after(1000, lambda: self.copy_btn.configure(text="Copy", fg=self.TEXT_DIM))

    def _readonly_handler(self, event):
        """Allow select-all (Ctrl+A) and copy (Ctrl+C) but block all other input."""
        # Allow Ctrl+A, Ctrl+C, arrow keys, Home, End, Shift+arrows for selection
        if event.state & 0x4:  # Ctrl held
            if event.keysym.lower() in ('a', 'c'):
                return  # allow
        if event.keysym in ('Left', 'Right', 'Up', 'Down', 'Home', 'End',
                            'Prior', 'Next', 'Shift_L', 'Shift_R'):
            return  # allow navigation
        return 'break'  # block everything else

    def _clear_output(self):
        self.output_text.delete('1.0', tk.END)
        self.detail_text.delete('1.0', tk.END)


def main():
    root = tk.Tk()
    app = SumerianIPAApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
