import rawpy, numpy as np, imagej
with rawpy.imread('RAW.tif') as raw:
    r = raw.raw_image_visible.astype(np.float32)
    rgb = raw.postprocess(demosaic_algorithm=rawpy.DemosaicAlgorithm(0), output_bps=16, no_auto_bright=True, gamma=(1,1))
    r_channel = rgb[:, :, 0]
    