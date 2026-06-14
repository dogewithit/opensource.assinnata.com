/**
 * Tools catalogue, the single source of truth for the tool grid.
 *
 * Grounded in Matteo Assinnata's curriculum (Trading Infrastructure Engineer).
 * A tool links to a tested project under examples/ when one exists. Tools
 * without a tested example simply show no link.
 *
 * proficiency: 1 to 5 (1 = familiar, 3 = working knowledge, 5 = production owner)
 */

export const GITHUB_BASE =
  'https://github.com/dogewithit/opensource.assinnata.com';

export type Proficiency = 1 | 2 | 3 | 4 | 5;

export interface ExampleRef {
  /** repo relative path, e.g. examples/aws-localstack */
  path: string;
  /** short label for the link */
  label?: string;
}

export interface Tool {
  name: string;
  /** short note on how I actually use it */
  note: string;
  proficiency: Proficiency;
  /** optional homepage for the tool */
  url?: string;
  /** a tested code example in this repo */
  example?: ExampleRef;
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
 * Software Engineering, my flagship code examples.
 */
export const softwareCategories: Category[] = [
  {
    id: 'software-engineering',
    title: 'Software Engineering',
    blurb: 'Real code I have written. Every example here is tested before it ships.',
    tools: [
      {
        name: 'Hyperliquid Markets Crawler',
        note: 'I crawl the live Hyperliquid markets into Postgres. It keeps the latest state with idempotent upserts and a snapshot history that only ever grows. 18 tests, one of which hits the real API.',
        proficiency: 5,
        url: 'https://hyperliquid.gitbook.io/hyperliquid-docs',
        example: { path: 'examples/hyperliquid-crawler', label: 'Python and Postgres' },
      },
    ],
  },
];

/**
 * Infrastructure and Observability, the stack, with a tested example wherever
 * one exists.
 */
export const infraCategories: Category[] = [
  {
    id: 'cloud-compute',
    title: 'Cloud and Compute',
    blurb: 'Where trading systems run, and how they scale while the market is live.',
    tools: [
      {
        name: 'AWS',
        note: 'My main cloud across every role. Networking, IAM, and keeping the bill sane for trading infrastructure.',
        proficiency: 5,
        url: 'https://aws.amazon.com/',
        example: { path: 'examples/aws-localstack', label: 'S3 and DynamoDB on LocalStack' },
      },
      {
        name: 'Kubernetes',
        note: 'Runs the trading and venture builder workloads. I ran EKS in production while trades were live.',
        proficiency: 5,
        url: 'https://kubernetes.io/',
        example: { path: 'examples/kubernetes-minikube', label: 'deploy and scale on minikube' },
      },
      {
        name: 'Amazon EKS',
        note: 'I designed the EKS and Fargate setup across a whole venture builder portfolio.',
        proficiency: 4,
        url: 'https://aws.amazon.com/eks/',
        example: { path: 'examples/kubernetes-minikube', label: 'the Kubernetes layer on minikube' },
      },
      {
        name: 'AWS Fargate',
        note: 'Serverless containers. It took node management off my plate on the EKS platform.',
        proficiency: 4,
        url: 'https://aws.amazon.com/fargate/',
      },
    ],
  },
  {
    id: 'iac',
    title: 'Infrastructure as Code',
    blurb: 'Infrastructure I can reproduce and review. Nothing is held up by hand.',
    tools: [
      {
        name: 'Terraform',
        note: 'How I describe and version cloud infrastructure. I have used it to provision real production infra.',
        proficiency: 4,
        url: 'https://www.terraform.io/',
        example: { path: 'examples/terraform-localstack', label: 'tflocal, apply then assert' },
      },
    ],
  },
  {
    id: 'cicd',
    title: 'CI/CD and Automation',
    blurb: 'A solid lifecycle so changes ship safely and often.',
    tools: [
      {
        name: 'CI/CD Pipelines',
        note: 'I automate the whole path from commit to production. Here, GitHub Actions runs every example test suite on each push.',
        proficiency: 4,
        url: 'https://docs.github.com/actions',
        example: { path: '.github/workflows/ci.yml', label: 'GitHub Actions workflow' },
      },
      {
        name: 'Feature branch environments',
        note: 'A throwaway environment for every branch, so every change can be reviewed on its own.',
        proficiency: 4,
      },
    ],
  },
  {
    id: 'observability',
    title: 'Observability',
    blurb: 'Monitoring as code, because you cannot run what you cannot see.',
    tools: [
      {
        name: 'OpenTelemetry',
        note: 'Traces, metrics, and logs that are not tied to any vendor, instrumented across the services.',
        proficiency: 4,
        url: 'https://opentelemetry.io/',
        example: { path: 'examples/opentelemetry-tracing', label: 'spans via an in memory exporter' },
      },
      {
        name: 'Prometheus',
        note: 'Collects the metrics and drives the alerts for production trading systems.',
        proficiency: 4,
        url: 'https://prometheus.io/',
        example: { path: 'examples/prometheus-metrics', label: 'the exposition format' },
      },
      {
        name: 'Grafana',
        note: 'Dashboards for the health of the systems and the trading on top of them.',
        proficiency: 4,
        url: 'https://grafana.com/',
        example: { path: 'examples/grafana-prometheus-minikube', label: 'provisioned dashboards on minikube' },
      },
    ],
  },
  {
    id: 'finops',
    title: 'FinOps and Cost',
    blurb: 'Reliability and efficiency are the same discipline.',
    tools: [
      {
        name: 'AWS Budgets',
        note: 'Guardrails that keep cloud spend predictable.',
        proficiency: 3,
        url: 'https://aws.amazon.com/aws-cost-management/aws-budgets/',
      },
      {
        name: 'Cost Anomaly Detection',
        note: 'I used anomaly analysis to cut cloud cost across a portfolio of projects.',
        proficiency: 3,
        url: 'https://aws.amazon.com/aws-cost-management/aws-cost-anomaly-detection/',
      },
    ],
  },
];
