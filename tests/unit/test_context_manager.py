"""
Unit Tests for ContextManager - Dictionary-based Templates.

Tests the new template system including:
- MetaData model and dynamic properties
- TemplateRegistry for custom templates
- Template + context.add() harmony (deep merge)
- Dynamic variable interpolation ({meta.field})
- Factory methods

Following the testing pyramid: these are UNIT tests (fast, isolated, no APIs).
"""

import pytest
from datetime import datetime

from src.components import (
    ContextManager,
    MetaData,
    SystemPromptTemplate,
    SYSTEM_PROMPT_TEMPLATES,
    TemplateRegistry,
)


# ==============================================================================
# MetaData Model Tests
# ==============================================================================

class TestMetaData:
    """Tests for the MetaData model."""

    def test_default_values(self):
        """Test that MetaData has sensible defaults."""
        meta = MetaData()
        
        assert meta.agent_name == "Agent"
        assert meta.agent_role == "AI Assistant"
        assert meta.agent_version == "1.0.0"
        assert meta.session_id is None
        assert meta.user_name is None
        assert meta.custom == {}

    def test_custom_values(self):
        """Test that MetaData accepts custom values."""
        meta = MetaData(
            agent_name="TestBot",
            agent_role="Tester",
            user_name="Arthur",
            session_id="sess_123"
        )
        
        assert meta.agent_name == "TestBot"
        assert meta.agent_role == "Tester"
        assert meta.user_name == "Arthur"
        assert meta.session_id == "sess_123"

    def test_current_time_property(self):
        """Test that current_time returns ISO format string."""
        meta = MetaData()
        
        time_str = meta.current_time
        
        assert isinstance(time_str, str)
        # Should be parseable as ISO datetime
        datetime.fromisoformat(time_str)

    def test_current_date_property(self):
        """Test that current_date returns YYYY-MM-DD format."""
        meta = MetaData()
        
        date_str = meta.current_date
        
        assert isinstance(date_str, str)
        # Should match YYYY-MM-DD pattern
        assert len(date_str) == 10
        assert date_str[4] == "-" and date_str[7] == "-"

    def test_current_datetime_property(self):
        """Test that current_datetime returns formatted string."""
        meta = MetaData()
        
        dt_str = meta.current_datetime
        
        assert isinstance(dt_str, str)
        # Should contain date and time
        assert " " in dt_str

    def test_get_field_direct(self):
        """Test get_field for direct attributes."""
        meta = MetaData(agent_name="Bot", user_name="User")
        
        assert meta.get_field("agent_name") == "Bot"
        assert meta.get_field("user_name") == "User"

    def test_get_field_property(self):
        """Test get_field for properties like current_time."""
        meta = MetaData()
        
        result = meta.get_field("current_time")
        
        assert result is not None
        assert isinstance(result, str)

    def test_get_field_custom_nested(self):
        """Test get_field for custom fields with dot notation."""
        meta = MetaData()
        meta.custom["project"] = "MBTDA"
        meta.custom["env"] = "test"
        
        assert meta.get_field("custom.project") == "MBTDA"
        assert meta.get_field("custom.env") == "test"
        assert meta.get_field("custom.nonexistent") is None

    def test_get_field_nonexistent(self):
        """Test get_field returns None for nonexistent fields."""
        meta = MetaData()
        
        assert meta.get_field("nonexistent_field") is None


# ==============================================================================
# TemplateRegistry Tests
# ==============================================================================

