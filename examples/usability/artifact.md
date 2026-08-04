## Team workspace settings

### Members

Team members are listed with an action for each row.

#### Controls

- Remove member button
- Promote to admin button
- Button

### Danger zone

A Delete workspace button sits below the member list. Activating it removes the workspace, all of
its documents, and every member's access, then lands the user on the workspace list. The workspace
list is the next screen in the flow; this spec defines no screen between the two, and no later
screen that acts on a removed workspace.

### Import errors

A bulk import accepts up to 12 rows at a time. When an import fails, the screen shows the message
"Something went wrong. Try again," a Retry button, and the number of rows that were submitted. The
row table is not redisplayed and no per-row state is shown.
