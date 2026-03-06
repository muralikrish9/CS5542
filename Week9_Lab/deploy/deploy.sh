#!/bin/bash
# CS 5542 — Week 9 Lab: Deployment Script
set -euo pipefail

echo "=== CyberAgent Deployment ==="
echo "Building Docker image..."
docker-compose -f deploy/docker-compose.yml build

echo "Starting services..."
docker-compose -f deploy/docker-compose.yml up -d

echo ""
echo "=== Deployment Complete ==="
echo "Dashboard: http://localhost:8501"
echo "Logs: docker-compose -f deploy/docker-compose.yml logs -f"
echo "Stop: docker-compose -f deploy/docker-compose.yml down"
