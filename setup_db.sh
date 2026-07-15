#!/bin/bash
# Setup PostgreSQL database for EduBot
# Run with: sudo -u postgres bash setup_db.sh

set -e

echo "Setting up EduBot database..."

psql <<EOF
-- Create user if not exists
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'edu_user') THEN
    CREATE USER edu_user WITH PASSWORD 'edu_pass';
  END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE edu_chatbot OWNER edu_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'edu_chatbot')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE edu_chatbot TO edu_user;
EOF

echo "Database setup complete!"
