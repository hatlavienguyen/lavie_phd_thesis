# lavie_phd_thesis

## Description
This respository contains the data (i.e., all input palaeo-reconstruciton models, the output data - both preliminary (i.e., during the test phases of the development) and final output) and the Python scripts that associate with the PhD Thesis named "Quantification of palaeo-reconstruction models" by Hoang Anh Tu (Lavie) Ridgway-Nguyen. The main obejctive of this research project is to derive and introduce to a geoscientific community a coherent and semi-automatically workflow to explore any present-day advanced global palaeo-reconstruciton model (also known as a plate tectonic model), extract the kinematic information imbedded in the model, and create kinematic features. Resulting kinematic features include continental amalgamations and plate line kinematic boundaries (i.e., divergent margins, convergent margins, locations of mid-oceanic ridges, pseudo-isochrons, and synthetic oceanic crusts). 
A detailed description of each step (i.e., software tools, specific Python scripts and modules, the input and output data of each step) in the semi-automatic workflow is included in the appendix of each chapter (i.e., from Chapter 2 to Chapter 5) of the thesis document. The document can be found and downloaded from: https://harvest.usask.ca/items/9eda0c7b-b1fc-4ecc-a241-138c3d65010e

## Support
For any support, please feel welcome to directly contact the author - Hoang Anh Tu (Lavie) Nguyen-Ridgway at hoanganhtu.nguyen@usask.ca
If you are interested in the output kinematic line features that we semi-automatically generated for the MER2021 model, please contact Hoang Anh Tu (Lavie) Nguyen-Ridgway at hoanganhtu.nguye@usask.ca

## Basic installing requirement
We used Anaconda to help us setup the Python environment as well as manage all packages for this project. We hence recommend using Anaconda to install Python 3.8 and setup the environment to run all modules. We created the text file called "python_requirement_packages.txt" which contains all required Python packages. After downloading Anaconda, we suggest running the following in the Anaconda Prompt:
    ```conda create --name new_env_name python=3.x #to create the working a new Python environment for the project``` 
    ```pip install -r requirements.txt```

## Example of Python GIS Environment Setup with `uv`. 
I, Hoang Anh Tu Lavie Nguyen-Ridgway, acknowledge the use of GPT Engine Copilot to create the instruction below to install Python and setup a Python working environment by using `uv` 

This guide provides a simple workflow for beginners to install **Python 3.11**, **JupyterLab**, and common GIS/data analysis packages using **uv** instead of Conda.

## Requirements

The environment will include:

- Python 3.11
- JupyterLab
- GeoPandas
- Pandas
- NumPy
- PyProj
- Shapely

---

## 1. Install uv

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm iex"
```

### macOS / Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify installation:

```bash
uv --version
```

---

## 2. Create a Project Folder

Create a folder for your GIS project:

```text
GIS_Project
```

Open a terminal inside that folder.

---

## 3. Initialize the Project

```bash
uv init
```

This creates a basic Python project structure.

---

## 4. Install Python 3.11

```bash
uv python install 3.11
```

Verify available Python versions:

```bash
uv python list
```

---

## 5. Create a Virtual Environment

```bash
uv venv --python 3.11
```

This creates a local virtual environment named:

```text
.venv
```

---

## 6. Activate the Environment

### Windows

```powershell
.venv\Scripts\activate
```

### macOS/Linux

```bash
source .venv/bin/activate
```

The prompt should now show:

```text
(.venv)
```

---

## 7. Install Required Packages

```bash
uv pip install geopandas pandas numpy pyproj shapely jupyterlab
```

This installs all required GIS and data analysis libraries.

---

## 8. Verify the Installation

Start Python:

```bash
python
```

Test the packages:

```python
import geopandas as gpd
import pandas as pd
import numpy as np
import pyproj
import shapely

print("Success!")
```

Exit Python:

```python
exit()
```

---

## 9. Launch JupyterLab

Start JupyterLab:

```bash
jupyter lab
```

A browser window should open automatically.

Create a new notebook:

```text
File → New Notebook → Python 3
```

---

## 10. Test GeoPandas

Run the following code in a notebook cell:

```python
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

df = pd.DataFrame({
    "City": ["Saskatoon", "Regina"],
    "Longitude": [-106.67, -104.62],
    "Latitude": [52.13, 50.45]
})

geometry = [
    Point(xy)
    for xy in zip(df["Longitude"], df["Latitude"])
]

gdf = gpd.GeoDataFrame(
    df,
    geometry=geometry,
    crs="EPSG:4326"
)

gdf
```

Press:

```text
Shift + Enter
```

You should see a GeoDataFrame displayed in the notebook.

---

## Daily Workflow

Whenever you return to the project:

### Activate the Environment

**Windows**

```powershell
.venv\Scripts\activate
```

**macOS/Linux**

```bash
source .venv/bin/activate
```

### Start JupyterLab

```bash
jupyter lab
```

---

## Installing Additional Packages

Add new packages whenever needed:

```bash
uv pip install matplotlib openpyxl pyarrow rtree
```

---

## Recommended Project Structure

```text
GIS_Project/
│
├── .venv/
├── notebooks/
│   └── analysis.ipynb
│
├── data/
│   ├── raw/
│   └── processed/
│
├── outputs/
│
└── pyproject.toml
```

This structure helps keep notebooks, source data, and outputs organized.

---

## Why Use JupyterLab?

For beginners, JupyterLab is often easier than a traditional IDE because it allows you to:

- Run code one cell at a time
- Immediately see results
- Combine code, notes, and visualizations
- Explore data interactively
- Learn Python and GeoPandas more easily

A common beginner-friendly GIS workflow is:

1. Install `uv`
2. Create a Python 3.11 virtual environment
3. Install GeoPandas and related packages
4. Use JupyterLab for analysis and experimentation
5. Move to VS Code later for larger projects



## Contributing
We encourage any feedback and sincerely appreciate for any suggestion to improve various aspect of this workflow.

## Copyright Hoang Anh Tu (Lavie) Nguyen, 2025. All rights reserved.
## Permission to use - same as the thesis which associates with this repository


## Project status
Active



## Acknowledgment
Bruce Eglington - University of Saskatchewan (USASK);
Jean-Christophe Wrobel-Daveau - Halliburton;
Graeme Nicoll - Halliburton;
Samuel Butler - University of Saskatchewan;
Wesley Ridgway - University of Saskatchewan;
Nathaniel Osgood - University of Saskatchewan;
Drew Heasman - University of Saskatchewan;
Dene Tarkyth - University of Saskatchewan;
Kevin Ansdell - University of Saskatchewan;
Alec Aitken - University of Saskatchewan;
John Cannon - University of Sydney;
Other members of the Department of Geological Sciences, Computer Science, and Physics at USASK;
Family and friends;
Use of GPT Engine such as Copilot and Gemini to assist with programming, English grammar and wording 

## License
GNU LESSER GENERAL PUBLIC LICENSE
 Version 2.1, February 1999

For more information, refer to LICENSE

## Project status
Active
