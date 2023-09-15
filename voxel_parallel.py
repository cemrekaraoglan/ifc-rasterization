import pyvista as pv
import numpy as np
from typing import Any, Tuple
import ifcopenshell
from importlib import reload 
import multiprocessing
import ifcopenshell
import ifcopenshell.geom
import time
import vtk
import pyopencl as cl
ifc_file = ifcopenshell.open(r"IFC Files\Project1.ifc")
#ifc_file = ifcopenshell.open(r"IFC Files\Clinic.ifc")
#ifc_file = ifcopenshell.open(r"IFC Files\Duplex.ifc")

def to_vtk_faces(faces : Tuple[tuple]) -> np.ndarray:
    faces=np.array(faces, dtype=np.int16)
    num_insertions = (len(faces) - 1) // 3
    # Generate an array of indices for insertions
    indices = np.arange(3, 3 * (num_insertions + 1), 3)
    indices = np.insert(indices, 0, 0)
    faces = np.insert(faces, indices, 3) 
      # Set up OpenCL context and queue
    platform = cl.get_platforms()[0]
    device = platform.get_devices()[0]
    context = cl.Context([device])
    queue = cl.CommandQueue(context)

    # Transfer data to the device
    faces_buffer = cl.Buffer(context, cl.mem_flags.READ_WRITE, size=faces.nbytes)
    indices_buffer = cl.Buffer(context, cl.mem_flags.READ_ONLY, size=indices.nbytes)
    cl.enqueue_copy(queue, faces_buffer, faces)
    cl.enqueue_copy(queue, indices_buffer, indices)

    # Create and build the OpenCL program
    program = cl.Program(context, """
    __kernel void insert(__global int16* faces, __global int* indices, int num_insertions) {
        int gid = get_global_id(0);
        if (gid < num_insertions) {
            int index = indices[gid];
            faces[index] = 3;
        }
    }
    """).build()

    # Execute the OpenCL kernel
    program.insert(queue, (num_insertions,), None, faces_buffer, indices_buffer, np.int32(num_insertions))

    # Retrieve the data from the device
    cl.enqueue_copy(queue, faces, faces_buffer).wait()

    return faces

def vtk_block_by_building_element(ifc_file):
    building_elements = ifc_file.by_type("IfcBuildingElement")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.APPLY_DEFAULT_MATERIALS, True)
    iterator = ifcopenshell.geom.iterator(settings, ifc_file, multiprocessing.cpu_count())
    multiblock = pv.MultiBlock()
    multiblock_openings = pv.MultiBlock()

    element_information = {} # Dictionary to hold element information
    exclude_list = ["IfcSpace", "IfcOpeningElement"]
    
    if iterator.initialize():
        while True:
            shape = iterator.get()
            if shape.type not in exclude_list:
                element = ifc_file.by_guid(shape.guid)
                        
                faces = shape.geometry.faces
                verts = shape.geometry.verts
                poly_data = pv.PolyData(list(verts), to_vtk_faces(faces))
                multiblock.append(poly_data)
                  
                if element in building_elements:
                #print(element.all_attributes()) --> why doesn't it work?
                        
                    element_information[shape.guid] = {
                    "Geo": poly_data, 
                    "Type": shape.type,
                    "Name": element.Name,
                    "Description": element.Description
                    }


            if not iterator.next():
                break
                
    return multiblock, element_information

def create_uniform_grid(bounds, voxel_size):
    """Create a uniform grid within the given bounds."""
    x = np.arange(bounds[0], bounds[1] + voxel_size, voxel_size)
    y = np.arange(bounds[2], bounds[3] + voxel_size, voxel_size)
    z = np.arange(bounds[4], bounds[5] + voxel_size, voxel_size)
    return pv.StructuredGrid(*np.meshgrid(x, y, z))

def boxes_touch(A, B):
    """
    Check if two 3D bounding boxes touch or overlap.
    
    Parameters:
    - A, B: Tuples representing the bounds of boxes A and B.
      Each tuple should be in the format (xmin, xmax, ymin, ymax, zmin, zmax).
    
    Returns:
    - True if the boxes touch or overlap, otherwise False.
    """
    
    # Check for overlap in the x, y, and z dimensions
    overlap_x = A[0] <= B[1] and A[1] >= B[0]
    overlap_y = A[2] <= B[3] and A[3] >= B[2]
    overlap_z = A[4] <= B[5] and A[5] >= B[4]
    
    # Return True if all dimensions overlap, otherwise False
    return overlap_x and overlap_y and overlap_z
   