class TestTemplateRegistry:
    """Tests for the TemplateRegistry."""

    def setup_method(self):
        """Clean up custom templates before each test."""
        # Clear any custom templates from previous tests
        TemplateRegistry._custom_templates.clear()

    def test_list_builtin_templates(self):
        """Test that built-in templates are listed."""
        templates = TemplateRegistry.list_templates()
        
        assert "minimal" in templates
        assert "general_assistant" in templates
        assert "task_agent" in templates
        assert "reactive_agent" in templates

    def test_get_builtin_template(self):
        """Test getting a built-in template."""
        template = TemplateRegistry.get("minimal")
        
        assert template is not None
        assert isinstance(template, dict)
        assert "identity" in template

    def test_register_custom_template(self):
        """Test registering a custom template."""
        custom = {
            "identity": {"name": "{meta.agent_name}"},
            "custom_section": {"key": "value"}
        }
        
        TemplateRegistry.register("my_template", custom)
        
        assert "my_template" in TemplateRegistry.list_templates()
        
        retrieved = TemplateRegistry.get("my_template")
        assert retrieved["custom_section"]["key"] == "value"

    def test_custom_template_takes_precedence(self):
        """Test that custom templates override built-in with same name."""
        # Register a custom template with same name as built-in
        TemplateRegistry.register("minimal", {"override": True})
        
        template = TemplateRegistry.get("minimal")
        
        assert "override" in template

    def test_unregister_template(self):
        """Test unregistering a custom template."""
        TemplateRegistry.register("temp", {"temp": True})
        assert "temp" in TemplateRegistry.list_templates()
        
        result = TemplateRegistry.unregister("temp")
        
        assert result is True
        assert "temp" not in TemplateRegistry.list_templates()

    def test_unregister_nonexistent(self):
        """Test unregistering a template that doesn't exist."""
        result = TemplateRegistry.unregister("nonexistent")
        
        assert result is False

    def test_get_returns_copy(self):
        """Test that get() returns a copy, not the original."""
        original = {"data": {"value": 1}}
        TemplateRegistry.register("copy_test", original)
        
        retrieved = TemplateRegistry.get("copy_test")
        retrieved["data"]["value"] = 999  # Modify the copy
        
        # Original should be unchanged
        retrieved_again = TemplateRegistry.get("copy_test")
        assert retrieved_again["data"]["value"] == 1


# ==============================================================================
# ContextManager Template Tests
# ==============================================================================

class TestContextManagerTemplates:
    """Tests for ContextManager template functionality."""

    def setup_method(self):
        """Clean up custom templates before each test."""
        TemplateRegistry._custom_templates.clear()

    def test_no_template(self):
        """Test ContextManager without template starts empty."""
        ctx = ContextManager()
        
        template = ctx.get_template()
        
        assert template == {}

    def test_template_by_name(self):
        """Test loading template by name."""
        ctx = ContextManager(template="minimal")
        
        template = ctx.get_template()
        
        assert "identity" in template

    def test_template_by_dict(self):
        """Test loading template from direct dictionary."""
        custom = {"my_section": {"key": "value"}}
        
        ctx = ContextManager(template=custom)
        
        template = ctx.get_template()
        assert template["my_section"]["key"] == "value"

    def test_set_template_by_name(self):
        """Test changing template by name."""
        ctx = ContextManager()
        
        ctx.set_template("general_assistant")
        
        template = ctx.get_template()
        assert "identity" in template
        assert "states_explanation" in template

    def test_set_template_by_dict(self):
        """Test changing template by dictionary."""
        ctx = ContextManager()
        
        ctx.set_template({"new": {"data": True}})
        
        template = ctx.get_template()
        assert template["new"]["data"] is True


# ==============================================================================
# Template + context.add() Harmony Tests
# ==============================================================================

class TestTemplateContextHarmony:
    """Tests for the harmony between templates and context.add()."""

    def test_add_extends_template(self):
        """Test that add() extends the template with new keys."""
        ctx = ContextManager(template={"base": {"key": "value"}})
        
        ctx.add("new_section", {"new_key": "new_value"})
        
        raw = ctx.get_raw_context()
        assert raw["base"]["key"] == "value"  # Template preserved
        assert raw["new_section"]["new_key"] == "new_value"  # New section added

    def test_add_overrides_template(self):
        """Test that add() overrides template keys."""
        ctx = ContextManager(template={"identity": {"name": "Original"}})
        
        ctx.add("identity", {"name": "Override"})
        
        raw = ctx.get_raw_context()
        assert raw["identity"]["name"] == "Override"

    def test_deep_merge(self):
        """Test that dictionaries are deep merged."""
        ctx = ContextManager(template={
            "config": {
                "level1": {
                    "a": 1,
                    "b": 2
                }
            }
        })
        
        ctx.add("config", {"level1": {"c": 3}})  # Add new key, keep existing
        
        raw = ctx.get_raw_context()
        assert raw["config"]["level1"]["a"] == 1  # Original preserved
        assert raw["config"]["level1"]["b"] == 2  # Original preserved
        assert raw["config"]["level1"]["c"] == 3  # New key added

    def test_list_replaced_not_merged(self):
        """Test that lists are replaced, not merged."""
        ctx = ContextManager(template={"items": [1, 2, 3]})
        
        ctx.add("items", [4, 5])
        
        raw = ctx.get_raw_context()
        assert raw["items"] == [4, 5]  # Completely replaced


