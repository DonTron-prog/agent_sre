#!/usr/bin/env python
"""
Example script demonstrating the SRE agent's alert processing workflow.
"""

import asyncio
import json
import time
from pathlib import Path
import sys
import os

# Add the parent directory to the path so we can import the sre_agent package
sys.path.insert(0, str(Path(__file__).parent.parent))

from sre_agent.alert_processor import AlertProcessor
from sre_agent.models.alert import AlertModel


# Define the infrastructure graph
infra_graph = {
    "regions": [
        {
            "name": "us-east-1",
            "projects": [
                {
                    "name": "ProjectA",
                    "vpcs": [
                        {
                            "id": "vpc-001",
                            "subnets": [
                                {
                                    "id": "subnet-101",
                                    "clusters": [
                                        {
                                            "name": "cluster-alpha",
                                            "nodes": [
                                                {
                                                    "name": "node-1",
                                                    "pods": [
                                                        {
                                                            "name": "auth-service-xyz-pod",
                                                            "containers": [
                                                                {
                                                                    "name": "auth-service",
                                                                    "version": "2.3.1",
                                                                    "process": "auth-service-app"
                                                                }
                                                            ]
                                                        },
                                                        {
                                                            "name": "payment-service-abc-pod",
                                                            "containers": [
                                                                {
                                                                    "name": "payment-service",
                                                                    "version": "1.8.0",
                                                                    "process": "payment-service-app"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                },
                                                {
                                                    "name": "node-2",
                                                    "pods": [
                                                        {
                                                            "name": "auth-service-uvw-pod",
                                                            "containers": [
                                                                {
                                                                    "name": "auth-service",
                                                                    "version": "2.3.1",
                                                                    "process": "auth-service-app"
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# Example alerts
example_alerts = [
    {
        "id": "alert-001",
        "type": "PodCrashLoop",
        "summary": "Pod auth-service-xyz-pod in cluster-alpha is in CrashLoopBackOff",
        "details": "The pod auth-service-xyz-pod has restarted 5 times in 15 minutes"
    },
    {
        "id": "alert-002",
        "type": "HighCPU",
        "summary": "Node node-1 in cluster-alpha has high CPU usage",
        "details": "CPU usage has been above 90% for the past 10 minutes"
    },
    {
        "id": "alert-003",
        "type": "NetworkLatency",
        "summary": "Service auth-service in cluster-alpha has high latency",
        "details": "Request latency has increased by 300% in the last 5 minutes"
    }
]


async def main():
    """Main entry point for the example."""
    
    # Print header
    print("\n" + "=" * 80)
    print(" " * 30 + "SRE AGENT EXAMPLE")
    print("=" * 80 + "\n")
    
    # Initialize the alert processor
    processor = AlertProcessor(infra_graph)
    
    # Process each example alert
    for i, alert in enumerate(example_alerts):
        print(f"\n\n{'='*80}")
        print(f"PROCESSING ALERT {i+1}/{len(example_alerts)}: {alert['type']}")
        print(f"{'='*80}\n")
        print(f"Alert ID: {alert['id']}")
        print(f"Type: {alert['type']}")
        print(f"Summary: {alert['summary']}")
        print(f"Details: {alert['details']}")
        print(f"\n{'-'*80}\n")
        
        # Start time
        start_time = time.time()
        
        try:
            print("Processing alert... (this may take a minute or two)")
            # Process the alert
            recommendation = await processor.process_alert(alert)
            
            # Debug information
            print(f"\nDEBUG - Recommendation type: {type(recommendation)}")
            if recommendation is None:
                print("ERROR: Recommendation is None")
            else:
                print(f"DEBUG - Recommendation keys: {recommendation.keys() if hasattr(recommendation, 'keys') else 'No keys'}")
            
            # Print the recommendation
            print(f"\n{'-'*80}")
            print("RECOMMENDATION:")
            print(f"{'-'*80}\n")
            if recommendation is not None:
                print(recommendation.get("recommendation_text", "No recommendation text available"))
            else:
                print("No recommendation available")
            
            # Print similar incidents
            if recommendation is not None and recommendation.get("similar_incidents"):
                print(f"\n{'-'*80}")
                print(f"SIMILAR INCIDENTS ({len(recommendation.get('similar_incidents', []))}):")
                print(f"{'-'*80}\n")
                
                for i, incident in enumerate(recommendation.get("similar_incidents", [])):
                    print(f"Incident {i+1} (Similarity: {incident.get('similarity_score', 0.0):.2f}):")
                    print(f"Error: {incident.get('error', '')}")
                    print(f"Solution: {incident.get('solution', '')}")
                    print()
            
            # Print time taken
            time_taken = time.time() - start_time
            print(f"\nProcessing completed in {time_taken:.2f} seconds.\n")
        
        except Exception as e:
            print(f"Error processing alert: {str(e)}")


if __name__ == "__main__":
    # Check if code-rag is installed
    try:
        import code_rag
    except ImportError:
        print("Error: code-rag package is not installed.")
        print("Please install it first by running:")
        print("pip install -e ../code-rag")
        sys.exit(1)
    
    # Check if the environment variables are set
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY environment variable is not set.")
        print("The agent might not work correctly without it.")
    
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Warning: OPENROUTER_API_KEY environment variable is not set.")
        print("The agent might not work correctly without it.")
        
    # Run the main function
    asyncio.run(main())