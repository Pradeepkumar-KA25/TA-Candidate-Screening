# Shared UI

`styles/ui-primitives.css` contains the application-wide presentation contracts for cards, buttons, form controls, search inputs, tables, and pagination.

All routed pages consume these primitives through the global `src/styles.css` import. Page styles should be limited to page-specific layouts or data visualizations; use the shared classes before adding another local control style.