/**
 * Tools catalogue — the single source of truth for the tool grid.
 *
 * Grounded in Matteo Assinnata's curriculum (Trading Infrastructure Engineer).
 * Every tool that ships an example links to a tested project under examples/.
 * Tools without a locally-testable example are marked `rejected` (see ROADMAP).
 *
 * proficiency: 1–5  (1 = familiar, 3 = working knowledge, 5 = deep / production-owner)
 */

export const GITHUB_BASE =
  'https://github.com/dogewithit/opensource.assinnata.com';

export type Proficiency = 1 | 2 | 3 | 4 | 5;

export interface ExampleRef {
  /** repo-relative path, e.g. examples/aws-localstack */
  path: string;
  /** short label for the link */
  label?: string;
}

export interface Tool {
  name: string;
  /** short, CV-grounded note on how it's actually used */
  note: string;
  proficiency: Proficiency;
  /** optional homepage for the tool */
  url?: string;
  /** a tested code example in this repo */
  example?: ExampleRef;
  /** set when there is no locally-tested example (honours tested-or-rejected) */
  rejected?: string;
}

export interface Category {
  id: string;
  title: string;
  blurb: string;
  tools: Tool[];
}

export const PROFICIENCY_LABELS: Record<Proficiency, string> = {
  1: 'Familiar',
  2: 'Practical',
  3: 'Proficient',
  4: 'Advanced',
  5: 'Production owner',
};

export function githubUrl(path: string): string {
  return `${GITHUB_BASE}/tree/main/${path}`;
}

/**
 * Software Engineering — flagship, fully-tested code examples.
 */
export const softwareCategories: Category[] = [
  {
    id: 'software-engineering',
    title: 'Software Engineering',
    blurb: 'Production-shaped code examples — each one tested before it ships.',
    tools: [
      {
        name: 'Hyperliquid Outcome-Markets Crawler',
        note: 'Crawls Hyperliquid outcome-market data into Postgres: idempotent latest-state upserts + append-only snapshot history. 14 tests.',
        proficiency: 5,
        url: 'https://hyperliquid.gitbook.io/hyperliquid-docs',
        example: { path: 'examples/hyperliquid-crawler', label: 'Python · Postgres' },
      },
    ],
  },
];

/**
 * Infrastructure & Observability — the stack, with tested examples where one
 * can be validated locally.
 */
export const infraCategories: Category[] = [
  {
    id: 'cloud-compute',
    title: 'Cloud & Compute',
    blurb: 'Where trading systems run, and how they scale under live load.',
    tools: [
      {
        name: 'AWS',
        note: 'Primary cloud across roles — networking, IAM, and cost optimization for trading infrastructure.',
        proficiency: 5,
        url: 'https://aws.amazon.com/',
        example: { path: 'examples/aws-localstack', label: 'S3 + DynamoDB · LocalStack' },
      },
      {
        name: 'Kubernetes',
        note: 'Orchestrates trading and venture-builder workloads; ran EKS in production under live trading.',
        proficiency: 5,
        url: 'https://kubernetes.io/',
        rejected: 'No reproducible local test on LocalStack community — needs a kind/real cluster.',
      },
      {
        name: 'Amazon EKS',
        note: 'Designed EKS Fargate infrastructure across an entire venture-builder portfolio.',
        proficiency: 4,
        url: 'https://aws.amazon.com/eks/',
        rejected: 'EKS is not faithfully reproducible on LocalStack community.',
      },
      {
        name: 'AWS Fargate',
        note: 'Serverless container compute — removed node management from the EKS platform.',
        proficiency: 4,
        url: 'https://aws.amazon.com/fargate/',
        rejected: 'No meaningful local test harness without a real cluster.',
      },
    ],
  },
  {
    id: 'iac',
    title: 'Infrastructure as Code',
    blurb: 'Reproducible, reviewable infrastructure — nothing held up by hand.',
    tools: [
      {
        name: 'Terraform',
        note: 'Infrastructure as code for cloud platforms; provisioned and versioned production infra.',
        proficiency: 4,
        url: 'https://www.terraform.io/',
        example: { path: 'examples/terraform-localstack', label: 'tflocal · apply + assert' },
      },
    ],
  },
  {
    id: 'cicd',
    title: 'CI/CD & Automation',
    blurb: 'A solid SDLC so changes ship safely and often.',
    tools: [
      {
        name: 'CI/CD Pipelines',
        note: 'Automated CI/CD with a solid SDLC; here, GitHub Actions runs every example test suite.',
        proficiency: 4,
        url: 'https://docs.github.com/actions',
        example: { path: '.github/workflows/ci.yml', label: 'GitHub Actions workflow' },
      },
      {
        name: 'Feature-branch Environments',
        note: 'Ephemeral per-branch environments so every change is reviewable in isolation.',
        proficiency: 4,
        rejected: 'An operational practice — demonstrated via CI, no standalone unit test.',
      },
    ],
  },
  {
    id: 'observability',
    title: 'Observability',
    blurb: '360° monitoring as code — you cannot run what you cannot see.',
    tools: [
      {
        name: 'OpenTelemetry',
        note: 'Vendor-neutral traces, metrics, and logs instrumented across services.',
        proficiency: 4,
        url: 'https://opentelemetry.io/',
        example: { path: 'examples/opentelemetry-tracing', label: 'spans · in-memory exporter' },
      },
      {
        name: 'Prometheus',
        note: 'Metrics collection and alerting for production trading systems.',
        proficiency: 4,
        url: 'https://prometheus.io/',
        example: { path: 'examples/prometheus-metrics', label: 'exposition format' },
      },
      {
        name: 'Grafana',
        note: 'Dashboards and visualization for live system and trading health.',
        proficiency: 4,
        url: 'https://grafana.com/',
        rejected: 'Dashboards are JSON config — no meaningful isolated unit test yet.',
      },
    ],
  },
  {
    id: 'finops',
    title: 'FinOps & Cost',
    blurb: 'Reliability and efficiency are the same discipline.',
    tools: [
      {
        name: 'AWS Budgets',
        note: 'Budgeting guardrails to keep cloud spend predictable.',
        proficiency: 3,
        url: 'https://aws.amazon.com/aws-cost-management/aws-budgets/',
        rejected: 'LocalStack Pro-only API — no community local test.',
      },
      {
        name: 'Cost Anomaly Detection',
        note: 'Cut cloud cost via anomaly analysis across a multi-project portfolio.',
        proficiency: 3,
        url: 'https://aws.amazon.com/aws-cost-management/aws-cost-anomaly-detection/',
        rejected: 'LocalStack Pro-only API — no community local test.',
      },
    ],
  },
];