# ==============================================================================
# Dynamic Variable Interpolation Tests
# ==============================================================================

class TestDynamicVariables:
    """Tests for {meta.field} interpolation."""

    def test_interpolate_agent_name(self):
        """Test interpolating {meta.agent_name}."""
        ctx = ContextManager()
        ctx.meta.agent_name = "TestBot"
        
        ctx.add("greeting", "Hello, I am {meta.agent_name}!")
        
        raw = ctx.get_raw_context()
        assert raw["greeting"] == "Hello, I am TestBot!"

    def test_interpolate_multiple_fields(self):
        """Test interpolating multiple fields in one string."""
        ctx = ContextManager()
        ctx.meta.agent_name = "Bot"
        ctx.meta.user_name = "User"
        
        ctx.add("message", "{meta.agent_name} says hello to {meta.user_name}")
        
        raw = ctx.get_raw_context()
        assert raw["message"] == "Bot says hello to User"

    def test_interpolate_in_template(self):
        """Test interpolation works in template values."""
        ctx = ContextManager(template={
            "identity": {"name": "{meta.agent_name}"}
        })
        ctx.meta.agent_name = "TemplateBot"
        
        raw = ctx.get_raw_context()
        
        assert raw["identity"]["name"] == "TemplateBot"

    def test_interpolate_nested_dict(self):
        """Test interpolation in nested dictionaries."""
        ctx = ContextManager()
        ctx.meta.agent_name = "NestedBot"
        
        ctx.add("config", {
            "level1": {
                "level2": {
                    "name": "{meta.agent_name}"
                }
            }
        })
        
        raw = ctx.get_raw_context()
        assert raw["config"]["level1"]["level2"]["name"] == "NestedBot"

    def test_interpolate_in_list(self):
        """Test interpolation in list items."""
        ctx = ContextManager()
        ctx.meta.agent_name = "ListBot"
        
        ctx.add("items", [
            "First: {meta.agent_name}",
            "Second item",
            {"nested": "{meta.agent_name}"}
        ])
        
        raw = ctx.get_raw_context()
        assert raw["items"][0] == "First: ListBot"
        assert raw["items"][1] == "Second item"
        assert raw["items"][2]["nested"] == "ListBot"

    def test_interpolate_custom_field(self):
        """Test interpolating custom meta fields."""
        ctx = ContextManager()
        ctx.meta.custom["project"] = "MBTDA"
        
        ctx.add("info", "Working on {meta.custom.project}")
        
        raw = ctx.get_raw_context()
        assert raw["info"] == "Working on MBTDA"

    def test_unknown_field_kept_as_is(self):
        """Test that unknown {meta.field} placeholders are kept."""
        ctx = ContextManager()
        
        ctx.add("text", "Unknown: {meta.nonexistent}")
        
        raw = ctx.get_raw_context()
        assert raw["text"] == "Unknown: {meta.nonexistent}"

    def test_fstring_works(self):
        """Test that f-strings work with add()."""
        ctx = ContextManager()
        current_time = datetime.now().isoformat()
        
        ctx.add("timestamp", f"Generated at {current_time}")
        
        raw = ctx.get_raw_context()
        assert raw["timestamp"] == f"Generated at {current_time}"


# ==============================================================================
# Factory Method Tests
# ==============================================================================

