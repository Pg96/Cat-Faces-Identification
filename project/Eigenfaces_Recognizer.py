import os

import cv2.cv2 as cv
import numpy as np


def norm_0_255(source: np.ndarray):
    src = source.copy()
    dst = None

    shape = source.shape
    if len(shape) == 2:  # single channel
        dst = cv.normalize(src, dst, 0, 255, cv.NORM_MINMAX, cv.CV_8UC1)
    elif len(shape) > 2 and shape[2] == 3:  # 3 channels
        dst = cv.normalize(src, dst, 0, 255, cv.NORM_MINMAX, cv.CV_8UC3)
    else:
        dst = src.copy()

    return dst


def read_csv(filename):
    labels = []
    faces = []

    with open(filename, "r+") as file:
        # {BEGIN} TOREMOVE
        dic = dict()
        # {END} TOREMOVE

        for line in file.readlines():
            spl = line.split(";")

            # TODO resize images if using i.jpg

            label = int(spl[1])

            # {BEGIN} TOREMOVE
            if label not in dic.keys():
                dic[label] = 1
            elif dic[label] > 10:
                continue
            dic[label] += 1
            # {END} TOREMOVE

            faces.append(cv.imread(spl[0], 0))
            labels.append(label)

    # {BEGIN} TOREMOVE
    print(dic)
    # {END} TOREMOVE
    return faces, labels


def train_recongizer(csv_filename):
    faces, labels = read_csv(csv_filename)

    print("Total faces: {0}\nTotal labels: {1}".format(len(faces), len(labels)))

    height = faces[0].shape[0]

    model: cv.face_BasicFaceRecognizer = cv.face.EigenFaceRecognizer_create()  # TODO check params

    # If this gives problems, just use faces instead of array
    model.train(faces, np.array(labels))

    print("train finished")

    return model, height


def predict(model: cv.face_BasicFaceRecognizer, height, face, sample_label=None,
            save_dir=None,
            show_mean=False,
            save_mean=False,
            show_faces=False,
            save_faces=False
            ):

    if not os.path.exists(face):
        raise RuntimeError("File {} does not exist!".format(face))

    input_face = cv.imread(face, 0)
    prediction = model.predict(input_face)

    if sample_label is not None:
        print("Predicted class = {0} with confidence = {1}; Actual class = {2}.\n\t Result: {3}"
              .format(prediction[0], prediction[1], sample_label,
                      "Success!" if prediction[0] == sample_label else "Failure!"))

    eigenvalues: np.ndarray = model.getEigenValues()
    eigenvectors: np.ndarray = model.getEigenVectors()
    mean = model.getMean()

    # normalized_mean = norm_0_255(mean.reshape(1, height))

    # reshaped = np.reshape(mean, (1, height))
    # print(mean.shape)
    reshaped = mean.reshape(height, -1)

    normalized_mean = norm_0_255(reshaped)

    if show_mean:
        show_image(normalized_mean)

    elif save_mean and save_dir is not None:
        cv.imwrite("{}_mean.jsp", normalized_mean)

    if show_faces or save_faces:
        for i in range(0, min(10, len(eigenvectors.T))):
            msg = "Eigenvalue #{0} ? {1}".format(i, eigenvalues.item(i))
            print(msg)

            ev = eigenvectors[:, i].copy()
            grayscale = norm_0_255(ev.reshape(height, -1))
            cgrayscale = cv.applyColorMap(grayscale, cv.COLORMAP_JET)

            if show_faces:
                show_image(cgrayscale)
            elif save_faces:
                cv.imwrite("eigenface_{}".format(i), norm_0_255(cgrayscale))

    # TODO Think about writing the reconstruction part


def show_image(image):
    cv.namedWindow('output', cv.WINDOW_NORMAL)
    # cv.resizeWindow('win', 1980, 1800)

    cv.imshow('output', image)
    cv.waitKey(0)
    cv.destroyAllWindows()


if __name__ == '__main__':
    mod, hei = train_recongizer("./subjects_aligned.csv")
    # TODO implement savemodel & loadmodel
    predict(model=mod, height=hei, face="../images/dataset/cropped/t/27_cropped_aligned.jpg", sample_label=1,
            show_mean=True, show_faces=True)
    predict(model=mod, height=hei, face="../images/dataset/cropped/c/9_cropped_aligned.jpeg", sample_label=0,
            show_mean=True, show_faces=True)
    # "../images/dataset/cropped/", "../images/output/eigenfaces/"
