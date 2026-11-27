# OMNIS UI engine

1. **Discover the design system before writing UI**: grep for the theme/tokens file (tailwind.config.*, theme.ts, CSS variables in :root, a components/ui folder). Reuse existing colors, spacing, radius, typography and components; never introduce a parallel set.
2. **Match conventions**: component file layout, styling method (Tailwind / CSS modules / styled), state management, icon library.
3. **Accessibility baseline**: semantic elements, labels for inputs, focus states, contrast, keyboard paths, `alt` text.
4. **Verify in a real browser when one is available** (Claude in Chrome, the built-in browser, or Playwright via `webapp-testing`): start the dev server (`omnis.py map` shows the command), open the page, exercise the changed interaction, check the console for errors, check a phone width (~390px) and a desktop width.
5. If no browser tool is available, say UI was **NOT VERIFIED visually** — never imply it was.
