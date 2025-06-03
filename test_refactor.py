#!/usr/bin/env python3
"""
Test script to verify the refactored architecture works correctly.
"""

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    # Test orchestration engine imports
    from orchestration_engine import (
        OrchestratorCore, 
        ConfigManager, 
        ExecutionContext,
        ContextAccumulator,
        ToolManager
    )
    print("✓ Orchestration engine core imports")
    
    from controllers.planning_agent import (
        SimplePlanSchema,
        PlanStepSchema,
        PlanningAgentOutputSchema
    )
    print("✓ Orchestration engine schema imports")
    
    # Test controller imports
    from controllers.planning_agent import SimplePlanningAgent
    print("✓ Planning agent controller imports")
    
    return True


def test_initialization():
    """Test that components can be initialized."""
    print("\nTesting initialization...")
    
    from orchestration_engine import OrchestratorCore, ConfigManager, ToolManager
    
    # Test configuration loading
    config = ConfigManager.load_configuration()
    print("✓ Configuration loading")
    
    # Test tool manager initialization
    tool_manager = ToolManager(config)
    print("✓ Tool manager initialization")
    
    # Test orchestrator core initialization
    orchestrator_core = OrchestratorCore(config, tool_manager)
    print("✓ Orchestrator core initialization")
    
    return True


def test_schema_creation():
    """Test that schemas can be created."""
    print("\nTesting schema creation...")
    
    from controllers.planning_agent import (
        PlanStepSchema,
        SimplePlanSchema
    )
    from orchestration_engine import ExecutionContext
    
    # Test step creation
    step = PlanStepSchema(description="Test step")
    print(f"✓ PlanStepSchema: {step.description}")
    
    # Test plan creation
    plan = SimplePlanSchema(
        alert="Test alert",
        context="Test context",
        steps=[step]
    )
    print(f"✓ SimplePlanSchema with {len(plan.steps)} steps")
    
    # Test execution context
    context = ExecutionContext(
        alert="Test alert",
        context="Test context",
        accumulated_knowledge="Test knowledge"
    )
    print(f"✓ ExecutionContext: {context.alert}")
    
    return True


def test_directory_structure():
    """Test that the directory structure is correct."""
    print("\nTesting directory structure...")
    
    import os
    
    # Check orchestration engine structure
    assert os.path.exists("orchestration_engine"), "orchestration_engine directory missing"
    assert os.path.exists("orchestration_engine/__init__.py"), "orchestration_engine/__init__.py missing"
    assert os.path.exists("orchestration_engine/orchestrator.py"), "orchestrator.py missing"
    assert os.path.exists("orchestration_engine/utils"), "utils directory missing"
    assert os.path.exists("orchestration_engine/agents"), "agents directory missing"
    assert os.path.exists("orchestration_engine/tools"), "tools directory missing"
    assert os.path.exists("orchestration_engine/schemas"), "schemas directory missing"
    print("✓ Orchestration engine structure")
    
    # Check controllers structure
    assert os.path.exists("controllers"), "controllers directory missing"
    assert os.path.exists("controllers/__init__.py"), "controllers/__init__.py missing"
    assert os.path.exists("controllers/planning_agent"), "planning_agent directory missing"
    assert os.path.exists("controllers/planning_agent/__init__.py"), "planning_agent/__init__.py missing"
    assert os.path.exists("controllers/planning_agent/simple_agent.py"), "simple_agent.py missing"
    print("✓ Controllers structure")
    
    # Check that old structure is gone
    assert not os.path.exists("orchestration_agent"), "Old orchestration_agent directory still exists"
    print("✓ Old structure cleaned up")
    
    return True


def main():
    """Run all tests."""
    print("🧪 Testing Refactored Architecture")
    print("=" * 50)
    
    try:
        test_imports()
        test_initialization()
        test_schema_creation()
        test_directory_structure()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Refactor successful!")
        print("\nNew architecture summary:")
        print("- orchestration_engine/: Reusable execution engine")
        print("- controllers/planning_agent/: Planning controller")
        print("- Clear separation of concerns")
        print("- Proper dependency flow")
        print("- Clean import structure")
        
        print("\nNext steps:")
        print("- Run: python example_usage.py (with OPENAI_API_KEY set)")
        print("- Create new controllers in controllers/ directory")
        print("- Import from orchestration_engine in new controllers")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    main()