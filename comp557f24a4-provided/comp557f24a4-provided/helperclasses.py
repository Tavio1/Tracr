### Name: Ottavio Ficacio
### ID: 261068575

import glm
import numpy as np

class Ray:
    def __init__(self, o: glm.vec3, d: glm.vec3):
        self.origin = o
        self.direction = d

    def getDistance(self, point: glm.vec3):
        return glm.length(point - self.origin)

    def getPoint(self, t: float):
        return self.origin + self.direction * t
    
    # Returns the ray transformed by a given matrix
    def transformRay(self, M: glm.mat4):
        
        # If the matrix is the identity, skip doing all the calculations
        if M == glm.mat4():
            return self, 1
        
        # Create and return a new ray that is this ray transformed by the given matrix
        trans_ray_point = (M * glm.vec4(self.origin.x, self.origin.y, self.origin.z, 1)).xyz
        trans_ray_dir = (M * glm.vec4(self.direction.x, self.direction.y, self.direction.z, 0)).xyz
        trans_ray = Ray(trans_ray_point, glm.normalize(trans_ray_dir))
        
        # Also returns the length scale in the direction of the ray
        length_scale = glm.length(trans_ray_dir) / glm.length(self.direction)

        return trans_ray, length_scale

class Material:
    def __init__(self, name: str, diffuse: glm.vec3, specular: glm.vec3, shininess: float):
        self.name = name
        self.diffuse = diffuse      # kd diffuse coefficient
        self.specular = specular    # ks specular coefficient
        self.shininess = shininess  # specular exponent        

class Light:
    def __init__(self, ltype: str, name: str, colour: glm.vec3, vector: glm.vec3, attenuation: glm.vec3, direction: glm.vec3, radius: int, samples: int):
        self.name = name
        self.type = ltype       # type is either "point" or "directional"
        self.colour = colour    # colour and intensity of the light
        self.vector = vector    # position, or normalized direction towards light, depending on the light type
        self.attenuation = attenuation # attenuation coeffs [quadratic, linear, constant] for point lights
        self.direction = direction # Direction of area light
        self.radius = radius # Radius of area light
        self.samples = samples # Number of samples for the area light
        
    # Returns the light intensity for the given intersection point
    def getIntensityAt(self, scene, intersection):
        if 0 > glm.dot(intersection.normal, glm.normalize(self.vector - intersection.position)):
            return glm.vec3(0,0,0)
        
        if self.type == "point":
            # Compute shadow ray (adding a small bias in the process)
            shadowRay = Ray(intersection.position + (0.001*intersection.normal), glm.normalize(self.vector - intersection.position))
            
            shadowInter = Intersection.default()
            
            # Check for any intersection 
            for obj in scene.objects:
                if shadowInter.isDefault() or shadowInter.t < 0:
                    shadowInter, ignore = obj.intersect(shadowRay)
                else:
                    break
            
            # If there is any intersection, don't calculate or include this light in the lighting calculation
            if not shadowInter.isDefault() and shadowInter.t > 0 and shadowRay.getDistance(shadowInter.position) < shadowRay.getDistance(self.vector):
                return glm.vec3(0,0,0)
            
            dist = glm.length(intersection.position - self.vector) # Get distance from light
            return self.colour / (self.attenuation.z + self.attenuation.y * dist + self.attenuation.x * (dist*dist))
        if self.type == "area":
            
            # Get info for the coordinate system defined by the area light
            coord_w = glm.vec3(1,0,0) if self.direction != glm.vec3(1,0,0) else glm.vec3(0,1,0)
            coord_u = glm.normalize(coord_w - (glm.dot(coord_w, self.direction) * self.direction))
            coord_v = glm.cross(self.direction, coord_u)
            
            hits = 0
            
            # Get the number of random samples that do hit the light
            for i in range(self.samples):
                # Create random point on the area light to test
                theta = np.random.randint(0, 359)
                scalar = np.random.random() * self.radius
                x_2d = scalar * glm.cos(theta)
                y_2d = scalar * glm.sin(theta)
                
                offset = x_2d * coord_u + y_2d * coord_v 
                
                sample_point = self.vector + offset
                
                # Compute shadow ray (adding a small bias in the process)
                shadowRay = Ray(intersection.position + (0.001*intersection.normal), glm.normalize(sample_point - intersection.position))
                
                shadowInter = Intersection.default()
                
                # Check for any intersection 
                for obj in scene.objects:
                    if shadowInter.isDefault() or shadowInter.t < 0:
                        shadowInter, ignore = obj.intersect(shadowRay)
                    else:
                        break
                
                # If there is any intersection, count a hit
                if not shadowInter.isDefault() and shadowInter.t > 0 and shadowRay.getDistance(shadowInter.position) < shadowRay.getDistance(self.vector):
                    hits += 1
            
            # Get distance from the light
            dist = glm.length(intersection.position - self.vector) 
            
            # Get attenuated intensity using distance
            attenuated_intensity = self.colour / (self.attenuation.z + self.attenuation.y * dist + self.attenuation.x * (dist*dist))
            
            # Scale intensity based on proportion of samples that actually hit the light
            
            return attenuated_intensity * ((self.samples - hits) / self.samples)
        else:
             self.colour

