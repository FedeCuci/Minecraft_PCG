# Introduction

Procedural content generation (PCG) has become a popular technique in
game development, as it enables the creation of diverse and dynamic game
worlds [@Kenny_2021]. PCG uses clever algorithms and automated processes
that can significantly reduce the burden on human designers and allow
for the generation of creative and novel landscapes. In this project, we
investigated the basics of PCG principles using Minecraft. We used the
`gdpc` Python library to interact with Minecraft worlds and automate the
building of various different structures. Given its straightforward
block structure and coordinate system, Minecraft offers a good
environment to practice the basics of PCG.\
The goal of this project is to develop a procedural building algorithm
that generates realistic and aesthetically pleasing houses in Minecraft.
The algorithm should adapt to its environment rather than change it to
accommodate its needs. Moreover, although structures can follow the same
architectural style, they should have a variance component. This means
that each time a structure is created, it should always look slightly
different.\
This report will cover the following key aspects of the project. First,
the methodology used for identifying suitable building locations within
the Minecraft world, with a focus on terrain analysis and \"flatness\"
detection. Second, the techniques employed to introduce variability and
randomness into the building process to make sure that each generated
house is unique. Finally, the challenges encountered during the
development process, including issues related to Minecraft's building
mechanics, coordinate systems, and biome diversity.

# Methods

## Area Selection

The first key step for building a procedurally generated structure in
Minecraft is to find the optimal area for the building process. I tried
several different algorithms to find the \"flatness\" of all the
sub-areas in the provided build area. For this project, I defined
\"flatness\" as \"the absence of abrupt changes in elevation.\"
Therefore, a flat area contains gentle slopes and minimal variations in
height over short distances. The reason for choosing flatness as my
optimal criterion is that it would ensure that I did not have to change
the environment as much.\
A flat area makes it easier for the algorithm to adapt the building
process to the environment when compared to a steeper area. It ensures
that fewer changes will have to be made to the environment to
accommodate a new structure in a realistic manner. Further, a flat area
would ensure that other structures are not already present in the
potential building area. For example, in Minecraft there are villages,
trees, and other structures that should not be built on top of.
Furthermore, even in the real world, it is more realistic to try and
find a flat area to build a house on, rather than complicating the
process and building it on hard terrain, such as mountains or the ocean.

## Water Detection

Detecting water is an important yet simple part of my algorithm. I
decided that my algorithm will not build on water, even if the whole
build area contains just water blocks. In such a case, it will return a
message saying that there is no optimal area to build a structure on. I
thought of different methods to detect water blocks. Although most
methods seemed quite complex, after some trial and error, I noticed that
subtracting `WORLDSLICE.heightmaps[’MOTION_BLOCKING’]` with
`WORLDSLICE.heightmaps[’OCEAN_FLOOR’]` returned a heightmap where any
non-zero number would signify the presence of water. To not build on
water, my algorithm therefore makes sure that no non-zero number is
returned from this heightmap within the coordinates of the optimal area.

## Average Gradient Magnitude

As mentioned, my algorithm determines the optimal area for the building
process based on how flat it is. To accomplish this, I used the average
gradient magnitude, which is a method that measures how much the height
changes from one point to the next in both the `x` and `y` directions.
In Python, the first step is to use `np.gradient()` to calculate the
rate of change of data in an array, in my case the heightmap of the
build area. Then, it calculates the magnitude of the gradient vector at
each point in the heightmap using the Pythagorean theorem to combine the
horizontal `(gx)` and vertical `(gy)`components, providing the overall
steepness. The Pythagorean theorem also removes negative values and
ensures that the gradient magnitude is always positive, representing the
absolute steepness, regardless of direction. Finally, by averaging all
the gradient-magnitude values in the area, it'll calculate the average
steepness of the area.

## Implementation

