### Name: Ottavio Ficacio
### ID: 261068575

import math
import glm
import numpy as np
import geometry as geom
import helperclasses as hc
from tqdm import tqdm

class Scene:

    def __init__(self,
                 width: int,
                 height: int,
                 jitter: bool,
                 samples: int,
                 dof: bool,
                 focal_length: float,
                 aperture: float,
                 dof_samples: int,
                 eye_position: glm.vec3,
                 lookat: glm.vec3,
                 up: glm.vec3,
                 fov: float,
                 ambient: glm.vec3,
                 lights: list[hc.Light],
                 objects: list[geom.Geometry]
                 ):
        self.width = width  # width of image
        self.height = height  # height of image
        self.aspect = width / height  # aspect ratio
        self.jitter = jitter  # should rays be jittered
        self.samples = samples  # number of rays per pixel
        self.dof = dof # should DOF be created
        self.focal_length = focal_length  # focal length
        self.aperture = aperture  # aperture size
        self.dof_samples = dof_samples  # number of samples for dof
        self.eye_position = eye_position  # camera position in 3D
        self.lookat = lookat  # camera look at vector
        self.up = up  # camera up position
        self.fov = fov  # camera field of view
        self.ambient = ambient  # ambient lighting
        self.lights = lights  # all lights in the scene
        self.objects = objects  # all objects in the scene

    def render(self):

        image = np.zeros((self.height, self.width, 3)) # image with row,col indices and 3 channels, origin is top left

        cam_dir = self.eye_position - self.lookat
        distance_to_plane = 1.0
        top = distance_to_plane * math.tan(0.5 * math.pi * self.fov / 180)
        right = self.aspect * top
        bottom = -top
        left = -right

        # Get eye coordinates
        w = glm.normalize(cam_dir)
        u = glm.normalize(glm.cross(self.up, w))
        v = glm.cross(w, u)
        
        # Get the difference in camera coordinates between each pixel
        diff_x = ((right - left) / self.width)
        diff_y = ((top - bottom) / self.height) 
        
        # Get the offset between each sample
        offset = 1.0 / (self.samples + 1)

        for col in tqdm(range(self.width)):
            for row in range(self.height):
                # Get colours of multiple rays, to average out later
                pixel_colours = []
                
                # Create multiple samples for Super Sampling
                for i in range(self.samples):
                    for j in range(self.samples):
                        # Generate rays
                        pixel_x = left + ((col + (offset * (i + 1))) * diff_x)
                        pixel_y =  top - ((row + (offset * (j + 1))) * diff_y)
                        
                        # Add jitter, if specified
                        if self.jitter == True:
                            pixel_x += (np.random.random() - 0.5) * (diff_x/(self.samples + 1))
                            pixel_y += (np.random.random() - 0.5) * (diff_y/(self.samples + 1))
                        
                        # Get direction
                        direction = glm.normalize(-distance_to_plane * w + pixel_x * u + pixel_y * v)
                        
                        # Implement depth of field
                        focal_point = self.eye_position + direction*self.focal_length  
                        for k in range(self.dof_samples):
                            # Generate random offset
                            dof_offset = glm.vec3(np.random.random()-0.5,np.random.random()-0.5,np.random.random()-0.5) * self.aperture

                            # Get random ray origin using the aperture size
                            ray_origin = self.eye_position + dof_offset
                            
                            # Get the direction to the focal point from this random origin
                            direction = glm.normalize(focal_point - ray_origin)
                            
                            # Create a view ray
                            ray = hc.Ray(ray_origin, direction)
                            
                            # Get the nearest intersection
                            inter = self.getNearestIntersection(ray)
                                
                            # If there is an intersection found for this ray:
                            if not inter.isDefault():
                                # Perform shading computations on the intersection point
                                pixel_colours.append(self.getColour(inter, ray))
                            else:
                                pixel_colours.append(glm.vec3(0, 0, 0))

                # Get average colour for pixel if we are getting multiple samples for each pixel
                colour = self.getAverageColour(pixel_colours)

                image[row, col, 0] = max(0.0, min(1.0, colour.x))
                image[row, col, 1] = max(0.0, min(1.0, colour.y))
                image[row, col, 2] = max(0.0, min(1.0, colour.z))

        return image
    
    # Returns the nearest intersection for the given ray
    def getNearestIntersection(self, ray: hc.Ray):
        intersection = hc.Intersection.default()
        
        # For each object
        for obj in self.objects:
            # Check for an intersection
            temp, ignore = obj.intersect(ray)
            
            # If one is found:
            if not temp.isDefault():
                # And there is no other intersection found yet, store this intersection
                if intersection.isDefault():
                    intersection = temp
                # Or if this intersection is closer than the current one, store this intersection
                elif temp.t < intersection.t:
                    intersection = temp
                # Otherwise do nothing
                
        # Return the nearest intersection found (or default if no intersection found)
        return intersection
    
    # Gets the colour for a given intersection and ray
    def getColour(self, intersection: hc.Intersection, ray: hc.Ray):
        colour = glm.vec3(0, 0, 0)
        
        # Calculate ambient shading
        La = intersection.mat.diffuse * self.ambient
        
        colour += La
        
        # For each light in the scene (sum contribution of each light)
        for light in self.lights:
            
            # Get light intensity
            I = light.getIntensityAt(self, intersection)
            
            # If light has no intensity, can skip the rest and move to the next
            if I == glm.vec3(0,0,0):
                continue
            
            # Get normalized l, the vector pointing towards the light
            l = glm.normalize(light.vector - intersection.position)
            # Get normalized v, the vector pointing towards the camera
            view = -glm.normalize(ray.direction)
            
            # Calculate the diffuse lambertian shading
            Ld = intersection.mat.diffuse * I * glm.max(0, glm.dot(intersection.normal, l))
            
            colour += Ld
            
            # Calculate the blinn-phong shading
            half = (view + l) / glm.length(view + l)
            
            Ls = intersection.mat.specular * I * (glm.max(0, glm.dot(intersection.normal, half)) ** intersection.mat.shininess)
            
            colour += Ls
            
        # Return colour for given ray and intersection
        return colour
    
    def getAverageColour(self, colours):
        # Average out all the colours in the array passed in
        output = glm.vec3(0,0,0)
        for colour in colours:
            output += colour
        output /= len(colours)
        
        return output