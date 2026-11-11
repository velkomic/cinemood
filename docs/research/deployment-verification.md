# Demonstration deployment: cost and HTTPS verification

Checked 2026-11-09. Proposal and documentation research only; no infrastructure, credentials, certificates or application deployment were created or tested. Supplements `aws-demo-hosting.md`.

## Proposed resource envelope

One on-demand, shared-tenancy **Linux x86 EC2 `t3.small` in Frankfurt (`eu-central-1`)**, running FastAPI, the small frontend, PostgreSQL/pgvector and a reverse proxy through Docker Compose. Use **20 GiB gp3**, baseline disk performance, and one Elastic IP retained throughout the agreed demonstration window, including stopped intervals. Target **20 total running hours** within a **seven-day window**; retain storage for at most one agreed month initially. S3 holds small raw ingestion snapshots and database backups; propose at most 1 GB retained initially. CloudWatch log ingestion is optional and excluded from the baseline. No RDS, ALB or NAT Gateway is proposed. This is a sizing hypothesis requiring a memory/latency check, not a capacity guarantee. AWS lists `t3.small` as 2 vCPUs, 2 GiB RAM and a 20% baseline per vCPU. [T3 specifications](https://aws.amazon.com/ec2/instance-types/t3/)

Explicitly configure CPU credits as **`standard`**: T3 normally launches in Unlimited mode, which can charge for surplus credits. Standard mode instead reduces CPU toward baseline when accrued credits run low. Build images before the demo where possible and verify startup performance under this limit. [Unlimited defaults and charges](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode.html), [Standard behavior](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-standard-mode.html)

## Price evidence and estimate limits

**Current Frankfurt compute and gp3 rates remain unverified.** A read-only attempt to retrieve the [official regional AWS price-list JSON](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-central-1/index.json) failed because shell DNS was unavailable; the web tool could not open that JSON. AWS's T3 page explicitly labels its displayed prices as US East, so those are not Frankfurt quotes. An [AWS Germany article](https://aws.amazon.com/de/blogs/germany/migrieren-sie-ihre-amazon-ebs-volumes-von-gp2-zu-gp3-und-sparen-sie-bis-zu-20-der-kosten/) quotes Frankfurt gp3 at USD 0.0952/GiB-month, but is historical evidence rather than a verified current tariff. Confirm the account's current regional quote using the [AWS Pricing Calculator](https://calculator.aws/) before provisioning.

| Item | Planning calculation, USD before tax |
| --- | ---: |
| Compute, **assumed allowance**, not an AWS quote | 20 h × 0.03 = 0.60 |
| Retained Elastic IP for seven days, **verified rate** | 168 h × 0.005 = 0.84 |
| gp3 storage, **assumed allowance**, retained one month | 20 GiB × 0.10 = 2.00 |
| Core illustrative subtotal | **3.44** |
| Small S3 storage/request/backup allowance, **assumed** | 0.30 |
| Illustrative AWS planning total | **3.74** |

AWS confirms USD 0.005/address-hour for both in-use and idle public IPv4 across commercial regions. gp3 baseline 3,000 IOPS and 125 MB/s are included; extra provisioned performance costs more. S3 charges include storage and requests, so the allowance needs checking against actual sizes and operations. [IPv4 pricing](https://aws.amazon.com/vpc/pricing/), [EBS pricing](https://aws.amazon.com/ebs/pricing/), [S3 pricing](https://aws.amazon.com/s3/pricing/)

These allowances are not caps or verified rates. The total excludes optional logs, snapshots, paid transfer beyond applicable allowances, taxes, currency conversion, domain registration/DNS, and OpenAI ingestion/experiments. **EUR 10 remains a provisional target for the whole project**, not EUR 10 reserved for AWS. No EUR conversion is asserted; check billing currency, exchange rate and applicable tax at approval time. Stopped EC2 retains billable EBS and S3 data; delete unneeded resources at the agreed retention deadline. [EC2 lifecycle and billing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html), [EBS pricing](https://aws.amazon.com/ebs/pricing/)

## HTTPS without purchasing a domain

Trusted public-IP certificates are supported. Use **Certbot 5.4+**, `certonly --preferred-profile shortlived --webroot --webroot-path <root> --ip-address <current-IP>`. Test with `--staging`, then remove that flag for a trusted certificate. Configure the reverse proxy to load the issued files; enable automatic renewal and a deploy hook to reload it. IP certificates use the short-lived profile, about six days; a stopped instance cannot renew, so startup must verify validity and issue/renew before serving HTTPS. [Official Certbot instructions](https://letsencrypt.org/2026/03/11/shorter-certs-certbot.html)

Serve the ACME challenge path publicly on **TCP port 80**, allow HTTPS on 443, and keep PostgreSQL private. HTTP-01 supports IP validation and requires port 80; webroot permits renewal while the proxy runs. Startup with a changed address requires a certificate for that new IP. [Let's Encrypt challenge requirements](https://letsencrypt.org/docs/challenge-types/)

## Collection continuity requires a stable host

**Propose retaining one Elastic IP through the demonstration window to preserve same-browser collection continuity across EC2 stop/start.** The earlier no-Elastic-IP option has a product conflict: EC2 normally assigns a new public IPv4 when restarted. Cookie host matching prevents sending the anonymous identifier to that new address; the collection can remain in PostgreSQL but appear absent to the visitor. This is an inference from EC2 addressing and the cookie standard, not an implementation test. [EC2 stop/start addressing](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html), [RFC 6265 host matching](https://www.rfc-editor.org/rfc/rfc6265#section-5.1.3)

Retain the EIP through the **entire demonstration window including stopped intervals**. A stable domain/subdomain updated to the current IP is an alternative if one is already available. A domain adds registration/DNS costs unless an existing subdomain is available. An EIP stays allocated until released: at the verified IPv4 rate, four days costs USD 0.48, five days USD 0.60, seven days USD 0.84, and a 30-day month USD 3.60. Each is additional to retained EBS costs. Releasing it loses continuity on a later demonstration. The retained EIP is a proposal, not an approved resource. [Elastic IP lifecycle](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html), [IPv4 rate](https://aws.amazon.com/vpc/pricing/)

Deployment acceptance still needs: a current regional estimate, acceptance of the proposed EIP retention window, explicit paid-resource approval, local sizing checks, and one verified AWS start → trusted HTTPS → saved collection → graceful stop/start → collection recovery flow. Restore a database backup once; verify EC2 reaches `stopped` after each demonstration and record the retention/deletion deadline. None of these operational checks has been completed.
