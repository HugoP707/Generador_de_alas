import numpy as np

from writeAnsysMsh_2D import writeAnsysMsh_2D


def Gmsh2Ansys_2D(gmshFileName, ansysFileName):
   # Open gmsh file
   fileName = gmshFileName + ".msh"
   fid = open(fileName, "r")

   GmshMeshFileFormatFlag = 0
   GmshPhysicalNameFlag = 0
   GmshNodesFlag = 0
   domain_dimension = 0

   nodes = []

   nodes_list = []
   elements_list = []
   zone_ids = []
   zone_id_names = []

   while True:
      xp = fid.readline()
      if xp == "":
         break
      xp = xp.strip()

      # MeshFormat
      if xp == "$MeshFormat":
         GmshMeshFileFormatFlag = 1
         fid.readline()  # version
         ## Gmsh lo genera en una misma linea (ahora por lo menos)
         #fid.readline()  # file-type
         #fid.readline()  # size

      # Physical names
      if xp == "$PhysicalNames":
         if GmshMeshFileFormatFlag != 1:
               raise Exception("Invalid Gmsh file: MeshFormat not found")

         GmshPhysicalNameFlag = 1
         no_of_names = int(fid.readline())

         for _ in range(no_of_names):
               parts = fid.readline().split()
               print(parts)
               current_dimension = int(parts[0])
               domain_dimension = max(domain_dimension, current_dimension)
               zone_id = int(parts[1])
               boundary_name = parts[2]


               if domain_dimension == 3:
                  raise Exception("Use Gmsh2Ansys_3D for 3D meshes")

               if current_dimension == 2:
                  pass

               zone_ids.append(zone_id)
               zone_id_names.append(boundary_name)

      # Nodes
      if xp == "$Nodes":
         if GmshPhysicalNameFlag != 1:
               raise Exception("Invalid Gmsh file: PhysicalNames missing")

         GmshNodesFlag = 1
         no_nodes = int(fid.readline().strip())
         previousNodes_num = 0
         i = 0

         while i < no_nodes:
            text = fid.readline()
            if text == "":
               break  # EOF safety

            if text.strip() == "":
               continue  # skip blank lines

            text_node = np.fromstring(text, sep=' ')
            Nodes_num = len(text_node)

            if Nodes_num == 0:
               continue

            if previousNodes_num == 0:
               previousNodes_num = Nodes_num

            elif Nodes_num > previousNodes_num:
               extra_cols = Nodes_num - previousNodes_num
               if len(nodes) > 0:
                     nodes = np.hstack([nodes, np.zeros((nodes.shape[0], extra_cols))])
               previousNodes_num = Nodes_num

            # construct a full row
            row = np.zeros(previousNodes_num)
            row[:Nodes_num] = text_node

            if len(nodes) == 0:
               nodes = row.reshape(1, -1)
            else:
               nodes = np.vstack([nodes, row])

            i += 1
      # Elements
      if xp == "$Elements":
         if GmshNodesFlag != 1:
               raise Exception("Invalid Gmsh file: Nodes before Elements")

         no_elements = int(fid.readline())
         for _ in range(no_elements):
               line = fid.readline().strip()
               if not line:
                  continue
               data = list(map(int, line.split()))
               elem_type = data[1]
               ntags = data[2]
               start_nodes = 3 + ntags
               elem_nodes = data[start_nodes:]
               # MATLAB stores: [elem-type, node-list...]
               elements_list.append([elem_type] + elem_nodes)

   fid.close()

   #nodes = np.array(nodes_list, dtype=float)
   # Pad elements so NumPy can store them
   max_len = max(len(r) for r in elements_list)
   elements_padded = [r + [0] * (max_len - len(r)) for r in elements_list]
   elements = np.array(elements_padded, dtype=int)

   #node = nodes[:, 1:]      # drop column 0
   print(nodes.shape)
   node = nodes[:, 1:]  # drop gmsh IDs, keep x,y

   # Extract fluid zone (only one zone_id assumed)
   zone_id = zone_ids[-1]
   elemF = elements[elements[:, 0] == zone_id, 1:]
   #elemF2 = elements[elements[:, 0] == zone_id][:, 1:]
   #print(elemF == elemF2)
   print(elemF.shape)
   print(elements[0])
   print(np.sort(np.unique(elemF)))
   print(np.sort(np.unique(elemF), 0).shape)
   print(node.shape)
   nodeF = node[np.sort(np.unique(elemF), 0), :]

   I_F = elemF.flatten()
   unique_nodes = np.sort(np.unique(I_F))
   MAPf = np.zeros((nodeF.shape[0] + 1,), dtype=int)

   for i, old in enumerate(unique_nodes):
      MAPf[old] = i + 1

   elemF = MAPf[elemF]

   # Build edges
   nF = elemF.shape[0]
   edgeF = np.vstack([
      elemF[:, [0, 1]],
      elemF[:, [1, 2]],
      np.column_stack([elemF[:, 2], elemF[:, 0]])
   ])

   # Sorted edges
   sorted_edgeF = np.sort(edgeF, axis=1)

   # MATLAB equivalent of:
   # [C, ia, ic] = unique(sorted_edgeF,'rows','first')
   _, idx_first, ic = np.unique(sorted_edgeF, axis=0,
                              return_index=True,
                              return_inverse=True)

   # MATLAB 'last'
   _, idx_last_rev, ic_rev = np.unique(sorted_edgeF[::-1], axis=0,
                                       return_index=True,
                                       return_inverse=True)
   idx_last = (sorted_edgeF.shape[0] - 1) - idx_last_rev

   # For each unique row, check if repeated
   internal_unique = idx_first != idx_last

   # Allocate output (one per original row)
   elements_sharing_edgeF = np.zeros((len(sorted_edgeF), 2), dtype=int)

   # Fill using ic (inverse mapping)
   for i in range(len(sorted_edgeF)):
      unique_id = ic[i]              # which unique row this row corresponds to
      if internal_unique[unique_id]: # internal edge?
         e1 = idx_first[unique_id]
         e2 = idx_last[unique_id]
         elements_sharing_edgeF[i] = [e1 + 1, e2 + 1]


   Faces = np.hstack([
      sorted_edgeF,
      elements_sharing_edgeF
   ])

   # Unique rows
   Faces = np.unique(Faces, axis=0)
   print(Faces)
   # Boundary elements
   boundary_elements = elements[elements[:, 0] != zone_id][:, 1:]

   total_num_Faces = Faces.shape[0]

   writeAnsysMsh_2D(
      ansysFileName,
      nodeF,
      elemF,
      total_num_Faces,
      Faces,
      boundary_elements,
      zone_ids,
      zone_id_names
   )


Gmsh2Ansys_2D("gmsh", "ansys.msh")