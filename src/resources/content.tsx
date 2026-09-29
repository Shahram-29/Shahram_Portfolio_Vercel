import { About, Blog, Gallery, Home, Newsletter, Person, Social, Work } from "@/types";
import { Line, Row, Text } from "@once-ui-system/core";

const person: Person = {
  firstName: "Shahram",
  lastName: "Sajawal",
  name: `Shahram Sajawal`,
  role: "Finance & Business Analytics",
  avatar: "/images/avatar.jpg",
  email: "shahramsajawal@gmail.com",
  location: "Europe/Dublin", // IANA time zone identifier
  languages: ["English", "Urdu"],
  locale: "en",
};

const newsletter: Newsletter = {
  display: false,
  title: <>Subscribe to {person.firstName}'s Newsletter</>,
  description: <>Occasional notes on Irish finance, FP&A and applied analytics</>,
};

const social: Social = [
  {
    name: "GitHub",
    icon: "github",
    link: "https://github.com/Shahram-29",
    essential: true,
  },
  {
    name: "LinkedIn",
    icon: "linkedin",
    link: "https://www.linkedin.com/in/shahram-sajawal",
    essential: true,
  },
  {
    name: "Email",
    icon: "email",
    link: `mailto:${person.email}`,
    essential: true,
  },
];

/**
 * Two tracks, same person:
 *  /finance  — FP&A, finance operations and credit control work
 *  /research — MSc dissertation and applied machine learning
 * Each track has its own headline, subline and filtered project list.
 * Project MDX files carry a `track:` field in their frontmatter.
 */
const tracks = {
  finance: {
    path: "/finance",
    label: "Finance",
    role: "FP&A & Finance Analyst",
    title: `${person.name} – FP&A & Finance Analyst`,
    description:
      "Irish FP&A, month-end reporting and receivables analytics, built in Python and SQL with tests.",
    headline: <>Finance that shows its working</>,
    featured: {
      display: true,
      title: (
        <Row gap="12" vertical="center">
          <strong className="ml-4">NaqCoDE finance function</strong>
          <Line background="brand-alpha-strong" vert height="20" />
          <Text marginRight="4" onBackground="brand-medium">
            Rebuilt in code, 78 tests
          </Text>
        </Row>
      ),
      href: "/work/pakistan-payroll-engine",
    },
    hero: "/images/hero-finance.jpg",
    stats: [
      { value: "3 yrs", label: "finance operations: payroll, reporting, reconciliation, AP" },
      { value: "4", label: "FP&A apps live on Streamlit Community Cloud" },
      { value: "6", label: "finance projects published, all tested" },
      { value: "10+", label: "visa applicants' financials reviewed (freelance)" },
    ],
    subline: (
      <>
        I'm {person.firstName}, a finance professional in Dublin finishing an{" "}
        <Text as="span" size="xl" weight="strong">
          MSc in Business Analytics
        </Text>
        . I build month-end pipelines, cash forecasts and tax models that are tested, documented and
        honest about their limits.
      </>
    ),
  },
  research: {
    path: "/research",
    label: "Research",
    role: "Business Analytics Researcher",
    title: `${person.name} – Business Analytics Research`,
    description:
      "Explainable deep learning for crisis transmission into Irish equity volatility, and other applied ML work.",
    headline: <>Asking whether the model actually knows anything</>,
    featured: {
      display: true,
      title: (
        <Row gap="12" vertical="center">
          <strong className="ml-4">MSc Dissertation</strong>
          <Line background="brand-alpha-strong" vert height="20" />
          <Text marginRight="4" onBackground="brand-medium">
            In progress
          </Text>
        </Row>
      ),
      href: "/work/crisis-volatility-lstm-shap",
    },
    hero: "/images/hero-research.jpg",
    stats: [
      { value: "5,243", label: "trading days analysed, Jan 2003 to Aug 2023" },
      { value: "3", label: "models benchmarked: LSTM, GARCH, HAR" },
      { value: "4", label: "crisis windows compared by origin" },
      { value: "1,547", label: "days attributed with SHAP, across 5 seeds" },
    ],
    subline: (
      <>
        I'm {person.firstName}, an{" "}
        <Text as="span" size="xl" weight="strong">
          MSc Business Analytics
        </Text>{" "}
        candidate at Dublin Business School. My dissertation tests whether an LSTM beats GARCH at
        forecasting Irish equity volatility across four crises — and reports the answer even when it
        is no.
      </>
    ),
  },
} as const;

const home: Home = {
  path: "/",
  image: "/images/og/home.jpg",
  label: "Home",
  title: `${person.name}'s Portfolio`,
  description: `Finance and business analytics work by ${person.name} — Irish FP&A, receivables analytics and explainable machine learning.`,
  headline: tracks.finance.headline,
  featured: tracks.finance.featured,
  subline: tracks.finance.subline,
};

