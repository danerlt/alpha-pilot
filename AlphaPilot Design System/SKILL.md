---
name: alphapilot-design
description: Use this skill to generate well-branded interfaces and assets for AlphaPilot, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files (colors_and_type.css, ui_kits/mobile_app/, preview/).

AlphaPilot is an AI-autonomous digital currency trading system for Binance, operating under strict risk controls and a constrained strategy framework. The brand voice is serious, engineering-focused, Chinese-primary with English technical terms preserved. Dark-mode first. Primary palette: mint `#00D395` (profit / PASS), rose `#FF4D6D` (loss / REJECT), violet `#7C5CFF` (AI decisions). No emoji. All numerics in JetBrains Mono.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out of `assets/` and reference `colors_and_type.css` for tokens. Reuse components from `ui_kits/mobile_app/` when building mobile screens.

If working on production code, read the tokens in `colors_and_type.css` and apply Tailwind theme + Lucide icons (`lucide-react`) to match the aesthetic established in the reference project (`github.com/danerlt/Hyper-Alpha-Arena`).

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions (surface/screen, scene, variation count, whether Chinese or English copy), and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.
