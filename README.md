# Café Passport

A personal café visit log with a ranking engine, split into two services along the
seam from Assignment 1 (ADR-2, ADR-6):

| Service | Folder | Owns | Database |
|---|---|---|---|
| cafes | `services/cafes` | cafés and visits | its own SQL Server database |
| analytics | `services/analytics` | rankings, stats, monthly budget | its own SQL Server database |

The UI (`ui/`) is a static site that calls both services from the browser. Analytics
reads visit data from cafes over HTTP (`GET /visits`, `GET /cafes`) with a 2 s timeout;
if cafes is down, analytics answers 503 with a clear error and the UI shows it.

**Live URL:** https://daqdabbahieu2024ui.z28.web.core.windows.net

## Run locally (one command)

1. Copy `.env.example` to `.env` and fill in three local passwords (no `$`, `'` or `"`).
2. Start everything:

       docker compose up --build

3. Open http://localhost:8080 (UI). Services: cafes on 8001, analytics on 8002.

Compose starts SQL Server, runs `db/init.sql` (one database and one login per service,
idempotent), then both services, which apply their migrations on startup.

## Run a single service

    docker compose up -d db db-init
    docker compose up --build cafes        # or: analytics

## Tests and coverage

Tests run against a throwaway database on the compose SQL Server:

    docker compose up -d db
    $env:TEST_ADMIN_URL = "mssql://sa:<sa password from .env>@localhost:1433/master"   # PowerShell
    cd services/cafes        # or services/analytics
    python -m pip install -r requirements.txt
    python -m pytest --cov

CI runs the same tests per service against a SQL Server container, plus lint (ruff),
a 70% coverage gate, and validation of `system.yaml` and both OpenAPI documents.

## How deployment works

- `.github/workflows/ci.yml` runs on every push and pull request: lint, tests with
  coverage, validation, and a Docker build per service.
- `.github/workflows/cd.yml` runs on every push to `main`: it calls CI, pushes each image
  to GHCR tagged with the commit SHA, signs in to Azure through OIDC as the managed
  identity `daqdabbah-ieu2024-github`, updates both Container Apps (connection string as
  a Container Apps secret), writes `ui/config.js` with the services' URLs, uploads `ui/`
  to the `$web` container, and fails unless both `/health` endpoints return 200.
- Nothing is changed in Azure by hand after the initial setup below.

## Initial Azure setup (done once, in Azure Cloud Shell, Bash)

Passwords are entered with `read -s` and never written down. Prefix: `daqdabbah-ieu2024`,
region `francecentral`.

