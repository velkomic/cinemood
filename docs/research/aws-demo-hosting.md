# AWS hosting for the demonstration MVP

Checked: 2026-11-09. Research and a proposal, not an accepted architecture or deployment verification. No infrastructure was provisioned.

## Recommendation

For the four-to-five-day MVP, propose one small Linux EC2 instance running Docker Compose: FastAPI, a lightweight UI, PostgreSQL with pgvector, and a reverse proxy. Keep PostgreSQL data on persistent EBS and its port private to Compose. Start with a 2 GiB RAM candidate, then verify memory and request latency locally before choosing the instance size. This sizing is an engineering assumption, not a capacity guarantee. pgvector provides a Docker image based on the PostgreSQL image. [pgvector installation](https://github.com/pgvector/pgvector#docker)

This keeps the demonstration's application and database under one start/stop procedure. It accepts a single point of failure and responsibility for database backups and host updates. RDS supports pgvector, but adds a second service and has a seven-day stopped-state limit; defer it unless managed database operation becomes a learning requirement. [RDS extension compatibility](https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-extensions.html)

## Verified billing and lifecycle facts

| Resource | While stopped or retained |
| --- | --- |
| Ordinary on-demand EC2 | Stopped instances incur no instance usage charge; attached EBS storage remains billable. Stopping containers alone does not stop EC2 billing. [EC2 billing FAQ](https://aws.amazon.com/ec2/faqs/) |
| EBS | Provisioned storage remains billed until deleted, even if detached. Snapshots have separate storage charges. [AWS EBS billing explanation](https://repost.aws/knowledge-center/ebs-charge-stopped-instance) |
| Public IPv4 / Elastic IP | Both in-use and idle public IPv4 addresses cost **USD 0.005/hour/address**. A retained Elastic IP therefore costs **USD 3.60 per 30-day month**. [VPC pricing](https://aws.amazon.com/vpc/pricing/) |
| EC2 auto-assigned public IPv4 | Stop/start normally changes the public address, so the next demonstration must discover and publish its current address. [EC2 stop/start](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html) |
| RDS PostgreSQL | Stops for at most seven consecutive days, then automatically starts. Storage and backup storage remain billed while stopped; a publicly accessible instance also retains a billable IPv4 address. This needs additional automation or deletion to satisfy long-term off-by-default operation. [RDS stop behavior](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_StopInstance.html) |

## Indicative short-use budget

The rendered AWS pricing pages did not expose a clearly verifiable EU instance/storage quote during this check. Do not treat the following allowances as AWS rates. Confirm the exact instance, Linux architecture, region, gp3 size and baseline performance in the [AWS Pricing Calculator](https://calculator.aws/) before requesting provisioning approval.

Planning example: **20 running hours**, one public IPv4 only while running, **20 GB gp3 retained for a full month**, an assumed compute allowance of **USD 0.03/hour**, and an assumed storage allowance of **USD 0.10/GB-month**:

| Item | Illustrative USD |
| --- | ---: |
| EC2 compute: 20 × 0.03 | 0.60 |
| Public IPv4: 20 × verified 0.005 | 0.10 |
| EBS: 20 × assumed 0.10 | 2.00 |
| Total before other usage and tax | **2.70** |
| Subsequent stopped month retaining only EBS | **2.00/month** |

AWS confirms gp3 storage is charged for provisioned GB and prorated by time; baseline 3,000 IOPS and 125 MB/s are included. Its published USD 0.08/GB-month example is explicitly for an unspecified region, so it is not an EU quotation. [EBS pricing](https://aws.amazon.com/ebs/pricing/)

The example excludes snapshots, extra disk performance, CPU surplus-credit charges where applicable, network transfer, logs, tax, currency conversion, and OpenAI ingestion/experiments. It assumes no RDS, NAT Gateway, ALB or other paid services. EUR 10 is the shared provisional target for the whole project’s initial use, not an AWS cap. Leave headroom for those other costs; verify the account's applicable rates rather than assuming credits or free-tier eligibility.

## HTTPS and shutdown proposal

A domain and ALB are avoidable: Let's Encrypt now offers publicly trusted IP-address certificates valid for 160 hours. Its documented Certbot path uses version 5.4+ with the short-lived profile; the reverse proxy must load the certificate and reload after renewal. For an auto-assigned EC2 address, obtain a certificate for the current IP on startup and handle expiry after time spent stopped. This is a candidate demo solution, not tested infrastructure. [Availability](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability), [Certbot instructions](https://letsencrypt.org/2026/03/11/shorter-certs-certbot.html)

Before provisioning, obtain explicit user approval for the concrete region, resources, estimate and retention period. After each demo, shut down gracefully and verify EC2 reaches `stopped`; do not retain an Elastic IP. Keep the disk only for the agreed retention period. At final teardown, export needed data and explicitly delete unneeded volumes and snapshots. Verify start, persistent data, HTTPS and stop once during the milestone; none of these deployment checks has been performed yet.
