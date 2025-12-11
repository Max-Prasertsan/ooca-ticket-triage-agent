"""
Region Status Tool
===================

Tool for checking the operational status of services
in specific geographic regions.

This implementation uses mock data for demonstration.
In production, this would integrate with a real status
monitoring system (DataDog, PagerDuty, etc.).
"""

import logging
from datetime import datetime, timezone
from typing import Type

from src.triage_agent.models.tools import (
    RegionStatusInput,
    RegionStatusOutput,
    ServiceStatus,
)
from src.triage_agent.tools.base import BaseTool

logger = logging.getLogger(__name__)


# Mock region status data
MOCK_REGION_STATUS = {
    "us-east": {
        "overall": "degraded",
        "services": [
            {
                "service_name": "api",
                "status": "operational",
                "latency_ms": 45,
                "last_incident": None
            },
            {
                "service_name": "dashboard",
                "status": "degraded",
                "latency_ms": 250,
                "last_incident": "2024-01-15T14:00:00Z"
            },
            {
                "service_name": "auth",
                "status": "operational",
                "latency_ms": 30,
                "last_incident": None
            },
            {
                "service_name": "database",
                "status": "degraded",
                "latency_ms": 180,
                "last_incident": "2024-01-15T13:45:00Z"
            }
        ],
        "active_incidents": ["INC-2024-0115-001"]
    },
    "us-west": {
        "overall": "healthy",
        "services": [
            {
                "service_name": "api",
                "status": "operational",
                "latency_ms": 35,
                "last_incident": None
            },
            {
                "service_name": "dashboard",
                "status": "operational",
                "latency_ms": 80,
                "last_incident": "2024-01-10T08:00:00Z"
            },
            {
                "service_name": "auth",
                "status": "operational",
                "latency_ms": 25,
                "last_incident": None
            },
            {
                "service_name": "database",
                "status": "operational",
                "latency_ms": 40,
                "last_incident": None
            }
        ],
        "active_incidents": []
    },
    "eu-west": {
        "overall": "healthy",
        "services": [
            {
                "service_name": "api",
                "status": "operational",
                "latency_ms": 55,
                "last_incident": None
            },
            {
                "service_name": "dashboard",
                "status": "operational",
                "latency_ms": 95,
                "last_incident": None
            },
            {
                "service_name": "auth",
                "status": "operational",
                "latency_ms": 40,
                "last_incident": None
            },
            {
                "service_name": "database",
                "status": "operational",
                "latency_ms": 50,
                "last_incident": None
            }
        ],
        "active_incidents": []
    },
    "apac": {
        "overall": "healthy",
        "services": [
            {
                "service_name": "api",
                "status": "operational",
                "latency_ms": 120,
                "last_incident": None
            },
            {
                "service_name": "dashboard",
                "status": "operational",
                "latency_ms": 150,
                "last_incident": None
            },
            {
                "service_name": "auth",
                "status": "operational",
                "latency_ms": 100,
                "last_incident": None
            },
            {
                "service_name": "database",
                "status": "operational",
                "latency_ms": 90,
                "last_incident": None
            }
        ],
        "active_incidents": []
    }
}


class RegionStatusTool(BaseTool[RegionStatusInput, RegionStatusOutput]):
    """
    Tool for checking regional service health status.
    
    Checks the operational status of services in specific
    geographic regions. Useful for correlating customer
    issues with known infrastructure problems.
    
    Attributes:
        name: "region_status"
        description: Description for the AI agent
        input_model: RegionStatusInput
        output_model: RegionStatusOutput
    
    Example:
        >>> tool = RegionStatusTool()
        >>> input_data = RegionStatusInput(region="us-east")
        >>> result = tool.execute(input_data)
        >>> print(result.overall_status)
        'degraded'
    """
    
    name: str = "region_status"
    description: str = (
        "Check the operational status of services in a specific geographic region. "
        "Returns overall health status, individual service statuses, latency metrics, "
        "and any active incidents. Use this to determine if a customer's issue might "
        "be related to a known infrastructure problem."
    )
    input_model: Type[RegionStatusInput] = RegionStatusInput
    output_model: Type[RegionStatusOutput] = RegionStatusOutput
    
    def _execute(self, input_data: RegionStatusInput) -> RegionStatusOutput:
        """
        Execute region status check.
        
        Args:
            input_data: Region identifier and optional service filters.
        
        Returns:
            RegionStatusOutput: Regional status information.
        """
        region = input_data.region.lower()
        logger.debug(f"Checking status for region: {region}")
        
        # Get current timestamp
        now = datetime.now(timezone.utc).isoformat()
        
        # Check if region exists
        if region not in MOCK_REGION_STATUS:
            logger.warning(f"Unknown region requested: {region}")
            return RegionStatusOutput(
                region=region,
                overall_status="unknown",
                services=[],
                active_incidents=[],
                last_updated=now
            )
        
        region_data = MOCK_REGION_STATUS[region]
        
        # Filter services if specific ones requested
        services_data = region_data["services"]
        if input_data.check_services:
            services_data = [
                s for s in services_data
                if s["service_name"] in input_data.check_services
            ]
        
        # Convert to ServiceStatus objects
        services = [
            ServiceStatus(
                service_name=s["service_name"],
                status=s["status"],
                latency_ms=s["latency_ms"],
                last_incident=s.get("last_incident")
            )
            for s in services_data
        ]
        
        logger.info(
            f"Region {region} status: {region_data['overall']} "
            f"({len(services)} services checked)"
        )
        
        return RegionStatusOutput(
            region=region,
            overall_status=region_data["overall"],
            services=services,
            active_incidents=region_data.get("active_incidents", []),
            last_updated=now
        )