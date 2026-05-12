### Name: Ottavio Ficacio
### ID: 261068575

import helperclasses as hc
import glm
import igl

class Geometry:
    def __init__(self, name: str, gtype: str, materials: list[hc.Material]):
        self.name = name
        self.gtype = gtype
        self.materials = materials

    def intersect(self, ray: hc.Ray):
        return hc.Intersection.default()

class Sphere(Geometry):
    def __init__(self, name: str, gtype: str, materials: list[hc.Material], center: glm.vec3, radius: float):
        super().__init__(name, gtype, materials)
        self.center = center
        self.radius = radius

    def intersect(self, ray: hc.Ray):
        # Create intersect code for Sphere

        disc = self.getDiscriminant(ray)
        
        # If discriminant is negative, there is no intersection, so we pass
        if disc < 0:
            return hc.Intersection.default(), hc.Intersection.default()
        
        # Else if discriminant is zero, there is one intersection, find and return it
        elif disc == 0:
            t = -glm.dot(ray.direction, ray.origin - self.center) / glm.dot(ray.direction, ray.direction)
            point = ray.getPoint(t)
            return hc.Intersection(t, self.getNormal(point), point, self.materials[0], "enter"), hc.Intersection(t, self.getNormal(point), point, self.materials[0], "exit")
        # Else the discriminant is positive, so there are two intersections, find both and return them
        else:
            t1 = (-glm.dot(ray.direction, ray.origin - self.center) + glm.sqrt(disc)) / glm.dot(ray.direction, ray.direction)
            t2 = (-glm.dot(ray.direction, ray.origin - self.center) - glm.sqrt(disc)) / glm.dot(ray.direction, ray.direction)
            
            t1_point = ray.getPoint(t1)
            t2_point = ray.getPoint(t2)
            
            # Return the nearer of the two intersections
            if t1 > t2:
                return hc.Intersection(t2, self.getNormal(t2_point), t2_point, self.materials[0], "enter"), hc.Intersection(t1, self.getNormal(t1_point), t1_point, self.materials[0], "exit")
            else:
                return hc.Intersection(t1, self.getNormal(t1_point), t1_point, self.materials[0], "enter"), hc.Intersection(t1, self.getNormal(t2_point), t2_point, self.materials[0], "exit")

        
    # Helper method to get the discriminant for analysis
    def getDiscriminant(self, ray: hc.Ray):
        d = ray.direction
        e = ray.origin
        
        discriminant = (glm.dot(d, e - self.center) ** 2) - (glm.dot(d, d) * (glm.dot(e - self.center, e - self.center) - (self.radius ** 2)))
        return discriminant
    
    # Helper method that returns the unit normal
    def getNormal(self, p: glm.vec3):
        return (p - self.center) / self.radius

class Plane(Geometry):
    def __init__(self, name: str, gtype: str, materials: list[hc.Material], point: glm.vec3, normal: glm.vec3):
        super().__init__(name, gtype, materials)
        self.point = point
        self.normal = normal

    def intersect(self, ray: hc.Ray):
        # Create intersect code for Plane
        
        # Calculate the direction vector of the ray dotted with the normal of the plane
        d_dot_n = glm.dot(ray.direction, self.normal)
        
        # If d.n is 0, there is no intersection so return the default intersection
        if d_dot_n == 0:
            return hc.Intersection.default(), hc.Intersection.default()
        
        # Else, there is an intersection, so calculate the t value 
        t = glm.dot(self.point - ray.origin, self.normal) / d_dot_n
        
        # If t is negative(i.e behind the camera), ignore it and return the default intersection
        if t < 0:
            return hc.Intersection.default(), hc.Intersection.default()
        
        # Get material for this point as described by the assignment specification document
        inter_point = ray.getPoint(t)
        inter_x = inter_point.x % 2
        inter_z = inter_point.z % 2
        if inter_x > 0 and inter_x < 1 and inter_z > 0 and inter_z < 1:
            mat = self.materials[0]
        elif inter_x > 1 and inter_x < 2 and inter_z > 1 and inter_z < 2:
            mat = self.materials[0]
        else:
            mat = self.materials[1]
        
        # Return the intersection of the point
        return hc.Intersection(t, self.normal, inter_point, mat, "enter"), hc.Intersection(t, -self.normal, inter_point, mat, "exit")

