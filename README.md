# Shahram Sajawal — portfolio

Personal portfolio site. Two tracks share one set of pages:

- **`/finance`** — FP&A, finance operations and credit control work
- **`/research`** — MSc dissertation and applied machine learning

Built on [Magic Portfolio](https://github.com/once-ui-system/magic-portfolio) by Once UI (Next.js 16, React 19).

## Running it

```bash
npm install
npm run dev
```

Then open http://localhost:3000 (it redirects to `/finance`).

## Where things live

| What | Where |
|---|---|
| Name, contact, bio, jobs, education, skills | `src/resources/content.tsx` |
| Track headlines and featured badges | the `tracks` object in `src/resources/content.tsx` |
| Colours, fonts, enabled routes, site URL | `src/resources/once-ui.config.ts` |
| Project case studies | `src/app/work/projects/*.mdx` |
| Analysis code behind a case study | `projects/<name>/` (Python; not part of the site build) |
| Notes/blog posts | `src/app/blog/posts/*.mdx` |
| Images | `public/images/` |

## Adding a project

Create a new `.mdx` file in `src/app/work/projects/`. The filename becomes the URL.
The frontmatter controls which track it appears under:

```yaml
---
title: "Project title"
publishedAt: "2026-09-28"     # controls ordering, newest first
track: "finance"              # "finance" or "research" — required for it to show
tag: "FP&A"
summary: "One or two sentences shown on the card."
images:
  - "/images/projects/your-chart.png"
link: "https://github.com/..."   # optional "View project" button
---
```

Without a `track`, a project renders at `/work` but appears on neither track's home page.

## Turning the Notes section on

It is off because there are no posts yet. To enable it:

1. Add an `.mdx` file to `src/app/blog/posts/`
2. Set `"/blog": true` in `routes` in `src/resources/once-ui.config.ts`

## Before deploying

- [ ] **Replace `public/images/avatar.jpg`** — it is currently a generated "SS" placeholder, not a photo
- [ ] Set `baseURL` in `src/resources/once-ui.config.ts` to the real deployed URL (currently `https://shahram-sajawal.vercel.app`)
- [ ] Optionally delete the unused template images in `public/images/gallery/`

## Deploying

Push to GitHub, then import the repository at [vercel.com/new](https://vercel.com/new).
Vercel detects Next.js automatically — no build configuration needed. Every push to `main`
redeploys.

## Licence

The Magic Portfolio template is licensed **CC BY-NC 4.0**: attribution is required and
commercial use is not permitted. The "Build your portfolio with Once UI" credit in the
footer satisfies the attribution requirement and should stay.

Project content, case-study text and figures are my own.
