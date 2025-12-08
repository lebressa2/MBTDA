# Context Contribution Pattern

## Overview

The Agent Framework uses the `IContextProvider` interface to automatically collect context from components. This eliminates the need for hardcoded component lists and ensures that any component implementing the interface will automatically contribute to the agent's context.

## How It Works

### 1. Interface Definition

```python
class IContextProvider(ABC):
    """
    Base interface for components that contribute to the agent's context.
    
    Components implementing this interface can automatically inject their
    context into the agent's system prompt.
    """
    
    # Flag to enable/disable context injection (default: True)
    inject_context: bool = True
    
    @abstractmethod
    def get_context_contribution(self) -> dict[str, Any]:
        """
        Get the context contribution from this component.
        
        Returns a dictionary that will be deep-merged into the agent's
        context.
        """
        pass
```

### 2. Automatic Discovery

The `Agent._collect_context_contributions()` method automatically discovers all components by:

1. Iterating through all agent attributes using `dir(self)`
2. Checking if each attribute implements `IContextProvider`
3. Calling `get_context_contribution()` if `inject_context=True`
4. Merging the contribution into the main context

**No hardcoded lists needed!** 🎉

## Implementation Example

### Creating a Context-Contributing Component

```python
from src.interfaces.base import IContextProvider

class MyCustomComponent(IContextProvider):
    """Example component that contributes context."""
    
    # Enable automatic context injection
    inject_context: bool = True
    
    def __init__(self):
        self.status = "active"
        self.data = {"key": "value"}
    
    def get_context_contribution(self) -> dict[str, Any]:
        """Provide context about this component."""
        return {
            "my_component": {
                "status": self.status,
                "data": self.data,
                "timestamp": time.time()
            }
        }
```

### Adding to Agent

```python
# Simply add the component to the agent
agent = Agent(
    text_provider=llm,
    memory=memory_manager,  # Implements IContextProvider
    tools=tool_manager,      # Implements IContextProvider
    workspace_manager=workspace,  # Implements IContextProvider
    my_custom=MyCustomComponent()  # Will be auto-discovered!
)
```

The agent will automatically discover and collect context from ALL components that implement `IContextProvider`.

## Existing Components

The following built-in interfaces already extend `IContextProvider`:

- **`IMemoryManager`**: Contributes recent messages and long-term memory
- **`IToolManager`**: Contributes available tools and descriptions
- **`IWorkspaceManager`**: Contributes workspace info (path, files, operations)

## Benefits

✅ **No Hardcoding**: No need to maintain a list of components  
✅ **Automatic Discovery**: New components are automatically detected  
✅ **Type Safety**: Interface ensures `get_context_contribution()` is implemented  
✅ **Flexible**: Can enable/disable injection per component with `inject_context`  
✅ **Maintainable**: Adding new components doesn't require changes to `Agent`  

## Disabling Context Injection

To disable automatic context injection for a specific component:

```python
class QuietComponent(IContextProvider):
    # Disable automatic injection
    inject_context: bool = False
    
    def get_context_contribution(self) -> dict[str, Any]:
        # Still required by interface, but won't be called automatically
        return {}
```

## Best Practices

1. **Avoid Key Collisions**: Use unique top-level keys in your contribution
   ```python
   # Good
   return {"my_component": {...}}
   
   # Bad (might collide with other components)
   return {"status": "active"}
   ```

2. **Keep It Relevant**: Only contribute information needed for LLM reasoning
   ```python
   # Good
   return {"workspace": {"current_path": "/workspace", "files_count": 42}}
   
   # Bad (too much detail)
   return {"workspace": {"every_file_content": {...}}}
   ```

3. **Handle Errors Gracefully**: The agent catches exceptions, but log them
   ```python
   def get_context_contribution(self) -> dict[str, Any]:
       try:
           return {"data": self.get_data()}
       except Exception as e:
           logger.error(f"Failed to get data: {e}")
           return {}
   ```

## Migration Notes

### Before (Hardcoded List)
```python
def _collect_context_contributions(self) -> None:
    # Had to manually list all components
    components = [
        self.memory,
        self.tools,
        self.workspace_manager,
        # Easy to forget new components!
    ]
    
    for component in components:
        if isinstance(component, IContextProvider):
            # ...
```

### After (Automatic Discovery)
```python
def _collect_context_contributions(self) -> None:
    # Automatically discovers ALL IContextProvider components
    for attr_name in dir(self):
        component = getattr(self, attr_name)
        if isinstance(component, IContextProvider):
            # ...
```

## Testing

To verify your component contributes context:

```python
def test_context_contribution():
    component = MyCustomComponent()
    
    # Check it implements the interface
    assert isinstance(component, IContextProvider)
    
    # Check it provides context
    context = component.get_context_contribution()
    assert "my_component" in context
    assert context["my_component"]["status"] == "active"
```

---

**Remember**: If you create a new component that should contribute to the agent's context, just implement `IContextProvider` and it will automatically be discovered! 🚀
