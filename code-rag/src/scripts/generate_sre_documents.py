"""
Script to generate synthetic SRE (Site Reliability Engineering) incident documents
and save them to a JSON file for ingestion into ChromaDB.

This script:
1. Generates 100 realistic SRE incident documents covering various categories
2. Adds appropriate metadata for each document
3. Saves them to a JSON file in the raw data directory
"""

import json
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add the parent directory to the path so we can import the code_rag package
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_rag.config import get_settings
from code_rag.utils.helpers import logger, setup_logger


# Define document types and their probabilities
DOCUMENT_TYPES = {
    "runbook": 0.4,
    "incident_report": 0.35,
    "architecture_doc": 0.1,
    "code_snippet": 0.1,
    "chat_log": 0.05,
}

# Define incident categories and their components
INCIDENT_CATEGORIES = {
    "pod_container_issues": {
        "errors": [
            "Pod {pod_name} stuck in CrashLoopBackOff state in namespace {namespace}",
            "Container {container_name} in pod {pod_name} terminated with OOMKilled error",
            "Pod {pod_name} in namespace {namespace} has ImagePullBackOff status",
            "Pod {pod_name} evicted due to node {node_name} being out of resources",
            "Multiple pods in {namespace} namespace showing high restart counts",
            "Container {container_name} in pod {pod_name} exceeded CPU limits consistently",
            "Init container failing in pod {pod_name} with exit code 1",
            "Pod {pod_name} stuck in ContainerCreating state for over 30 minutes",
            "Several pods in {namespace} showing RunContainerError",
            "Pod {pod_name} terminated unexpectedly with exit code 137"
        ],
        "contexts": [
            "during peak traffic hours",
            "after recent deployment",
            "following infrastructure maintenance",
            "after node auto-scaling event",
            "during database migration",
            "following security patch updates",
            "during canary deployment",
            "after config map update",
            "following network policy changes",
            "after cluster upgrade"
        ],
        "solutions": [
            "Increased memory limits in the deployment manifest from {old_value}Mi to {new_value}Mi and redeployed the application.",
            "Added readiness probe with appropriate timing values to prevent premature traffic routing.",
            "Fixed image tag in deployment spec from '{incorrect_tag}' to '{correct_tag}'.",
            "Added node anti-affinity rules to distribute pods across multiple nodes to prevent resource contention.",
            "Implemented horizontal pod autoscaling based on custom metrics to handle traffic spikes.",
            "Updated node selectors to ensure pods land on nodes with sufficient resources.",
            "Fixed misconfigured liveness probe that was causing unnecessary restarts.",
            "Corrected environment variable {env_var} that was incorrectly set to '{incorrect_value}' instead of '{correct_value}'.",
            "Updated init container script to handle permission issues correctly.",
            "Added resource requests to match resource limits to improve pod scheduling efficiency."
        ]
    },
    "networking_issues": {
        "errors": [
            "Intermittent connectivity issues between service {service_name} and {target_service} in namespace {namespace}",
            "DNS resolution failures for service {service_name} in namespace {namespace}",
            "Latency spikes of {latency_ms}ms observed in traffic to {service_name}",
            "Network timeouts when accessing external endpoint {endpoint_url}",
            "Ingress controller for {service_name} returning HTTP 503 errors intermittently",
            "Connection refused errors when pods try to reach {database_service}",
            "TLS handshake failures between {client_service} and {server_service}",
            "Network policy {policy_name} blocking essential traffic to {service_name}",
            "Load balancer for {service_name} reporting unhealthy backends",
            "CoreDNS pods showing high error rates and latency"
        ],
        "contexts": [
            "during high traffic periods",
            "after network policy update",
            "following DNS configuration change",
            "after ingress controller update",
            "during cross-region traffic",
            "after security group changes",
            "during service mesh deployment",
            "following CNI plugin update",
            "after adding new cluster nodes",
            "during multi-cluster operations"
        ],
        "solutions": [
            "Increased TCP keepalive settings to prevent connection termination during idle periods.",
            "Updated CoreDNS configuration to increase cache TTL from {old_ttl}s to {new_ttl}s.",
            "Applied network policy to allow traffic between {service_a} and {service_b} namespaces.",
            "Fixed misconfigured service selector that was causing traffic misdirection.",
            "Implemented connection pooling to reduce connection establishment overhead.",
            "Updated ingress timeout settings from {old_timeout}s to {new_timeout}s to accommodate longer processing times.",
            "Fixed TLS certificate mismatch by updating the secret with the correct certificate chain.",
            "Optimized MTU settings to prevent packet fragmentation issues.",
            "Implemented retry logic with exponential backoff for critical service communications.",
            "Added health checks to detect and route around problematic endpoints."
        ]
    },
    "deployment_failures": {
        "errors": [
            "Failed to deploy version {version} of {service_name} to {environment}",
            "Rollout of {service_name} stuck at {percent}% completion",
            "Canary deployment of {service_name} showing increased error rates compared to baseline",
            "Helm chart installation of {release_name} failed with timeout error",
            "Blue-green deployment switch failed for {service_name}",
            "Deployment {deployment_name} failed validation checks",
            "ConfigMap {config_map} referenced by deployment {deployment_name} not found",
            "Secret {secret_name} required by deployment {deployment_name} has incorrect format",
            "Post-deployment tests for {service_name} failed with {error_count} errors",
            "Deployment {deployment_name} created pods that failed readiness probes"
        ],
        "contexts": [
            "during scheduled release window",
            "during automated CI/CD pipeline run",
            "during manual hotfix deployment",
            "as part of major version upgrade",
            "during rollback operation",
            "following configuration change",
            "during infrastructure migration",
            "as part of A/B testing deployment",
            "during multi-service coordinated release",
            "following security patch implementation"
        ],
        "solutions": [
            "Fixed invalid YAML indentation in deployment manifest that was causing parsing errors.",
            "Updated resource requirements to be within cluster quota limits.",
            "Corrected image pull secret reference to use namespace-specific secret.",
            "Implemented progressive rollout strategy with 10% increments instead of 50% to reduce impact.",
            "Added pre-deployment validation step to check for config map existence and format.",
            "Updated health check endpoints to use /health/ready instead of deprecated /status path.",
            "Fixed dependency order in Helm chart to ensure database migrations run before application pods.",
            "Implemented post-deployment smoke tests to validate critical user paths.",
            "Added missing service account permissions required by the application.",
            "Updated container command arguments to properly reference mounted config files."
        ]
    },
    "resource_constraints": {
        "errors": [
            "Node {node_name} CPU usage at {cpu_percent}%, causing throttling of multiple pods",
            "Cluster exceeded {resource_type} quota in namespace {namespace}",
            "Pod {pod_name} terminated due to memory pressure on node {node_name}",
            "Horizontal Pod Autoscaler unable to scale {deployment_name} due to reaching maximum replica count",
            "Persistent volumes in namespace {namespace} approaching capacity at {used_percent}%",
            "Node {node_name} reporting disk pressure with {free_space}GB remaining",
            "ETCd database size grown to {size_gb}GB causing performance degradation",
            "API server showing high latency due to excessive requests from {client_name}",
            "Prometheus storage utilization at {used_percent}%, retention period reduced automatically",
            "Connection pool for {database_name} exhausted with {connection_count} active connections"
        ],
        "contexts": [
            "during month-end processing",
            "following data import job",
            "during unexpected traffic spike",
            "after adding new application features",
            "during backup operation",
            "following log level change to DEBUG",
            "during overlapping cron jobs",
            "after enabling detailed metrics collection",
            "during heavy reporting workload",
            "following inadequate cleanup of temporary resources"
        ],
        "solutions": [
            "Implemented vertical pod autoscaling to automatically adjust resource requests based on actual usage.",
            "Increased cluster capacity by adding {node_count} nodes to handle peak workload.",
            "Optimized query patterns to reduce database CPU usage by {percent_reduction}%.",
            "Implemented connection pooling to limit maximum concurrent database connections.",
            "Added memory limits to prevent single pod from consuming excessive resources.",
            "Configured pod disruption budget to ensure critical services maintain minimum availability.",
            "Implemented rate limiting on API to prevent client from overwhelming the service.",
            "Added pod anti-affinity rules to distribute resource-intensive workloads across nodes.",
            "Scheduled batch processing jobs to run during off-peak hours.",
            "Implemented efficient caching layer to reduce computational load by {percent_reduction}%."
        ]
    },
    "api_errors": {
        "errors": [
            "Service {service_name} reporting {error_count} HTTP 500 errors per minute",
            "API endpoint {endpoint_path} returning unexpected HTTP 503 responses",
            "Timeout errors when calling {external_api} with threshold set to {timeout_seconds}s",
            "Rate limiting triggered on {api_name} API, rejecting {reject_percent}% of requests",
            "Webhook {webhook_name} failing with connection refused errors",
            "Circuit breaker open for {service_name} after {failure_count} consecutive failures",
            "API authentication failures spiked to {error_rate} per minute for service {service_name}",
            "Invalid response format from {service_name} breaking downstream consumer {consumer_name}",
            "API gateway reporting increased latency of {latency_ms}ms for path {endpoint_path}",
            "Version mismatch in API call from {client_version} client to {server_version} server"
        ],
        "contexts": [
            "after API version update",
            "during high load period",
            "following authentication service change",
            "during multiple concurrent client requests",
            "after schema change",
            "following gateway configuration update",
            "during failover testing",
            "after client library update",
            "following certificate rotation",
            "during distributed tracing implementation"
        ],
        "solutions": [
            "Implemented retry mechanism with exponential backoff for transient network errors.",
            "Added circuit breaker pattern to fail fast when downstream service is unavailable.",
            "Updated API rate limits from {old_limit} to {new_limit} requests per minute based on usage patterns.",
            "Fixed serialization issue in API response by updating content type header.",
            "Implemented request validation middleware to catch invalid inputs before reaching service logic.",
            "Added comprehensive error handling with detailed error codes and messages.",
            "Updated timeout configuration from {old_timeout}s to {new_timeout}s based on p99 latency metrics.",
            "Implemented API versioning to maintain backward compatibility.",
            "Added correlation IDs to all requests for improved traceability across services.",
            "Updated client authentication to use JWT tokens instead of legacy API keys."
        ]
    },
    "database_issues": {
        "errors": [
            "Database {database_name} connection pool exhausted with {max_connections} active connections",
            "Replication lag on {database_name} read replica increased to {lag_seconds} seconds",
            "Database query timeout after {timeout_seconds}s for service {service_name}",
            "Deadlock detected in {database_name} affecting transactions from {service_name}",
            "Database {database_name} disk usage at {used_percent}% causing write performance degradation",
            "Increased error rate of {error_rate}% for database operations from service {service_name}",
            "Schema migration failed for {database_name} during deployment of version {version}",
            "Connection failures to {database_name} reported by multiple services",
            "Cache hit ratio for {database_name} dropped to {hit_ratio}%, causing increased database load",
            "Database {database_name} CPU utilization peaked at {cpu_percent}% causing query performance issues"
        ],
        "contexts": [
            "during peak transaction period",
            "following schema update",
            "after adding new indexes",
            "during data archiving process",
            "following configuration change",
            "during backup operation",
            "after query pattern change",
            "following application release",
            "during data import job",
            "after database instance resize"
        ],
        "solutions": [
            "Optimized slow-performing query by adding index on {column_name}, reducing execution time from {old_time}ms to {new_time}ms.",
            "Implemented connection pooling with appropriate sizing based on workload characteristics.",
            "Added read replicas to distribute read queries and reduce primary database load.",
            "Updated database configuration to increase {parameter_name} from {old_value} to {new_value}.",
            "Implemented query timeout handling to prevent long-running queries from affecting other operations.",
            "Refactored application to use batch operations instead of individual queries for bulk operations.",
            "Added database monitoring with alerting for critical metrics like connection count, query time, and error rate.",
            "Implemented data partitioning strategy to improve query performance and maintenance operations.",
            "Updated database instance size from {old_size} to {new_size} to accommodate increased workload.",
            "Added circuit breaker pattern to prevent cascading failures when database experiences issues."
        ]
    }
}

