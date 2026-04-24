# Query Builder UI Design System

Status: Approved shell milestone

## 1. Product Character

This UI is a governed data workflow surface, not a landing page, dashboard, or Material clone.

The right tone is balanced enterprise:

- professional without feeling sterile
- premium without decorative excess
- dense enough to feel useful
- clear enough for non-technical operators

The shell must already communicate the real product structure: source selection, related data, columns, filters, parameters, and sort/limit.

## 2. Theme Foundation

- Theme: light only
- Surface character: warm whites and soft cool neutrals
- Accent character: restrained orange for primary actions and active emphasis
- Geometry: soft corners only
- Depth: shallow, broad shadows with low contrast

### Core Palette

| Role | Value | Usage |
| --- | --- | --- |
| Canvas background | `#f7f2ea` | page background |
| Primary panel surface | `#fffaf2` | builder and preview surfaces |
| Raised surface | `#fffdf8` | table and preview wells |
| Muted surface | `#f1eadf` | section and table contrast |
| Border neutral | `#d7dee8` | panel and control borders |
| Border strong | `#b9c3d0` | active outlines and separators |
| Text strong | `#17202a` | headings and key labels |
| Text default | `#334155` | body copy |
| Text muted | `#5d6875` | helper text and metadata |
| Accent primary | `#c8641a` | primary action and active emphasis |
| Accent primary hover | `#a95213` | hover and pressed state |
| Accent wash | `#ffe5cf` | selected or highlighted backgrounds |
| SQL surface | `#101820` | SQL preview background |
| SQL text | `#f4efe6` | SQL preview foreground |

## 3. Typography

### Font Families

- UI text: `IBM Plex Sans`
- Technical text: `IBM Plex Mono`

### Rules

- Headings are firm and compact, never oversized marketing headlines.
- Section labels use small uppercase text with restrained tracking.
- Body copy stays plain and direct.
- SQL and technical tokens always use the mono face.
- Do not use `Inter`, `Roboto`, or Material defaults.

## 4. Shape And Spacing

### Radius Scale

- Small controls: `10px`
- Default controls: `14px`
- Large panel shells: `20px` to `28px`
- Pills and segmented toggles: full rounded

Never use sharp corners.

### Spacing Character

- builder rail is structured and rhythmic, not cramped
- section separation comes from border rhythm and vertical spacing
- do not stack cards inside cards
- avoid giant empty gaps that waste workflow space

## 5. Layout Principles

- Desktop-first split layout
- Builder rail width around `420px`
- Preview pane fills the remaining width
- Most builder sections default expanded
- Preview mode control remains visually anchored near the preview title
- The left rail should feel like a structured form workbench, not a settings sidebar

## 6. Component Styling

### Panels

- Main surfaces use warm white fills with cool neutral borders.
- Depth is subtle and wide, never dark and floating.
- Use one surface per section. No nested card stacks.

### Buttons

- Primary buttons use the orange accent with white text.
- Secondary buttons stay light with clear border definition.
- Hover states should sharpen contrast, not add gimmicks.

### Inputs And Selectors

- Inputs should feel precise and quiet.
- Border emphasis increases on hover and focus.
- Focus states should be visible but restrained.
- Controls should not resemble Material fields.

### Tabs And Segmented Controls

- Use pill or softly rounded segmented treatments.
- Active state should feel deliberate and controlled.
- Avoid loud fill colors except for genuinely primary emphasis.

### SQL Surface

- SQL view uses mono type, dark technical contrast, and readable spacing.
- It should look technical and readable without turning into a terminal parody.

## 7. Interaction Style

- Interactions should feel immediate and calm.
- Motion should be short and purposeful.
- Expand/collapse transitions should be subtle.
- Hover, focus, and active states must already feel production-grade.
- Do not add playful animation, elastic motion, or decorative flourishes.

## 8. Language Rules

Use business language in visible UI labels:

- `Start with`
- `Add related data`
- `Choose columns`
- `Filter rows`
- `Parameters`
- `Sort & Limit`

Avoid exposing raw SQL vocabulary in the primary builder rail.

## 9. Anti-Goals

Do not let the UI drift into any of these patterns:

- Material UI lookalike
- hard-corner enterprise boxes
- dashboard KPI chrome
- nested cards
- wireframe placeholders
- flashy gradients
- dark theme
- oversized empty marketing spacing

## 10. Implementation Contract

For the shell milestone:

- styling comes from Angular component CSS, Tailwind tooling, CSS tokens, and `QUERY_BUILDER_PT`
- export only `QueryBuilderComponent` and `QUERY_BUILDER_PT`
- keep interaction state local to the shell component
- use the demo app only for local visualization and verification
- do not fake data persistence, backend workflows, API services, or secondary library surfaces
