from datetime import datetime
from typing import Optional, Dict, Any
from app.db.cosmos import get_audit_container
import uuid


def write_audit_log(
    tenant_id: str,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Write an audit log entry to Cosmos DB.

    Args:
        tenant_id: ID of the tenant
        user_id: ID of the user performing the action
        action: Action performed (e.g., "LOGIN", "CREATE_MEMBER", "DELETE_PAYMENT")
        entity_type: Type of entity affected (e.g., "USER", "MEMBER", "PAYMENT")
        entity_id: ID of the entity affected
        metadata: Additional metadata

    Returns:
        ID of the created audit log document
    """
    audit_log = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "user_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        # Audit logging is best effort. An unavailable or unconfigured Cosmos
        # account must never make the business operation (including login) fail.
        container = get_audit_container()
        response = container.create_item(body=audit_log)
        return audit_log["id"]
    except Exception as e:
        # Log the error but don't fail the main operation
        print(f"Failed to write audit log: {str(e)}")
        return None


def get_audit_logs(
    tenant_id: str,
    limit: int = 100,
    offset: int = 0
) -> list:
    """
    Retrieve audit logs for a tenant.

    Args:
        tenant_id: ID of the tenant
        limit: Maximum number of logs to return
        offset: Number of logs to skip

    Returns:
        List of audit log documents
    """
    container = get_audit_container()

    query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id ORDER BY c.timestamp DESC OFFSET @offset LIMIT @limit"

    items = list(container.query_items(
        query=query,
        parameters=[
            {"name": "@tenant_id", "value": tenant_id},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
    ))

    return items