# Generate fake service and component names
SERVICE_NAMES = [
    "user-service", "order-processor", "payment-gateway", "notification-service",
    "product-catalog", "recommendation-engine", "analytics-service", "authentication-service",
    "inventory-manager", "shipping-service", "cart-service", "search-service",
    "billing-service", "reporting-service", "api-gateway", "configuration-service",
    "logging-service", "monitoring-service", "cache-service", "messaging-service"
]

DATABASE_NAMES = [
    "users-db", "orders-db", "products-db", "payments-db", "analytics-db",
    "auth-db", "metrics-db", "logs-db", "inventory-db", "catalog-db"
]

NAMESPACES = [
    "production", "staging", "development", "testing", "demo", 
    "system", "monitoring", "data", "integration", "api"
]

NODE_NAMES = [
    "worker-node-1", "worker-node-2", "worker-node-3", "worker-node-4",
    "master-node-1", "master-node-2", "master-node-3",
    "infra-node-1", "infra-node-2", "data-node-1", "data-node-2"
]

CONTAINER_NAMES = [
    "app", "sidecar", "init", "proxy", "cache", "worker", "cron", 
    "metrics", "logger", "backup", "sync", "api", "frontend", "backend"
]

# Helper function to generate a random date within the last year
def random_date(days_back=365):
    today = datetime.now()
    days = random.randint(1, days_back)
    random_date = today - timedelta(days=days)
    return random_date.strftime("%Y-%m-%d %H:%M:%S")

