# Alias groups — interchangeable surface spellings

Data read by `scripts/aliases.py`, never by an agent. It ships with the plugin
because it is generic technology vocabulary and holds nothing about any
candidate. Extend it in your own job folder as `alias_groups.md`, in this same
format; the two merge at read time and a group sharing any member with a group
here extends that group rather than competing with it.

One group per bullet, members comma-separated. Members are interchangeable
spellings of **one** technology — never near-neighbours ("Postgres" and "MySQL"
are two groups, not one), because assembly will substitute freely inside a
group and a wrong member is a false claim.

A member carrying an uppercase letter matches case-sensitively, which is what
keeps `Go` from firing on "go live" and `ML` on "html". An all-lowercase member
matches case-insensitively. Short members are matched as whole tokens, so avoid
adding one that is a token inside a longer member you also use — `CI` inside
`CI/CD` would rewrite the longer spelling from the middle.

## Alias groups

- PostgreSQL, Postgres
- MySQL, My SQL
- Microsoft SQL Server, MSSQL, SQL Server
- Elasticsearch, Elastic Search
- Apache Kafka, Kafka
- RabbitMQ, Rabbit MQ
- Ruby on Rails, Rails, RoR
- JavaScript, JS
- TypeScript, TS
- Node.js, NodeJS
- React.js, ReactJS
- Vue.js, VueJS
- Golang, Go
- C#, C Sharp, CSharp
- .NET, dotnet
- Kubernetes, K8s
- Amazon Web Services, AWS
- Google Cloud Platform, GCP, Google Cloud
- Microsoft Azure, Azure
- Infrastructure as Code, IaC
- CI/CD, CICD
- Test-Driven Development, TDD
- Object-Oriented Programming, OOP
- Machine Learning, ML
- Site Reliability Engineering, SRE
- Software as a Service, SaaS
- REST, RESTful
- Single Sign-On, SSO
- Extract Transform Load, ETL
