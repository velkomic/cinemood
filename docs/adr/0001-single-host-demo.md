# Run the demonstration on one EC2 host

For the four-to-five-day MVP, run FastAPI and PostgreSQL/pgvector together under Docker Compose on one EC2 instance, with S3 snapshots and database backups. This keeps the local and hosted environments similar and supports an application that is started only for demonstrations within a small budget; ECS, a load balancer, and RDS do not currently justify their additional setup and operational cost.

We accept responsibility for database backups, restoration, security updates, and host failure recovery. This choice limits availability and isolation, so revisit it if the project later requires continuous public service. Stopping EC2 does not eliminate retained-storage costs; paid provisioning still requires explicit approval.
