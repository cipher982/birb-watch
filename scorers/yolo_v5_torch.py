import torch


class YOLOv5Torch:
    def __init__(self):
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)

    def score_frame(self, frame):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(device)
        frame = [frame]
        results = self.model(frame)
        labels = results.xyxyn[0][:, -1].cpu().numpy().astype(int)
        cord = results.xyxyn[0][:, :-1].cpu().numpy()
        return labels, cord
