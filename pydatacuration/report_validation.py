import re
from datetime import timedelta
from enum import Enum
from pathlib import Path

import docx
import pandas as pd
import typer
from trogon.typer import init_tui

from .custom_logging import CustomLogger


app = typer.Typer(rich_markup_mode='rich')
init_tui(app)


def extract_tables_from_word(docx_path: Path) -> list:
    """Extract tables from a Word document."""
    doc = docx.Document(str(docx_path))
    return doc.tables


def table_to_dataframe(table):
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
            row = row[:len(headers)]

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

    return df


def count_status_markers(data_frame: pd.DataFrame) -> dict:
    """Count the X markers in each status column (P, RQU, RCM, NS, NA)."""
    status_columns = ['P', 'RQU', 'RCM', 'NS', 'NA']
    status_counts = dict.fromkeys(status_columns, 0)

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
                if cell_str == 'X':
                    status_counts[column] += 1

    return status_counts


def calculate_total_time(data_frame: pd.DataFrame) -> str:
    """Calculate total time from the Time Spent column.

    Format expected: HH:MM:SS.
    """
    total_time = timedelta()
    time_column = 'Time Spent'

    # Find the time column - it might have different naming
    time_columns = [col for col in data_frame.columns if 'time' in col.lower()]
    if time_columns:
        time_column = time_columns[0]

    # Regular expression to match time format HH:MM:SS
    time_pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2})')

    # Process each time entry
    for _, row in data_frame.iterrows():
        if time_column in row:
            time_str = str(row[time_column])
            match = time_pattern.match(time_str)
            if match:
                hours, minutes, seconds = map(int, match.groups())
                total_time += timedelta(hours=hours, minutes=minutes, seconds=seconds)

    return str(total_time)


def analyze_word_doc_tables(docx_path: Path) -> dict:
    """Main function to analyze tables in Word document."""
    results = {
        'status_counts': {'P': 0, 'RQU': 0, 'RCM': 0, 'NS': 0, 'NA': 0},
        'total_time': '',
        'table_data': []
    }

    # Extract tables
    tables = extract_tables_from_word(docx_path)

    total_seconds = 0

    # Process each table
    for i, table in enumerate(tables):
        df = table_to_dataframe(table)
        results['table_data'].append(df)

        # Print the raw DataFrame for debugging
        # print(f'\nTable {i+1} structure:')
        # print(df.head())
        # print(f'Columns: {df.columns.tolist()}')

        # Count X markers in status columns
        table_status_counts = count_status_markers(df)
        print(f'Table {i + 1} status counts: {table_status_counts}')

        for key, value in table_status_counts.items():
            results['status_counts'][key] += value

        # Calculate time spent
        time_column = [col for col in df.columns if 'time' in col.lower()]
        if time_column:
            col_name = time_column[0]
            for _, row in df.iterrows():
                if col_name in row and row[col_name]:
                    time_str = str(row[col_name])
                    match = re.match(r'(\d{2}):(\d{2}):(\d{2})', time_str)
                    if match:
                        h, m, s = map(int, match.groups())
                        total_seconds += h * 3600 + m * 60 + s


    # Format the total time
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    results['total_time'] = f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    return results


def parse_word_path(ticket_number: str, level: str) -> Path:
    """Parse the Word document path based on the ticket number."""
    # Define the base path
    base_path = Path('./workdir') / ticket_number / 'log_files'
    # Construct the Word document path
    word_doc_path = base_path / f'{ticket_number}_log_{level}-level.docx'
    return Path(word_doc_path)


class CurationLogLevels(str, Enum):
    """Enum for curation log levels."""
    high = 'high'
    medium = 'medium'


@app.command()
def report_validation(
    ticket_number: str = typer.Argument(..., help='Ticket number for the report'),
    level: CurationLogLevels = typer.Option(..., help='Level of the report'),
    parent_dir: str = typer.Argument('./workdir', help='Parent directory for the report'),
):
    """Main entry point for the report validation."""
    # Initialize logger
    logger = CustomLogger.get_logger('report_validation')

    # level 
    level_str = str(level.value)

    # Parse the Word document path
    word_doc_path = parse_word_path(ticket_number, level_str)

    # Analyze the Word document tables
    results = analyze_word_doc_tables(word_doc_path)

    # Print final results
    print('\n--- FINAL RESULTS ---')
    print(f"Status column counts: {results['status_counts']}")
    print(f"Total time spent: {results['total_time']}")


if __name__ == '__main__':
    app()

    # print('\n--- FINAL RESULTS ---')
    # print(f"Status column counts: {results['status_counts']}")
    # print(f"Total time spent: {results['total_time']}")

    # # Detailed results for each status column
    # print('\nStatus column details:')
    # for key, value in results['status_counts'].items():
    #     print(f'{key}: {value} occurrences')

    # # Optional: Export results to CSV
    # try:
    #     results_df = pd.DataFrame([results['status_counts']])
    #     results_df['Total Time'] = results['total_time']
    #     results_df.to_csv('table_analysis_results.csv', index=False)
    #     print('\nResults exported to table_analysis_results.csv')
    # except Exception as e:
    #     print(f'Error exporting results: {e}')
