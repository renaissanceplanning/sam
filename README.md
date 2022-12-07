# sam
 Standard Acquisition Methods for commonly used datasets in planning applications

# Required Setup
`sam` utilizes the rpy2 library to interface with R for downloading census and performing some spatial operations.
Currently, there isn't a direct way to reference these libraries from the project environment that is setup by default and the 
below steps are needed to ensure rputils can load the R libraries

1) Install R (download from here: https://cran.r-project.org/bin/windows/base/)
2) Open R terminal and run the following commands:

       install.packages("tigris")
       install.packages("sf")
       install.packages("lwgeom")
       install.packages("tidycensus")

`sam` will now use your system R install as the default when trying to utilize the downloader tools

    