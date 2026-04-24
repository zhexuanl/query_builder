## 1. Change Alignment

- [x] 1.1 Retarget the active OpenSpec artifacts to the shell milestone; remove out-of-scope capability specs from this change

## 2. Workspace Scaffold

- [ ] 2.1 Create the Angular workspace under `frontend/` with one library project and one demo app
- [ ] 2.2 Configure the library package surface as `@query-builder/ui` with `<qb-query-builder>` as the shell entry point

## 3. Theme Foundation

- [ ] 3.1 Install and configure PrimeNG in unstyled mode with Tailwind-based styling
- [ ] 3.2 Create and export `QUERY_BUILDER_PT` plus the shell design tokens required for the approved visual direction

## 4. Shell Components

- [ ] 4.1 Implement `QueryBuilderComponent` as the only exported shell component
- [ ] 4.2 Implement the split-panel layout with the business-language builder sections: `Start with`, `Add related data`, `Choose columns`, `Filter rows`, `Parameters`, `Sort & Limit`
- [ ] 4.3 Implement preview pane shell states for `empty`, `data`, and `sql` using local UI state only

## 5. Demo And Verification

- [ ] 5.1 Build the demo app to render `<qb-query-builder>` and exercise section expansion plus preview state switching
- [ ] 5.2 Run automated verification: `ng test query-builder-ui --watch=false`, `ng build query-builder-ui`, and `ng build demo`
- [ ] 5.3 Run local verification: `ng serve demo` plus manual browser checks for shell layout, section expansion, preview state switching, and theme behavior
