import pickle

import requests
import cv2
import pandas as pd
import rasterio
import numpy as np
import json
import subprocess

# from osgeo import osr
#
# Retrieve an image using rasdaman
service_endpoint = "https://ows.rasdaman.org/rasdaman/ows"

# Parameters
threshold = 0.9
output_format = "image/tiff"
output_file = "query_result.tiff"

# CRS: 32631
# Sample: https://www.google.com/maps/@50.7240279,9.0168918,12z
query = '''
for $c in (S2_L2A_32631_B08_10m),
    $d in (S2_L2A_32631_B04_10m)

let $cutOut := [ ansi( "2021-04-09" ), E( 670000:679000 ), N( 4990220:4993220 ) ]
return
  encode( (

      (((float) $c - $d) / ((float) $c + $d)) [ $cutOut ] > {thr}
 ) * 255

  , "{outfrmt}")
'''.format(thr=threshold, outfrmt=output_format)

response = requests.post(service_endpoint, data = {'query': query}, verify=False)

# Save the response to a picture
print("Convert to tiff")
with open(output_file, "wb") as f:
    f.write(response.content)

# Get the jpeg image
query2 = '''
for $c in (S2_L2A_32631_B08_10m),
    $d in (S2_L2A_32631_B04_10m)

let $cutOut := [ ansi( "2021-04-09" ), E( 670000:679000 ), N( 4990220:4993220 ) ]
return
  encode( (

      (((float) $c - $d) / ((float) $c + $d)) [ $cutOut ] > {thr}
 ) * 255

  , "{outfrmt}")
'''.format(thr=threshold, outfrmt="image/jpeg")

response = requests.post(service_endpoint, data = {'query': query2}, verify=False)

# Save the response to a picture
print("Convert to jpeg")
with open("query_result.jpeg", "wb") as f:
    f.write(response.content)

# Open the two files
im = cv2.imread("query_result.jpeg", cv2.IMREAD_GRAYSCALE) # Machine Visio
src = rasterio.open("query_result.tiff") # Coordinates

# Converting image to a binary image
# (black and white only image).
_, matrix = cv2.threshold(im, 110, 255,
                         cv2.THRESH_BINARY)

data2 = np.where(matrix == 255)
x2 = []
y2 = []

for i in range(data2[0].size):
    x2.append(data2[0][i])
    y2.append(data2[1][i])

data3 = list(zip(x2, y2))

pdData = pd.DataFrame(data3, columns =['x', 'y'])

from sklearn.cluster import DBSCAN
# cluster the data into five clusters
dbscan = DBSCAN(eps = 8, min_samples = 4).fit(pdData) # fitting the model
labels = dbscan.labels_ # getting the labels

unique_labels = np.unique(labels)

ourDict = {}

for i in range(unique_labels.size):
    ourDict[i] = {}
    ourDict[i]["Centroid"] = pdData[labels == unique_labels[i]].mean(0)
    ourDict[i]["Points"] = pdData[labels == unique_labels[i]]
    # With coordinates
    xs, ys = rasterio.transform.xy(src.transform, ourDict[i]["Centroid"][0], ourDict[i]["Centroid"][1])
    xsP, ysP = rasterio.transform.xy(src.transform, ourDict[i]["Points"]["x"], ourDict[i]["Centroid"]["y"])

    ourDict[i]["CentroidCoord"] = [xs, ys]

    # Get the coordinates of the centroid
    cent1 = ourDict[i]["CentroidCoord"][0]
    cent2 = ourDict[i]["CentroidCoord"][1]

    cmd = 'echo {} {} | gdaltransform -s_srs EPSG:32631 -t_srs EPSG:4326'.format(cent1, cent2)
    out = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").split()

    coordPoints = list(zip(xsP, ysP))
    ourDict[i]["PointsCoord"] = coordPoints

    coordPointsTrans = []

    for j in range(coordPoints.__len__()):
        cmd = 'echo {} {} | gdaltransform -s_srs EPSG:32631 -t_srs EPSG:4326'.format(coordPoints[j][0], coordPoints[j][1])
        out = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").split()

        coordPointsTrans.append([float(out[0]), float(out[1])])

    # coordPointsTrans.append([float(out[0]), float(out[1])])

    ourDict[i]["CentroidCoordTrans"] = [float(out[0]), float(out[1])]
    ourDict[i]["PointsCoordTrans"] = coordPointsTrans

with open('saved_dictionary.pkl', 'wb') as f:
    pickle.dump(ourDict, f)

np.save('points_centroids.npy', ourDict)


# with open(filename, 'wb') as outfile:
#     json.dump(data, outfile)

print()

