# DIVS UI/UX Standards

**Status:** Active  
**Current visual reference:** Driver Workspace  
**Scope:** DIVS frontend interfaces  
**Owner:** DIVS product and engineering

This document defines the shared visual and interaction standards for DIVS. The Driver Workspace is the current reference implementation. These standards apply to the Driver Workspace now and should guide future workspaces unless the product owner explicitly changes them.

## 1. Core principles

DIVS interfaces must be:

- **Clear:** users can understand a page, status, action, or warning without guessing.
- **Consistent:** the same meaning uses the same color, component, and interaction pattern throughout the product.
- **Readable:** body text and controls remain comfortable to read on phones and desktops.
- **Responsive:** content must adapt without horizontal page overflow, clipped controls, or overlapping text.
- **Accessible:** controls are keyboard accessible, have visible focus, and do not rely on color alone to communicate meaning.
- **Truthful:** verification and performance statuses must reflect actual system data. Visual emphasis must never imply a check has passed when it has not.

## 2. Brand and semantic colors

Use the following palette as the default DIVS interface language. Prefer shared CSS variables or design tokens over one-off color values.

| Purpose | Light theme | Dark theme | Usage |
|---|---|---|---|
| Primary action / brand blue | `#2563EB` | `#60A5FA` | Main buttons, links, selected states, focus indicators |
| Primary hover | `#1D4ED8` | `#93C5FD` | Hover and active feedback |
| Green highlight | `#00C853` | `#4ADE80` | Positive highlights and successful completion |
| Success surface | `#E8F9EF` | `#102B20` | Success messages and positive status backgrounds |
| Warning | `#B7791F` | `#F5D58A` | Pending action, attention, caution |
| Warning surface | `#FFF7E6` | `#332912` | Warning banners and pending status backgrounds |
| Error / danger | `#B42318` | `#FECACA` | Failed actions, critical errors, rejected states |
| Error surface | `#FFF0F0` | `#2A1111` | Error banners and danger status backgrounds |
| Light page background | `#F5F7FA` | `#080B10` | Workspace page background |
| Surface / card | `#FFFFFF` | `#111821` | Cards, menus, panels |
| Muted surface | `#F8FAFC` | `#0D141C` | Secondary surfaces |
| Main text | `#17212B` | `#EDF2F7` | Headings and body text |
| Muted text | `#64748B` | `#A5B2C1` | Supporting text and metadata |
| Border | `#E2E8F0` | `#293543` | Card, field, and section boundaries |

### Color rules

1. Blue communicates an action, link, selection, or primary brand emphasis. It does not mean verification has passed.
2. Green communicates a positive or successful state. Use it for verified/passed/active states only when the underlying data supports that state.
3. Yellow/amber communicates pending work, caution, or something requiring attention. Pending must not look like success.
4. Red communicates errors, failed/rejected states, destructive actions, or critical restrictions.
5. Neutral surfaces and text carry ordinary content. Do not color every element.
6. Maintain readable contrast in both themes. Never place muted text on a similarly muted surface.
7. Color must be accompanied by a readable label, icon, or other cue; never use color as the only status indicator.

## 3. Typography

Typography must remain readable on small mobile screens and must scale without breaking layouts.

| Element | Recommended size |
|---|---:|
| Main page title | 1.6–2rem, responsive |
| Section heading | 1.15–1.35rem |
| Card title | 1rem |
| Body copy | 0.95–1rem |
| Supporting copy | 0.875–0.9rem |
| Form labels | 0.9–1rem |
| Input text | 1rem minimum |
| Status badge | 0.75–0.8rem |
| Metadata / timestamps | 0.8rem minimum |
| Large statistic | 1.2–1.6rem or responsive |

Typography rules:

- Use a clear hierarchy: page title, section heading, card title, body, supporting information.
- Use comfortable line height: generally 1.4–1.6 for body text.
- Avoid shrinking important text to fit a card. Allow wrapping or adjust the layout instead.
- Avoid long all-caps text. Reserve uppercase styling for short labels or eyebrow text.
- Do not use tiny text for important status, warnings, form labels, or actions.
- Mobile overrides must not reduce important workspace text below readable sizes.

## 4. Buttons and actions

### Primary button
- Blue background with white text.
- Used for the main action on a screen or within a form.
- Must have a clear action label, adequate height, and visible hover/focus/disabled states.

### Secondary button
- Transparent or neutral surface with blue text and a visible border where appropriate.
- Used for a supporting action that should not compete with the primary action.

### Destructive button
- Red text and/or red border.
- Used for destructive or irreversible actions.
- Use a confirmation step when the action has significant consequences.

### Button interaction states
- Default: clear visual affordance.
- Hover: darker/lighter brand surface or subtle elevation.
- Focus: visible keyboard outline with sufficient contrast.
- Active: clear pressed feedback.
- Disabled/loading: visibly unavailable; prevent duplicate submissions and communicate progress.
- Do not use a link styled as a button for an action that changes application state. Use a button for actions and a link for navigation.

## 5. Links

- Links use the DIVS blue accent and must be visually distinguishable from ordinary body text.
- Link labels should describe the destination or action (for example, "Edit profile", not "Click here").
- Provide hover and keyboard-focus feedback.
- Navigation links should not be presented as disabled-looking text unless the feature is genuinely unavailable.
- Use consistent link styling across cards, menus, panels, and workspace navigation.