class TestFactoryMethods:
    """Tests for ContextManager factory methods."""

    def test_create_minimal(self):
        """Test create_minimal factory method."""
        ctx = ContextManager.create_minimal(
            agent_name="MinimalBot",
            agent_role="Minimal Role"
        )
        
        assert ctx.meta.agent_name == "MinimalBot"
        assert ctx.meta.agent_role == "Minimal Role"
        
        template = ctx.get_template()
        assert "identity" in template

    def test_create_general_assistant(self):
        """Test create_general_assistant factory method."""
        ctx = ContextManager.create_general_assistant(
            agent_name="AssistantBot",
            agent_role="Helper",
            user_name="TestUser",
            session_id="sess_001"
        )
        
        assert ctx.meta.agent_name == "AssistantBot"
        assert ctx.meta.user_name == "TestUser"
        assert ctx.meta.session_id == "sess_001"
        
        template = ctx.get_template()
        assert "states_explanation" in template
        assert "protocols_explanation" in template

    def test_create_task_agent(self):
        """Test create_task_agent factory method."""
        ctx = ContextManager.create_task_agent(
            agent_name="TaskBot",
            session_id="task_001"
        )
        
        assert ctx.meta.agent_name == "TaskBot"
        assert ctx.meta.session_id == "task_001"
        
        template = ctx.get_template()
        assert "operating_modes" in template

    def test_create_reactive_agent(self):
        """Test create_reactive_agent factory method."""
        ctx = ContextManager.create_reactive_agent(
            agent_name="ReactiveBot",
            session_id="reactive_001"
        )
        
        assert ctx.meta.agent_name == "ReactiveBot"
        
        template = ctx.get_template()
        assert "state_machine" in template
        assert "event_handling" in template

    def test_create_from_template(self):
        """Test create_from_template factory method."""
        custom = {"custom": {"key": "value"}}
        
        ctx = ContextManager.create_from_template(
            template=custom,
            agent_name="CustomBot",
            user_name="CustomUser"
        )
        
        assert ctx.meta.agent_name == "CustomBot"
        assert ctx.meta.user_name == "CustomUser"
        
        template = ctx.get_template()
        assert template["custom"]["key"] == "value"

    def test_create_from_template_extra_kwargs_go_to_custom(self):
        """Test that extra kwargs go to meta.custom."""
        ctx = ContextManager.create_from_template(
            template={},
            agent_name="Bot",
            extra_field="extra_value",
            another_field=123
        )
        
        assert ctx.meta.custom["extra_field"] == "extra_value"
        assert ctx.meta.custom["another_field"] == 123


# ==============================================================================
# Snapshot Tests
# ==============================================================================

class TestSnapshots:
    """Tests for snapshot functionality with templates."""

    def test_snapshot_includes_template(self):
        """Test that snapshot includes the template."""
        ctx = ContextManager(template={"test": True})
        ctx.add("dynamic", "value")
        
        snapshot = ctx.get_snapshot()
        
        assert "template" in snapshot
        assert snapshot["template"]["test"] is True
        assert "context" in snapshot
        assert snapshot["context"]["dynamic"] == "value"

    def test_restore_snapshot_restores_template(self):
        """Test that restore_snapshot restores the template."""
        ctx = ContextManager(template={"original": True})
        
        snapshot = ctx.get_snapshot()
        
        # Change template
        ctx.set_template({"changed": True})
        
        # Restore
        ctx.restore_snapshot(snapshot)
        
        template = ctx.get_template()
        assert template["original"] is True
        assert "changed" not in template


# ==============================================================================
# populate_system_message Tests
# ==============================================================================

class TestPopulateSystemMessage:
    """Tests for the populate_system_message method."""

    def test_empty_context_returns_empty(self):
        """Test that empty context returns empty string."""
        ctx = ContextManager()
        
        result = ctx.populate_system_message()
        
        assert result == ""

    def test_template_is_formatted(self):
        """Test that template is formatted in output."""
        ctx = ContextManager(template={"identity": {"name": "Bot"}})
        ctx.meta.agent_name = "TestBot"
        
        result = ctx.populate_system_message()
        
        assert "identity" in result.lower() or "name" in result

    def test_interpolation_in_output(self):
        """Test that meta variables are interpolated in output."""
        ctx = ContextManager(template={
            "identity": {"name": "{meta.agent_name}"}
        })
        ctx.meta.agent_name = "InterpolatedBot"
        
        result = ctx.populate_system_message()
        
        assert "InterpolatedBot" in result
        assert "{meta.agent_name}" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
