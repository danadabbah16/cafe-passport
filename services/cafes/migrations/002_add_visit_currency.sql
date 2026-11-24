-- Adds a currency to every visit. Existing rows are kept and backfilled with
-- 'EUR' by the default constraint; nothing is dropped or recreated.
ALTER TABLE visits
    ADD currency NCHAR(3) NOT NULL
    CONSTRAINT df_visits_currency DEFAULT 'EUR';