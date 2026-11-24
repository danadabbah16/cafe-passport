CREATE TABLE cafes (
                       id           INT IDENTITY(1,1) PRIMARY KEY,
                       name         NVARCHAR(200) NOT NULL UNIQUE,
                       neighborhood NVARCHAR(200) NULL,
                       city         NVARCHAR(200) NOT NULL,
                       created_at   DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
);

CREATE TABLE visits (
                        id         INT IDENTITY(1,1) PRIMARY KEY,
                        cafe_id    INT NOT NULL REFERENCES cafes(id),
                        visit_date NVARCHAR(10) NOT NULL,
                        drink      NVARCHAR(200) NOT NULL,
                        price      FLOAT NOT NULL CHECK (price >= 0),
                        rating     INT NOT NULL CHECK (rating BETWEEN 1 AND 10),
                        notes      NVARCHAR(1000) NULL
);