# Helper function to generate random duration in minutes
def random_duration():
    return random.randint(5, 240)

def generate_random_string_value(options, path=""):
    if isinstance(options, list):
        value = random.choice(options)
    else:
        value = str(options)
        
    if "{" in value and "}" in value:
        # Replace placeholders with random values
        if "{service_name}" in value:
            value = value.replace("{service_name}", random.choice(SERVICE_NAMES))
        if "{target_service}" in value:
            value = value.replace("{target_service}", random.choice(SERVICE_NAMES))
        if "{client_service}" in value:
            value = value.replace("{client_service}", random.choice(SERVICE_NAMES))
        if "{server_service}" in value:
            value = value.replace("{server_service}", random.choice(SERVICE_NAMES))
        if "{service_a}" in value:
            value = value.replace("{service_a}", random.choice(SERVICE_NAMES))
        if "{service_b}" in value:
            value = value.replace("{service_b}", random.choice(SERVICE_NAMES))
        if "{database_service}" in value:
            value = value.replace("{database_service}", random.choice(DATABASE_NAMES))
        if "{database_name}" in value:
            value = value.replace("{database_name}", random.choice(DATABASE_NAMES))
        if "{namespace}" in value:
            value = value.replace("{namespace}", random.choice(NAMESPACES))
        if "{pod_name}" in value:
            service = random.choice(SERVICE_NAMES)
            pod_id = random.randint(1000, 9999)
            value = value.replace("{pod_name}", f"{service}-{pod_id}")
        if "{node_name}" in value:
            value = value.replace("{node_name}", random.choice(NODE_NAMES))
        if "{container_name}" in value:
            value = value.replace("{container_name}", random.choice(CONTAINER_NAMES))
        if "{deployment_name}" in value:
            value = value.replace("{deployment_name}", random.choice(SERVICE_NAMES))
        if "{consumer_name}" in value:
            value = value.replace("{consumer_name}", random.choice(SERVICE_NAMES))
        if "{client_name}" in value:
            value = value.replace("{client_name}", random.choice(SERVICE_NAMES))
        if "{release_name}" in value:
            value = value.replace("{release_name}", random.choice(SERVICE_NAMES))
        if "{config_map}" in value:
            service = random.choice(SERVICE_NAMES)
            value = value.replace("{config_map}", f"{service}-config")
        if "{secret_name}" in value:
            service = random.choice(SERVICE_NAMES)
            value = value.replace("{secret_name}", f"{service}-secret")
        if "{endpoint_path}" in value:
            service = random.choice(SERVICE_NAMES)
            paths = ["/api/v1/users", "/api/v2/orders", "/health", "/metrics", "/status", "/data"]
            value = value.replace("{endpoint_path}", f"{service}{random.choice(paths)}")
        if "{api_name}" in value:
            value = value.replace("{api_name}", random.choice(SERVICE_NAMES))
        if "{webhook_name}" in value:
            service = random.choice(SERVICE_NAMES)
            value = value.replace("{webhook_name}", f"{service}-webhook")
        if "{external_api}" in value:
            apis = ["payment-processor", "shipping-api", "tax-calculator", "auth-provider", "analytics-api"]
            value = value.replace("{external_api}", random.choice(apis))
        if "{endpoint_url}" in value:
            urls = ["https://api.example.com/v1", "https://partner-api.example.org/data", 
                   "https://auth.example.net/oauth", "https://metrics.example.io/collect"]
            value = value.replace("{endpoint_url}", random.choice(urls))
        if "{policy_name}" in value:
            policies = ["default-deny", "allow-monitoring", "restrict-egress", "database-access"]
            value = value.replace("{policy_name}", random.choice(policies))
        if "{environment}" in value:
            envs = ["production", "staging", "testing", "development"]
            value = value.replace("{environment}", random.choice(envs))
        if "{version}" in value:
            value = value.replace("{version}", f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}")
        if "{old_value}" in value:
            old = random.randint(100, 500)
            value = value.replace("{old_value}", str(old))
        if "{new_value}" in value:
            new = random.randint(500, 1000)
            value = value.replace("{new_value}", str(new))
        if "{percent}" in value:
            value = value.replace("{percent}", str(random.randint(10, 95)))
        if "{error_count}" in value:
            value = value.replace("{error_count}", str(random.randint(10, 1000)))
        if "{latency_ms}" in value:
            value = value.replace("{latency_ms}", str(random.randint(100, 5000)))
        if "{timeout_seconds}" in value:
            value = value.replace("{timeout_seconds}", str(random.randint(5, 60)))
        if "{reject_percent}" in value:
            value = value.replace("{reject_percent}", str(random.randint(10, 90)))
        if "{failure_count}" in value:
            value = value.replace("{failure_count}", str(random.randint(3, 20)))
        if "{error_rate}" in value:
            value = value.replace("{error_rate}", str(random.randint(5, 50)))
        if "{cpu_percent}" in value:
            value = value.replace("{cpu_percent}", str(random.randint(80, 99)))
        if "{used_percent}" in value:
            value = value.replace("{used_percent}", str(random.randint(80, 95)))
        if "{free_space}" in value:
            value = value.replace("{free_space}", str(random.randint(1, 10)))
        if "{size_gb}" in value:
            value = value.replace("{size_gb}", str(random.randint(5, 30)))
        if "{connection_count}" in value:
            value = value.replace("{connection_count}", str(random.randint(100, 500)))
        if "{old_ttl}" in value:
            old_ttl = random.randint(10, 30)
            value = value.replace("{old_ttl}", str(old_ttl))
        if "{new_ttl}" in value:
            new_ttl = random.randint(30, 120)
            value = value.replace("{new_ttl}", str(new_ttl))
        if "{old_timeout}" in value:
            old_timeout = random.randint(5, 15)
            value = value.replace("{old_timeout}", str(old_timeout))
        if "{new_timeout}" in value:
            new_timeout = random.randint(15, 60)
            value = value.replace("{new_timeout}", str(new_timeout))
        if "{client_version}" in value:
            value = value.replace("{client_version}", f"v{random.randint(1, 3)}")
        if "{server_version}" in value:
            value = value.replace("{server_version}", f"v{random.randint(2, 4)}")
        if "{incorrect_tag}" in value:
            value = value.replace("{incorrect_tag}", f"v{random.randint(1, 5)}.{random.randint(0, 9)}")
        if "{correct_tag}" in value:
            value = value.replace("{correct_tag}", f"v{random.randint(1, 5)}.{random.randint(0, 9)}")
        if "{env_var}" in value:
            env_vars = ["DATABASE_URL", "API_KEY", "LOG_LEVEL", "CACHE_TTL", "MAX_CONNECTIONS"]
            value = value.replace("{env_var}", random.choice(env_vars))
        if "{incorrect_value}" in value:
            incorrect = ["localhost:5432", "DEBUG", "false", "http://old-service", ""]
            value = value.replace("{incorrect_value}", random.choice(incorrect))
        if "{correct_value}" in value:
            correct = ["db.example.com:5432", "INFO", "true", "https://new-service", "60s"]
            value = value.replace("{correct_value}", random.choice(correct))
        if "{old_limit}" in value:
            old_limit = random.randint(50, 200)
            value = value.replace("{old_limit}", str(old_limit))
        if "{new_limit}" in value:
            new_limit = random.randint(200, 500)
            value = value.replace("{new_limit}", str(new_limit))
        if "{node_count}" in value:
            value = value.replace("{node_count}", str(random.randint(2, 5)))
        if "{percent_reduction}" in value:
            value = value.replace("{percent_reduction}", str(random.randint(20, 60)))
        if "{max_connections}" in value:
            value = value.replace("{max_connections}", str(random.randint(50, 200)))
        if "{lag_seconds}" in value:
            value = value.replace("{lag_seconds}", str(random.randint(30, 300)))
        if "{hit_ratio}" in value:
            value = value.replace("{hit_ratio}", str(random.randint(40, 70)))
        if "{column_name}" in value:
            columns = ["user_id", "timestamp", "status", "order_id", "transaction_id"]
            value = value.replace("{column_name}", random.choice(columns))
        if "{old_time}" in value:
            old_time = random.randint(500, 2000)
            value = value.replace("{old_time}", str(old_time))
        if "{new_time}" in value:
            new_time = random.randint(50, 200)
            value = value.replace("{new_time}", str(new_time))
        if "{parameter_name}" in value:
            parameters = ["max_connections", "shared_buffers", "work_mem", "effective_cache_size"]
            value = value.replace("{parameter_name}", random.choice(parameters))
        if "{old_size}" in value:
            sizes = ["t2.small", "m5.large", "r5.xlarge"]
            value = value.replace("{old_size}", random.choice(sizes))
        if "{new_size}" in value:
            sizes = ["m5.xlarge", "r5.2xlarge", "c5.2xlarge"]
            value = value.replace("{new_size}", random.choice(sizes))
            
    return value

