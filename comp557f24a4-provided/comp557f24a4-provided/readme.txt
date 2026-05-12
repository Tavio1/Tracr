Name: Ottavio Ficaccio
ID: 261068575

I have implemented all the required features outlines in the assignment description, as well as 3 extra features for
objective 11: Area Lights, Depth of Field Blur, and Constructive Solid Geometry.

You can see the example scene of the Area Lights in scenes/AreaLight.json and out/AreaLight.png. The code which implements 
the feature is in helperclasses.py(around line 78), in scene_parser.py(line 76) it takes in the settings for the area light 
from the .json. The implementation generates multiple shadow rays as defined by the samples variable, which have starting
positions which are in the direction defined, and randomly in a radius around the center of the light. Then the intensity of
the light at the given intersection point is scaled by the percent of the samples that actually hit the light (defining how 
"in shadow" that point is). The blending can be improved by taking more samples, and the spread can be increased/decreased
by changing the radius of the area light.


You can see the example scene of the Depth of Field blur in scenes/DOF.json and out/DOF.png. The code which implements
the feature is in scene.py(around line 90), and in scene_parser.py(line 32) is the code that takes in the settings for DOF,
if they are specified in the .json. The implementation gets a focal point (after the Super Sampling step, so both can be 
done at the same time) at a given distance from the ray, generates a random new ray origin using the aperture size, and then
uses that ray as the viewing ray. The tightness of the area of focus can be increased/decreased by changing the aperture, and
the quality of the blending can be improved by taking more samples.


You can see the example scene of the Constructive Solid Geometry in scenes/CSG.json and out/CSG.png. The code that implements
the feature is in geometry.py(line 269) and helperclasses.py(line 159), and in scene_parser.py(line 154) it takes in the 
defintion of the CSG objects from the .json. The implementation uses a helper class called the IntersectionList, which stores
essentially sets of ranges that a ray is intersecting with objects. These IntersectionLists are created recursively for the CSG
object trees, and the class defines static methods to do the set operations(union, difference, intersection) on these ranges,
along with transforming/maintaining acuracy of the intersection information as it changes through the different operations, so 
the visualization in the raytracer maintains its correctness. I also had to change the intersect function for all geometry objects
to return both the entrance intersection and the exit intersection for all the primitive shapes. These are used to define the
IntersectionLists as primitives get combined. 

