from azure.cosmos import CosmosClient, PartitionKey, exceptions
from app.core.config import settings
from typing import Optional

# Global Cosmos client instance
_cosmos_client: Optional[CosmosClient] = None


def get_cosmos_client() -> CosmosClient:
    """Get or initialize the Cosmos DB client."""
    global _cosmos_client

    if _cosmos_client is None:
        _cosmos_client = CosmosClient(
            url=settings.cosmos_endpoint,
            credential=settings.cosmos_key
        )

    return _cosmos_client


def get_audit_container():
    """
    Get or create the audit log container in Cosmos DB.
    Creates the database and container if they don't exist.
    """
    client = get_cosmos_client()

    try:
        # Try to get existing database
        database = client.get_database_client(settings.cosmos_database)
    except exceptions.CosmosResourceNotFoundError:
        # Create database if it doesn't exist
        database = client.create_database(settings.cosmos_database)

    try:
        # Try to get existing container
        container = database.get_container_client("audit_logs")
    except exceptions.CosmosResourceNotFoundError:
        # Create container if it doesn't exist
        # Partition key: tenant_id (for multi-tenant data isolation)
        container = database.create_container(
            id="audit_logs",
            partition_key=PartitionKey(path="/tenant_id"),
            offer_throughput=400  # Minimum for serverless
        )

    return container


def close_cosmos_client():
    """Close the Cosmos DB client connection."""
    global _cosmos_client

    if _cosmos_client is not None:
        _cosmos_client.close()
        _cosmos_client = None
