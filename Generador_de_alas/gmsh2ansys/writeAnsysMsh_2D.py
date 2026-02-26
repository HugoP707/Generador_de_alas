import numpy as np


def writeAnsysMsh_2D(
   mshFileName,
   node,
   elem,
   total_num_faces,
   faces,
   boundary_elements,
   zone_ids,
   zone_id_names
):
   node_size = node.shape[0]
   fid = open(mshFileName + ".msh", "w")

   fid.write('(0 "Created by G Y SANDESH REDDY , MAYANK CHAUHAN and SHUBHAM SAMANT")\n')
   fid.write('(0 "Part of the research work @ Dr Pardha and Dr Supradeepan Research Group, BITS Hydearbad")\n')

   fid.write("(2 2)\n")
   fid.write('(0 "Grid dimensions:")\n')
   fid.write(f"(10 (0 1 {node_size:02x} 0 3))\n")
   fid.write(f"(12 (0 1 {elem.shape[0] + boundary_elements.shape[0]:02x} 0 0))\n")
   fid.write(f"(13 (0 1 {total_num_faces:02x} 0 0))\n\n\n")

   fid.write(f"(10 (1 1 {node_size:02x}  1 3)(\n")
   for row in node:
      fid.write(f"{row[0]} {row[1]} 0.0\n")
   fid.write("))\n\n")

   face_type = 2
   boundary_type_2 = 2
   boundary_type_1 = 5

   # internal faces
   face_id = 2
   int_faces = faces[faces[:, -1] != 0]
   num_faces_start = 1
   num_faces_end = int_faces.shape[0]

   fid.write(f"(13 ({face_id:02x} {num_faces_start:02x} {num_faces_end:02x} {boundary_type_2} {face_type})\n(\n")
   for row in int_faces:
      fid.write(f"{row[0]:02x} {row[1]:02x} {row[2]:02x} {row[3]:02x}\n")
   fid.write("))\n\n")

   # boundary faces
   for i, zid in enumerate(zone_ids):
      face_id += 1

      boundary_face = boundary_elements[boundary_elements[:, 0] == zid][:, :2]
      boundary_face = np.sort(boundary_face, axis=1)

      # map to faces
      idx = []
      for bf in boundary_face:
         print(np.where((faces[:, :2] == bf).all(axis=1)))
         loc = np.where((faces[:, :2] == bf).all(axis=1))[0][0]
         idx.append(loc)

      boundary_face = faces[idx, :]

      num_faces_start = num_faces_end + 1
      num_faces_end += boundary_face.shape[0]

      fname = zone_id_names[i][1:-1]  # strip quotes

      fid.write(f"(13 ({face_id:02x} {num_faces_start:02x} {num_faces_end:02x} {boundary_type_1} {face_type})\n(\n")
      for row in boundary_face:
         fid.write(f"{row[0]:02x} {row[1]:02x} {row[2]:02x} {row[3]:02x}\n")
      fid.write("))\n\n")

   # elements
   fid.write(f"(12 (1 1 {elem.shape[0]:02x} 1 1)(\n")
   NOE = np.full((elem.shape[0],), elem.shape[1])
   for e in NOE:
      fid.write(f"{e} {e} {e} {e} {e} {e} {e} {e}\n")
   fid.write(")())\n\n")

   # block 39
   fid.write('(39 (1 fluid fluid)())\n')
   face_id = 2
   fid.write(f"(39 ({face_id} interior interior)())\n")

   for i, zid in enumerate(zone_ids):
      face_id += 1
      fname = zone_id_names[i][1:-1]
      fid.write(f"(39 ({face_id} pressure-outlet {fname})())\n")

   fid.close()
