start_indices = [0, 0, 0]
end_indices = [15, 15, 1]

# Calculate the total number of cells along each axis
num_cells_x = end_indices[0] - start_indices[0] + 1
num_cells_y = end_indices[1] - start_indices[1] + 1
num_cells_z = end_indices[2] - start_indices[2] + 1

# Calculate the total number of cells in the grid
total_cells = num_cells_x * num_cells_y * num_cells_z

# Generate the list of cell indices
cell_indices = []
for i in range(num_cells_x):
    for j in range(num_cells_y):
        for k in range(num_cells_z):
            cell_index = (start_indices[0] + i) * num_cells_y * num_cells_z + (start_indices[1] + j) * num_cells_z + (start_indices[2] + k)
            cell_indices.append(cell_index)

# Print the list of cell indices
print(cell_indices)
