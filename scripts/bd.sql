-- Créer la base de données (si elle n'existe pas)
SELECT 'CREATE DATABASE crypto_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'crypto_db')\gexec

-- Se connecter à la base
\c crypto_db;

-- Table principale des données crypto
CREATE TABLE IF NOT EXISTS crypto_temps_reel (
    id BIGSERIAL PRIMARY KEY,
    crypto_id VARCHAR(100) NOT NULL,
    rang INTEGER NOT NULL,
    symbole VARCHAR(20) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    supply_circulant DOUBLE PRECISION,
    supply_max DOUBLE PRECISION,
    market_cap_usd DOUBLE PRECISION,
    volume_24h_usd DOUBLE PRECISION,
    prix_usd DOUBLE PRECISION,
    variation_24h_pourcent DOUBLE PRECISION,
    vwap_24h DOUBLE PRECISION,
    timestamp_import VARCHAR(100),
    market_cap_milliards DOUBLE PRECISION,
    volume_24h_millions DOUBLE PRECISION,
    date_import DATE,
    heure_import VARCHAR(20),
    categorie VARCHAR(50),
    tendance VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table de logs du pipeline
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id BIGSERIAL PRIMARY KEY,
    operation VARCHAR(100),
    records_affected INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'success'
);

-- Table de monitoring
CREATE TABLE IF NOT EXISTS monitoring_stats (
    id BIGSERIAL PRIMARY KEY,
    check_timestamp TIMESTAMP,
    records_count INTEGER,
    anomalies_detected INTEGER,
    market_cap_total DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour les performances
CREATE INDEX IF NOT EXISTS idx_crypto_date ON crypto_temps_reel(date_import);
CREATE INDEX IF NOT EXISTS idx_crypto_rank ON crypto_temps_reel(rang);
CREATE INDEX IF NOT EXISTS idx_crypto_trend ON crypto_temps_reel(tendance);
CREATE INDEX IF NOT EXISTS idx_crypto_symbol ON crypto_temps_reel(symbole);

-- Vues pour les rapports
CREATE OR REPLACE VIEW crypto_dashboard AS
SELECT 
    rang,
    symbole,
    nom,
    prix_usd,
    variation_24h_pourcent,
    market_cap_milliards,
    volume_24h_millions,
    tendance,
    date_import,
    heure_import
FROM crypto_temps_reel 
WHERE date_import = CURRENT_DATE
ORDER BY rang;

CREATE OR REPLACE VIEW market_summary AS
SELECT 
    date_import,
    COUNT(*) as crypto_count,
    AVG(variation_24h_pourcent) as avg_variation,
    SUM(market_cap_usd) as total_market_cap,
    SUM(volume_24h_usd) as total_volume
FROM crypto_temps_reel 
GROUP BY date_import
ORDER BY date_import DESC;

-- Données de test (optionnel)
INSERT INTO pipeline_logs (operation, records_affected, status) 
VALUES ('database_setup', 0, 'success')
ON CONFLICT DO NOTHING;

-- Message de confirmation
SELECT '✅ Base de données crypto configurée avec succès' as status;