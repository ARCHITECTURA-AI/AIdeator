from unittest import mock
from uuid import UUID

from aideator.cli import build_parser, command_validate


def test_validate_parser_registration():
    parser = build_parser()
    args = parser.parse_args(["validate", "My Idea", "--description", "Desc", "--mode", "hybrid"])
    assert args.title == "My Idea"
    assert args.description == "Desc"
    assert args.mode == "hybrid"
    assert args.func == command_validate

@mock.patch("aideator.cli.execute_run")
@mock.patch("aideator.cli.save_idea")
@mock.patch("aideator.cli.save_run")
@mock.patch("db.reports.get_report")
def test_command_validate_flow(mock_get_report, mock_save_run, mock_save_idea, mock_execute_run):
    # Setup mocks
    mock_save_idea.return_value = mock.Mock(idea_id=UUID("00000000-0000-0000-0000-000000000001"))
    mock_run = mock.Mock(run_id=UUID("00000000-0000-0000-0000-000000000002"))
    mock_save_run.return_value = mock_run
    
    mock_report = mock.Mock()
    # Mock card attributes as needed
    mock_card = mock.Mock(score=90, title="Card 1", summary="Good")
    mock_card.type = "demand"
    mock_card.meta = {"band": "A"}
    
    mock_report.cards = [mock_card]
    mock_report.artifact_path = "path/to/doc.md"
    mock_get_report.return_value = mock_report

    # Execute
    parser = build_parser()
    args = parser.parse_args(["validate", "Test Title"])
    
    with mock.patch("builtins.print") as mock_print:
        command_validate(args)

    # Verify
    mock_save_idea.assert_called_once()
    mock_save_run.assert_called_once()
    mock_execute_run.assert_called_once_with(mock_run.run_id)
    mock_get_report.assert_called_once_with(mock_run.run_id)
    
    # Check that we printed the summary
    mock_print.assert_any_call("VALIDATION SUMMARY")
    # In the code: print(f"[{card.type.upper()}] {card.title}")
    mock_print.assert_any_call("[DEMAND] Card 1")
