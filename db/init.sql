-- Idempotent: safe to run on every `docker compose up`.
-- One database per service, one login per service with access to its own database only.
-- Passwords come from sqlcmd variables, never from this file.

IF DB_ID('cafes') IS NULL CREATE DATABASE cafes;
GO
IF DB_ID('analytics') IS NULL CREATE DATABASE analytics;
GO

IF SUSER_ID('cafes_app') IS NULL CREATE LOGIN cafes_app WITH PASSWORD = '$(CAFES_DB_PASSWORD)';
GO
USE cafes;
IF USER_ID('cafes_app') IS NULL CREATE USER cafes_app FOR LOGIN cafes_app;
ALTER ROLE db_ddladmin ADD MEMBER cafes_app;
ALTER ROLE db_datareader ADD MEMBER cafes_app;
ALTER ROLE db_datawriter ADD MEMBER cafes_app;
GO

USE master;
IF SUSER_ID('analytics_app') IS NULL CREATE LOGIN analytics_app WITH PASSWORD = '$(ANALYTICS_DB_PASSWORD)';
GO
USE analytics;
IF USER_ID('analytics_app') IS NULL CREATE USER analytics_app FOR LOGIN analytics_app;
ALTER ROLE db_ddladmin ADD MEMBER analytics_app;
ALTER ROLE db_datareader ADD MEMBER analytics_app;
ALTER ROLE db_datawriter ADD MEMBER analytics_app;
GO