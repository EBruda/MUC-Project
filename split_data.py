import csv
import os
import sys

def split_csv_into_windows(input_file, lines_per_window=6000):
    """
    Splits the input CSV file into multiple CSV files, each containing lines_per_window lines.
    The header is preserved in each split file.

    :param input_file: Path to the input CSV file.
    :param lines_per_window: Number of lines (excluding the header) per split file.
    """
    if not os.path.isfile(input_file):
        print(f"Error: {input_file} does not exist.")
        return

    # Read the entire CSV
    with open(input_file, mode='r', encoding='utf-8') as f_in:
        reader = csv.reader(f_in)
        header = next(reader, None)  # The first line is the header

        if header is None:
            print(f"Error: {input_file} appears to be empty.")
            return

        rows = list(reader)

    total_rows = len(rows)
    if total_rows == 0:
        print("The CSV file is empty (after the header). Nothing to split.")
        return

    # Create output directory (optional, you can remove this if you just want them
    # in the same directory as input)
    output_dir = os.path.join(os.path.dirname(input_file), "split_csv_files")
    os.makedirs(output_dir, exist_ok=True)

    # Calculate how many split files we need
    total_splits = (total_rows + lines_per_window - 1) // lines_per_window

    # Generate each split file
    for split_index in range(total_splits):
        start = split_index * lines_per_window
        end = min((split_index + 1) * lines_per_window, total_rows)
        chunk = rows[start:end]

        # Construct output file path
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}_window_{split_index + 1}.csv")

        with open(output_file, mode='w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            # Write the header first
            writer.writerow(header)
            # Write the chunk of rows
            writer.writerows(chunk)

        print(f"Created {output_file} with rows {start + 1} to {end} (inclusive).")


if __name__ == "__main__":
    """
    Usage:
        python split_csv_into_windows.py <path_to_your_CSV_file> [lines_per_window]

    Example:
        python split_csv_into_windows.py motion_data.csv 6000
    """
    if len(sys.argv) < 2:
        print("Usage: python split_csv_into_windows.py <CSV_FILE> [LINES_PER_WINDOW]\n")
        sys.exit(1)

    input_csv_file = sys.argv[1]

    # If user provides a custom lines_per_window, use it; otherwise default to 6000 (1 minute @ 100Hz)
    if len(sys.argv) == 3:
        lines_per_window = int(sys.argv[2])
    else:
        lines_per_window = 1500

    split_csv_into_windows(input_csv_file, lines_per_window)