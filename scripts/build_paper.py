import os
import subprocess
import sys

def merge_files(base_dir, output_md):
    """Merges markdown files into a single file."""
    files_to_merge = ["main.md", "references.md", "appendix.md"]
    
    with open(output_md, "w") as outfile:
        for fname in files_to_merge:
            path = os.path.join(base_dir, fname)
            if os.path.exists(path):
                with open(path, "r") as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n")
                    # LaTeX page break for Pandoc
                    outfile.write('\\newpage\n\n')
            else:
                print(f"Warning: {path} not found")
    print(f"Merged Markdown created at {output_md}")

def build_pdf(input_md, output_pdf):
    """Converts Markdown to PDF using Pandoc."""
    # Check if pandoc is installed
    try:
        subprocess.run(["pandoc", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("Error: Pandoc is not installed. Please run 'brew install pandoc'.")
        sys.exit(1)

    # Run pandoc from the paper directory so relative paths (figures/) work
    paper_dir = os.path.dirname(input_md)
    input_filename = os.path.basename(input_md)
    output_filename = os.path.basename(output_pdf)

    cmd = [
        "pandoc",
        input_filename,
        "-o", output_filename,
        "--pdf-engine=pdflatex",
        "--variable", "geometry:margin=1in",
        "--variable", "fontsize=11pt",
        "--number-sections",
        "--toc"
    ]
    
    print(f"Running in {paper_dir}: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, cwd=paper_dir)
        print(f"Successfully generated {output_pdf}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF: {e}")
        sys.exit(1)

def main():
    base_dir = "paper"
    if not os.path.exists(base_dir):
        print(f"Error: Directory '{base_dir}' not found.")
        sys.exit(1)

    # Intermediate merged markdown file
    merged_md = os.path.join(base_dir, "market_forensics_v3_full.md")
    # Final PDF output
    output_pdf = os.path.join(base_dir, "market_forensics_v3.pdf")
    
    merge_files(base_dir, merged_md)
    build_pdf(merged_md, output_pdf)

if __name__ == "__main__":
    main()
