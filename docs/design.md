# Design Specification: The Lenny Growth Assistant

**Version:** 1.0.0  
**Design Philosophy:** Precision, Restraint, and High Density (Inspired by Claude Artifacts, Linear, and Vercel)  
**Author:** Forward Deployed Engineer  

---

### 1. UI/UX Principles & Aesthetic Direction

1. **Information-Dense & Distraction-Free:** Designed for product leaders who value time. High typography hierarchy, minimal decorative chrome, and purposeful whitespace.
2. **Context Continuity:** The conversation remains always visible. Artifacts slide out into a side-by-side split pane rather than occluding the chat or navigating away.
3. **Transparent Grounding:** Every insight and quote is visually tied to its source through clickable/expandable citation chips, showing the episode title, guest name, and timestamp.
4. **Safety as a First-Class Feature:** Clear visual indicators identify sandboxed execution environments, giving users confidence that generated code is safely isolated.

---

### 2. Information Architecture & Dual-Pane Layout

The layout is split into two primary panels on desktop, dynamically adapting to a stacked view on smaller viewports.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  The Lenny Growth Assistant   [ Model: Ollama (Local) ▼ ] [ Mode: Default ▼ ]   [● System OK]│
├───────────────────────┬───────────────────────────────────┬─────────────────────────────────┤
│ SESSIONS              │ CHAT THREAD                       │ ARTIFACT VIEWER                 │
│                       │                                   │                                 │
│ ＋ New Chat           │ User:                             │ [Preview]  [Code]   [📋] [⬇] [✕] │
│                       │ How do I find product-market fit? │ ─────────────────────────────── │
│ 💬 Finding PMF in B2B │                                   │                                 │
│ 💬 Retention Loops    │ Lenny Assistant:                  │  Interactive PMF Engine         │
│ 💬 Pricing Strategy   │ In episode #142 with Rahul Vohra  │  ┌───────────────────────────┐  │
│                       │ (Superhuman), PMF is measured by: │  │ Survey Score: [ 42% ]     │  │
│                       │                                   │  │ [=========|========]      │  │
│                       │ • "Very Disappointed" metric      │  │ Result: Strong PMF Signal │  │
│                       │ • Segmentation by power users     │  └───────────────────────────┘  │
│                       │                                   │                                 │
│                       │ [🏷️ Rahul Vohra • 12:40]          │ (Sandboxed iframe: allow-scripts│
│                       │                                   │  isolated from parent DOM)      │
│                       │ ┌───────────────────────────────┐ │                                 │
│                       │ │ 📦 Artifact: PMF Engine       │ │                                 │
│                       │ │ Click to open in viewer ➔     │ │                                 │
│                       │ └───────────────────────────────┘ │                                 │
│                       ├───────────────────────────────────┤                                 │
│                       │ [ Ask a product or growth question...                      ] [ Send ]│
└───────────────────────┴───────────────────────────────────┴─────────────────────────────────┘
```

---

### 3. Key Interaction States & Micro-interactions

#### 3.1 Chat Stream State Flow
1. **Prompt Submitted:** Input field clears, user bubble appears immediately.
2. **Status Event:** Subtle animated pulse badge displays retrieval activity: `Searching Lenny's Podcast archives...`.
3. **Citations Received:** Collapsible citation accordion populates with relevant guest cards before token stream starts.
4. **Streaming Tokens:** Smooth text flow with syntax-highlighted markdown (GFM).
5. **Artifact Detected:** As `<artifact>` tags are encountered in the stream, an interactive "Artifact Card" is rendered in the chat stream, and the side drawer slides open with the preview.

#### 3.2 Artifact Viewer States
- **Preview Tab:** Renders native Markdown using GitHub Flavored Markdown or HTML/CSS inside the sandboxed iframe.
- **Code Tab:** Shows formatted source code with one-click "Copy to Clipboard" and line numbering.
- **Action Toolbar:**
  - *Copy Code:* Instant visual checkmark feedback ("Copied!").
  - *Download File:* Exports as `.html` or `.md`.
  - *Expand/Collapse:* Toggles between 50% split view and full-width focus mode.
  - *Close:* Dismisses the drawer smoothly without losing chat context.

---

### 4. Typography, Color System & Design Tokens

```css
/* Color Palette */
--bg-primary: #0f172a;       /* Slate 900 - Deep focused dark surface */
--bg-secondary: #1e293b;     /* Slate 800 - Cards & Sidebar */
--bg-tertiary: #334155;      /* Slate 700 - Hover states & borders */
--text-primary: #f8fafc;     /* Slate 50 - High-contrast readable copy */
--text-secondary: #94a3b8;   /* Slate 400 - Metadata & timestamps */
--accent-primary: #6366f1;   /* Indigo 500 - Primary actions & links */
--accent-hover: #4f46e5;     /* Indigo 600 - Hover buttons */
--badge-citation: #064e3b;   /* Emerald 900 - Grounded source tag */
--badge-citation-text: #34d399; /* Emerald 400 */
--border-subtle: #334155;    /* Slate 700 */
```

---

### 5. Accessibility & Responsive Heuristics

1. **WCAG 2.1 AA Compliance:**
   - All text achieves a minimum contrast ratio of $4.5:1$ against backgrounds.
   - Interactive buttons have explicit focus rings (`focus:ring-2 focus:ring-indigo-500`).
2. **Keyboard Navigation:**
   - `Enter` submits prompt, `Shift + Enter` inserts newline.
   - `Esc` closes the Artifact drawer.
   - Standard tab order across sidebar, chat, and artifact viewer.
3. **Responsive Breakpoints:**
   - Desktop ($\ge 1024\text{px}$): Dual-pane split (50/50 or 60/40).
   - Tablet / Mobile ($< 1024\text{px}$): Sidebar becomes a slide-out drawer, Artifact Viewer opens in an overlay modal with full-screen toggle.
