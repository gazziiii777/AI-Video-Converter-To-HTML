import re
import pandas as pd
from openpyxl.styles import Font, Alignment
import os

def parse_fact_check_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extract the table data using regex
    table_pattern = re.compile(r'\| (.*?) \| (.*?) \| (.*?) \| (.*?) \| (.*?) \|', re.MULTILINE)
    matches = table_pattern.findall(content)
    
    # Create a DataFrame from the matches
    df = pd.DataFrame(matches, columns=['Claim', 'Source Citation', 'Original Text', 'Accuracy Assessment', 'Notes'])
    
    # Remove any empty rows that might have been captured
    df = df[df['Claim'].str.strip() != '']
    
    return df

def export_to_excel(df_list, sheet_names, output_file):
    # Create a Pandas Excel writer using openpyxl
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
        # Write each dataframe to a separate sheet
        for df, sheet_name in zip(df_list, sheet_names):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Get the workbook and worksheet for styling
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Apply styling
            header_font = Font(bold=True)
            for cell in worksheet[1]:
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.2
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Freeze the header row
            worksheet.freeze_panes = 'A2'

if __name__ == "__main__":
    output_file = 'fact_check_analysis.xlsx'
    df_list = []
    sheet_names = []
    
    # Список конкретных файлов для парсинга
    file_numbers = [9, 13, 17, 21, 25, 29, 32, 36, 40, 44, 48, 52]
    
    for num in file_numbers:
        input_file = f'output_prompt_{num}.txt'
        if not os.path.exists(input_file):
            print(f"File {input_file} not found, skipping...")
            continue
        
        print(f"Parsing {input_file}...")
        try:
            df = parse_fact_check_file(input_file)
            df_list.append(df)
            sheet_names.append(f'Analysis_{num}')
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
    
    if df_list:
        print(f"Exporting to {output_file}...")
        export_to_excel(df_list, sheet_names, output_file)
        print(f"Done! Excel file created with {len(df_list)} sheets:")
        print(", ".join(sheet_names))
    else:
        print("No files were processed. Check if input files exist.")