const about: About = {
  path: "/about",
  label: "About",
  title: `About – ${person.name}`,
  description: `Meet ${person.name}, finance and business analytics professional based in Dublin`,
  tableOfContent: {
    display: true,
    subItems: false,
  },
  avatar: {
    display: true,
  },
  calendar: {
    display: false,
    link: "https://cal.com",
  },
  intro: {
    display: true,
    title: "Introduction",
    description: (
      <>
        Shahram is a Dublin-based finance professional with three years of experience across
        payroll, financial reporting, bank reconciliation, accounts payable and audit support,
        currently completing an MSc in Business Analytics at Dublin Business School. He works at the
        point where accounting meets analytics: month-end pipelines that produce a board pack,
        receivables models backtested against what customers actually paid, and a dissertation that
        reports a negative result rather than tuning until it looks good.
      </>
    ),
  },
  work: {
    display: true,
    title: "Work Experience",
    experiences: [
      {
        company: "Independent (freelance)",
        timeframe: "2025 – present",
        role: "Financial Documentation Review",
        achievements: [
          <>
            Reviewed personal bank statements and supporting financial records for more than
            ten student visa applicants, identifying the deposits and transaction patterns a
            visa officer would expect to see evidenced.
          </>,
          <>
            Advised on which supporting documents substantiate each source of funds — salary
            records, tax returns, sponsor declarations, property and loan documentation — and
            where a stated source was not yet supported by the paperwork.
          </>,
          <>
            The work is source-of-funds review in substance: the question is always whether
            the documentary trail actually supports the balance on the statement, which is the
            same test applied in KYC and client due diligence.
          </>,
        ],
        images: [],
      },
      {
        company: "NaqCoDE Technologies Pvt Ltd",
        timeframe: "Oct 2024 – Aug 2025",
        role: "Finance Associate",
        achievements: [
          <>
            Prepared monthly, quarterly and annual financial statements — balance sheet, income
            statement and cash flow — for leadership to use in budgeting and investment decisions.
          </>,
          <>
            Managed company-wide operational and administrative spend and led cost-saving
            initiatives that reduced monthly expenditure by about 15%.
          </>,
          <>
            Built Excel models and automated recurring reports, improving reporting turnaround by
            about 20% and cutting manual data entry.
          </>,
          <>
            Reconciled company bank accounts monthly against the cash book, identifying
            unpresented payments, lodgements in transit and charges that had never been
            recorded, and clearing the resulting journals.
          </>,
          <>
            Designed and operated the expense payment voucher control — vouchers raised in
            finance, approved by a director, disbursed by the CEO — so that no single person
            could release a payment, and every payment carried an approval trail.
          </>,
          <>
            Ran end-to-end monthly payroll, prepared individual and company tax filings, and
            supported the senior auditor in preparing the annual financial statements.
          </>,
        ],
        images: [],
      },
      {
        company: "Nawaz Construction Limited",
        timeframe: "Oct 2022 – Sep 2024",
        role: "Accounts Assistant",
        achievements: [
          <>
            Processed and tracked supplier invoices and payment runs, maintaining accounts-payable
            controls and day-to-day cash-flow visibility.
          </>,
          <>
            Reconciled all company bank accounts, investigating and clearing discrepancies so the
            ledgers stayed audit-ready.
          </>,
          <>
            Handled supplier and procurement queries across multiple construction projects,
            resolving invoice and payment disputes.
          </>,
        ],
        images: [],
      },
      {
        company: "Atlas Honda Limited",
        timeframe: "Jul 2021 – Aug 2021",
        role: "Finance Intern",
        achievements: [
          <>
            Analysed written-off inventory and identified stock that could be returned to suppliers.
          </>,
          <>
            Supported the resolution of supplier and retailer tax issues involving non-registered
            taxpayers.
          </>,
        ],
        images: [],
      },
    ],
  },
  studies: {
    display: true,
    title: "Studies",
    institutions: [
      {
        name: "Dublin Business School",
        description: (
          <>
            MSc Business Analytics, 2025–2026. Dissertation on explainable deep learning for crisis
            transmission into Irish equity volatility. Results expected early 2027.
          </>
        ),
      },
      {
        name: "National University of Sciences and Technology (NUST)",
        description: (
          <>
            BSc Accounting and Finance, 2018–2022. CGPA 3.00/4.00. Coursework included econometrics,
            applied time series in finance and two statistics modules.
          </>
        ),
      },
      {
        name: "ACCA",
        description: <>Part-qualified.</>,
      },
    ],
  },
  technical: {
    display: true,
    title: "Technical skills",
    skills: [
      {
        title: "Python for finance",
        description: (
          <>
            pandas, scikit-learn, statsmodels and PyTorch. Used for month-end pipelines, receivables
            forecasting, GARCH/HAR benchmarks and LSTM models — each project carries unit tests.
          </>
        ),
        tags: [{ name: "Python", icon: "rocket" }],
        images: [
          {
            src: "/images/projects/month-end-revenue-bridge.png",
            alt: "Revenue bridge splitting variance into volume, price and FX",
            width: 16,
            height: 9,
          },
        ],
      },
      {
        title: "SQL & data modelling",
        description: (
          <>
            CTEs, window functions, derived tables and conditional aggregation. The SaaS metrics
            project writes its MRR bridge, retention and cohort tables entirely in SQL over DuckDB.
          </>
        ),
        tags: [{ name: "SQL", icon: "grid" }],
        images: [
          {
            src: "/images/projects/saas-cohort-retention.png",
            alt: "Cohort retention table showing annual renewal steps",
            width: 16,
            height: 9,
          },
        ],
      },
      {
        title: "Accounting systems & Excel",
        description: (
          <>
            QuickBooks Online in practice, plus advanced Excel modelling — PivotTables, lookups and
            automation of recurring reports. Certified training in SAP Financials and Excel for
            FP&A.
          </>
        ),
        tags: [{ name: "Excel", icon: "document" }],
        images: [],
      },
      {
        title: "Irish reporting & tax rules",
        description: (
          <>
            FRS 102 / Companies Act 2014 Schedule 3 layouts, Irish corporation tax with the 35% R&D
            credit and Pillar Two top-up tax, PAYE/USC/PRSI, and ECB and CSO data pipelines.
          </>
        ),
        tags: [{ name: "Ireland", icon: "globe" }],
        images: [
          {
            src: "/images/projects/ct-pillar-two.png",
            alt: "Pillar Two top-up tax by R&D spend",
            width: 16,
            height: 9,
          },
        ],
      },
      {
        title: "Internal control design",
        description: (
          <>
            Segregation of duties written down as code: prepare, approve, disburse, with the
            approved amount frozen at sign-off and re-checked at payment. Plus bank
            reconciliation that classifies every difference rather than listing it, and
            refuses to pass while an unrecorded bank item remains.
          </>
        ),
        tags: [{ name: "Controls", icon: "document" }],
        images: [],
      },
      {
        title: "Source-of-funds review",
        description: (
          <>
            Reading a personal bank statement against the story it is supposed to support:
            which deposits need a documented origin, which supporting records establish it,
            and where the paperwork does not yet back the balance. The same test used in KYC
            and client due diligence.
          </>
        ),
        tags: [{ name: "Due diligence", icon: "eye" }],
        images: [],
      },
    ],
  },
};