def voxelize_space(meshes, voxel_size, mesh_info):
    """Voxelize space and check intersections with given mesh."""
    opening_list = ["IfcDoor", "IfcWindow"]

    grid = create_uniform_grid(meshes.bounds, voxel_size)
    num_points = grid.cell_centers().n_points

    mask = np.zeros(num_points, dtype=bool)
    cell_to_guid = {}

    print(f'Total number of voxels: {num_points}')

    # Set up OpenCL context and queue
    platform = cl.get_platforms()[0]
    device = platform.get_devices()[0]
    context = cl.Context([device])
    queue = cl.CommandQueue(context)

    # Create and build the OpenCL program
    program = cl.Program(context, """
    __kernel void check_intersection(__global float4* mesh_bounds, __global float4* cell_bounds, __global int* mask, __global int* cell_to_guid, int mesh_type, int guid, int num_points) {
        int gid = get_global_id(0);
        if (gid < num_points) {
            float4 mesh_bound = mesh_bounds[gid];
            float4 cell_bound = cell_bounds[gid];
            int overlap_x = mesh_bound.x <= cell_bound.y && mesh_bound.y >= cell_bound.x;
            int overlap_y = mesh_bound.z <= cell_bound.w && mesh_bound.w >= cell_bound.z;
            int overlap_z = mesh_bound.s0 <= cell_bound.s1 && mesh_bound.s1 >= cell_bound.s0;
            if (overlap_x && overlap_y && overlap_z) {
                mask[gid] = 1;
                cell_to_guid[gid] = guid;
            }
        }
    }
    """).build()

    select_enclosed = vtk.vtkSelectEnclosedPoints()
    select_enclosed.SetInputData(grid.cell_centers())

    for guid, mesh_data in mesh_info.items():
        mesh = mesh_data['Geo']
        mesh_type = mesh_data['Type']
        mesh_bounds = np.array(mesh.bounds, dtype=np.float32).reshape(-1, 4)  # Convert bounds to float4 array

        select_enclosed.SetSurfaceData(mesh)
        select_enclosed.Update()

        # Transfer data to the device
        mesh_bounds_buffer = cl.Buffer(context, cl.mem_flags.READ_ONLY, size=mesh_bounds.nbytes)
        mask_buffer = cl.Buffer(context, cl.mem_flags.READ_WRITE, size=mask.nbytes)
        cell_to_guid_buffer = cl.Buffer(context, cl.mem_flags.READ_WRITE, size=cell_to_guid.nbytes)
        cl.enqueue_copy(queue, mesh_bounds_buffer, mesh_bounds)
        cl.enqueue_copy(queue, mask_buffer, mask)
        cl.enqueue_copy(queue, cell_to_guid_buffer, cell_to_guid)

        for i in range(num_points):
            cell = grid.extract_cells(i)
            cell_bounds = np.array(cell.bounds, dtype=np.float32).reshape(-1, 4)  # Convert bounds to float4 array

            # Transfer cell bounds to the device
            cell_bounds_buffer = cl.Buffer(context, cl.mem_flags.READ_ONLY, size=cell_bounds.nbytes)
            cl.enqueue_copy(queue, cell_bounds_buffer, cell_bounds)

            # Execute the OpenCL kernel
            program.check_intersection(queue, (num_points,), None, mesh_bounds_buffer, cell_bounds_buffer, mask_buffer, cell_to_guid_buffer, np.int32(mesh_type), np.int32(guid), np.int32(num_points))

        # Retrieve the data from the device
        cl.enqueue_copy(queue, mask, mask_buffer).wait()
        cl.enqueue_copy(queue, cell_to_guid, cell_to_guid_buffer).wait()

    return grid, mask, cell_to_guid

meshes_all, info = vtk_block_by_building_element(ifc_file)

p = pv.Plotter()
start_time = time.time()
voxel_size = 0.5

# Voxelize the entire space of the combined mesh
grid, mask, cell_info = voxelize_space(meshes_all, voxel_size, info)
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time taken to voxelize: {elapsed_time:.4f} seconds")

# Visualization
p.add_mesh(grid, opacity=0.3, show_edges=True)
p.add_mesh(grid.extract_cells(np.where(mask)[0]), color="red", opacity=0.5)
p.show()