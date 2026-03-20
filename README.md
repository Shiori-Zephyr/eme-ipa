# eme-ipa

A Sumerian transliteration to IPA converter with a desktop GUI. Phonological values follow Jagersma (2010), *A Descriptive Grammar of Sumerian*, Chapter 3: Phonology.

## What it does

eme-ipa takes standard Assyriological transliteration as input and produces IPA transcriptions based on Jagersma's phonological reconstruction. It handles period-dependent sound changes, marks uncertain or context-dependent values, and strips numeric sign indices automatically.

Two period settings are available:

- **3rd millennium BCE** — the earlier phonological system, with plain voiceless stops for b/d/g, the affricate [tsʰ] for ř, and phonemic /h/, /j/, and /÷/.
- **~2000 BCE onwards** — reflects the voicing shifts, phoneme losses (ř, h, j), and the progressive weakening of the glottal stop.

The interface includes three tabs: a live converter with segment-by-segment detail output, a reference table of all mapped phonemes, and a notes panel summarizing the key phonological arguments from Jagersma.

## Requirements

- Python 3.x
- tkinter (included with most Python installations)
- A font with IPA support (e.g. Noto Sans)

## Usage

```bash
python eme-ipa.py
```

Type or paste transliteration into the input field. Output updates on each keystroke. Use `-` for morpheme boundaries. Numeric indices (e.g. `sa₁₀`, `gu₄`) are stripped automatically.

Common alternate input forms are accepted: `sh` → š, `x` → ḫ, `ŋ` → ĝ, etc.

## Phonological highlights

Some values that may be surprising if you're used to reading transliteration at face value:

- **b/d/g** = [p t k] in the 3rd millennium, not voiced stops. They only became voiced around 2000 BCE, and remained voiceless word-finally and in clusters.
- **p/t/k** = [pʰ tʰ kʰ], voiceless aspirated. Confirmed by Graeco-Babyloniaca transcriptions.
- **z** = [ts], an affricate, not a fricative. Evidence from Akkadian correspondences and Berossos' use of Greek Ξ.
- **ř** = [tsʰ], the aspirated counterpart of /z/. Lost as a phoneme before Ur III, merging with /r/ (south) or /d/ (north).
- **r** = [ɾ], a tap, not a trill. Supported by the sound change t→r intervocalically and the confusion of syllable-final /r/ with /d/ and /t/.

Values marked with `?` in the output are uncertain or context-dependent.

## Supported segments

| Transliteration | 3rd mil. | ~2000+ | Notes |
|---|---|---|---|
| b d g | [p t k] | [p~b t~d k~ɡ] | plain voiceless → voiced (context-dependent) |
| p t k | [pʰ tʰ kʰ] | [pʰ tʰ kʰ] | voiceless aspirated |
| z | [ts] | [ts~dz] | affricate |
| ř | [tsʰ] | — | aspirated affricate, lost before Ur III |
| s š ḫ | [s ʃ x] | [s ʃ x] | fricatives |
| h | [h] | — | lost by Ur III |
| ĝ | [ŋ] | [ŋ] | velar nasal |
| m n | [m n] | [m n] | nasals |
| l | [l] | [l] | lateral |
| r | [ɾ] | [ɾ] | tap |
| j | [j] | — | semivowel, lost by end of Ur III |
| ÷ | [ʔ] | [ʔ~∅] | glottal stop, progressively lost |

## Reference

Jagersma, A.H. (2010). *A Descriptive Grammar of Sumerian*. PhD dissertation, Universiteit Leiden.

## License

This is free and unencumbered software released into the public domain.
