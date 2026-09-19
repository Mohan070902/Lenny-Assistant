# Agent Transcript 03: Security & Sandboxed Artifact Isolation

**Date:** 2026-09-19  
**Agent:** Antigravity (Forward Deployed Engineer Pairing Agent)  
**Objective:** Formulate and verify the defense-in-depth isolation strategy for untrusted LLM-generated HTML artifacts.

---

### Threat Modeling: Untrusted Generated HTML/CSS
LLMs instructed to generate interactive calculators, mock dashboards, or visual components may inadvertently (or maliciously via prompt injection) output malicious payloads containing:
- Stealing cookies via `document.cookie`
- Reading parent application localStorage / session tokens
- Modifying or hijacking the parent DOM (phishing attacks)
- Unauthorized background network requests to third-party endpoints

### Isolation Strategy Implemented

#### 1. DOMPurify Sanitization Layer
- Prior to mounting any markup into the browser rendering context, the artifact string passes through `DOMPurify.sanitize(content, { WHOLE_DOCUMENT: true, ... })`.
- This strips dangerous protocols (`javascript:`, `data:text/html`), invalid forms of obfuscation, and unpermitted script attributes.

#### 2. Strict Iframe Sandboxing (`sandbox="allow-scripts"`)
- The sanitized HTML is delivered via `srcDoc` to an `<iframe>` configured with:
  ```html
  <iframe sandbox="allow-scripts" srcDoc={cleanHtml} />
  ```
- **What is permitted:**
  - `allow-scripts`: Permitted so that interactive artifacts (e.g. ROI sliders, growth calculators, charting libraries) can execute DOM event handlers and JavaScript functions within their isolated frame.
- **What is explicitly blocked:**
  - `allow-same-origin` is **STRICTLY OMITTED**. Because the iframe runs in a unique, null origin:
    - It CANNOT read or write parent `document.cookie`.
    - It CANNOT access parent `localStorage` or `sessionStorage`.
    - It CANNOT navigate or alter the parent window (`window.top` or `window.parent`).
    - It CANNOT trigger form submissions to parent origin credentials.
  - `allow-top-navigation` is **BLOCKED**. The iframe cannot redirect the user to phishing destinations.

### Verification
- Tested mounting an artifact attempting to read `window.parent.document.cookie`.
- Browser blocked the cross-origin access with: `SecurityError: Blocked a frame with origin "null" from accessing a cross-origin frame.`
- Verified interactive calculators function seamlessly with local button clicks and calculation state.
