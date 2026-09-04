"""Tests for the selected_projects feature."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.aap_watcher.database.models import AAPRecord, Base
from src.aap_watcher.database.repository import Repository
from src.aap_watcher.schema import AAPExtraction


def test_aap_extraction_selected_projects_field():
    """Test that AAPExtraction has selected_projects field."""
    extraction = AAPExtraction(
        title="Test AAP",
        organisation="Test Org",
        selected_projects=["Project 1", "Project 2"]
    )
    
    assert extraction.selected_projects == ["Project 1", "Project 2"]
    assert extraction.title == "Test AAP"
    assert extraction.organisation == "Test Org"


def test_repository_save_aap_with_selected_projects():
    """Test that repository correctly saves AAP with selected projects."""
    # Setup
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    
    repo = Repository(session_factory)
    
    # Create extraction with selected projects
    extraction = AAPExtraction(
        title="Test AAP",
        organisation="Test Org",
        description="Test description",
        selected_projects=["Project A", "Project B", "Project C"]
    )
    
    # Save the AAP
    change_event = repo.save_aap(extraction)
    
    # Verify it was saved correctly
    assert change_event.type == "new"
    assert change_event.version == 1
    
    # Retrieve and check
    latest = repo.latest(extraction.dedupe_key())
    assert latest is not None
    assert latest.title == "Test AAP"
    assert latest.organisation == "Test Org"
    assert latest.selected_projects == "Project A, Project B, Project C"


def test_repository_multiple_versions_with_selected_projects():
    """Test that selected projects are preserved across versions."""
    # Setup  
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    
    repo = Repository(session_factory)
    
    # Create first version with selected projects
    extraction1 = AAPExtraction(
        title="Test AAP",
        organisation="Test Org",
        description="Version 1",
        selected_projects=["Project A"]
    )
    
    change_event1 = repo.save_aap(extraction1)
    assert change_event1.type == "new"
    assert change_event1.version == 1
    
    # Create second version with different selected projects
    extraction2 = AAPExtraction(
        title="Test AAP",
        organisation="Test Org",
        description="Version 2", 
        selected_projects=["Project B", "Project C"]
    )
    
    change_event2 = repo.save_aap(extraction2)
    assert change_event2.type == "modified"
    assert change_event2.version == 2
    
    # Check both versions exist and have correct selected projects
    history = repo.history(extraction1.dedupe_key())
    assert len(history) == 2
    
    # First version
    assert history[0].selected_projects == "Project A"
    
    # Second version  
    assert history[1].selected_projects == "Project B, Project C"


def test_repository_empty_selected_projects():
    """Test that empty selected projects are handled correctly."""
    # Setup
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    
    repo = Repository(session_factory)
    
    # Create extraction with no selected projects
    extraction = AAPExtraction(
        title="Test AAP",
        organisation="Test Org",
        description="Test description",
        selected_projects=[]
    )
    
    change_event = repo.save_aap(extraction)
    assert change_event.type == "new"
    assert change_event.version == 1
    
    # Retrieve and check
    latest = repo.latest(extraction.dedupe_key())
    assert latest is not None
    assert latest.selected_projects == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])