# IFC to 3D Mesh Conversion and Analysis

This project involves processing IFC (Industry Foundation Classes) files to extract geometric data, create point clouds, and perform rasterization for analysis purposes. The code is written in Python and utilizes several libraries including `pyvista`, `numpy`, `open3d`, `ifcopenshell`, and others.

The algorithm aims to provide a solution to address the efficiency and scalability challenges faced by the Architecture, Engineering, and Construction (AEC) industry when working with large or broken Building Information Modelling (BIM) models missing the required semantic data. The primary objectives of the code are:

- Conversion of IFC Models to 3D Meshes: Utilizes libraries such as Open3D and PyVista to convert Industry Foundation Classes (IFC) files into 3D meshes. This conversion facilitates easier and faster geometric processing and analysis.

- Point Cloud Generation: Transforming the 3D meshes into point clouds, offers a more efficient representation of the model's geometry, which can be crucial for various analyses.

- Rasterization: Creates a 3D grid to check intersections of the meshes with the grid. This is essential for ensuring accurate geometric representation and for tasks like collision detection.

- Optimization of Grid Size: Determines the optimal grid size for representing the IFC model geometry. This ensures that the model's complex geometries are accurately represented, avoiding issues like broken geometries and inaccurate model checking.

- Building Element Analysis: Currently, it fetches concrete elements from the IFC file and calculates their volume, aiding in tasks like Quantity Take-Off (QTO). Under development for further implementations.

- Visualization: The code provides a visualization of the point cloud and the 3D grid, allowing users to visually inspect and verify the processed model.

In essence, this study offers a computational solution to efficiently process, analyze, and visualize large BIM models, addressing the challenges of reliability, performance bottlenecks, and grid size optimization. This contributes to the broader goal of enhancing the utilization of IFC models in the AEC industry.


## Dependencies

- `pyvista`
- `numpy`
- `multiprocessing`
- `ifcopenshell`
- `open3d`
- `pandas`


## Overview

The script performs the following operations:

1. **IFC File Loading**: Loads an IFC file for processing.
2. **Mesh Generation**: Converts the IFC file into 3D meshes using Open3D.
3. **Point Cloud Creation**: Generates a point cloud from the 3D meshes.
4. **Rasterization**: Creates a 3D grid and checks the intersections of the meshes with the grid.
5. **Visualization**: Visualizes the point cloud and the 3D grid using PyVista.
6. **Room Detection**: The function `find_rooms` identifies enclosed spaces within the IFC file based on the processed grid.
7. **Parameter Tuning**: Allows for tuning parameters like cell sizes for different levels of detail in processing.
8. **Quantitative Analysis**: The function `fetch_element_quantities` extracts the number of cells with the same attributes from the IFC file for further analysis.
9. **Batch Processing**: Processes multiple IFC files in a directory and outputs results in a structured format.


## Functions

- `open3d_block_by_element(ifc_file)`: Converts IFC file elements into 3D meshes.
- `create_uniform_grid(bounds, voxel_size)`: Creates a uniform grid within the given bounds.
- `open3d_to_pyvista(point_cloud_o3d)`: Converts an Open3D point cloud to a PyVista point cloud.
- `voxelize_space(bounds, element_information, pcd_list, voxel_size)`: Creates a 3D grid and checks the intersections of the meshes with the grid.
- `get_sampling_points(mesh, voxel_size, points_per_unit_area=120)`: Calculates the number of points to sample based on the mesh size.
- `create_point_cloud(all_meshes, voxel_size)`: Creates a point cloud from a mesh.


## Usage

1. Ensure you have all the required dependencies installed.
2. Update the path to the desired IFC file in the script.
3. Run the script to generate the 3D meshes, and point cloud, and perform the analysis.


## Output

The script will display the visualization of the point cloud and the 3D grid. It will also print the total volume of concrete elements in the IFC file.


## Example

```python
file_name = "IFC Files/02_Duplex.ifc"
results1, results2, grid = process_ifc_file(file_name, x_size=0.1, y_size=0.1, z_size=0.1)
grid_with_rooms = find_rooms(grid, file_name)
