import re
from enum import Enum
from pathlib import Path

import docx
import pandas as pd
import typer
from loguru import logger


app = typer.Typer(rich_markup_mode='rich')


class ReportValidation:
    """Class to handle report validation tasks."""

    def __init__(self) -> None:
        """Initialize the ReportValidation class."""
        self.logger = logger

    @staticmethod
    def extract_tables_from_word(docx_path: Path) -> list:
        """Extract tables from a Word document."""
        doc = docx.Document(str(docx_path))
        return doc.tables

    def table_to_dataframe(self, table):
        """Convert a docx table to pandas DataFrame, handling merged cells and specific status columns."""
        # Extract all rows including header
        rows_data = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            rows_data.append(row_data)

        # Handle case where the first row might be merged and not contain all column headers
        # If P, RQU, RCM, NS, NA columns are in a specific position (as shown in images)
        headers = []
        max_columns = max(len(row) for row in rows_data)

        # Find the row with the most complete headers
        header_row_index = 0
        for i, row in enumerate(rows_data):
            # Skip rows that are too short
            if len(row) < 5:
                continue

            # Check if this row contains status column headers
            contains_status_columns = any(col in {'P', 'RQU', 'RCM', 'NS', 'NA'} for col in row)
            if contains_status_columns:
                header_row_index = i
                break

        # Use the identified header row
        if header_row_index < len(rows_data):
            headers = rows_data[header_row_index]
        else:
            # Fallback: create generic headers if none found
            headers = [f'Column_{i}' for i in range(max_columns)]

        # Ensure the status columns are explicitly included
        status_columns = ['P', 'RQU', 'RCM', 'NS', 'NA']
        for status_col in status_columns:
            if status_col not in headers:
                # Try to find index of these columns based on position
                # This is based on the images showing these columns are usually consecutive
                if 'P' in headers:
                    p_index = headers.index('P')
                    for i, col in enumerate(status_columns):
                        if p_index + i < len(headers):
                            headers[p_index + i] = col
                        else:
                            # Add missing columns
                            headers.append(col)
                else:
                    # Just append if we can't find position
                    headers.append(status_col)

        # Create data rows, skipping the header row
        data = []
        for i, row in enumerate(rows_data):
            if i == header_row_index:
                continue  # Skip the header row

            # Pad row if shorter than headers
            if len(row) < len(headers):
                row += [''] * (len(headers) - len(row))

            # Truncate row if longer than headers
            if len(row) > len(headers):
                row = row[: len(headers)]

            # Create row dictionary
            row_dict = dict(zip(headers, row))

            # Look for 'X' markers in the right positions for status columns
            for idx, col in enumerate(status_columns):
                if col not in row_dict or not row_dict[col]:
                    # Try to find X in the expected position based on the header
                    if 'P' in headers:
                        p_index = headers.index('P')
                        if p_index + idx < len(row) and row[p_index + idx] == 'X':
                            row_dict[col] = 'X'

            data.append(row_dict)

        # Create DataFrame
        df = pd.DataFrame(data)

        logger.debug(f'DataFrame columns: {df.columns.tolist()}')

        return df

    def count_status_markers(self, data_frame: pd.DataFrame) -> dict:
        """Count the X markers in each status column (P, RQU, RCM, NS, NA)."""
        status_columns = ['P', 'RQU', 'RCM', 'NS', 'NA']
        status_counts = dict.fromkeys(status_columns, 0)  # Use dict comprehension for initialization

        # Iterate through rows to count X marks
        for _, row in data_frame.iterrows():
            for column in status_columns:
                # Try different ways to access the column value
                cell_value = None

                # Try direct access
                if column in data_frame.columns:
                    cell_value = row.get(column)

                # Try case-insensitive match
                if cell_value is None:
                    for col_name in data_frame.columns:
                        if col_name.upper() == column:
                            cell_value = row.get(col_name)
                            break

                # Check if the cell contains 'X' (case insensitive)
                if cell_value is not None:
                    cell_str = str(cell_value).strip().upper()
                    if cell_str in {'X', 'x'}:
                        status_counts[column] += 1

        return status_counts

    def calculate_time_directly(self, tables) -> tuple:
        """Calculate total time directly from tables.

        Returns both formatted time string and total seconds.
        """
        total_seconds = 0
        time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2})')

        # Only process value[2]:
        for i in range(len(tables)):
            time_str = tables.iloc[i].values[2] if not None else None
            match = time_pattern.match(time_str)
            if match:
                hours, minutes, seconds = map(int, match.groups())
                total_seconds += hours * 3600 + minutes * 60 + seconds
            elif time_str and time_str != 'Time Spent':
                msg = typer.style(
                    f'❌Invalid time format value found in the "Time Spent" column: {time_str}. Please fix it and re-run the validation.',
                    fg='red',
                )
                typer.echo(msg)
                continue

        # Format the result
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        formatted_time = f'{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}'

        return formatted_time, total_seconds

    def analyze_word_doc_tables(self, docx_path: Path) -> dict:
        """Main function to analyze tables in Word document."""
        results = {'status_counts': {'P': 0, 'RQU': 0, 'RCM': 0, 'NS': 0, 'NA': 0}, 'total_time': '', 'table_data': []}

        # Extract tables
        tables = self.extract_tables_from_word(docx_path)

        # Process each table for status counts
        # Only process table 2 (i.e. index 1)
        df = self.table_to_dataframe(tables[1])
        results['table_data'].append(df)

        # Count X markers in status columns
        table_status_counts = self.count_status_markers(df)

        for key, value in table_status_counts.items():
            results['status_counts'][key] += value

        # Calculate time directly from the tables - more reliable approach
        formatted_time, _ = self.calculate_time_directly(df)
        results['total_time'] = formatted_time

        return results

    @staticmethod
    def parse_word_path(ticket_number: str, level: str, parent_dir: str = './workdir') -> Path:
        """Parse the Word document path based on the ticket number."""
        # Define the base path
        base_path = Path(parent_dir) / ticket_number / 'log_files'
        # Construct the Word document path
        word_doc_path = base_path / f'{ticket_number}_log_{level}-level.docx'
        # Check if the file exists
        if not word_doc_path.exists():
            # Try to use wildcard search for the file
            matches = list(base_path.glob(f'{ticket_number}_log_{level}-level*.docx'))
            if matches:
                return matches[0]
        return word_doc_path

    @staticmethod
    def check_final_results(level: str, check_num) -> None:
        """Check final results and see whether the result is valid or not."""
        expected_high_level_checks = 32
        expected_medium_checks = 18

        if level == 'high' and check_num != expected_high_level_checks:
            msg = typer.style(
                f"❌ Invalid number of check marks ('X') for high level: {check_num}. Should be {expected_high_level_checks}.",
                fg='red',
            )  # noqa: E501
            typer.echo(msg)
        elif level == 'medium' and check_num != expected_medium_checks:
            msg = typer.style(
                f"❌ Invalid number of check marks ('X') for medium level: {check_num}. Should be {expected_medium_checks}.",
                fg='red',
            )  # noqa: E501
            typer.echo(msg)
        else:
            typer.echo('✅ Total number of check marks (X) is valid.')


