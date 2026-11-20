---
name: Obsidian Forensics
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1b'
  surface-container: '#1f1f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e2e2e2'
  on-surface-variant: '#c0c7d3'
  inverse-surface: '#e2e2e2'
  inverse-on-surface: '#303030'
  outline: '#8a919d'
  outline-variant: '#404752'
  surface-tint: '#9fcaff'
  primary: '#9fcaff'
  on-primary: '#003259'
  primary-container: '#52a8ff'
  on-primary-container: '#003c69'
  inverse-primary: '#0061a5'
  secondary: '#7cdb8b'
  on-secondary: '#003914'
  secondary-container: '#027330'
  on-secondary-container: '#95f5a2'
  tertiary: '#c6c6c7'
  on-tertiary: '#2f3131'
  tertiary-container: '#a3a4a4'
  on-tertiary-container: '#383a3b'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d2e4ff'
  primary-fixed-dim: '#9fcaff'
  on-primary-fixed: '#001d37'
  on-primary-fixed-variant: '#00497e'
  secondary-fixed: '#97f8a4'
  secondary-fixed-dim: '#7cdb8b'
  on-secondary-fixed: '#002109'
  on-secondary-fixed-variant: '#005320'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#131313'
  on-background: '#e2e2e2'
  surface-variant: '#353535'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '500'
    lineHeight: 52px
    letterSpacing: -3.36px
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '500'
    lineHeight: 36px
    letterSpacing: -1.8px
  headline-lg:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '500'
    lineHeight: 40px
    letterSpacing: -2.2px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '500'
    lineHeight: 30px
    letterSpacing: -1.2px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 28px
    letterSpacing: -1.0px
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 22px
    letterSpacing: -0.5px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.2px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: -0.1px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0px
  code-lg:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: -0.2px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: -0.1px
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0px
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 12px
    letterSpacing: 0.8px
spacing:
  gutter: 0.5rem
  gutter-desktop: 1rem
  margin: 1rem
  margin-desktop: 1.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system targets SecOps engineers, threat intelligence analysts, and security developers who require instantaneous, high-density situational awareness. The aesthetic is Brutalist Cyber-Technical: unapologetically raw, surgical, and devoid of decorative consumer fluff. It balances functional industrial discipline with hyper-focused digital telemetry.

The interface prioritizes information throughput, strict visual parsing hierarchy, and terminal-grade legibility over soft consumer styling. Interactions feel immediate, stark, and definitive—evoking zero-trust security postures and cold room forensic intelligence.

## Colors

The color system is engineered strictly for dark environments, anchored by a deep obsidian core (`#000000`) and low-luminance steps (`#080808`, `#0A0A0A`, `#111111`) to prevent eye fatigue during prolonged low-light surveillance operations.

### Surface Architecture
- **Base Canvas:** `#000000` (absolute zero background)
- **Recessed / Secondary Background:** `#080808`
- **Surface (Containers / Panels):** `#0A0A0A`
- **Elevated Canvas (Flyouts, Popovers):** `#111111`
- **Status Container Base:** `#1F1F1F`

### Structural Borders
- **Standard Structural Hairline:** `rgba(255, 255, 255, 0.145)`
- **Interactive / Active Hairline:** `rgba(82, 168, 255, 0.4)`

### Typography Tones
- **Primary Readout:** `#FFFFFF` (100% luminance, high urgency)
- **Secondary Readout:** `#999999` (metadata, labels, descriptions)
- **Muted Readout:** `#666666` (timestamps, grid metrics, disabled states)

### Status & Telemetry
- **Active / Engaged:** `#52A8FF` (system operations, telemetry streams, focus rings)
- **Pass / Nominal:** `#62C073` (secure state, cryptographic validation pass)
- **Warning / Degraded:** `#999999` (anomalies under passive triage)
- **Failure / Breach Indicator:** `#EDEDED` (stark monochrome alert for anomalous disruption)

## Typography

Typography enforces an uncompromising dual structure:
1. **Structural & Editorial (Inter):** Tight tracking (-1px to -3.36px on display headlines), medium 500 weights, strictly structured for headers, contextual alerts, and prose.
2. **Forensic Telemetry (Monospace):** Compact tabular digits, memory addresses, SHA-256 signatures, network interfaces, and protocol traces. Always mapped to `#999999` or `#666666` for auxiliary metadata, shifting to `#FFFFFF` when selected or critical.

All monospace data tables must enforce `font-feature-settings: "tnum" 1` to guarantee absolute vertical column stability across real-time dynamic data feeds.

## Layout & Spacing

The platform is constructed on a strict 8px spatial grid with 4px sub-intervals for dense data packing. Space is treated pragmatically: large gaps are avoided in analytical interfaces to preserve information density within viewports.