## 6. Status badges

Use consistent status labels and semantic colors:

| Status meaning | Color |
|---|---|
| Approved, passed, active, upheld | Green |
| Pending, submitted, in review, needs review | Amber |
| Rejected, failed, suspended, denied | Red |
| Informational / neutral / unavailable | Neutral or blue, according to meaning |

- Show the actual status in text.
- Keep badge padding and text size consistent.
- Do not use green for pending states or amber for completed success.
- Do not convert unavailable or unknown data into a successful status.

## 7. Messages, warnings, and errors

- **Success:** green surface and text; explain what succeeded.
- **Warning:** amber surface and text; explain what needs attention and, where possible, the next step.
- **Error:** red surface and text; explain what failed and how the user can recover.
- **Information:** neutral or blue surface; provide context without suggesting urgency.
- Use appropriate accessible semantics such as `role="status"` for non-urgent updates and `role="alert"` for urgent errors.
- Do not expose internal stack traces, secrets, or sensitive backend details to users.
- Keep warning and error copy concise, specific, and actionable.

## 8. Cards, panels, and layout

- Use consistent surface colors, borders, corner radii, and spacing.
- Use cards to group related information, not to decorate every individual line.
- Maintain clear spacing between sections and inside panels.
- Keep important actions easy to find.
- Long names, addresses, identifiers, and messages must wrap safely.
- Avoid fixed widths that cause horizontal page scrolling.
- Use consistent alignment for headings, badges, counts, and action controls.

## 9. Forms and inputs

- Labels must remain visible; placeholders are not a replacement for labels.
- Inputs should use readable text (normally 1rem), adequate height, and clear borders.
- Focused fields use the blue accent and a visible focus treatment.
- Validation errors appear near the relevant field and explain how to correct the value.
- Preserve entered values when validation fails where safe to do so.
- Required fields and optional fields must be clearly identified.
- Do not communicate validation state using color alone.

## 10. Light and dark themes

Both themes are supported product experiences, not afterthoughts.

- Use semantic tokens so the same component changes correctly with the active theme.
- Check text, borders, cards, menus, buttons, badges, warnings, and errors in both themes.
- Do not hardcode a light-only surface or dark-only text inside a reusable component.
- Avoid pure black/white combinations where a softer surface improves hierarchy, unless a specific design area intentionally uses them.
- Theme changes must not alter application behaviour or data.

## 11. Responsive behaviour

Design mobile-first and verify both narrow and wide layouts.

- No horizontal page overflow at common phone widths.
- Cards and grids collapse to one column when content becomes cramped.
- Navigation may scroll horizontally when appropriate, but the page itself must not.
- Buttons remain large enough to tap and do not overlap.
- Text wraps instead of being clipped or forcing fixed-width containers wider.
- Test long translated Swahili labels as well as English labels; translated text can be longer.
- At very narrow widths, stack content rather than shrinking text excessively.

## 12. Accessibility and interaction

- All interactive controls must be keyboard reachable.
- Provide visible `:focus-visible` styling.
- Use semantic buttons for actions and links for navigation.
- Provide accessible names for icon-only controls.
- Preserve logical heading order and meaningful page landmarks.
- Respect reduced-motion preferences.
- Do not rely only on hover to reveal essential information.
- Use sufficient contrast for text, icons, borders, and focus indicators.

## 13. English and Swahili

- All user-facing workspace labels, status names, messages, and action labels must support English and Swahili.
- Do not translate identifiers, API values, or internal enum keys.
- Keep the same meaning and severity across languages.
- Allow for longer Swahili labels without clipping or overlapping.
- Dates and times should use an appropriate locale.

## 14. Driver Workspace implementation guidance

The Driver Workspace is the current reference implementation. Its interface should consistently apply:

- Blue for primary actions, navigation links, selected states, and focus.
- Green for verified/successful states and positive highlights.
- Amber for pending verification, cautions, and restrictions requiring attention.
- Red for failed checks, errors, rejected states, and critical restrictions.
- Larger readable typography for profile details, section headings, verification rows, performance history, notifications, and supporting copy.
- Responsive cards and rows that wrap safely on mobile.
- Equivalent presentation in light and dark themes.

Do not change API contracts, permission rules, verification decisions, performance calculations, or user data merely to achieve a visual effect.

## 15. Implementation checklist

Before considering a workspace UI change complete, verify:

- [ ] Typography hierarchy is readable on mobile and desktop.
- [ ] Primary buttons are blue; secondary actions are visually quieter.
- [ ] Links are consistently styled and clearly navigable.
- [ ] Success, warning, error, and informational states use the correct semantic treatment.
- [ ] Status badges include text and reflect real system state.
- [ ] Light and dark themes both remain readable.
- [ ] English and Swahili labels fit without clipping.
- [ ] Keyboard focus is visible and controls have accessible names.
- [ ] No horizontal page overflow or overlapping content is introduced.
- [ ] Existing application behaviour and backend contracts remain unchanged.

---

**Change policy:** Update this document when the product owner approves a change to the shared design language. Until then, use it as the source of truth for DIVS workspace UI/UX work.
