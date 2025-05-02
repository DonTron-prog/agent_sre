"""
Infrastructure graph service for the SRE agent.
"""

import re
from typing import Dict, Any, Optional


class InfrastructureGraphService:
    """
    Service for interacting with the infrastructure knowledge graph.
    
    This service provides methods to:
    - Extract context from the infrastructure graph for a specific alert
    - Find specific resources in the graph
    - Analyze relationships between components
    """
    
    def __init__(self, graph_data: Dict[str, Any]):
        """
        Initialize with the infrastructure graph data.
        
        Args:
            graph_data: Infrastructure knowledge graph data
        """
        self.graph = graph_data
    
    def get_context_for_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant infrastructure context for an alert.
        
        Args:
            alert: The alert to extract context for
            
        Returns:
            Dictionary with relevant infrastructure context
        """
        # Parse alert to identify the affected components
        resource_type = None
        resource_name = None
        cluster_name = None
        
        # Extract information based on alert type
        if alert["type"] == "PodCrashLoop":
            resource_type = "pod"
            # Extract pod name and cluster from the summary
            pod_match = re.search(r"Pod\s+(\S+)\s+in\s+(\S+)", alert["summary"])
            if pod_match:
                resource_name = pod_match.group(1)
                cluster_name = pod_match.group(2)
        elif alert["type"] == "HighCPU":
            resource_type = "node"
            # Extract node name
            node_match = re.search(r"Node\s+(\S+)\s+", alert["summary"])
            if node_match:
                resource_name = node_match.group(1)
        elif alert["type"] == "NetworkLatency":
            resource_type = "service"
            # Extract service name
            service_match = re.search(r"Service\s+(\S+)\s+", alert["summary"])
            if service_match:
                resource_name = service_match.group(1)
                
        # Navigate the graph to find the relevant context
        context = self._find_resource_context(resource_type, resource_name, cluster_name)
        return context
    
    def _find_resource_context(self, 
                              resource_type: Optional[str], 
                              resource_name: Optional[str], 
                              cluster_name: Optional[str]) -> Dict[str, Any]:
        """
        Traverse the graph to find context for a specific resource.
        
        Args:
            resource_type: Type of resource (pod, node, service, etc.)
            resource_name: Name of the resource
            cluster_name: Name of the cluster
            
        Returns:
            Dictionary with relevant context
        """
        # If no information is available, return empty context
        if not resource_type or not resource_name:
            return {}
        
        # Traverse the graph to find the relevant context
        for region in self.graph.get("regions", []):
            for project in region.get("projects", []):
                for vpc in project.get("vpcs", []):
                    for subnet in vpc.get("subnets", []):
                        for cluster in subnet.get("clusters", []):
                            # If cluster name is provided, skip non-matching clusters
                            if cluster_name and cluster.get("name") != cluster_name:
                                continue
                                
                            # Handle pod resources
                            if resource_type == "pod":
                                context = self._find_pod_context(
                                    cluster, resource_name, region, project, vpc, subnet
                                )
                                if context:
                                    return context
                            
                            # Handle node resources
                            elif resource_type == "node":
                                context = self._find_node_context(
                                    cluster, resource_name, region, project, vpc, subnet
                                )
                                if context:
                                    return context
        
        # Return empty dict if resource not found                            
        return {}
    
    def _find_pod_context(self, cluster, pod_name, region, project, vpc, subnet):
        """Find context for a specific pod."""
        for node in cluster.get("nodes", []):
            for pod in node.get("pods", []):
                if pod.get("name") == pod_name:
                    return {
                        "region": region.get("name"),
                        "project": project.get("name"),
                        "vpc_id": vpc.get("id"),
                        "subnet_id": subnet.get("id"),
                        "cluster": cluster.get("name"),
                        "node": node.get("name"),
                        "pod": pod,
                        "containers": pod.get("containers", []),
                    }
        return None
    
    def _find_node_context(self, cluster, node_name, region, project, vpc, subnet):
        """Find context for a specific node."""
        for node in cluster.get("nodes", []):
            if node.get("name") == node_name:
                return {
                    "region": region.get("name"),
                    "project": project.get("name"),
                    "vpc_id": vpc.get("id"),
                    "subnet_id": subnet.get("id"),
                    "cluster": cluster.get("name"),
                    "node": node,
                    "pods": node.get("pods", []),
                }
        return None