### Grid Framework
- **Desktop (>=1280px):** 12-column or 16-column flexible dashboard grid. Gutters locked to `1rem` (16px), canvas margins at `1.5rem` (24px).
- **Tablet (768px - 1279px):** 8-column layout. Gutters locked to `0.5rem` (8px), canvas margins at `1rem` (16px).
- **Mobile (<768px):** 4-column compact flow. Gutters and outer margins set to `0.5rem` (8px). Analytical panels collapse into vertically scrollable stacked cards.

Panels must feature high internal density using `space-xs` (4px) and `space-sm` (8px) for tabular logs, metric blocks, and forensic feeds.

## Elevation & Depth

This brutalist system rejects traditional soft, floating drop shadows. Visual depth is established through tonal stacking, razor-thin borders, and selective radial glow emitters:

- **Surface Layering:** Zero base elevation begins at `#000000`. Mid-level workspaces use `#080808`. Surface cards rest at `#0A0A0A`. Modals, menus, and drawer overlays sit on `#111111`.
- **Delimitation:** Panels and interfaces do not use drop shadows to separate themselves; they utilize a crisp `1px solid rgba(255, 255, 255, 0.145)` border.
- **Accents & Radial Glow:** High-priority cards (active threat vectors, selected telemetry units) incorporate a faint, subtle top-edge radial gradient: `radial-gradient(circle at 50% 0%, rgba(82, 168, 255, 0.08) 0%, transparent 70%)`.
- **Focused & Interactive States:** Elements illuminate their outer bounding border to `rgba(82, 168, 255, 0.5)` with no soft blur, maintaining crisp vector outlines.

## Shapes

The geometric architecture is built on a 0px border-radius standard for all core structural components, upholding a brutalist, console-native identity.

- **Panels, Windows, Buttons, Inputs, Cards:** `0px` radius. Sharp, precise corners that connect flush across the structural border grid.
- **Exception (Pill Indicators):** Telemetry status chips explicitly break the sharp grid with fully rounded caps (`9999px`) to immediately denote them as atomic status units distinct from structural frames.

## Components

### Buttons (`.btn-square`)
- **Geometry:** `0px` border-radius, strict rectangular bounding box.
- **Padding:** Vertical `0.5rem` (8px), Horizontal `1rem` (16px).
- **Variants:**
  - *Primary:* Background `#FFFFFF`, text `#000000`, weight 500. Hover: `#EDEDED`.
  - *Active / Action:* Background `#52A8FF`, text `#000000`, weight 500. Hover: `rgba(82, 168, 255, 0.85)`.
  - *Secondary / Outline:* Background `#000000`, border `1px solid rgba(255, 255, 255, 0.145)`, text `#FFFFFF`. Hover: Background `#111111`, border color `#FFFFFF`.
  - *Destructive / Danger:* Background `#000000`, border `1px solid #EDEDED`, text `#EDEDED`.

### Cards & Analytical Panels
- **Structure:** Background `#0A0A0A`, border `1px solid rgba(255, 255, 255, 0.145)`.
- **Internal Padding:** `1rem` (16px) or `1.5rem` (24px) depending on density context.
- **Header:** Delimited by a bottom border `1px solid rgba(255, 255, 255, 0.145)` with `JetBrains Mono` uppercase section labeling.

### Status Chips (Pill Indicators)
- **Geometry:** Pill shape (border-radius `9999px`).
- **Surface:** Background `#1F1F1F`, border `1px solid rgba(255, 255, 255, 0.145)`.
- **Content:** 6px solid circular status dot on the left, followed by uppercase `JetBrains Mono` label (`10px` caps).
- **Indicators:**
  - *PASS:* Status dot `#62C073`
  - *WARN:* Status dot `#999999`
  - *FAIL:* Status dot `#EDEDED`
  - *ACTIVE:* Status dot `#52A8FF`

### Input Fields
- **Geometry:** Height 36px, `0px` border-radius.
- **Styling:** Background `#080808`, border `1px solid rgba(255, 255, 255, 0.145)`, text `#FFFFFF`.
- **Typography:** `JetBrains Mono`, 12px.
- **Focus:** Border `1px solid #52A8FF`, outline none.

### Checkboxes & Radios
- **Geometry:** Checkbox `14px x 14px`, 0px border-radius. Radio `14px x 14px`, round.
- **Border:** `1px solid rgba(255, 255, 255, 0.2)`. Background `#000000`.
- **Checked State:** Checkbox fills with `#52A8FF` and a `#000000` sharp tick. Radio features an inset `#52A8FF` center dot.

### Forensic Data Tables & Telemetry Lists
- **Structure:** Flush full-width layouts. Cell border-bottom `1px solid rgba(255, 255, 255, 0.08)`.
- **Typography:** Monospaced tabular numbers (`code-md`), text color `#999999`, highlighting to `#FFFFFF` on row hover (`#080808`).
- **Spacing:** Vertical cell padding strictly `6px` or `8px` for maximum viewport throughput.