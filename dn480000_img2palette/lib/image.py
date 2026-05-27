"""
Helper functions for image processing

The color space conversion functions are modified from functions of the
Python package scikit-image, https://github.com/scikit-image/scikit-image.
scikit-image has the following license.

Copyright (C) 2019, the scikit-image team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

 1. Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.
 3. Neither the name of skimage nor the names of its contributors may be
    used to endorse or promote products derived from this software without
    specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""

from PIL import Image
import numpy as np
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import pairwise_distances
import requests
from io import BytesIO
import os

from dotenv import load_dotenv

load_dotenv()

sls_stage = os.getenv("SLS_STAGE")

if sls_stage == 'local':
    import plotly.graph_objects as go

default_k = 4

xyz_ref_white = np.asarray((0.95047, 1.0, 1.08883))

xyz_from_rgb = np.array(
    [
        [0.412453, 0.357580, 0.180423],
        [0.212671, 0.715160, 0.072169],
        [0.019334, 0.119193, 0.950227],
    ]
)

rgb_from_xyz = np.linalg.inv(xyz_from_rgb)


def rgb2xyz(rgb_arr):
    """
    Convert colur from RGB to CIE 1931 XYZ

    Parameters
    ----------
    rgb_arr: ndarray
        Color in RGB
    
    Returns
    ------
    xyz_arr: ndarray
        Color in CIE 1931 XYZ
    
    """
    xyz_arr = np.copy(rgb_arr)
    mask = xyz_arr > 0.04045
    xyz_arr[mask] = np.power((xyz_arr[mask] + 0.055) / 1.055, 2.4)
    xyz_arr[~mask] /= 12.92
    return xyz_arr @ np.transpose(xyz_from_rgb)


def xyz2lab(xyz_arr):
    """
    Convert colur from CIE 1931 XYZ to CIE 1976 L*a*b*

    Parameters
    ----------
    xyz_arr: ndarray
        Color in CIE 1931 XYZ
    
    Returns
    ------
    lab_arr: ndarray
        Color in CIE 1976 L*a*b*
    
    """
    lab_arr = np.copy(xyz_arr) / xyz_ref_white
    mask = lab_arr > 0.008856
    lab_arr[mask] = np.cbrt(lab_arr[mask])
    lab_arr[~mask] = 7.787 * lab_arr[~mask] + 16.0 / 116.0
    x, y, z = lab_arr[:, 0], lab_arr[:, 1], lab_arr[:, 2]
    L = (116.0 * y) - 16.0
    a = 500.0 * (x - y)
    b = 200.0 * (y - z)
    return np.transpose(np.asarray((L, a, b)))


def lab2xyz(lab_arr):
    """
    Convert colur from CIE 1976 L*a*b* to CIE 1931 XYZ

    Parameters
    ----------
    lab_arr: ndarray
        Color in CIE 1976 L*a*b*
    
    Returns
    ------
    xyz_arr: ndarray
        Color in CIE 1931 XYZ
    
    """
    L, a, b = lab_arr[:, 0], lab_arr[:, 1], lab_arr[:, 2]
    y = (L + 16.0) / 116.0
    x = (a / 500.0) + y
    z = y - (b / 200.0)
    if np.any(z < 0):
        invalid = np.nonzero(z < 0)
        warn(
            "Color data out of range: Z < 0 in %s pixels" % invalid[0].size,
            stacklevel=2,
        )
        z[invalid] = 0
    xyz_arr = np.transpose(np.asarray((x, y, z)))
    mask = xyz_arr > 0.2068966
    xyz_arr[mask] = np.power(xyz_arr[mask], 3.0)
    xyz_arr[~mask] = (xyz_arr[~mask] - 16.0 / 116.0) / 7.787
    # rescale to the reference white (illuminant)
    xyz_arr *= xyz_ref_white
    return xyz_arr


def xyz2rgb(xyz_arr):
    """
    Convert colur from CIE 1931 XYZ to RGB

    Parameters
    ----------
    xyz_arr: ndarray
        Color in CIE 1931 XYZ
    
    Returns
    ------
    rgb_arr: ndarray
        Color in RGB
    
    """
    rgb_arr = xyz_arr @ np.transpose(rgb_from_xyz)
    mask = rgb_arr > 0.0031308
    rgb_arr[mask] = 1.055 * np.power(rgb_arr[mask], 1 / 2.4) - 0.055
    rgb_arr[~mask] *= 12.92
    rgb_arr = np.clip(rgb_arr, 0, 1)
    return rgb_arr


def rgb2lab(rgb_arr):
    """
    Convert colur from RGB to CIE 1976 L*a*b*

    Parameters
    ----------
    rgb_arr: ndarray
        Color in RGB
    
    Returns
    -------
    lab_arr: ndarray
        Color in CIE 1976 L*a*b*
    
    """
    return xyz2lab(rgb2xyz(rgb_arr))


def lab2rgb(lab_arr):
    """
    Convert colur from CIE 1976 L*a*b* to RGB

    Parameters
    ----------
    lab_arr: ndarray
        Color in CIE 1976 L*a*b*
    
    Returns
    ------
    rgb_arr: ndarray
        Color in RGB
    
    """
    return xyz2rgb(lab2xyz(lab_arr))


def get_lab_data(im):
    """
    Convert colur from CIE 1976 L*a*b* to RGB

    Parameters
    ----------
    im: Image
        Image to create palette
    
    Returns
    ------
    lab_arr: ndarray
        Color in CIE 1976 L*a*b*
    
    """
    img_size = 150, 150
    im.thumbnail(img_size)
    pixel_rgb = np.asarray(im)
    # Range of RGB in Pillow is [0, 255], that in skimage is [0, 1]
    pixel_lab = rgb2lab(pixel_rgb.reshape(-1, pixel_rgb.shape[-1]) / 255)
    return pixel_lab.reshape(-1, pixel_lab.shape[-1])


def make_img(colors, counts):
    """
    Create image from colors

    Parameters
    ----------
    colors: ndarray
        Color in RGB
    counts: ndarray
        Number of data points in each color cluster

    Returns
    ------
    img: Image
        Generated image
    
    """
    img_size = 512, 512
    n_clusters = len(colors)
    lengths = (
        ((counts / np.sum(counts)) + (1.0 / n_clusters)) / 2.0 * img_size[0]
    ).astype(np.uint16)
    # Ensure sum of lengths equals img_size[0]
    lengths[0] = lengths[0] + (img_size[0] - np.sum(lengths))
    pixel_group = np.array(
        [np.tile(colors[i], (lengths[i], img_size[1], 1)) for i in range(n_clusters)]
    )
    pixel_rgb = np.transpose(np.concatenate(pixel_group), (1, 0, 2))
    return Image.fromarray(pixel_rgb, mode="RGB")


def get_hex_string(rgb_arr):
    """
    Covert RGB color to HEX values

    Parameters
    ----------
    rgb_arr: ndarray
        Color in RGB

    Returns
    ------
    hex_names: str
        HEX values of color
    
    """
    def int2hex(integer):
        hex_string = hex(integer)[2:]
        if len(hex_string) < 2:
            return "0" + hex_string
        return hex_string

    return "".join(np.vectorize(int2hex)(rgb_arr)).upper()


def cluster_kmeans(data, n_clusters):
    """
    Partition data with k-means clustering

    Parameters
    ----------
    data: ndarray
        Data points
    n_clusters: int
        Number of clusters

    Returns
    ------
    centers: ndarray
        Clusters centers
    labels: ndarray
        Center label of every data point
    
    """
    kmeans = KMeans(n_clusters)
    labels = kmeans.fit_predict(data)
    centers = kmeans.cluster_centers_
    return centers, labels


def compute_medoid(data):
    """
    Get medoid of data

    Parameters
    ----------
    data: ndarray
        Data points

    Returns
    ------
    medoid: ndarray
        Medoid
    
    """
    dist_mat = pairwise_distances(data)
    return data[np.argmin(dist_mat.sum(axis=0))]


def cluster_agglo(data, n_clusters):
    """
    Partition data with agglomerative clustering

    Parameters
    ----------
    data: ndarray
        Data points
    n_clusters: int
        Number of clusters

    Returns
    ------
    centers: ndarray
        Clusters centers
    labels: ndarray
        Center label of every data point
    
    """
    ac = AgglomerativeClustering(n_clusters)
    labels = ac.fit_predict(data)
    print("Completed agglomerative clustering")
    centers = np.empty([n_clusters, 3])
    for i in range(n_clusters):
        centers[i] = compute_medoid(data[labels == i])
    return centers, labels


def get_cluster(centers, labels):
    """
    Sort cluster centers and count number of labels

    Parameters
    ----------
    centers: ndarray
        Clusters centers
    labels: ndarray
        Center label of every data point

    Returns
    ------
    sort_centers: ndarray
        Clusters centers sorted by number of label descending
    sort_labels: ndarray
        Sorted center label of every data point
    sort_counts: ndarray
        Number of data points of sorted centers
    
    """
    _, counts = np.unique(labels, return_counts=True)
    sort_idx = (-counts).argsort()
    sort_labels = np.vectorize(lambda i: list(sort_idx).index(i))(labels)
    return centers[sort_idx], sort_labels, counts[sort_idx]


def get_palette(im, k):
    """
    Create a palette from an image

    Parameters
    ----------
    im: Image
        Image to create palette from
    k: int
        Number of pallete colors
        If None or k is outside of the range [2, 10], uses default_k as k
    
    Returns
    ------
    im_output: Image
        Image of palette colors
    hex_colors: ndarray
        Palette colors in HEX values
    
    """
    if k is None:
        k = default_k
    elif k < 2 or k > 10:
        k = default_k
    data = get_lab_data(im)
    print("Get {} clusters".format(k))
    centers, labels = cluster_agglo(data, k)
    sorted_centers, _, counts = get_cluster(centers, labels)
    # Range of RGB in Pillow is [0, 255], that in skimage is [0, 1]
    centers_rgb = (255 * lab2rgb(sorted_centers)).astype(np.uint8)
    print("Clusters are")
    print(centers_rgb)
    return (
        make_img(centers_rgb, counts),
        np.apply_along_axis(get_hex_string, 1, centers_rgb),
    )


def get_palette_plot(im, k):
    """
    Create a palette from an image and plot clusters in 3D 

    Parameters
    ----------
    img: Image
        Image to create palette.
    k: int
        Number of pallete colors.
        If None or k is outside of the range [2, 10], uses default_k as k
    
    Returns
    ------
    im_output: Image
        Image of palette colors
    hex_colors: ndarray
        Palette colors in HEX values
    
    """
    if k is None:
        k = default_k
    elif k < 2 or k > 10:
        k = default_k
    data = get_lab_data(im)
    print("Get {} clusters".format(k))
    centers, labels = cluster_agglo(data, k)
    sorted_centers, sorted_labels, counts = get_cluster(centers, labels)
    # Range of RGB in Pillow is [0, 255], that in skimage is [0, 1]
    centers_rgb = (255 * lab2rgb(sorted_centers)).astype(np.uint8)
    print("Clusters in RGB are")
    print(centers_rgb)
    centers_hex = np.apply_along_axis(get_hex_string, 1, centers_rgb)
    plot_3d(data, sorted_labels, centers_hex)
    return (
        make_img(centers_rgb, counts),
        centers_hex,
    )


def plot_3d(data, labels, centers_hex):
    """
    Plot clustered data in 3D 

    Parameters
    ----------
    data: ndarray
        Data points
    labels: ndarray
        Labels of every data point
    centers_hex: ndarray
        Color in HEX values
    
    """
    l, a, b = np.transpose(data)
    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=a,
                y=b,
                z=l,
                mode="markers",
                marker={
                    "size": 3,
                    "color": np.vectorize(lambda hex: "#" + hex)(centers_hex)[labels],
                    "opacity": 0.1,
                },
            )
        ]
    )
    fig.update_layout(
        scene={"xaxis_title": "a", "yaxis_title": "b", "zaxis_title": "L",}
    )
    fig.show()


def get_image_from_url(url):
    """
    Download and create image

    Parameters
    ----------
    url: str
        Image link
    
    Returns
    ------
    im: Image
        Image downloaded
    
    """
    print("Get image from ", url)
    response = requests.get(url)
    return Image.open(BytesIO(response.content))
