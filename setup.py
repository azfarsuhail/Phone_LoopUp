#!/usr/bin/env python3
"""
Phone Lookup Tool - Installation Script
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the contents of README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else "Phone Lookup Tool"

# Read requirements.txt
def read_requirements():
    requirements_file = this_directory / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, 'r', encoding='utf-8') as f:
            requirements = [line.strip() for line in f 
                          if line.strip() and not line.startswith('#') and not line.strip() == 'tkinter']
        return requirements
    return []

def get_version():
    """Get version from version file or default to 1.0.0"""
    version_file = this_directory / "VERSION"
    if version_file.exists():
        return version_file.read_text().strip()
    return "1.0.0"

setup(
    # Basic Information
    name="phone-lookup-tool",
    version=get_version(),
    description="A desktop application for looking up phone numbers using the Eyecon API and embedding images in Excel files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # Author Information
    author="Azfar Suhail",
    author_email="your.email@example.com",
    url="https://github.com/azfarsuhail/Phone_LoopUp.git",
    
    # Project Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],
    
    # Keywords
    keywords="phone lookup, excel, image embedding, api, desktop application",
    
    # Packages and Dependencies
    packages=find_packages(),
    install_requires=read_requirements(),
    python_requires=">=3.8",
    
    # Entry Points
    entry_points={
        "console_scripts": [
            "phone-lookup-tool=main:main",
        ],
    },
    
    # Include additional files
    include_package_data=True,
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/azfarsuhail/Phone_LoopUp/issues",
        "Source": "https://github.com/azfarsuhail/Phone_LoopUp",
    },
)

if __name__ == "__main__":
    print("Phone Lookup Tool setup script")
    print("To install: pip install .")
    print("To develop: pip install -e .")