def generate_sre_incident() -> Dict[str, Any]:
    """Generate a single SRE incident document with error and solution"""
    
    # Select document type based on probabilities
    doc_type = random.choices(
        list(DOCUMENT_TYPES.keys()),
        weights=list(DOCUMENT_TYPES.values()),
        k=1
    )[0]
    
    # Select incident category
    category = random.choice(list(INCIDENT_CATEGORIES.keys()))
    category_data = INCIDENT_CATEGORIES[category]
    
    # Generate error message and context
    error_template = generate_random_string_value(category_data["errors"])
    context = generate_random_string_value(category_data["contexts"])
    full_error = f"{error_template} {context}"
    
    # Generate solution
    solution = generate_random_string_value(category_data["solutions"])
    
    # Generate metadata
    incident_date = random_date()
    resolution_date = datetime.strptime(incident_date, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=random_duration())
    
    # Generate a structured document
    incident = {
        "error": full_error,
        "solution": solution,
        "metadata": {
            "incident_id": f"INC-{random.randint(10000, 99999)}",
            "severity": random.choice(["P1", "P2", "P3", "P4"]),
            "category": category.replace("_", " ").title(),
            "incident_date": incident_date,
            "resolution_date": resolution_date.strftime("%Y-%m-%d %H:%M:%S"),
            "resolution_time_minutes": random_duration(),
            "document_type": doc_type,
            "affected_services": [random.choice(SERVICE_NAMES) for _ in range(random.randint(1, 3))],
            "tags": [category] + [random.choice(["kubernetes", "cloud", "networking", "database", "microservices", "monitoring", "security", "performance"]) for _ in range(random.randint(1, 3))]
        }
    }
    
    return incident

def generate_sre_documents(count: int = 100) -> List[Dict[str, Any]]:
    """Generate multiple SRE incident documents"""
    
    logger.info(f"Generating {count} synthetic SRE incident documents...")
    documents = []
    
    for _ in range(count):
        incident = generate_sre_incident()
        documents.append(incident)
    
    logger.info(f"Successfully generated {len(documents)} SRE incident documents")
    return documents

def save_documents_to_json(documents: List[Dict[str, Any]], output_path: str) -> None:
    """Save the generated documents to a JSON file"""
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(documents, f, indent=2)
    
    logger.info(f"Saved {len(documents)} documents to {output_path}")

def main():
    """Main entry point for the script"""
    
    # Configure logging
    logger = setup_logger()
    
    # Get settings
    settings = get_settings()
    
    logger.info("Starting SRE document generation process")
    
    # Generate documents
    documents = generate_sre_documents(count=100)
    
    # Save to JSON file
    output_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/sre_incidents.json")))
    save_documents_to_json(documents, output_path)
    
    logger.info(f"Document generation complete. File saved to {output_path}")

if __name__ == "__main__":
    main()