class AABB(Geometry):
    def __init__(self, name: str, gtype: str, materials: list[hc.Material], minpos: glm.vec3, maxpos: glm.vec3):
        # dimension holds information for length of each size of the box
        super().__init__(name, gtype, materials)
        self.minpos = minpos
        self.maxpos = maxpos

    def intersect(self, ray: hc.Ray):
        # Create intersect code for Cube
        
        # Get the t values for intersection between all 6 planes that define the box
        t_values = [0, 0, 0, 0, 0, 0] 
                #= [xmin, ymin, zmin, xmax, ymax, zmax]
        for i in range(6):
            # Get the normal of this plane
            normal = glm.vec3(0,0,0)
            normal[i % 3] = 1
            
            if i < 3:
                position = self.minpos
            else:
                position = self.maxpos
            
            
            # Calculate the direction vector of the ray dotted with the normal of the plane
            d_dot_n = glm.dot(ray.direction, normal)
            
            # If d.n is 0, there is no intersection so check if that means the ray is inside the slab or not
            if d_dot_n == 0:
                # If ray is inside the slab:
                if ray.origin[i % 3] > self.minpos[i % 3] and ray.origin[i % 3] < self.maxpos[i % 3]:
                    # Set the min value to be very small
                    if i < 3:
                        t_values[i] = -1000
                    # Set the max value to be very large
                    else:
                        t_values[i] = 1000
                # Else ray is outside of slab, so return the default intersection
                else:
                    return hc.Intersection.default(), hc.Intersection.default()
                
                # Go to next plane
                continue
            
            # Else, there is an intersection, so calculate the t value 
            t = glm.dot(position - ray.origin, normal) / d_dot_n
            
            # Store the t value
            t_values[i] = t
        
        
        # Get tmin and tmax
        tmin = max(min(t_values[0], t_values[3]), min(t_values[1], t_values[4]), min(t_values[2], t_values[5]))
        tmax = min(max(t_values[0], t_values[3]), max(t_values[1], t_values[4]), max(t_values[2], t_values[5]))
        
        # No intersection with box, return default
        if tmax < tmin:
            return hc.Intersection.default(), hc.Intersection.default()
        # Or if intersect is in the wrong direction, return default
        elif tmin < 0:
            return hc.Intersection.default(), hc.Intersection.default()
        # Else, return the intersect found
        else:
            return hc.Intersection(tmin, self.getNormal(tmin, t_values), ray.getPoint(tmin), self.materials[0], "enter"), hc.Intersection(tmax, self.getNormal(tmax, t_values), ray.getPoint(tmax), self.materials[0], "exit")
    
    # Helper function to get the normal of the nearest plane for the given tmin and t_values
    def getNormal(self, t, t_values):
        for i in range(6):
            if t_values[i] == t:
                normal = glm.vec3(0,0,0)
                normal[i%3] = 1 if i >= 3 else -1
                return normal

class Mesh(Geometry):
    def __init__(self, name: str, gtype: str, materials: list[hc.Material], translate: glm.vec3, scale: float,
                 filepath: str):
        super().__init__(name, gtype, materials)
        verts, _, norms, self.faces, _, _ = igl.read_obj(filepath)
        self.verts = []
        self.norms = []
        for v in verts:
            self.verts.append((glm.vec3(v[0], v[1], v[2]) + translate) * scale)
        for n in norms:
            self.norms.append(glm.vec3(n[0], n[1], n[2]))

    def intersect(self, ray: hc.Ray):
        # Create intersect code for Mesh
        
        inter = hc.Intersection.default()
        
        # For each face in the mesh
        for face in self.faces:
            # get vectors for this face
            a = self.verts[face[0]]
            b = self.verts[face[1]]
            c = self.verts[face[2]]
            
            # get normal for this face
            normal = glm.normalize(glm.cross(a - b, b - c))
            
            # check for intersection with plane defined by normal
            d_dot_n = glm.dot(ray.direction, normal)
            
            # if d.n = 0, there is no intersection with the plane so skip to next face
            if d_dot_n == 0:
                continue
            
            # otherwise there is an intersection, so get t and the intersection point
            t = glm.dot(a - ray.origin, normal) / d_dot_n
            p = ray.getPoint(t)
            
            # if t is negative(i.e. behind the camera), ignore it and skip to next face
            if t < 0:
                continue
            
            # Check if point is w/i the triangle
            if glm.dot(glm.cross(b-a, p-a), normal) > 0 and glm.dot(glm.cross(c-b, p-b), normal) > 0 and glm.dot(glm.cross(a-c, p-c), normal) > 0:
                # Create the intersection
                curr_inter = hc.Intersection(t, normal, p, self.materials[0], "enter")
                # If it is, check if this intersection is closer than any other that has been found
                if inter.isDefault():
                    inter = curr_inter
                elif inter.t > curr_inter.t and curr_inter.t > 0:
                    inter = curr_inter
            
        # Return the nearest intersection (if any are found), otherwise returns the default intersection
        return inter, hc.Intersection.default()