In practical terms, the algorithm starts by looping through the whole
heightmap provided by the `gdpc` library. The heightmap is given as 2D
`numpy` array, which simplifies calculations as `numpy` offers handy
built-in methods that make operations more abstract. In each iteration
of the nested for loops, the algorithm systematically examines every
possible region of a predetermined size within the larger 2D array. It
moves through the array row by row and column by column, taking each
potential sub-array of the specified dimensions. For example, if we
specify a 10x10 sub-array size on a 50x50 heightmap, the algorithm will
evaluate all 1,681 possible positions where a 10x10 square could be
placed within the larger array. Although this method might be
computationally expensive and not practical for very large build areas,
it is adequate for the given 100x100 build area. A visual representation
of the result of the algorithm can be seen in Figure
[1](#fig:heatmap){reference-type="ref" reference="fig:heatmap"}, where
the left heatmap shows the height difference of each block in the build
area, and the right image displays the optimal area found by the
algorithm.

![Heightmap heatmap](heatmap.png){#fig:heatmap width="1\\linewidth"}

## Rationale for using Flatness

When researching how to best calculate the flatness of an area given a
height map, I found out that there are many ways to calculate the
flatness of an area [@anthropic]. However, I noticed that, in my case, a
'good enough' area will almost certainly be found with a simple
algorithm. Using the Average Gradient Magnitude visually seemed to
provide reliable results, so I decided to stick with it for more
testing. For simplicity, I tested the effectiveness of different
algorithms using a random 2D `numpy` array similar to the heightmap
provided by `gdpc`. To get a better visualization of the results of the
algorithm, I used `matplotlib` to create a heightmap showing the
flattest area in any given build area in Minecraft.

## Preparation the Optimal Area for Building

To minimize the impact on the external environment, my algorithm checks
for the presence of trees in the optimal area and its surroundings. It
does this in the same way that water is detected. It subtracts
`WORLDSLICE.heightmaps[’MOTI`\
`ON_BLOCKING_NO_LEAVES’]` from
`WORLDSLICE.heightmaps[’MOTION_BLOCKING’`\
`]`, where any non-zero number signifies the presence of a leaf block.
In Minecraft, if there are any leaves present, it likely means that
there are trees. Therefore, the algorithm begins to scan each block's
height relative to its neighbors using a 7×7 window centered on the
block. It does this by computing whether said block is more than two
standard deviations away from the median if its neighbor blocks. In my
case, the neighbor blocks are an area of `7x7`. If the center block is
considered to be an outlier, such as the\
When trees are detected in the optimal building location, the algorithm
employs a sophisticated smoothing technique to clear them naturally. It
analyzes each block's height relative to its neighbors using a 7×7
window centered on the block. For each position, it calculates:

1.  The median height of all blocks in the window

2.  The standard deviation of heights in the window

3.  Whether the center block's height is an outlier (more than 2
    standard deviations from the median)

If a block is identified as an outlier, it means that it is likely part
of a tree trunk or other vertical structures. The algorithm then
replaces this height value with the local median height, thereby
creating a smoothed heightmap that represents what the terrain would
look like without trees. This smoothed heightmap is then used to clear
blocks from the natural terrain height up to 20 blocks higher, removing
trees while preserving the natural structure of the environment.

Once the flattest area is calculated, a foundation for the house is
built. The foundation adapts to the terrain surface without removing any
blocks. If needed, the foundation creates a completely flat surface by
placing blocks in the right positions to reach the height of the highest
block in the optimal area. This ensures that a minimum amount of blocks
are used.

## Variability and Randomness

There are several things that add variability and randomness to my
building process. These are:

-   The placement of the house itself within the build area: As
    explained above, an algorithm always finds the flattest area in the
    build area to build the house on

-   The dimensions of the house: the height of the walls, the windows,
    and and the roof is always different

-   The placement of the interiors of the house: The interiors adapt to
    the random size of the house

-   The placement of the garden flowers: Flowers are always placed in a
    random position outside of the house

-   The materials used to make the house: There are 4 different
    palettes/designs for a single house. A random one will be chosen
    each time the house is generated

Together, these factors ensure that each time a house is generated, it
never looks the same. To add randomness and variability in Python, it is
possible to use the random library. The random parameters are hard-coded
in the script and ensure that although the house has variance in its
design, it still remains realistic. Although each individual parameter
has a limited range of variation, their interaction produces
exponentially more possible outcomes. For example, with 4 material
palettes, approximately 4 possible wall heights, and numerous possible
dimensions and placements, the system can generate thousands of unique
house designs. An example of what the houses can look like can be seen
in the figures in the Appendix.

# Challenges

I encountered several challenges during this project. Of course, gdpc
being an unfamiliar library to me, it was at first hard to wrap my head
around how it handled the building mechanics (such as placing, removing,
and loading blocks), its coordinate system, etc. In addition, it was
also difficult to build an aesthetically pleasing house, as I did not
know which materials would look good with each other. However, after
looking at some online examples, it was easy to take inspiration.
[@blockpalettes]\
On top of that, at the beginning, I made the mistake of testing my
structures mainly on one biome, which happened to be the jungle. This
unfortunately led me to \"overfit\" my house to that biome, and it would
not adapt to different environments. This made me lose a lot of time in
the beginning and had to start almost from scratch later on. Testing the
changes in the code itself was also time-consuming. A new build area
always had to be created, and orienting oneself in the Minecraft world
took time.\
Further, there were challenges where LLMs [@anthropic; @openai] came in
useful in brainstorming and helped me solve some specific problems in
the project. An example where AI came in very useful was in helping me
understand how to build the roof using staircases. The technicalities of
using staircases for the roof and making them face in the right
direction were difficult for me, so AI has helped me there. Furthermore,
AI has given me inspiration for different palettes to be used for my
house, alongside online images and video tutorials. Lastly, AI helped me
make visual plots of my algorithm and the heightmaps using matplotlib,
as I was not very familiar with this library.

## Possible Future Improvements

In terms of algorithmic improvements, I believe the algorithm could be
smarter by not building in places where it is to steep. Currently, the
algorithm only avoids water, but it will always build on mountains, no
matter how high the foundation will be. At times, this can make the
house look quite unrealistic. Another option would be to use pillars in
the corner of the house instead of building a complete foundation each
time.\
Finally, to make the interiors of the house even more realistic while
maintaining variance, it is possible to divide the interior into
different rooms in an appropriate way. That way, even though the
location of the rooms would always be random, the furniture inside the
rooms is always appropriate to its respective room. That means that a
bed block and a furnace block should not be in the same room, as it is
not realistic to have cooking gadgets in the bedroom or a bed in the
kitchen.\
Another cool improvement that could be made is to make the house adapt
to its biome. For example, in the \"Ice Spikes\" or \"Ice Plains\"
biomes, the script could make an igloo as a house. In the desert, it
could make a wooden structure that resembles more of a camp. In the
jungle, it could try to create a tree house. There are endless
possibilities when thinking of linking a structure to the respective
biome it's being built on. Because the current script does not adapt the
structure to its biome, it can result in less realistic results.\
Moreover, a key insight that I noticed is that although randomness and
variance create more interesting structures, they often come at the
expense of beliefability. Random structures with many different
materials do not reflect real-world structures, which are more organized
and monotone. That is why I opted to increase the number of parameters
to be randomized rather than increase the range of variance of those
parameters. This helped increase the variance of houses while
maintaining a more realistic look to the structure. One key observation
is the trade-off between randomization and believability. An example of
this is that the walls are never shorter than four blocks. Having walls
where it is not possible to enter the house does not make any sense.
Therefore, I added hardcoded constraints for the range of values walls
can take.\
Lastly, I believe there could be a better garden. Unfortunately, this
was the last thing I worked on, and including a garden proved
challenging, as the algorithm for finding an optimal area did not take
the garden into account. This led to problems with the garden being
built outside of the build area and other problems. However, it would be
possible to add a fence around the house, a path that leads to the
entrance, a pond, etc.

# Conclusion

Overall I found this project to be quite daunting at first, but I noticed
that once I started to work on it, I was able to make slow but steady
progress. For me, it was the right difficulty where I got stuck several
times but was almost always able to figure it out with a satisfactory
result if given time and effort. The procedural building system shows a
reasonable degree of adaptability to its environment and variation in
its features. However, there is room for improvement in terms of
biome-specific architectural styles, better handling of minor
obstructions, and better garden logic.

# Appendix

![House Variation 1](house.png){#fig:house width="0.75\\linewidth"}

![House Variation 2](house2.png){#fig:house2 width="0.75\\linewidth"}

![House Variation 3](house3.png){#fig:house3 width="0.75\\linewidth"}

![House Variation 4 (interior)](interior.png){#fig:interior
width="0.75\\linewidth"}