const blog: Blog = {
  path: "/blog",
  label: "Notes",
  title: "Notes on finance, data and Irish rules",
  description: `Occasional write-ups by ${person.name}`,
};

const work: Work = {
  path: "/work",
  label: "Work",
  title: `Projects – ${person.name}`,
  description: `Finance and analytics projects by ${person.name}`,
};

const gallery: Gallery = {
  path: "/gallery",
  label: "Gallery",
  title: `Charts – ${person.name}`,
  description: `Selected charts from ${person.name}'s projects`,
  images: [
    {
      src: "/images/projects/month-end-revenue-bridge.png",
      alt: "Revenue bridge splitting variance into volume, price and FX effects",
      orientation: "horizontal",
    },
    {
      src: "/images/projects/ar-forecast-backtest.png",
      alt: "Receivables cash forecast backtested against actual collections",
      orientation: "horizontal",
    },
    {
      src: "/images/projects/crisis-qlike-by-window.png",
      alt: "QLIKE forecast error by crisis window for LSTM, GARCH and HAR",
      orientation: "horizontal",
    },
    {
      src: "/images/projects/irish-marginal-rates.png",
      alt: "Irish marginal tax rate by salary showing the USC and PRSI cliffs",
      orientation: "horizontal",
    },
    {
      src: "/images/projects/ecb-curve-snapshots.png",
      alt: "Euro area AAA yield curve on four key dates",
      orientation: "horizontal",
    },
    {
      src: "/images/projects/crisis-shap-shares.png",
      alt: "SHAP attribution shares by crisis window",
      orientation: "horizontal",
    },
    {
      src: "/images/projects/cso-inflation-mortgages.png",
      alt: "Irish CPI inflation against new mortgage rates, 2003 to 2026",
      orientation: "horizontal",
    },
    {
      src: "/images/projects/saas-cohort-retention.png",
      alt: "SaaS cohort retention heatmap",
      orientation: "horizontal",
    },
  ],
};

export { person, social, newsletter, home, about, blog, work, gallery, tracks };