class Intersection:
    
    def __init__(self, t: float, normal: glm.vec3, position: glm.vec3, material: Material, change: str):
        self.t = t
        self.normal = normal
        self.position = position
        self.mat = material
        self.change = change
    
    @staticmethod
    def default(): # create an empty intersection record with t = inf
        return Intersection(t=float("inf"), normal=None, position=None, material=None, change="")
    
    # Helper method to tell if this Intersection is the default one
    def isDefault(self):
        return self.t == float("inf")
    
    # Returns a transformed intersection by the given matrix
    def transformIntersection(self, M: glm.mat4, length_scale: float):
        # If the matrix is the identity, skip doing all the calculations
        if M == glm.mat4():
            return self
        
        # Otherwise transform this intersection by the matrix and return it
        trans_inter_norm = glm.normalize(M * glm.vec4(self.normal.x, self.normal.y, self.normal.z, 0).xyz)
        trans_inter_pos = (M * glm.vec4(self.position.x, self.position.y, self.position.z, 1)).xyz
        trans_t = self.t / length_scale
        trans_inter = Intersection(trans_t, trans_inter_norm, trans_inter_pos, self.mat, self.change)
        
        return trans_inter

# Helper class for managing the intersections for a constructive solid geometry node
class IntersectionList:
    def __init__(self, min_inter=None, max_inter=None):
        self.intersections = []
        
        if not min_inter == None:
            if not min_inter.isDefault():
                self.intersections.append(min_inter)
                self.intersections.append(max_inter)
    
    def isEmpty(self):
        return len(self.intersections) == 0
    
    # Adds an intersection to the list, at the given index or at the end by default
    def add(self, intersection: Intersection, index=-1):
        if index == -1:
            self.intersections.append(intersection)
        else:        
            self.intersections.insert(index, intersection)
    
    # Sorts the list in order of ascending t values
    def sort(self):
        self.intersections.sort(key=lambda x: x.t)
    
    # Gets the intersection at the given index or the first one by default
    def get(self, index=0):
        return self.intersections[index]
    
    # Removes the intersection at the given index, or the last one by default
    def remove(self, index=-1):
        self.intersections.pop(index)
    
    # Static method that returns an intersection list that is the mathematical union operator for two intersection lists
    @staticmethod
    def union(left, right):
        temp = IntersectionList()
        
        # Add all intersections from the left
        for intersection in left.intersections:
            temp.add(intersection)
        
        # Add all intersections from the right
        for intersection in right.intersections:
            temp.add(intersection)
            
        # Sort the intersection list
        temp.sort()
        
        indices_to_keep = []
        
        stack = []
        
        # For each intersection in the list, create a stack tracking entrances and exits
        for i in range(len(temp.intersections)):
            if temp.get(i).change == "enter":
                # If stack is empty, this is an absolute entrance, so keep it
                if len(stack) == 0:
                    indices_to_keep.append(i)
                stack.append(i)
            elif temp.get(i).change == "exit":
                # If stack will be empty after this, this is an absolute exit, so keep it
                if len(stack) == 1:
                    indices_to_keep.append(i)
                stack.pop()
            else:
                print("ERROR: Invalid Change for Intersection")
            
        union = IntersectionList()
        
        for i in indices_to_keep:
            union.add(temp.get(i))
            
        return union
    
    
    # Static method that returns an intersection list that is the mathematical difference operator for two intersection lists
    @staticmethod
    def difference(left, right):
        
        # If left is empty return empty(by returning left), or if right is empty return left
        if left.isEmpty() or right.isEmpty():
            return left
        
        difference = IntersectionList()
        
        # Get create indexes to count across each list in order
        i,j = 0,0
        
        leftIter = left.get(i)
        rightIter = right.get(j)
        
        adding = False
        subtracting = False
        
        while i+j < len(left.intersections)+len(right.intersections):
            # if left is next in sorted order
            if (leftIter.t < rightIter.t or not j < len(right.intersections)) and i < len(left.intersections):
                # Set adding if we are entering
                if leftIter.change == "enter":
                    # If we were not adding and are not subtracting, save this as an absolute entrance
                    if not adding and not subtracting:
                        difference.add(leftIter)
                    adding = True
                # Stop adding if we are exiting
                elif leftIter.change == "exit":
                    # If we were adding and are not subtracting, save this as an absolute exit
                    if adding and not subtracting:
                        difference.add(leftIter)
                    adding = False
                
                # Iterate
                i += 1
                if i != len(left.intersections):
                    leftIter = left.get(i)
            # else right is next in sorted order
            else:
                # Start subtracting if we are entering
                if rightIter.change == "enter":
                    # If we were not subtracting and are adding, save this as an exit
                    if not subtracting and adding:
                        difference.add(Intersection(rightIter.t, -rightIter.normal, rightIter.position, rightIter.mat, "exit")) 
                    subtracting = True
                # Stop subtracting if we are exiting
                elif rightIter.change == "exit":
                    # If we were subtracting and are adding, save this as an entrance
                    if subtracting and adding:
                        difference.add(Intersection(rightIter.t, -rightIter.normal, rightIter.position, rightIter.mat, "enter"))
                    subtracting = False
        
                
                # Iterate
                j += 1
                if j != len(right.intersections):
                    rightIter = right.get(j)
        
        return difference
    
    
    # Static method that returns an intersection list that is the mathematical intersection operator for two intersection lists
    @staticmethod
    def intersection(left, right):
        
        #If either are empty, return empty
        if left.isEmpty() or right.isEmpty():
            return IntersectionList()
        
        intersection = IntersectionList()
        
        # Get create indexes to count across each list in order
        i,j = 0,0
        
        leftIter = left.get(i)
        rightIter = right.get(j)
        
        leftExists = False
        rightExists = False
        
        while i+j < len(left.intersections)+len(right.intersections):
            # if left is next in sorted order
            if (leftIter.t < rightIter.t or not j < len(right.intersections)) and i < len(left.intersections):
                # Set leftExists if we are entering
                if leftIter.change == "enter":
                    # If left didn't exist and right does, save this as an entrance
                    if not leftExists and rightExists:
                        intersection.add(leftIter)
                    leftExists = True
                # Set not leftExists if we are exiting
                elif leftIter.change == "exit":
                    # If left did exist and right does, save this as an exit
                    if leftExists and rightExists:
                        intersection.add(leftIter)
                    leftExists = False
                
                # Iterate
                i += 1
                if i != len(left.intersections):
                    leftIter = left.get(i)
            # else right is next in sorted order
            else:
                # Set rightExists if we are entering
                if rightIter.change == "enter":
                    # If right didn't exist and left does, save this as an entrance
                    if not rightExists and leftExists:
                        intersection.add(rightIter) 
                    rightExists = True
                # Set not rightExists if we are exiting
                elif rightIter.change == "exit":
                    # If right did exist and left does, save this as an exit
                    if rightExists and leftExists:
                        intersection.add(rightIter)
                    rightExists = False
        
                
                # Iterate
                j += 1
                if j != len(right.intersections):
                    rightIter = right.get(j)
        
        return intersection
        