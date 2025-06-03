#!/usr/bin/env python3
"""
Example usage of the refactored orchestration engine with planning agent.
"""

from controllers.planning_agent.atomic_executor import process_alert_with_atomic_planning


def main():
    """Demonstrate the new architecture."""
    
    # Example alert and context
    alert = "High CPU usage detected on web server cluster"
    context = "Production environment, peak traffic hours, multiple servers affected"
    
    print("🚀 Starting SRE Planning Agent")
    print(f"Alert: {alert}")
    print(f"Context: {context}")
    print("-" * 60)
    
    # Execute the planning workflow using the new executor
    result = process_alert_with_atomic_planning(alert, context)
    
    print("-" * 60)
    print("📊 Final Results:")
    print(f"Success: {result.success}")
    print(f"Steps completed: {len([s for s in result.plan.steps if s.status == 'completed'])}/{len(result.plan.steps)}")
    
    print("\n📋 Summary:")
    print(result.summary)


if __name__ == "__main__":
    main()