import os

import numpy as np
import onnxruntime
import torch

from utils.onnx import letterbox, non_max_suppression


class YOLOv5ONNX:
    def __init__(self, model_path):
        self.model = onnxruntime.InferenceSession(model_path)

    def score_frame(self, frame, half=False):
        # img = letterbox(img0, new_shape=(960, 960))[0]
        img = np.moveaxis(frame, -1, 0)
        img = torch.from_numpy(img).to("cpu")
        img = img.half() if half else img.float()
        img /= 255  # 0 - 255 to 0.0 - 1.0
        if len(img.shape) == 3:
            img = img[None]
        # img = img.numpy()

        outputs = self.model.get_outputs()
        inputs = self.model.inputs()
        y = self.model.run([outputs[0].name], {inputs[0].name: img})[0]
        y = torch.tensor(y) if isinstance(y, np.ndarray) else y

        pred = non_max_suppression(y)

        return pred

    def show_img(
        pred,
        img0,
        img,
        names,
        hide_labels=False,
        hide_conf=False,
    ):
        s = f"image_"
        for i, det in enumerate(pred):  # per image
            print(det)
            im0, frame = img0.copy(), img
            # save_path = str(save_dir / p.name)  # im.jpg
            s += "%gx%g " % img.shape[2:]  # print string

            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0  # for save_crop
            annotator = Annotator(im0, line_width=3, example=str(names))

            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                    print(s)
                # Write results
                for *xyxy, conf, cls in reversed(det):
                    if view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = (
                            None
                            if hide_labels
                            else (names[c] if hide_conf else f"{names[c]} {conf:.2f}")
                        )
                        annotator.box_label(xyxy, label, color=colors(c, True))

            im0 = annotator.result()
            plt.imshow(im0)