class CurationLogLevels(str, Enum):
    """Enum for curation log levels."""

    high = 'high'
    medium = 'medium'


@app.command()
def validate_report(
    ticket_number: str = typer.Argument(..., help='Ticket number for the report'),
    level: CurationLogLevels = typer.Option(..., help='Level of the report'),
    parent_dir: str = typer.Argument('./workdir', help='Parent directory for the report'),
    export_csv: bool = typer.Option(False, '--export-csv', help='Export results to CSV'),
) -> dict:
    """Validate curation reports by analyzing tables in Word documents.

    This script analyzes the tables in a curation log document and reports:
    - Count of X markers in status columns (P, RQU, RCM, NS, NA)
    - Total time spent on curation tasks

    Example usage:
        python -m report_validation ABC123 --level high
    """
    # # Initialize logger - now using loguru globally

    # Initialize ReportValidation class
    report_validator = ReportValidation()

    # Parse the Word document path
    word_doc_path = report_validator.parse_word_path(ticket_number, str(level.value), parent_dir)

    if not word_doc_path.exists():
        error_msg = f'Document not found: {word_doc_path}'
        raise typer.BadParameter(error_msg)

    typer.echo(f'Analyzing document: {word_doc_path}\n')

    # Analyze the Word document tables
    results = report_validator.analyze_word_doc_tables(word_doc_path)

    # Print final results
    typer.echo('\n--- FINAL RESULTS ---')
    typer.echo(f'Status column counts: {results["status_counts"]}')
    typer.echo(f'Total time spent: {results["total_time"]}')

    # Calculate overall count
    total_x_count = sum(results['status_counts'].values())
    typer.echo(f'Total X count: {total_x_count}')

    report_validator.check_final_results(str(level.value), total_x_count)

    # Export results to CSV if requested
    if export_csv:
        csv_path = word_doc_path.parent / f'{ticket_number}_{str(level.value)}_results.csv'
        try:
            # Create a DataFrame with results
            results_df = pd.DataFrame([results['status_counts']])
            results_df['Total Time'] = results['total_time']
            results_df['Total X Count'] = total_x_count

            # Add ticket metadata
            results_df['Ticket Number'] = ticket_number
            results_df['Level'] = level

            # Export to CSV
            results_df.to_csv(csv_path, index=False)
            print(f'Results exported to: {csv_path}')
        except Exception as e:
            logger.error(f'Error exporting results to CSV: {e}')

    return results


if __name__ == '__main__':
    app()
