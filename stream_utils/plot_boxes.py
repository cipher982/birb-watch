import cv2


def plot_boxes(model, results, frame):
    labels, cord = results
    n = len(labels)
    x_shape, y_shape = frame.shape[1], frame.shape[0]
    bird_boxes = []
    for i in range(n):
        row = cord[i]
        x1 = int(row[0] * x_shape)
        y1 = int(row[1] * y_shape)
        x2 = int(row[2] * x_shape)
        y2 = int(row[3] * y_shape)
        bgr = (0, 255, 0)  # color of the box
        classes = model.names  # Get the name of label index
        label_font = cv2.FONT_HERSHEY_SIMPLEX  # Font for the label.
        if row[4] < 0.2 and classes[labels[i]] == "bird":
            continue
        if row[4] < 0.6 and classes[labels[i]] != "bird":
            continue
        cv2.rectangle(frame, (x1, y1), (x2, y2), bgr, 2)  # Plot the boxes
        cv2.putText(
            frame, classes[labels[i]], (x1, y1), label_font, 0.9, bgr, 2
        )  # Put a label over box.

        if classes[labels[i]] == "bird":
            print("Found bird")
            bird_box = frame[y1:y2, x1:x2]
            bird_boxes.append(bird_box)

    return frame, bird_boxes
