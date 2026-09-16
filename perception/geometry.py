from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class Letterbox:
    source_w: int
    source_h: int
    target_w: int
    target_h: int

    def __post_init__(self):
        if min(self.source_w,self.source_h,self.target_w,self.target_h)<=0:
            raise ValueError("Dimensions must be positive")

    @property
    def scale(self):
        return min(self.target_w/self.source_w,self.target_h/self.source_h)

    @property
    def padding(self):
        return ((self.target_w-self.source_w*self.scale)/2,
                (self.target_h-self.source_h*self.scale)/2)

    def to_model(self,x,y):
        px,py=self.padding
        return x*self.scale+px,y*self.scale+py

    def to_source(self,x,y):
        px,py=self.padding
        return (x-px)/self.scale,(y-py)/self.scale


def tensor_layout(shape: list[int]) -> str:
    if len(shape)!=4 or shape[0]!=1:
        raise ValueError("Expected a fixed batch-one image tensor")
    first,last=shape[1]==3,shape[-1]==3
    if first==last or min(shape)<=0:
        raise ValueError("Ambiguous or unsupported RGB tensor shape")
    return "NCHW" if first else "NHWC"


def prepare_rgb(rgb: np.ndarray, shape: list[int], mean=(0.,0.,0.), std=(1.,1.,1.)):
    """Shared nearest-pixel letterbox convention, explicit RGB float32 normalization.

    Padding = 114/255 before normalization. Pixel centers are inverse mapped.
    Android uses the same convention to permit strict input parity fixtures.
    """
    layout=tensor_layout(shape)
    th,tw=(shape[2],shape[3]) if layout=="NCHW" else (shape[1],shape[2])
    if rgb.ndim!=3 or rgb.shape[2]!=3 or any(s<=0 for s in std):
        raise ValueError("Invalid RGB image or normalization")
    sh,sw=rgb.shape[:2]
    transform=Letterbox(sw,sh,tw,th)
    px,py=transform.padding
    xs=(np.arange(tw)+.5-px)/transform.scale
    ys=(np.arange(th)+.5-py)/transform.scale
    valid=(ys[:,None]>=0)&(ys[:,None]<sh)&(xs[None,:]>=0)&(xs[None,:]<sw)
    out=np.full((th,tw,3),114,dtype=np.float32)
    sampled=rgb[np.clip(np.floor(ys).astype(int),0,sh-1)[:,None],np.clip(np.floor(xs).astype(int),0,sw-1)[None,:]]
    out[valid]=sampled[valid]
    out=(out/255-np.asarray(mean,dtype=np.float32))/np.asarray(std,dtype=np.float32)
    return (out.transpose(2,0,1) if layout=="NCHW" else out)[None].astype(np.float32),transform
