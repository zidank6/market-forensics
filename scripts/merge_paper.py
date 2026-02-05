import os

def merge_files():
    base_dir = "paper"
    output_file = os.path.join(base_dir, "market_forensics_v3_full.md")
    
    files_to_merge = ["main.md", "references.md", "appendix.md"]
    
    with open(output_file, "w") as outfile:
        for fname in files_to_merge:
            path = os.path.join(base_dir, fname)
            if os.path.exists(path):
                with open(path, "r") as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n")
                    # explicit page break for PDF converters often looks like this
                    outfile.write('<div style="page-break-before: always;"></div>\n\n')
            else:
                print(f"Warning: {path} not found")
                
    print(f"Merged file created at {output_file}")

if __name__ == "__main__":
    merge_files()