class Node(Geometry):
    def __init__(self, name: str, gtype: str, M: glm.mat4, materials: list[hc.Material]):
        super().__init__(name, gtype, materials)        
        self.children: list[Geometry] = []
        self.M = M
        self.Minv = glm.inverse(M)

    def intersect(self, ray: hc.Ray):
        # Create intersect code for Node
        
        # Transform ray to local coords by multiplying by M^-1
        trans_ray, length_scale = ray.transformRay(self.Minv)
        
        inter = hc.Intersection.default()
        back_inter = hc.Intersection.default()
        
        # Check children for intersects
        for child in self.children:
            child_inter, child_back_inter = child.intersect(trans_ray)
            
            # If an intersect was found
            if not child_inter.isDefault():
                # And we have not found another, just store it
                if inter.isDefault():
                    inter = child_inter
                    back_inter = child_back_inter
                # Or, if this intersection is shorter than the other, store it
                elif child_inter.t < inter.t:
                    inter = child_inter
                    back_inter = child_back_inter
            
        # Then, if a hit was found, transform hit info back to world coords and return it
        if not inter.isDefault():
            untrans_inter = inter.transformIntersection(self.M, length_scale)
            untrans_back_inter = back_inter.transformIntersection(self.M, length_scale)
            
            return untrans_inter, untrans_back_inter
        else:
            return hc.Intersection.default(), hc.Intersection.default()
        
class CSG(Geometry):
    def __init__(self, name: str, gtype: str, left, right, operation: str, M: glm.mat4, materials: list[hc.Material]):
        super().__init__(name, gtype, materials)        
        self.left = left
        self.right = right
        self.operation = operation
        self.M = M
        self.Minv = glm.inverse(M)
    
    def intersect(self, ray: hc.Ray):
        # Create intersect code for CSG
        
        # Get the intersection list for the object
        inter_list = CSG.getInterList(self, ray)
        
        # If any intersections were found
        if not inter_list.isEmpty():
            # Return the nearest positive entrance intersection
            for i in range(len(inter_list.intersections)):
                if inter_list.get(i).t > 0 and inter_list.get(i).change == "enter":
                    return inter_list.get(i), inter_list.get(i+1)
        
        # Else if no intersections were found (or no positive entrance intersections were found), return default
        return hc.Intersection.default(), hc.Intersection.default()
    
    @staticmethod
    def getInterList(node, ray: hc.Ray):
        # if the given node is a CSG, we need to get its intersection lists
        if type(node) is CSG:
            # Transform ray to local coords by multiplying by M^-1
            trans_ray, length_scale = ray.transformRay(node.Minv)
            
            # Get intersection lists for left and right child
            left_inter_list = CSG.getInterList(node.left, trans_ray)
            right_inter_list = CSG.getInterList(node.right, trans_ray)
            
            # Do the operation defined by this node
            output_inter_list = CSG.doOperation(left_inter_list, node.operation, right_inter_list)
            
            # If we have found any intersections
            if not output_inter_list.isEmpty():
                # Transform them all out of the local coordinate system
                for i in range(len(output_inter_list.intersections)):
                    inter = output_inter_list.get(i)
                    
                    untrans_inter = inter.transformIntersection(node.M, length_scale)
                    
                    # Replace intersection in list with untransformed version
                    output_inter_list.add(untrans_inter, i)
                    output_inter_list.remove(i+1)

            # Return the intersection list
            return output_inter_list
        # Else the node is a primitive, so create an intersection list
        else:
            min_inter, max_inter = node.intersect(ray)
            inter_list = hc.IntersectionList(min_inter, max_inter)
            return inter_list
    
    # Helper method to call the operation specified on the two given intersection lists
    @staticmethod
    def doOperation(left_list: hc.IntersectionList, operation: str, right_list: hc.IntersectionList):
        match operation:
            case "union":
                output = hc.IntersectionList.union(left_list, right_list)
            case "difference":
                output = hc.IntersectionList.difference(left_list, right_list)
            case "reverse_difference":
                output = hc.IntersectionList.difference(right_list, left_list)
            case "intersection":
                output = hc.IntersectionList.intersection(left_list, right_list)
            case _:
                print("ERROR: invalid operation")
        
        return output