```bash
az account set --subscription "Azure for Students"
PREFIX=daqdabbah-ieu2024; RG=rg-$PREFIX; LOCATION=francecentral
UI_STORAGE=daqdabbahieu2024ui; SQL_SERVER=$PREFIX-sql; SQL_ADMIN=cpadmin

# Providers and resource group
for p in Microsoft.App Microsoft.OperationalInsights Microsoft.Sql Microsoft.Storage Microsoft.ManagedIdentity; do az provider register --namespace $p; done
az group create --name $RG --location $LOCATION

# UI: storage static website
az storage account create --name $UI_STORAGE --resource-group $RG --location $LOCATION --sku Standard_LRS --kind StorageV2
az storage blob service-properties update --account-name $UI_STORAGE --static-website --index-document index.html

# SQL server and two serverless databases (free offer)
read -s -p "SQL admin password: " SQL_ADMIN_PASSWORD; echo
az sql server create --name $SQL_SERVER --resource-group $RG --location $LOCATION --admin-user $SQL_ADMIN --admin-password "$SQL_ADMIN_PASSWORD"
az sql server firewall-rule create --resource-group $RG --server $SQL_SERVER --name AllowAzureServices --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
for db in cafes analytics; do
  az sql db create --resource-group $RG --server $SQL_SERVER --name $PREFIX-$db-db --edition GeneralPurpose --compute-model Serverless --family Gen5 --capacity 1 --min-capacity 0.5 --backup-storage-redundancy Local --use-free-limit true --free-limit-exhaustion-behavior AutoPause
done

# One contained user per database (firewall opened to Cloud Shell only for this, then closed)
MY_IP=$(curl -s ifconfig.me)
az sql server firewall-rule create --resource-group $RG --server $SQL_SERVER --name TempSetup --start-ip-address $MY_IP --end-ip-address $MY_IP
read -s -p "cafes user password: " CAFES_DB_PASSWORD; echo
read -s -p "analytics user password: " ANALYTICS_DB_PASSWORD; echo
~/sqlcmd -S $SQL_SERVER.database.windows.net -d $PREFIX-cafes-db -U $SQL_ADMIN -P "$SQL_ADMIN_PASSWORD" -Q "CREATE USER cafes_app WITH PASSWORD = '<secret>'; ALTER ROLE db_ddladmin ADD MEMBER cafes_app; ALTER ROLE db_datareader ADD MEMBER cafes_app; ALTER ROLE db_datawriter ADD MEMBER cafes_app;"
~/sqlcmd -S $SQL_SERVER.database.windows.net -d $PREFIX-analytics-db -U $SQL_ADMIN -P "$SQL_ADMIN_PASSWORD" -Q "CREATE USER analytics_app WITH PASSWORD = '<secret>'; ALTER ROLE db_ddladmin ADD MEMBER analytics_app; ALTER ROLE db_datareader ADD MEMBER analytics_app; ALTER ROLE db_datawriter ADD MEMBER analytics_app;"
az sql server firewall-rule delete --resource-group $RG --server $SQL_SERVER --name TempSetup

# Container Apps (placeholder image; the first CD run replaces it)
UI_URL=https://daqdabbahieu2024ui.z28.web.core.windows.net
az containerapp env create --name $PREFIX-env --resource-group $RG --location $LOCATION
az containerapp create --name $PREFIX-cafes --resource-group $RG --environment $PREFIX-env --image mcr.microsoft.com/k8se/quickstart:latest --target-port 8000 --ingress external --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi --env-vars UI_ORIGIN=$UI_URL
CAFES_FQDN=$(az containerapp show --name $PREFIX-cafes --resource-group $RG --query properties.configuration.ingress.fqdn -o tsv)
az containerapp create --name $PREFIX-analytics --resource-group $RG --environment $PREFIX-env --image mcr.microsoft.com/k8se/quickstart:latest --target-port 8000 --ingress external --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi --env-vars UI_ORIGIN=$UI_URL CAFES_URL=https://$CAFES_FQDN CAFES_TIMEOUT_S=2

# Pipeline identity (OIDC), Contributor on the resource group only
RG_ID=$(az group show --name $RG --query id -o tsv)
az identity create --name $PREFIX-github --resource-group $RG --location $LOCATION
PRINCIPAL_ID=$(az identity show --name $PREFIX-github --resource-group $RG --query principalId -o tsv)
az role assignment create --assignee-object-id $PRINCIPAL_ID --assignee-principal-type ServicePrincipal --role Contributor --scope $RG_ID
az identity federated-credential create --name github-main --identity-name $PREFIX-github --resource-group $RG --issuer https://token.actions.githubusercontent.com --subject "repo:danadabbah16/cafe-passport:ref:refs/heads/main" --audiences api://AzureADTokenExchange
az identity federated-credential create --name github-main-ids --identity-name $PREFIX-github --resource-group $RG --issuer https://token.actions.githubusercontent.com --subject "repo:danadabbah16@232573881/cafe-passport@1410811212:ref:refs/heads/main" --audiences api://AzureADTokenExchange

# Read access for the professors
az role assignment create --assignee amartini@faculty.ie.edu --role Reader --scope $RG_ID
az role assignment create --assignee bserra@faculty.ie.edu --role Reader --scope $RG_ID
```

**GitHub configuration** (Settings → Secrets and variables → Actions):
secrets `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `CAFES_DB_PASSWORD`,
`ANALYTICS_DB_PASSWORD`, `CI_SA_PASSWORD`; variables `PREFIX`, `RESOURCE_GROUP`, `UI_STORAGE`.

## Security incident log

- **2026-11-24: local SQL Server sa password committed.** From 2026-11-10 the `sa`
  password of the local development SQL Server container was written in
  `docker-compose.yml`. It was only ever used by a throwaway container on a developer
  laptop, never in Azure or any shared system. Action: the password was rotated and all
  passwords moved to a gitignored `.env` (template in `.env.example`). The old value
  remains in Git history but no longer grants access to anything.