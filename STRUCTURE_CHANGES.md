# Frontend Structure Reorganization

## Overview
The frontend has been reorganized from a shared `/static` directory to page-specific modules under `/pages`. Each page (login, register, home) now has its own `css/` and `js/` subdirectories containing only the relevant files for that page.

## New Directory Structure

```
frontend/
├── pages/
│   ├── login/
│   │   ├── css/
│   │   │   └── login.css
│   │   └── js/
│   │       └── login.js
│   ├── register/
│   │   ├── css/
│   │   │   └── register.css
│   │   └── js/
│   │       └── register.js
│   └── home/
│       ├── css/
│       │   ├── main.css
│       │   ├── sidebar.css
│       │   ├── chat.css
│       │   ├── buttons.css
│       │   └── modal.css
│       └── js/
│           ├── app.js
│           ├── state.js
│           ├── modal.js
│           ├── friendRequests.js
│           ├── status.js
│           └── chat.js
├── static/
│   └── avatars/         # Kept for avatar images
└── templates/
    ├── login.html       # Updated to use /pages/login/
    ├── register.html    # Updated to use /pages/register/
    └── home.html        # Updated to use /pages/home/
```

## Changes Made

### 1. Login Page Module
- **Created:** `pages/login/css/login.css`
  - Extracted all inline styles from login.html
  - Includes: body, container, form, buttons, error messages
  
- **Created:** `pages/login/js/login.js`
  - Extracted all inline scripts from login.html
  - Handles: form submission, error display, URL param checking

- **Updated:** `templates/login.html`
  - Removed all inline `<style>` and `<script>` tags
  - Added: `<link rel="stylesheet" href="/pages/login/css/login.css">`
  - Added: `<script src="/pages/login/js/login.js"></script>`

### 2. Register Page Module
- **Created:** `pages/register/css/register.css`
  - Extracted all inline styles from register.html
  - Includes: body, container, form, avatar grid, password hints
  
- **Created:** `pages/register/js/register.js`
  - Extracted all inline scripts from register.html
  - Handles: avatar selection, form validation, error display

- **Updated:** `templates/register.html`
  - Removed all inline `<style>` and `<script>` tags
  - Added: `<link rel="stylesheet" href="/pages/register/css/register.css">`
  - Added: `<script src="/pages/register/js/register.js"></script>`

### 3. Home Page Module
- **Moved:** All CSS files from `static/css/` to `pages/home/css/`
  - buttons.css, chat.css, main.css, modal.css, sidebar.css

- **Moved:** All JS files from `static/js/` to `pages/home/js/`
  - app.js, chat.js, friendRequests.js, modal.js, state.js, status.js

- **Updated:** `templates/home.html`
  - Changed all `/static/css/` paths to `/pages/home/css/`
  - Changed all `/static/js/` paths to `/pages/home/js/`

### 4. Backend Updates
- **Updated:** `backend/app/main.py`
  - Added `PAGES_DIR` variable pointing to `frontend/pages`
  - Added new static mount: `app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")`
  - Kept original `/static` mount for avatar images

## Benefits

1. **Better Organization**: Each page's assets are grouped together
2. **Easier Maintenance**: Finding CSS/JS for a specific page is straightforward
3. **Reduced Confusion**: No more wondering which CSS/JS belongs to which page
4. **Scalability**: Easy to add new pages with their own assets
5. **Cleaner Templates**: No more inline styles/scripts in HTML files

## Testing

Server is running at: http://0.0.0.0:8000

Test the following:
- ✅ Login page loads with proper styling
- ✅ Register page loads with proper styling  
- ✅ Home page loads with all functionality (chat, friends, status)
- ✅ All JavaScript modules load correctly
- ✅ Avatar images still display (from /static/avatars/)

## Notes

- The `/static/avatars/` directory remains unchanged
- All page-specific JavaScript uses ES6 modules with relative imports
- Home page JS files (app.js) exports functions for use in templates
