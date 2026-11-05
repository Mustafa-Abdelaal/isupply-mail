---
paths:
  - "**/{ui,widgets,components,screens,pages,views,features,theme,l10n,i18n,locales}/**"
  - "**/*.{tsx,jsx,vue,svelte,xaml,storyboard,xib}"
---

# UI code

Our users are non-technical staff on six platforms, many of them reading and writing Arabic.

- **Strings**: every user-facing string goes through the localization layer (English and Arabic). No
  concatenated sentences; use ICU/plural-aware messages.
- **RTL**: use logical layout (start/end, never left/right) and mirror directional icons. Render message
  subject and body with `dir="auto"` so mixed Arabic/English text displays correctly. Verify in an RTL
  locale.
- **Accessibility (WCAG 2.2 AA)**: every control has an accessible name and keyboard access with
  visible focus. Contrast is at least 4.5:1, touch targets at least 44×44 pt/48 dp, and the UI respects
  OS font scaling and reduced motion.
- **Email-client UX**: lists are virtualized (100k-message folders), states exist for empty, loading,
  error and offline, destructive actions offer undo, and send shows progress and outbox state.
  Keyboard shortcuts on desktop and web.
- **Architecture**: no protocol or business logic in widgets/components. UI talks to the app core
  through view models or state, and platform specifics go through adapters.
- **Verify**: `/verify-ui` with screenshots in LTR + RTL, light + dark, phone + desktop widths. Ask the
  `ux-a11y-reviewer` subagent to review new screens.
