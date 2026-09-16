import numpy as np
import pytest
from dataset_tools.sample import split_at,dhash
from dataset_tools.label_qc import audit
from perception.geometry import Letterbox,prepare_rgb,tensor_layout


@pytest.mark.parametrize("dims",[(720,1280),(1080,1920),(1080,2400),(1440,3200),(2208,1840),(1920,1080)])
def test_letterbox_round_trip(dims):
    w,h=dims
    tr=Letterbox(w,h,320,320)
    for x,y in [(0,0),(w/2,h/2),(w,h),(w*.12,h*.86)]:
        assert tr.to_source(*tr.to_model(x,y))==pytest.approx((x,y))


def test_tensor_layout_and_channels():
    rgb=np.array([[[255,0,128],[0,255,0]],[[0,0,255],[255,255,255]]],dtype=np.uint8)
    a,_=prepare_rgb(rgb,[1,3,8,8]); b,_=prepare_rgb(rgb,[1,8,8,3])
    assert np.allclose(a.transpose(0,2,3,1),b)
    assert a[0,0,0,0]==1 and a[0,1,0,0]==0
    assert a[0,2,0,0]==pytest.approx(128/255)


@pytest.mark.parametrize("shape",[[1,3,3,3],[2,3,640,640],[1,4,5,6],[1,3,-1,-1]])
def test_unsupported_tensors_rejected(shape):
    with pytest.raises(ValueError): tensor_layout(shape)


def test_letterbox_padding_not_stretched():
    rgb=np.zeros((8,2,3),dtype=np.uint8)
    out,tr=prepare_rgb(rgb,[1,3,8,8])
    assert np.allclose(out[:,:,:,:3],114/255)
    assert np.all(out[:,:,:,3:5]==0)


def test_split_embargo():
    assert split_at(0,1000)=="train"
    assert split_at(699,1000)=="embargo"
    assert split_at(720,1000)=="val"
    assert split_at(850,1000)=="embargo"
    assert split_at(900,1000)=="test"


def test_pseudo_label_test_quarantine_and_quality():
    label=dict(sample_id="a",**{"class":"goon"},box=[.1,.2,.3,.4],teacher="teacher",teacher_revision="sha",
               confidence=.99,track_confirmations=3,appearance_consistency=.95,temporal_iou=.8)
    result=audit([dict(id="a",split="test")],[label])
    assert not result["accepted"] and result["rejected"][0]["reason"]=="test_is_quarantined"
    result=audit([dict(id="a",split="train")],[label,label,dict(label,box=[1,2,3,4])])
    assert len(result["accepted"])==1 and len(result["rejected"])==2
    assert result["accepted"][0]["label_status"]=="pseudo" and result["ground_truth_count"]==0


def test_duplicate_hash_stable():
    frame=np.arange(30*40*3,dtype=np.uint8).reshape(30,40,3)
    assert dhash(frame)==dhash(frame.copy())
