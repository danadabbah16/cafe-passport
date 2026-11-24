-- One row: the user's monthly budget goal (single-user app, see ADR-5)
CREATE TABLE budget_goal (
                             id           INT NOT NULL PRIMARY KEY CHECK (id = 1),
                             monthly_goal FLOAT NOT NULL CHECK (monthly_goal > 0),
                             updated_at   DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);